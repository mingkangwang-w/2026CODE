# -*- coding: utf-8 -*-
"""问题 1：预热平衡阶段（t<=1800 s）的温度场与水分场。

附录 2 常物性：rho=820 kg/m^3、cp=2600 J/(kg·K)、k=0.36 W/(m·K)（标量，不随 C 变）；
水分扩散系数 D = 7e-9*exp(-0.89/C)，只依赖 C。
半解析通道：Bessel 特征展开 + Duhamel 叠加（对分段线性环境温度逐模态精确递推）。
"""
from __future__ import annotations

import json

import numpy as np
from scipy.optimize import brentq
from scipy.special import j0, j1, jn_zeros

import data_io
import params as P
import properties as PR
import resultio as RIO
import solver as SV
import xlsx_writer as XW

PROPS = PR.APPENDIX2
PROPS_FORMULA_TAG = "附录2 常物性 rho=820, cp=2600, k=0.36; D = 7e-9*exp(-0.89/C)"
# A_n 按 mu_n^{-3/2} 交替衰减，sum A_n = 1 的截断误差需压到 1e-5 以下才不污染
# 与有限体积解的对照（目标偏差量级 1e-3 K），故取上千阶模态。
N_MODES = 2000


def bessel_eigenvalues(bi: float, n_modes: int = N_MODES) -> np.ndarray:
    """解 mu_n J_1(mu_n) = Bi_h J_0(mu_n)，根在 J_0 相邻零点间交替变号。"""
    def residual(mu):
        return mu * j1(mu) - bi * j0(mu)

    brackets = np.concatenate(([1e-9], jn_zeros(0, n_modes + 1)))
    roots = []
    for lo, hi in zip(brackets[:-1], brackets[1:]):
        f_lo, f_hi = residual(lo), residual(hi)
        if f_lo == 0.0:
            roots.append(lo)
        elif f_lo * f_hi < 0.0:
            roots.append(brentq(residual, lo, hi, xtol=1e-14, rtol=8.9e-16))
        if len(roots) == n_modes:
            break
    if len(roots) < n_modes:
        raise AssertionError(f"仅求得 {len(roots)} 个特征值，少于 {n_modes}")
    return np.array(roots)


def modal_amplitudes(mu: np.ndarray) -> np.ndarray:
    """A_n = 2 J_1(mu_n) / (mu_n [J_0^2(mu_n)+J_1^2(mu_n)])，满足 sum A_n J_0 = 1。"""
    return 2.0 * j1(mu) / (mu * (j0(mu) ** 2 + j1(mu) ** 2))


def bessel_duhamel_temperature(t_query, r_query_m, env, n_modes: int = N_MODES):
    """Bessel 展开 + Duhamel 叠加的半解析温度场（独立通道，不借用数值解）。

    每个模态满足 dc_n/dt = -lam_n (c_n - A_n g(t))，g(t)=T_inf(t)-T0 在附件 1 的
    60 s 网格上分段线性，故区间内可逐模态精确积分（无时间离散误差）。
    """
    bi = P.BI_H_A2
    mu = bessel_eigenvalues(bi, n_modes)
    amp = modal_amplitudes(mu)
    lam = mu ** 2 * P.ALPHA_A2 / P.R0_M ** 2
    unity_gap = abs(float(np.sum(amp)) - 1.0)   # r=0 处 J_0=1，故 sum A_n 应为 1
    if unity_gap > 1e-5:
        raise AssertionError(f"sum A_n 与 1 相差 {unity_gap:.3e}，模态数不足或幅值公式有误")

    knots = np.unique(np.concatenate((env.t[env.t <= max(np.max(t_query), 0.0) + 1e-9],
                                      np.atleast_1d(t_query).astype(float), [0.0])))
    knots.sort()
    g_knots = env.T_inf(knots) - P.T0_DEGC
    coef = np.zeros(n_modes)
    out = {}
    query_set = {float(v) for v in np.atleast_1d(t_query)}
    if 0.0 in query_set:
        out[0.0] = np.full(np.size(r_query_m), P.T0_DEGC, dtype=float)
    for i in range(knots.size - 1):
        dt_seg = knots[i + 1] - knots[i]
        if dt_seg <= 0.0:
            continue
        slope = (g_knots[i + 1] - g_knots[i]) / dt_seg
        decay = np.exp(-lam * dt_seg)
        target = amp * g_knots[i + 1] - amp * slope / lam
        coef = target + decay * (coef - amp * g_knots[i] + amp * slope / lam)
        t_here = float(knots[i + 1])
        if t_here in query_set:
            basis = j0(np.outer(np.atleast_1d(r_query_m) / P.R0_M, mu))
            out[t_here] = P.T0_DEGC + basis @ coef
    return out


def run(n_cells=None, dt=None):
    """生产求解：附录 2 常物性，t<=1800 s，输出步长 1 s / 0.1 cm。"""
    n_cells = P.N_CELLS if n_cells is None else n_cells
    dt = P.DT_Q1_S if dt is None else dt
    env = data_io.get_env()
    hist = SV.simulate_fixed(PROPS, dt, env, n_cells=n_cells,
                             t_end_s=P.Q1_FILE_T_END_S, out_dt_s=P.Q1_FILE_DT_S)
    return hist, env


def _table_stride(hist):
    """表 1/2 的 5 个径向位置在节点网格上的步长（0.5 cm 间距，N=80 时为 20）。"""
    dr_cm = P.R0_CM / (len(hist.C_fields[0]) - 1)
    stride = int(round(P.Q1_TABLE_RADII_CM[1] / dr_cm))
    if abs(stride * dr_cm - P.Q1_TABLE_RADII_CM[1]) > 1e-12:
        raise AssertionError(f"表 1/2 径向间距 {P.Q1_TABLE_RADII_CM[1]} cm 不落在节点上")
    return stride


def _paper_tables(hist):
    """表 1（温度）与表 2（水分浓度）：指定 7 个非等间隔时刻 × 5 个径向位置。"""
    times = np.array(hist.times)
    stride = _table_stride(hist)
    tables = {"table1_temperature": [], "table2_moisture": []}
    for t_label in P.Q1_TABLE_TIMES_S:
        idx = int(np.argmin(np.abs(times - t_label)))
        if abs(times[idx] - t_label) > 1e-9:
            raise AssertionError(f"表 1/2 时刻 {t_label} s 不在输出网格上")
        tables["table1_temperature"].append(
            {"t_s": t_label, "values": [round(float(v), P.DECIMALS)
                                        for v in hist.T_fields[idx][::stride]]})
        tables["table2_moisture"].append(
            {"t_s": t_label, "values": [round(float(v), P.DECIMALS)
                                        for v in hist.C_fields[idx][::stride]]})
    return tables


def _analytic_gap(hist, env):
    """bd_q1_analytic_gap：与 Bessel–Duhamel 半解析解在 5 个径向位置的最大偏差。"""
    radii_m = np.array(P.Q1_TABLE_RADII_CM) / P.CM_PER_M
    query = [float(t) for t in P.Q1_TABLE_TIMES_S]
    analytic = bessel_duhamel_temperature(query, radii_m, env)
    times = np.array(hist.times)
    stride = _table_stride(hist)
    gaps, detail = [], {}
    for t_label in query:
        idx = int(np.argmin(np.abs(times - t_label)))
        numeric = hist.T_fields[idx][::stride]
        dev = np.abs(numeric - analytic[t_label])
        gaps.append(float(dev.max()))
        detail[f"{t_label:.0f}s"] = {
            "numeric": [round(float(v), 6) for v in numeric],
            "analytic": [round(float(v), 6) for v in analytic[t_label]],
            "max_abs_dev": float(dev.max()),
        }
    return float(max(gaps)), detail


def validate_constraints(hist, env, tables, xlsx_report):
    """B-01/02/04/06/08/09/10/11/12/19/23/28/29 在问题 1 的落点，全部硬断言。"""
    T_all = np.array(hist.T_fields)
    C_all = np.array(hist.C_fields)
    if not (np.isfinite(T_all).all() and np.isfinite(C_all).all()):
        raise AssertionError("B-19：出现非有限值")
    if not (C_all >= -1e-9).all() or not (C_all <= P.C0 + 1e-9).all():
        raise AssertionError(f"B-10：C 越界 [{C_all.min()}, {C_all.max()}]")
    T_inf_max = float(np.max(hist.T_inf_hist))
    if not (T_all >= 27.0).all() or not (T_all <= T_inf_max + 1.0).all():
        raise AssertionError(f"B-10：T 越界 [{T_all.min()}, {T_all.max()}]")
    if not (np.diff(C_all, axis=1) <= 1e-12).all():
        raise AssertionError("B-11：C 沿 r 非单调非增")
    if hist.n_center_violations != 0 or hist.argmax_max != 0:
        raise AssertionError(
            f"bd_center_is_wettest：argmax_r C = {hist.argmax_max}，"
            f"max_r C - C[0] = {hist.max_center_deficit:.3e}")
    if np.ptp(PROPS.rho(C_all)) != 0.0 or np.ptp(PROPS.cp(C_all)) != 0.0 \
            or np.ptp(PROPS.k(C_all)) != 0.0:
        raise AssertionError("B-04：问题 1 物性不是常数")
    eps_final = hist.eps_M[-1]
    if not eps_final < P.EPS_M_LIMIT:
        raise AssertionError(f"B-12：eps_M={eps_final:.3e} 超出 {P.EPS_M_LIMIT}")
    T_end, C_end = hist.T_fields[-1], hist.C_fields[-1]
    res_T = SV.robin_flux_residual(T_end, PROPS.k(C_end), P.R0_M, P.H_CONV,
                                   hist.T_inf_hist[-1], n_cells=len(T_end) - 1)
    res_C = SV.robin_flux_residual(C_end, PROPS.D(C_end, T_end), P.R0_M, P.HM_CONV,
                                   hist.C_inf_hist[-1], n_cells=len(C_end) - 1)
    # B-06 的判据写在温度上（阈值 1e-3）。水分同法核对，但其边界层厚度小于一个网格，
    # 三点重建的 O(δ²) 截断在 N=80 上约 1.4e-3；实测收敛阶 1.68→1.82→1.91（N=40→320），
    # 属离散重建误差而非通量表达式错误，故水分取 1e-2。
    if not res_T < 1e-3:
        raise AssertionError(f"B-06：温度 Robin 通量残差 {res_T:.3e} 超出 1e-3")
    if not res_C < 1e-2:
        raise AssertionError(f"B-06：水分 Robin 通量残差 {res_C:.3e} 超出 1e-2")
    sym_T = SV.center_symmetry(T_end, P.R0_M, n_cells=len(T_end) - 1)
    sym_C = SV.center_symmetry(C_end, P.R0_M, n_cells=len(C_end) - 1)
    if not (sym_T["ratio"] < 1e-2 and sym_C["ratio"] < 1e-2):
        raise AssertionError(f"B-09：中心对称性比值 T={sym_T['ratio']:.3e}, C={sym_C['ratio']:.3e}")
    if [row["t_s"] for row in tables["table1_temperature"]] != P.Q1_TABLE_TIMES_S:
        raise AssertionError("B-23：表 1 时刻标签与题面不符")
    if xlsx_report["温度"]["dt_s"] != P.Q1_FILE_DT_S:
        raise AssertionError("B-29：result1.xlsx 时间步长不为 1 s")
    return {"eps_M": eps_final, "robin_res_T": res_T, "robin_res_C": res_C,
            "center_sym_T": sym_T, "center_sym_C": sym_C,
            "T_range": [float(T_all.min()), float(T_all.max())],
            "C_range": [float(C_all.min()), float(C_all.max())],
            "max_diff_C": hist.max_diff_C, "argmax_max": hist.argmax_max,
            "max_center_deficit": hist.max_center_deficit,
            "n_center_violations": hist.n_center_violations}


def validate_capability(hist, env, tables, xlsx_report, analytic_gap):
    """CAPABILITY_CHECKLIST P1-C1 ~ P1-C4 的 falsifiable_check，越界即 raise。"""
    # P1-C1 (a) 分式指数；(b) 常物性标量
    if "exp(-0.89/" not in P.FORMULA_D_A2 or "exp(-0.89*" in P.FORMULA_D_A2:
        raise AssertionError("P1-C1(a)：D 未写成分式指数")
    if not PROPS.is_constant():
        raise AssertionError("P1-C1(b)：问题 1 引用了 C 依赖物性")
    if (PROPS.rho_const, PROPS.cp_const, PROPS.k_const) != (820.0, 2600.0, 0.36):
        raise AssertionError("P1-C1(b)：附录 2 常物性数值不符")
    # P1-C1 (d) 中心对称与物理界限已在 validate_constraints 内断言
    # P1-C2：表格标签与数值一致性
    if [row["t_s"] for row in tables["table2_moisture"]] != P.Q1_TABLE_TIMES_S:
        raise AssertionError("P1-C2：表 2 时刻标签不符")
    for row in tables["table1_temperature"] + tables["table2_moisture"]:
        if len(row["values"]) != len(P.Q1_TABLE_RADII_CM):
            raise AssertionError("P1-C2：表格列数不等于 5 个径向位置")
    times = np.array(hist.times)
    stride = _table_stride(hist)
    for row in tables["table1_temperature"]:
        idx = int(np.argmin(np.abs(times - row["t_s"])))
        ref = hist.T_fields[idx][::stride]
        if float(np.max(np.abs(np.array(row["values"]) - ref))) > 1e-4:
            raise AssertionError("P1-C2：表 1 数值与完整场不一致（容差 1e-4）")
    # P1-C3/P1-C4：交付结构
    if list(xlsx_report["sheets"]) != list(P.Q1_SHEETS):
        raise AssertionError("P1-C4：result1.xlsx 工作表名与模板不符")
    for sheet in P.Q1_SHEETS:
        if xlsx_report[sheet]["n_cols"] != P.N_OUT_COLS:
            raise AssertionError("P1-C4：result1.xlsx 列数不为 21")
    # bd_q1_analytic_gap
    if not analytic_gap < 0.01:
        raise AssertionError(f"bd_q1_analytic_gap：偏差 {analytic_gap:.4f} K 超过 0.01 K")
    return True


def main():
    hist, env = run()
    tables = _paper_tables(hist)
    analytic_gap, analytic_detail = _analytic_gap(hist, env)

    T_rows = SV.sample_columns(np.array(hist.T_fields))
    C_rows = SV.sample_columns(np.array(hist.C_fields))
    path = XW.write_two_sheet_result(P.OUTPUT_DIR / "result1.xlsx", hist.times,
                                    P.OUT_RADII_CM, T_rows, C_rows)
    xlsx_report = XW.verify_written(path, P.Q1_SHEETS, P.Q1_FILE_DT_S, P.N_OUT_COLS)

    diag = validate_constraints(hist, env, tables, xlsx_report)
    validate_capability(hist, env, tables, xlsx_report, analytic_gap)
    explicit = SV.explicit_cross_check(PROPS, P.DT_Q1_S, env, P.Q1_FILE_T_END_S)
    explicit_gap = float(np.max(np.abs(explicit["T_final"] - hist.T_fields[-1])))
    explicit_gap_C = float(np.max(np.abs(explicit["C_final"] - hist.C_fields[-1])))

    payload = {
        "problem": 1,
        "title": "预热平衡阶段的温度场与水分场",
        "method": "守恒型有限体积 + 向后 Euler/Picard；附录 2 常物性",
        "property_group": PROPS_FORMULA_TAG,
        "grid": {"n_cells": P.N_CELLS, "dt_s": P.DT_Q1_S, "dr_cm": P.R0_CM / P.N_CELLS,
                 "out_dt_s": P.Q1_FILE_DT_S, "out_dr_cm": P.Q1_FILE_DR_CM,
                 "n_steps": hist.n_steps},
        "output_radii_cm": P.OUT_RADII_CM,
        "paper_tables": tables,
        "table_radii_cm": P.Q1_TABLE_RADII_CM,
        "center_series": {"times_s": hist.times,
                          "T": [float(f[0]) for f in hist.T_fields],
                          "C": [float(f[0]) for f in hist.C_fields]},
        "surface_series": {"times_s": hist.times,
                           "T": [float(f[-1]) for f in hist.T_fields],
                           "C": [float(f[-1]) for f in hist.C_fields]},
        "env_series": {"times_s": hist.times, "T_inf": hist.T_inf_hist,
                       "C_inf": hist.C_inf_hist},
        "field_T": RIO.field_grid(hist.times, hist.T_fields, every=10),
        "field_C": RIO.field_grid(hist.times, hist.C_fields, every=10),
        "mass_balance": {"times_s": hist.times, "M": hist.M_hist, "Q": hist.Q_hist,
                         "eps_M": hist.eps_M},
        "analytic_validation": {"n_modes": N_MODES, "Bi_h": P.BI_H_A2,
                                "max_abs_dev_K": analytic_gap, "detail": analytic_detail},
        "explicit_cross_check": {"dt_used_s": explicit["dt_used_s"],
                                 "dt_stable_s": explicit["dt_stable_s"],
                                 "dt_row_bound_s": explicit["dt_row_bound_s"],
                                 "n_steps": explicit["n_steps"],
                                 "max_abs_dev_T_K": explicit_gap,
                                 "max_abs_dev_C": explicit_gap_C},
        "characteristic_times": {"tau_heat_s": P.TAU_HEAT_A2_S, "tau_mass_s": P.TAU_MASS_A2_S,
                                 "alpha_m2_s": P.ALPHA_A2, "Bi_h": P.BI_H_A2,
                                 "Bi_m": P.BI_M_A2},
        "diagnostics": diag,
        "xlsx_report": xlsx_report,
        "summary": {
            "T_center_1800s": float(hist.T_fields[-1][0]),
            "T_surface_1800s": float(hist.T_fields[-1][-1]),
            "C_center_1800s": float(hist.C_fields[-1][0]),
            "C_surface_1800s": float(hist.C_fields[-1][-1]),
            "eps_M": diag["eps_M"],
            "analytic_gap_K": analytic_gap,
        },
    }
    out_path, nbytes = RIO.write_results("problem_1_results", payload)
    print(f"[problem_1] 写出 {out_path.name} ({nbytes} bytes)、{path.name}")
    print(f"[problem_1] t=1800 s 温度 = {[round(float(v), 4) for v in T_rows[-1][::5]]}")
    print(f"[problem_1] t=1800 s 水分 = {[round(float(v), 4) for v in C_rows[-1][::5]]}")
    print(f"[problem_1] result1.xlsx 行数 = "
          f"{xlsx_report[P.Q1_SHEETS[0]]['n_rows']}，"
          f"t: {xlsx_report[P.Q1_SHEETS[0]]['t_first']} → "
          f"{xlsx_report[P.Q1_SHEETS[0]]['t_last']} s")
    print(f"[problem_1] eps_M = {diag['eps_M']:.3e}, 半解析偏差 = {analytic_gap:.4f} K")
    print(f"[problem_1] 显式交叉验证偏差 T={explicit_gap:.4f} K, C={explicit_gap_C:.3e}")
    return payload


if __name__ == "__main__":
    main()
