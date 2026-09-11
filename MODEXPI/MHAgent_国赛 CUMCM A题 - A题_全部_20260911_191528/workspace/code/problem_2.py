# -*- coding: utf-8 -*-
"""问题 2：全过程变物性双向强耦合模型（附录 3），输出截取前 3 h。

附录 3：rho=650+128C、cp=1450+2736C/(C+1)、k=0.21+0.38C/(C+1)，
D = 2.4e-3*exp(-0.45/C)*exp(-3850/T_K)，T_K = T + 273.15。
控制方程形式唯一，预热段与恒温段的差异只体现在边界驱动上（P2-C2(c)）；
求解器不含硬编码终止时刻，可直接推进过 1e5 s 供问题 3 复用（P2-C1(c)）。
"""
from __future__ import annotations

import numpy as np

import data_io
import params as P
import properties as PR
import resultio as RIO
import solver as SV
import xlsx_writer as XW

PROPS = PR.APPENDIX3
PROPS_FORMULA_TAG = (f"附录3 变物性 {P.FORMULA_PROPS_A3}; {P.FORMULA_D_A3}")
LONG_RUN_T_END_S = 1.1e5       # P2-C1(c)：同一求解器直接推进过 1e5 s，不改代码结构
LONG_RUN_OUT_DT_S = 1.0e4      # 取 1e4 使末次采样恰落在 1.1e5 s 上
CONSERVATION_GAIN_MIN = 10.0   # P2-C1(d)：关闭守恒型格式后残差至少恶化一个量级


def run(n_cells=None, dt=None, t_end_s=None, out_dt_s=None, interface_mode="mean"):
    """生产求解：附录 3 变物性，输出步长 1 s / 0.1 cm。"""
    n_cells = P.N_CELLS if n_cells is None else n_cells
    dt = P.DT_Q2_S if dt is None else dt
    env = data_io.get_env()
    hist = SV.simulate_fixed(PROPS, dt, env, n_cells=n_cells,
                             t_end_s=P.Q2_FILE_T_END_S if t_end_s is None else t_end_s,
                             out_dt_s=P.Q2_FILE_DT_S if out_dt_s is None else out_dt_s,
                             interface_mode=interface_mode)
    return hist, env


def _table_stride(hist):
    """表 3/4 的 5 个径向位置在节点网格上的步长（0.5 cm 间距，N=80 时为 20）。"""
    dr_cm = P.R0_CM / (len(hist.C_fields[0]) - 1)
    stride = int(round(P.Q2_TABLE_RADII_CM[1] / dr_cm))
    if abs(stride * dr_cm - P.Q2_TABLE_RADII_CM[1]) > 1e-12:
        raise AssertionError(f"表 3/4 径向间距 {P.Q2_TABLE_RADII_CM[1]} cm 不落在节点上")
    return stride


def _paper_tables(hist):
    """表 3（温度）与表 4（水分浓度）：行标签为小时，取值时刻为 t=3600*h 秒。"""
    times = np.array(hist.times)
    stride = _table_stride(hist)
    tables = {"table3_temperature": [], "table4_moisture": []}
    for t_h in P.Q2_TABLE_TIMES_H:
        t_s = t_h * P.SECONDS_PER_HOUR
        idx = int(np.argmin(np.abs(times - t_s)))
        if abs(times[idx] - t_s) > 1e-9:
            raise AssertionError(f"表 3/4 时刻 {t_h} h 不在输出网格上")
        tables["table3_temperature"].append(
            {"t_h": t_h, "t_s": t_s, "values": [round(float(v), P.DECIMALS)
                                                for v in hist.T_fields[idx][::stride]]})
        tables["table4_moisture"].append(
            {"t_h": t_h, "t_s": t_s, "values": [round(float(v), P.DECIMALS)
                                                for v in hist.C_fields[idx][::stride]]})
    return tables


def long_run_probe(n_cells=None):
    """P2-C1(c)：同一 simulate_fixed 推进到 1.1e5 s（> 1e5），仅换 t_end_s 参数。"""
    env = data_io.get_env()
    hist = SV.simulate_fixed(PROPS, P.DT_Q3_S, env, n_cells=n_cells,
                             t_end_s=LONG_RUN_T_END_S,
                             out_dt_s=LONG_RUN_OUT_DT_S)
    C_end = hist.C_fields[-1]
    return {"t_end_s": float(hist.step_times[-1]),      # 实际推进到的时刻
            "t_last_recorded_s": float(hist.times[-1]), # 最后一个采样输出时刻
            "n_steps": hist.n_steps, "dt_s": P.DT_Q3_S,
            "maxC_end": float(C_end.max()), "C_center_end": float(C_end[0]),
            "T_center_end": float(hist.T_fields[-1][0]),
            "eps_M_end": float(hist.eps_M[-1]),
            "env_T_inf_end": float(hist.T_inf_hist[-1]),
            "env_C_inf_end": float(hist.C_inf_hist[-1]),
            "finite": bool(np.isfinite(C_end).all()
                           and np.isfinite(hist.T_fields[-1]).all())}


def conservation_form_probe(n_cells=None, dt=None, t_end_s=None):
    """P2-C1(d)/B-14：守恒型（界面平均）与非守恒型（节点单侧）残差对照。"""
    t_end_s = 600.0 if t_end_s is None else t_end_s
    dt = P.DT_Q2_S if dt is None else dt
    env = data_io.get_env()
    out = {}
    for mode in ("mean", "node"):
        hist = SV.simulate_fixed(PROPS, dt, env, n_cells=n_cells, t_end_s=t_end_s,
                                 out_dt_s=t_end_s, interface_mode=mode)
        out[mode] = float(hist.eps_M[-1])
    gain = out["node"] / max(out["mean"], 1e-30)
    return {"eps_M_conservative": out["mean"], "eps_M_node_sided": out["node"],
            "degradation_factor": float(gain), "t_end_s": t_end_s}


MISUSE_RATIO_MAX = 1e-10       # 摄氏误用把 exp(-3850/323) 变成 exp(-3850/50)，量级悬殊


def celsius_misuse_probe():
    """P2-C1(a)：把摄氏值直接代入 exp(-3850/T) 会把 D 压低多少个量级。

    exp(-3850/323.15) ≈ e^-11.9，exp(-3850/50) = e^-77：误用使 D 小到不可能烘干，
    故 T_K 换算不是形式要求而是量级要求。
    """
    T_c = 50.0
    d_kelvin = float(PROPS.D(P.C0, T_c))
    d_celsius = float(P.D_A3_PRE * np.exp(P.D_A3_EXP_C / P.C0)
                      * np.exp(P.D_A3_EXP_T / T_c))
    return {"T_degC": T_c, "T_K": T_c + P.KELVIN_OFFSET,
            "D_kelvin": d_kelvin, "D_celsius_misuse": d_celsius,
            "ratio_misuse_over_correct": d_celsius / d_kelvin}


def validate_constraints(hist, env, tables, xlsx_report):
    """B-01/02/03/06/09/10/11/12/19/22/28/29 在问题 2 的落点，全部硬断言。"""
    T_all = np.array(hist.T_fields)
    C_all = np.array(hist.C_fields)
    if not (np.isfinite(T_all).all() and np.isfinite(C_all).all()):
        raise AssertionError("B-19：出现非有限值")
    if not (C_all >= -1e-9).all() or not (C_all <= P.C0 + 1e-9).all():
        raise AssertionError(f"B-10：C 越界 [{C_all.min()}, {C_all.max()}]")
    T_inf_max = float(np.max(hist.T_inf_hist))
    if not (T_all >= P.T0_DEGC - 1e-9).all() or not (T_all <= T_inf_max + 1.0).all():
        raise AssertionError(f"B-10：T 越界 [{T_all.min()}, {T_all.max()}]")
    if not (np.diff(C_all, axis=1) <= 1e-12).all():
        raise AssertionError("B-11：C 沿 r 非单调非增")
    if hist.n_center_violations != 0 or hist.argmax_max != 0:
        raise AssertionError(
            f"bd_center_is_wettest：argmax_r C = {hist.argmax_max}，"
            f"max_r C - C[0] = {hist.max_center_deficit:.3e}")
    eps_final = hist.eps_M[-1]
    if not eps_final < P.EPS_M_LIMIT:
        raise AssertionError(f"B-12：eps_M={eps_final:.3e} 超出 {P.EPS_M_LIMIT}")
    T_end, C_end = hist.T_fields[-1], hist.C_fields[-1]
    res_T = SV.robin_flux_residual(T_end, PROPS.k(C_end), P.R0_M, P.H_CONV,
                                   hist.T_inf_hist[-1], n_cells=len(T_end) - 1)
    res_C = SV.robin_flux_residual(C_end, PROPS.D(C_end, T_end), P.R0_M, P.HM_CONV,
                                   hist.C_inf_hist[-1], n_cells=len(C_end) - 1)
    if not res_T < 1e-3:
        raise AssertionError(f"B-06：温度 Robin 通量残差 {res_T:.3e} 超出 1e-3")
    if not res_C < 1e-2:
        raise AssertionError(f"B-06：水分 Robin 通量残差 {res_C:.3e} 超出 1e-2")
    sym_T = SV.center_symmetry(T_end, P.R0_M, n_cells=len(T_end) - 1)
    sym_C = SV.center_symmetry(C_end, P.R0_M, n_cells=len(C_end) - 1)
    if not (sym_T["ratio"] < 1e-2 and sym_C["ratio"] < 1e-2):
        raise AssertionError(f"B-09：中心对称性比值 T={sym_T['ratio']:.3e}, C={sym_C['ratio']:.3e}")
    # B-22：环境驱动在数据段外仍有定义，取平台常值而非线性外推
    if abs(env.T_inf_scalar(2.0e5) - P.T_INF_PLATEAU_REF) > 1e-3:
        raise AssertionError("B-22：t 远超数据段时 T_inf 未取平台常值")
    if abs(env.C_inf_scalar(2.0e5) - P.C_INF_PLATEAU_REF) > 1e-5:
        raise AssertionError("B-22：t 远超数据段时 C_inf 未取平台常值")
    if xlsx_report["温度"]["dt_s"] != P.Q2_FILE_DT_S:
        raise AssertionError("B-29：result2.xlsx 时间步长不为 1 s")
    return {"eps_M": eps_final, "robin_res_T": res_T, "robin_res_C": res_C,
            "center_sym_T": sym_T, "center_sym_C": sym_C,
            "T_range": [float(T_all.min()), float(T_all.max())],
            "C_range": [float(C_all.min()), float(C_all.max())],
            "max_diff_C": hist.max_diff_C, "argmax_max": hist.argmax_max,
            "max_center_deficit": hist.max_center_deficit,
            "n_center_violations": hist.n_center_violations,
            "prop_ptp_min": hist.prop_ptp_min, "T_K_range": hist.T_K_range,
            "picard_rounds_max": int(max(hist.picard_rounds))}


def validate_capability(hist, tables, xlsx_report, long_run, cons_probe, misuse):
    """CAPABILITY_CHECKLIST P2-C1 ~ P2-C4 的 falsifiable_check，越界即 raise。"""
    # P2-C1(a)：Arrhenius 用开尔文，且运行时 T_K 落在 [273, 400]
    if "exp(-3850/T_K)" not in P.FORMULA_D_A3:
        raise AssertionError("P2-C1(a)：D 公式未标注 T_K")
    lo, hi = hist.T_K_range
    if not (273.0 <= lo and hi <= 400.0):
        raise AssertionError(f"P2-C1(a)：运行时 T_K 区间 [{lo:.2f}, {hi:.2f}] 越界")
    if not misuse["ratio_misuse_over_correct"] < MISUSE_RATIO_MAX:
        raise AssertionError("P2-C1(a)：摄氏误用应使 D 量级悬殊，探针未能区分两种写法")
    # P2-C1(b)：rho/cp/k 逐节点随 C 更新，全时程极差不为 0
    for name in ("rho", "cp", "k", "D"):
        if not hist.prop_ptp_min[name] > 0.0:
            raise AssertionError(f"P2-C1(b)：{name} 沿 r 极差最小值为 0，物性被冻结")
    if PROPS.is_constant():
        raise AssertionError("P2-C1(b)：问题 2 引用了常物性组")
    # P2-C1(c)：同一求解器推进过 1e5 s
    if not (long_run["t_end_s"] > 1.0e5 and long_run["finite"]):
        raise AssertionError(f"P2-C1(c)：长时程只推进到 {long_run['t_end_s']} s")
    if not long_run["maxC_end"] < P.C0:
        raise AssertionError("P2-C1(c)：长时程未见水分下降")
    # P2-C1(d)：关闭守恒型格式后残差显著变差
    if not cons_probe["degradation_factor"] > CONSERVATION_GAIN_MIN:
        raise AssertionError(
            f"P2-C1(d)：非守恒型残差仅恶化 {cons_probe['degradation_factor']:.2f} 倍")
    # P2-C3：论文表以小时为行标签，xlsx 以秒为 A 列，单位不混用
    if [row["t_h"] for row in tables["table3_temperature"]] != P.Q2_TABLE_TIMES_H:
        raise AssertionError("P2-C3：表 3 时刻标签不等于 0.5~3.0 h")
    if [row["t_h"] for row in tables["table4_moisture"]] != P.Q2_TABLE_TIMES_H:
        raise AssertionError("P2-C3：表 4 时刻标签不等于 0.5~3.0 h")
    if max(P.Q2_TABLE_TIMES_H) > P.Q2_FILE_T_END_S:
        raise AssertionError("P2-C3：论文表时间单位疑似与 xlsx 混用")
    if xlsx_report["温度"]["t_last"] != int(P.Q2_FILE_T_END_S):
        raise AssertionError("P2-C3：result2.xlsx A 列末值不是 10800 s")
    times = np.array(hist.times)
    stride = _table_stride(hist)
    for key, fields in (("table3_temperature", hist.T_fields),
                        ("table4_moisture", hist.C_fields)):
        for row in tables[key]:
            idx = int(np.argmin(np.abs(times - row["t_s"])))
            ref = fields[idx][::stride]
            if len(row["values"]) != len(P.Q2_TABLE_RADII_CM):
                raise AssertionError(f"P2-C3：{key} 列数不等于 5 个径向位置")
            if float(np.max(np.abs(np.array(row["values"]) - ref))) > 1e-4:
                raise AssertionError(f"P2-C3：{key} 数值与完整场不一致（容差 1e-4）")
    # P2-C4：交付结构
    if list(xlsx_report["sheets"]) != list(P.Q2_SHEETS):
        raise AssertionError("P2-C4：result2.xlsx 工作表名与模板不符")
    for sheet in P.Q2_SHEETS:
        if xlsx_report[sheet]["n_cols"] != P.N_OUT_COLS:
            raise AssertionError("P2-C4：result2.xlsx 列数不为 21")
    return True


def main():
    hist, env = run()
    tables = _paper_tables(hist)
    long_run = long_run_probe()
    cons_probe = conservation_form_probe()
    misuse = celsius_misuse_probe()

    T_rows = SV.sample_columns(np.array(hist.T_fields))
    C_rows = SV.sample_columns(np.array(hist.C_fields))
    path = XW.write_two_sheet_result(P.OUTPUT_DIR / "result2.xlsx", hist.times,
                                     P.OUT_RADII_CM, T_rows, C_rows,
                                     sheet_names=P.Q2_SHEETS)
    xlsx_report = XW.verify_written(path, P.Q2_SHEETS, P.Q2_FILE_DT_S, P.N_OUT_COLS)

    diag = validate_constraints(hist, env, tables, xlsx_report)
    validate_capability(hist, tables, xlsx_report, long_run, cons_probe, misuse)

    payload = {
        "problem": 2,
        "title": "全过程变物性双向强耦合模型（输出截取前 3 h）",
        "method": "守恒型有限体积 + 向后 Euler/Picard；附录 3 变物性双向耦合",
        "property_group": PROPS_FORMULA_TAG,
        "grid": {"n_cells": P.N_CELLS, "dt_s": P.DT_Q2_S, "dr_cm": P.R0_CM / P.N_CELLS,
                 "out_dt_s": P.Q2_FILE_DT_S, "out_dr_cm": P.Q2_FILE_DR_CM,
                 "n_steps": hist.n_steps},
        "output_radii_cm": P.OUT_RADII_CM,
        "paper_tables": tables,
        "table_radii_cm": P.Q2_TABLE_RADII_CM,
        "table_times_h": P.Q2_TABLE_TIMES_H,
        "center_series": {"times_s": hist.times,
                          "T": [float(f[0]) for f in hist.T_fields],
                          "C": [float(f[0]) for f in hist.C_fields]},
        "surface_series": {"times_s": hist.times,
                           "T": [float(f[-1]) for f in hist.T_fields],
                           "C": [float(f[-1]) for f in hist.C_fields]},
        "env_series": {"times_s": hist.times, "T_inf": hist.T_inf_hist,
                       "C_inf": hist.C_inf_hist},
        "field_T": RIO.field_grid(hist.times, hist.T_fields, every=60),
        "field_C": RIO.field_grid(hist.times, hist.C_fields, every=60),
        "mass_balance": {"times_s": hist.times, "M": hist.M_hist, "Q": hist.Q_hist,
                         "eps_M": hist.eps_M},
        "long_run_probe": long_run,
        "conservation_form_probe": cons_probe,
        "celsius_misuse_probe": misuse,
        "property_profiles": {
            "C_nodes": [float(v) for v in hist.C_fields[-1][::P.OUT_NODE_STRIDE]],
            "rho": [float(v) for v in PROPS.rho(hist.C_fields[-1])[::P.OUT_NODE_STRIDE]],
            "cp": [float(v) for v in PROPS.cp(hist.C_fields[-1])[::P.OUT_NODE_STRIDE]],
            "k": [float(v) for v in PROPS.k(hist.C_fields[-1])[::P.OUT_NODE_STRIDE]],
            "D": [float(v) for v in PROPS.D(hist.C_fields[-1],
                                            hist.T_fields[-1])[::P.OUT_NODE_STRIDE]],
        },
        "diagnostics": diag,
        "xlsx_report": xlsx_report,
        "summary": {
            "T_center_3h": float(hist.T_fields[-1][0]),
            "T_surface_3h": float(hist.T_fields[-1][-1]),
            "C_center_3h": float(hist.C_fields[-1][0]),
            "C_surface_3h": float(hist.C_fields[-1][-1]),
            "eps_M": diag["eps_M"],
            "long_run_t_end_s": long_run["t_end_s"],
            "conservation_degradation_factor": cons_probe["degradation_factor"],
        },
    }
    out_path, nbytes = RIO.write_results("problem_2_results", payload)
    print(f"[problem_2] 写出 {out_path.name} ({nbytes} bytes)、{path.name}")
    print(f"[problem_2] t=3 h 温度 = {[round(float(v), 4) for v in T_rows[-1][::5]]}")
    print(f"[problem_2] t=3 h 水分 = {[round(float(v), 4) for v in C_rows[-1][::5]]}")
    print(f"[problem_2] result2.xlsx 行数 = {xlsx_report['温度']['n_rows']}，"
          f"t: {xlsx_report['温度']['t_first']} → {xlsx_report['温度']['t_last']} s")
    print(f"[problem_2] eps_M = {diag['eps_M']:.3e}，Picard 最大轮数 = "
          f"{diag['picard_rounds_max']}")
    print(f"[problem_2] 长时程推进到 {long_run['t_end_s']:.0f} s，"
          f"max_r C = {long_run['maxC_end']:.4f}")
    print(f"[problem_2] 非守恒型残差恶化 {cons_probe['degradation_factor']:.1f} 倍 "
          f"({cons_probe['eps_M_conservative']:.2e} → {cons_probe['eps_M_node_sided']:.2e})")
    print(f"[problem_2] T_K 区间 = [{diag['T_K_range'][0]:.2f}, {diag['T_K_range'][1]:.2f}]，"
          f"摄氏误用会把 D 压到 {misuse['ratio_misuse_over_correct']:.3e} 倍")
    return payload


if __name__ == "__main__":
    main()
