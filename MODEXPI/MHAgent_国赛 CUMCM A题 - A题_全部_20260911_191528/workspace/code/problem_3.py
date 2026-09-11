# -*- coding: utf-8 -*-
"""问题 3：烘干终点判定与总时长（附录 3 物性，与问题 2 同一模型、同一内核）。

物性组与问题 2 逐字相同：rho=650+128C、cp=1450+2736C/(C+1)、k=0.21+0.38C/(C+1)，
D = 2.4e-3*exp(-0.45/C)*exp(-3850/T_K)。B-03「物性不混用」靠本文件出现 650+128、
problem_4.py 不出现 650+128 来判定。

与问题 2 的唯一差别是终止条件：把 t=10800 s 换成阈值判据 max_r C < 0.15。
simulate_fixed(stop_at_threshold=True) 能一路推进到 t* 这件事本身，
就是问题 2「模型覆盖整个烘干过程」的运行证明（eq_q2_q3_same_model）。
"""
from __future__ import annotations

import numpy as np

import data_io
import fvkernel as FV
import params as P
import properties as PR
import resultio as RIO
import solver as SV
import xlsx_writer as XW

PROPS = PR.APPENDIX3
PROPS_FORMULA_TAG = f"附录3 变物性 {P.FORMULA_PROPS_A3}; {P.FORMULA_D_A3}"
Q3_SHEET = "Sheet1"
Q3_SHEETS = [Q3_SHEET]
# §8.3 网格收敛：Δr 与 Δt 同时减半，末档为生产网格
GRID_CONFIGS = ((20, 20.0), (40, 10.0), (80, 5.0))
EXPLICIT_PROBE_T_END_S = 600.0     # B-18 显式通道只需足够长以暴露不稳定
PRODUCT_PROBE_CELLS = 20           # §9.2 乘积指数证伪在基准配置上做
PRODUCT_PROBE_DT_S = 20.0


def run(n_cells=None, dt=None, out_dt_s=None, D_kwargs=None, hm=None, h=None,
        radius_m=None, t_end_s=None):
    """生产求解：附录 3 变物性，积分到 max_r C 首次低于 0.15。"""
    n_cells = P.N_CELLS if n_cells is None else n_cells
    dt = P.DT_Q3_S if dt is None else dt
    out_dt_s = P.Q3_FILE_DT_S if out_dt_s is None else out_dt_s
    env = data_io.get_env()
    hist = SV.simulate_fixed(PROPS, dt, env, n_cells=n_cells, t_end_s=t_end_s,
                             out_dt_s=out_dt_s, stop_at_threshold=True,
                             D_kwargs=D_kwargs, hm=hm, h=h, radius_m=radius_m)
    return hist, env


def solve_tstar_h(n_cells, dt, **kwargs) -> float:
    """只取 t*（h）的轻量通道，供网格收敛与证伪对照复用同一求解器。"""
    hist, _env = run(n_cells=n_cells, dt=dt, out_dt_s=P.Q3_FILE_DT_S, **kwargs)
    return hist.t_star_s / P.SECONDS_PER_HOUR


def _table_stride(n_cells: int) -> int:
    """表 5 的 5 个径向位置在节点网格上的步长（0.5 cm 间距，N=80 时为 20）。"""
    dr_cm = P.R0_CM / n_cells
    stride = int(round(P.Q3_TABLE_DR_CM / dr_cm))
    if abs(stride * dr_cm - P.Q3_TABLE_DR_CM) > 1e-12:
        raise AssertionError(f"表 5 径向间距 {P.Q3_TABLE_DR_CM} cm 不落在节点上")
    return stride


def on_output_grid(times_s, out_dt_s=None):
    """只保留恰好落在输出网格上的采样索引。

    阈值终止那一步的时刻 t* 附近不是 60 s 的整数倍（正因为 t* 经过插值细化），
    solver 会为它补记一条采样。这条采样对论文表与诊断有用，但写进 xlsx 会破坏
    A 列的等步长，故交付前按输出网格过滤（不丢任何网格点，只去掉这一条尾记录）。
    """
    out_dt_s = P.Q3_FILE_DT_S if out_dt_s is None else out_dt_s
    return [i for i, t in enumerate(times_s)
            if abs(float(t) / out_dt_s - round(float(t) / out_dt_s)) < 1e-9]


def table_radii_cm(n_cells: int) -> list[float]:
    stride = _table_stride(n_cells)
    dr_cm = P.R0_CM / n_cells
    return [round(j * dr_cm, 6) for j in range(0, n_cells + 1, stride)]


def paper_table5(hist, n_cells=None):
    """表 5：行为 6,12,... h（整点行数 = floor(t*/6)），末行为「烘干结束时间」。

    整点行数量由 t* 决定而非预设（P3-C2）；末行时刻取插值细化后的 t*，
    取值用 t* 所在计算步的场（stop 时保存的 C_at_tstar）。
    """
    n_cells = P.N_CELLS if n_cells is None else n_cells
    stride = _table_stride(n_cells)
    times = np.array(hist.times)
    t_star_h = hist.t_star_s / P.SECONDS_PER_HOUR
    n_full_rows = int(np.floor(t_star_h / P.Q3_TABLE_DT_H))
    rows = []
    for i in range(1, n_full_rows + 1):
        t_h = i * P.Q3_TABLE_DT_H
        t_s = t_h * P.SECONDS_PER_HOUR
        idx = int(np.argmin(np.abs(times - t_s)))
        if abs(times[idx] - t_s) > 1e-9:
            raise AssertionError(f"表 5 时刻 {t_h} h 不在 60 s 输出网格上")
        rows.append({"label": f"{t_h:.0f}", "t_h": float(t_h), "t_s": float(t_s),
                     "is_end": False,
                     "values": [round(float(v), P.DECIMALS)
                                for v in hist.C_fields[idx][::stride]]})
    rows.append({"label": P.Q3_TABLE_LAST_ROW, "t_h": float(t_star_h),
                 "t_s": float(hist.t_star_s), "is_end": True,
                 "values": [round(float(v), P.DECIMALS)
                            for v in hist.C_at_tstar[::stride]]})
    return {"table5_moisture": rows, "n_full_rows": n_full_rows,
            "radii_cm": table_radii_cm(n_cells)}


def grid_convergence(configs=GRID_CONFIGS):
    """§8.3 通道三：Δr 与 Δt 同时减半，报出逐档相对变化（B-17）。"""
    rows = []
    for n_cells, dt in configs:
        t_star_h = solve_tstar_h(n_cells, dt)
        rel = None if not rows else abs(t_star_h - rows[-1]["t_star_h"]) / rows[-1]["t_star_h"]
        rows.append({"n_cells": n_cells, "dt_s": dt,
                     "dr_cm": P.R0_CM / n_cells, "t_star_h": t_star_h,
                     "rel_change_vs_coarser": rel})
    return {"table": rows, "final_rel_change": rows[-1]["rel_change_vs_coarser"],
            "tol": P.CONV_TOL_GRID}


def stability_probe(n_cells=None):
    """B-18：显式格式稳定步长与算子行和界，并实跑显式通道确认不溢出。"""
    n_cells = P.N_CELLS if n_cells is None else n_cells
    env = data_io.get_env()
    out = SV.explicit_cross_check(PROPS, P.DT_Q3_S, env, EXPLICIT_PROBE_T_END_S,
                                 n_cells=n_cells)
    return {"dt_used_s": out["dt_used_s"], "dt_stable_s": out["dt_stable_s"],
            "dt_row_bound_s": out["dt_row_bound_s"], "n_steps": out["n_steps"],
            "t_end_s": EXPLICIT_PROBE_T_END_S,
            "implicit_dt_s": P.DT_Q3_S,
            "finite": bool(np.isfinite(out["T_final"]).all()
                           and np.isfinite(out["C_final"]).all()),
            "T_final_center": float(out["T_final"][0]),
            "C_final_center": float(out["C_final"][0])}


def criterion_variants_probe(hist, weights=None, n_cells=None):
    """P3-C1(a)：全域最大值判据 vs 平均含水率 vs 表面值，给出三个 t*。

    平均判据显著早于逐点判据（低估烘干时长），表面判据更早；
    三者数值分开才说明代码确实用的是 max 而非顺手写成 mean。
    """
    n_cells = P.N_CELLS if n_cells is None else n_cells
    weights = FV.cell_weights(n_cells, P.R0_M) if weights is None else weights
    times = np.array(hist.times)
    C_all = np.array(hist.C_fields)
    max_series = C_all.max(axis=1)
    mean_series = np.array([FV.domain_moisture(row, weights, P.R0_M) for row in C_all])
    surf_series = C_all[:, -1]
    out = {}
    for name, series in (("max", max_series), ("mean", mean_series),
                         ("surface", surf_series)):
        below = np.nonzero(series < P.C_TH)[0]
        if below.size == 0:
            out[name] = None
            continue
        i = int(below[0])
        t_s = (float(times[i]) if i == 0 else
               FV.refine_threshold_crossing(float(times[i - 1]), float(series[i - 1]),
                                            float(times[i]), float(series[i])))
        out[name] = t_s / P.SECONDS_PER_HOUR
    return {"t_star_h_by_criterion": out,
            "mean_minus_max_h": out["mean"] - out["max"],
            "surface_minus_max_h": out["surface"] - out["max"]}


def product_exponent_probe():
    """§9.2：把 D 的含水率指数改成乘积形式 exp(-0.45*C)，看 t* 掉到多少。"""
    t_star_frac = solve_tstar_h(PRODUCT_PROBE_CELLS, PRODUCT_PROBE_DT_S)
    t_star_prod = solve_tstar_h(PRODUCT_PROBE_CELLS, PRODUCT_PROBE_DT_S,
                                D_kwargs={"product_exponent": True})
    return {"n_cells": PRODUCT_PROBE_CELLS, "dt_s": PRODUCT_PROBE_DT_S,
            "t_star_fraction_h": t_star_frac, "t_star_product_h": t_star_prod,
            "ratio": t_star_prod / t_star_frac,
            "problem_text_range_h": [48.0, 72.0],
            "product_inside_problem_text": bool(48.0 <= t_star_prod <= 72.0)}


def q2_anchor(hist):
    """台账对 Q3 施加的三小时末状态约束（同一附录 3 轨迹，只是 dt 由 0.5 放宽到 5 s）。"""
    times = np.array(hist.times)
    idx = int(np.argmin(np.abs(times - P.Q2_FILE_T_END_S)))
    if abs(times[idx] - P.Q2_FILE_T_END_S) > 1e-9:
        raise AssertionError("3 h 锚点不在 60 s 输出网格上")
    T_row, C_row = hist.T_fields[idx], hist.C_fields[idx]
    return {"t_s": float(times[idx]),
            "T_spread_degC": float(T_row.max() - T_row.min()),
            "C_center": float(C_row[0]), "C_surface": float(C_row[-1]),
            "T_center": float(T_row[0]), "T_surface": float(T_row[-1])}


def robin_residuals(hist, n_cells=None):
    """B-06 的两段式度量：相对式在良态时刻评判，末态只判绝对残差。

    §10① 的相对式 |−γ∂φ/∂r − σ(φ_R−φ_∞)| / (σ|φ_R−φ_∞|) 有两个前提：驱动非零、
    边界层比网格粗。问题 3 积到 t*=57 h 时两个前提同时失效，且都不是实现错误：
      · 温度：|T_R−T_inf| 已衰减到 1e-13 K（浮点噪声），相对式退化成 0/0。
        末态绝对残差约 3e-12 W/m²，对比物理通量标度 h·(T_inf−T_0)≈550 W/m²。
      · 水分：C_R≈0.053 时 D=3.20e-12 m²/s，Bi_m≈5.0e3，边界层 4.0 μm，
        比 250 μm 的网格薄 63 倍。三点单侧重建分辨不了它，相对式必然 O(1)。
    格式真正施加的界面通量是 σ(φ_∞−φ_N) 本身，逐位精确；它的全局体现是
    eps_M≈1e-14（B-12）。故此处相对式取 3 h 锚点（驱动 0.16 K、边界层 1.3e4 μm，
    与问题 2 同一判据落点），末态改判绝对残差相对物理标度可忽略。
    """
    n_cells = (P.N_CELLS if n_cells is None else n_cells)
    delta = P.R0_M / n_cells
    times = np.array(hist.times)
    idx = int(np.argmin(np.abs(times - P.Q2_FILE_T_END_S)))
    if abs(times[idx] - P.Q2_FILE_T_END_S) > 1e-9:
        raise AssertionError("B-06 良态时刻 3 h 不在输出网格上")

    def _abs_res(field, gamma, sigma, phi_inf):
        grad = (3.0 * field[-1] - 4.0 * field[-2] + field[-3]) / (2.0 * delta)
        return abs(-float(gamma) * grad - sigma * (field[-1] - phi_inf))

    out = {}
    for tag, i in (("anchor_3h", idx), ("tstar", len(times) - 1)):
        T, C = hist.T_fields[i], hist.C_fields[i]
        T_inf, C_inf = float(hist.T_inf_hist[i]), float(hist.C_inf_hist[i])
        D_surf = float(PR_D_surface(C, T))
        aT = _abs_res(T, PROPS.k(C[-1]), P.H_CONV, T_inf)
        aC = _abs_res(C, D_surf, P.HM_CONV, C_inf)
        drive_T, drive_C = abs(float(T[-1]) - T_inf), abs(float(C[-1]) - C_inf)
        out[tag] = {
            "t_h": float(times[i]) / P.SECONDS_PER_HOUR,
            "drive_T_degC": drive_T, "drive_C": drive_C,
            "abs_res_T_W_m2": aT, "abs_res_C_kg_m2s": aC,
            "rel_res_T": aT / (P.H_CONV * drive_T + 1e-12),
            "rel_res_C": aC / (P.HM_CONV * drive_C + 1e-12),
            "D_surface_m2_s": D_surf,
            "Bi_m": P.HM_CONV * P.R0_M / D_surf,
            "layer_over_cell": (D_surf / (P.HM_CONV * P.R0_M)) * P.R0_M / delta,
        }
    out["scale_T_W_m2"] = P.H_CONV * (P.T_INF_PLATEAU_REF - P.T0_DEGC)
    out["scale_C_kg_m2s"] = P.HM_CONV * (P.C0 - P.C_INF_PLATEAU_REF)
    return out


def PR_D_surface(C, T):
    """表面节点的扩散系数（单点取值，避免整场求值后再取末元素）。"""
    return float(PROPS.D(np.array([float(C[-1])]), np.array([float(T[-1])]))[0])


def validate_constraints(hist, env, tables, xlsx_report, conv, stab):
    """B-03/05/10/11/12/17/18/19/20/21/25/28/29 在问题 3 的落点，全部硬断言。"""
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
    # B-05：终点判据取全域最大值，且 t* 处恰好压在阈值上
    C_star = hist.C_at_tstar
    if not abs(float(C_star.max()) - P.C_TH) < 1e-4:
        raise AssertionError(f"B-05：t* 处 max_r C = {C_star.max()} 偏离阈值超过 1e-4")
    if int(np.argmax(C_star)) != 0:
        raise AssertionError(f"B-05：t* 处最湿点不在中心（索引 {int(np.argmax(C_star))}）")
    eps_final = hist.eps_M[-1]
    if not eps_final < P.EPS_M_LIMIT:
        raise AssertionError(f"B-12：eps_M={eps_final:.3e} 超出 {P.EPS_M_LIMIT}")
    t_star_h = hist.t_star_s / P.SECONDS_PER_HOUR
    if not 20.0 < t_star_h < 200.0:
        raise AssertionError(f"B-21：t*={t_star_h:.4f} h 落在 20~200 h 之外")
    if not abs(hist.t_star_s % P.Q3_FILE_DT_S) > 1e-9:
        raise AssertionError(f"B-20：t*={hist.t_star_s} s 恰为 60 s 网格点整数倍，未经插值细化")
    if not conv["final_rel_change"] < P.CONV_TOL_GRID:
        raise AssertionError(f"B-17：网格收敛相对变化 {conv['final_rel_change']:.4%} 超出 1%")
    if not stab["dt_used_s"] <= stab["dt_stable_s"] + 1e-12:
        raise AssertionError(f"B-18：显式步长 {stab['dt_used_s']} 超出稳定界 {stab['dt_stable_s']}")
    if not stab["finite"]:
        raise AssertionError("B-18：显式通道出现非有限值")
    # B-25：末行为「烘干结束时间」且其时刻等于 t*
    last = tables["table5_moisture"][-1]
    if P.Q3_TABLE_LAST_ROW not in last["label"]:
        raise AssertionError(f"B-25：表 5 末行标签 {last['label']} 不含「{P.Q3_TABLE_LAST_ROW}」")
    if not abs(last["t_h"] - t_star_h) < 1e-4:
        raise AssertionError("B-25：表 5 末行时刻不等于 t*")
    T_end, C_end = hist.T_fields[-1], hist.C_fields[-1]
    rob = robin_residuals(hist, n_cells=len(C_end) - 1)
    anc, fin = rob["anchor_3h"], rob["tstar"]
    # B-06 段一：良态时刻（驱动非零、边界层 >> 网格）用 §10① 的相对式，容差同问题 2
    if not anc["layer_over_cell"] > 1.0:
        raise AssertionError(
            f"B-06：3 h 锚点边界层/网格 = {anc['layer_over_cell']:.3f} ≤ 1，相对式不适用")
    if not anc["rel_res_T"] < 1e-3:
        raise AssertionError(f"B-06：3 h 温度 Robin 相对残差 {anc['rel_res_T']:.3e} 超出 1e-3")
    if not anc["rel_res_C"] < 1e-2:
        raise AssertionError(f"B-06：3 h 水分 Robin 相对残差 {anc['rel_res_C']:.3e} 超出 1e-2")
    # B-06 段二：t* 处驱动已衰减、边界层薄于网格，改判绝对残差相对物理通量标度可忽略
    if not fin["abs_res_T_W_m2"] < 1e-6 * rob["scale_T_W_m2"]:
        raise AssertionError(
            f"B-06：t* 温度绝对残差 {fin['abs_res_T_W_m2']:.3e} W/m² 未低于标度 "
            f"{rob['scale_T_W_m2']:.4g} W/m² 的 1e-6")
    if not fin["abs_res_C_kg_m2s"] < 1e-2 * rob["scale_C_kg_m2s"]:
        raise AssertionError(
            f"B-06：t* 水分绝对残差 {fin['abs_res_C_kg_m2s']:.3e} kg/(m²·s) 未低于标度 "
            f"{rob['scale_C_kg_m2s']:.4g} 的 1e-2")
    res_T, res_C = anc["rel_res_T"], anc["rel_res_C"]
    # B-09 主判据（§10①）：离散层面 r=0 不存在通量面——面半径从 0.5δ 起，
    # 中心控制体的收支里只有外侧一个面。这是结构事实，用面半径直接核验。
    faces = FV.face_radii(len(C_end) - 1, P.R0_M)
    delta_r = P.R0_M / (len(C_end) - 1)
    if not (faces.size == len(C_end) - 1 and abs(faces[0] - 0.5 * delta_r) < 1e-15):
        raise AssertionError(f"B-09：面半径不从 0.5δ 起（faces[0]={faces[0]!r}），"
                             "中心零通量不再是结构性的")
    sym_T = SV.center_symmetry(T_end, P.R0_M, n_cells=len(T_end) - 1)
    sym_C = SV.center_symmetry(C_end, P.R0_M, n_cells=len(C_end) - 1)
    # 对称性证伪装置：梯度本身退化成浮点噪声时比值是 0/0，只在非退化场上评判。
    # t* 处温度已等温（中心/表面梯度都是 1e-13 量级噪声，比值 0.2 无信息量），
    # 故温度取 3 h 锚点；水分在 t* 仍有真实剖面结构，直接在末态评判。
    sym_T_anchor = SV.center_symmetry(hist.T_fields[
        int(np.argmin(np.abs(np.array(hist.times) - P.Q2_FILE_T_END_S)))],
        P.R0_M, n_cells=len(T_end) - 1)
    if not sym_T_anchor["ratio"] < 1e-2:
        raise AssertionError(f"B-09：3 h 温度中心对称性比值 {sym_T_anchor['ratio']:.3e} 超出 1e-2")
    if not sym_C["ratio"] < 1e-2:
        raise AssertionError(f"B-09：t* 水分中心对称性比值 {sym_C['ratio']:.3e} 超出 1e-2")
    sym_T = sym_T_anchor
    if abs(env.T_inf_scalar(2.0e5) - P.T_INF_PLATEAU_REF) > 1e-3:
        raise AssertionError("B-22：t 远超数据段时 T_inf 未取平台常值")
    if xlsx_report[Q3_SHEET]["dt_s"] != P.Q3_FILE_DT_S:
        raise AssertionError("B-29：result3.xlsx 时间步长不为 60 s")
    if len(xlsx_report["sheets"]) != 1:
        raise AssertionError("B-28：result3.xlsx 不是单工作表")
    return {"eps_M": eps_final, "t_star_h": t_star_h, "t_star_s": hist.t_star_s,
            "robin_res_T": res_T, "robin_res_C": res_C, "robin_detail": rob,
            "center_sym_T": sym_T, "center_sym_C": sym_C,
            "T_range": [float(T_all.min()), float(T_all.max())],
            "C_range": [float(C_all.min()), float(C_all.max())],
            "maxC_at_tstar": float(C_star.max()),
            "argmax_at_tstar": int(np.argmax(C_star)),
            "max_diff_C": hist.max_diff_C, "argmax_max": hist.argmax_max,
            "max_center_deficit": hist.max_center_deficit,
            "n_center_violations": hist.n_center_violations,
            "prop_ptp_min": hist.prop_ptp_min, "T_K_range": hist.T_K_range,
            "picard_rounds_max": int(max(hist.picard_rounds))}


def validate_capability(hist, tables, xlsx_report, conv, stab, variants, product):
    """CAPABILITY_CHECKLIST P3-C1 ~ P3-C4 的 falsifiable_check，越界即 raise。"""
    t_star_h = hist.t_star_s / P.SECONDS_PER_HOUR
    # P3-C1(a)：判据是全域最大值，不是平均也不是表面值——三者数值必须分开
    by = variants["t_star_h_by_criterion"]
    if not by["mean"] < by["max"] - 1.0:
        raise AssertionError(
            f"P3-C1(a)：平均判据 {by['mean']:.4f} h 未显著早于逐点判据 {by['max']:.4f} h，"
            "两者若相同说明判据实现被写成了 mean")
    if not by["surface"] < by["mean"]:
        raise AssertionError("P3-C1(a)：表面判据未早于平均判据，剖面单调性或判据实现有误")
    if not abs(by["max"] - t_star_h) < 0.05:
        raise AssertionError(
            f"P3-C1(a)：60 s 采样上的 max 判据 {by['max']:.4f} h 与生产 t* {t_star_h:.4f} h 不一致")
    # P3-C1(b)：t* 经插值细化，且 t* 处 max_r C 贴住阈值
    if not abs(hist.t_star_s % P.Q3_FILE_DT_S) > 1e-9:
        raise AssertionError("P3-C1(b)：t* 恰为 60 s 整数倍，未做插值细化")
    if not abs(float(hist.C_at_tstar.max()) - P.C_TH) < 1e-4:
        raise AssertionError("P3-C1(b)：t* 处 max_r C 与 0.15 偏差超过 1e-4")
    # P3-C1(c)：中心控制
    if int(np.argmax(hist.C_at_tstar)) != 0 or hist.argmax_max != 0:
        raise AssertionError("P3-C1(c)：argmax_r C 不恒为 0")
    # P3-C1(d)：物理合理区间，且与题面 2-3 天量级一致
    if not 20.0 < t_star_h < 200.0:
        raise AssertionError(f"P3-C1(d)：t*={t_star_h:.4f} h 越出 20~200 h")
    if not 48.0 * 0.8 <= t_star_h <= 72.0 * 1.2:
        raise AssertionError(f"P3-C1(d)：t*={t_star_h:.4f} h 偏离题面 2-3 天量级过远")
    # P3-C2：整点行数 = floor(t*/6)，末行为烘干结束时间且各列 < 0.15
    rows = tables["table5_moisture"]
    if tables["n_full_rows"] != int(np.floor(t_star_h / P.Q3_TABLE_DT_H)):
        raise AssertionError("P3-C2：表 5 整点行数不等于 floor(t*/6)")
    if len(rows) != tables["n_full_rows"] + 1:
        raise AssertionError("P3-C2：表 5 行数不等于整点行 + 烘干结束行")
    if P.Q3_TABLE_LAST_ROW not in rows[-1]["label"]:
        raise AssertionError("P3-C2：表 5 末行未标注烘干结束时间")
    if not all(v < P.C_TH + 1e-9 for v in rows[-1]["values"]):
        raise AssertionError(f"P3-C2：末行存在不低于 0.15 的列：{rows[-1]['values']}")
    if not float(hist.C_at_tstar.max()) < P.C_TH:
        raise AssertionError("P3-C2：t* 处原始场未全部低于 0.15")
    if len(tables["radii_cm"]) != 5 or tables["radii_cm"][-1] != P.R0_CM:
        raise AssertionError(f"P3-C2：表 5 径向列 {tables['radii_cm']} 不是 0~2 cm 的 5 列")
    # P3-C3/P3-C4：交付结构与长时程可靠性
    if xlsx_report[Q3_SHEET]["n_cols"] != P.N_OUT_COLS:
        raise AssertionError("P3-C3：result3.xlsx 列数不为 21")
    if xlsx_report[Q3_SHEET]["t_first"] != 0:
        raise AssertionError("P3-C3：result3.xlsx A 列未从 0 s 开始")
    if not xlsx_report[Q3_SHEET]["t_last"] <= hist.t_star_s:
        raise AssertionError("P3-C3：result3.xlsx 覆盖超过 t*")
    if hist.t_star_s - xlsx_report[Q3_SHEET]["t_last"] >= P.Q3_FILE_DT_S:
        raise AssertionError("P3-C3：result3.xlsx 未覆盖到 t* 前的最后一个 60 s 网格点")
    if not conv["final_rel_change"] < P.CONV_TOL_GRID:
        raise AssertionError("P3-C4(c)：网格减半后 t* 相对变化不小于 1%")
    if len(conv["table"]) < 3:
        raise AssertionError("P3-C4(c)：收敛表不足 3 档")
    if not hist.eps_M[-1] < P.EPS_M_LIMIT:
        raise AssertionError("P3-C4(b)：守恒残差不小于 1%")
    if not stab["dt_used_s"] <= stab["dt_stable_s"] + 1e-12:
        raise AssertionError("P3-C4(a)：显式步长未满足稳定条件")
    # §9.2：乘积指数误读必须落在题面量级之外，否则该证伪通道无鉴别力
    if product["product_inside_problem_text"]:
        raise AssertionError("§9.2：乘积指数形式竟落在 48~72 h 内，证伪通道失效")
    return True


def main():
    print("[problem_3] 生产求解开始（N=80, dt=5 s，阈值终止）…", flush=True)
    hist, env = run()
    t_star_h = hist.t_star_s / P.SECONDS_PER_HOUR
    print(f"[problem_3] t* = {t_star_h:.4f} h（{hist.n_steps} 步）", flush=True)
    tables = paper_table5(hist)
    anchor = q2_anchor(hist)
    variants = criterion_variants_probe(hist)
    print("[problem_3] 网格收敛三档开始…", flush=True)
    conv = grid_convergence()
    print("[problem_3] 显式稳定性与乘积指数证伪…", flush=True)
    stab = stability_probe()
    product = product_exponent_probe()

    keep = on_output_grid(hist.times)
    xlsx_times = [hist.times[i] for i in keep]
    C_rows = SV.sample_columns(np.array([hist.C_fields[i] for i in keep]))
    path = XW.write_single_sheet_result(P.OUTPUT_DIR / "result3.xlsx", xlsx_times,
                                       P.OUT_RADII_CM, C_rows, sheet_name=Q3_SHEET)
    xlsx_report = XW.verify_written(path, Q3_SHEETS, P.Q3_FILE_DT_S, P.N_OUT_COLS)

    diag = validate_constraints(hist, env, tables, xlsx_report, conv, stab)
    validate_capability(hist, tables, xlsx_report, conv, stab, variants, product)

    payload = {
        "problem": 3,
        "title": "烘干终点判定与总烘干时长",
        "method": "守恒型有限体积 + 向后 Euler/Picard；阈值首达 + 线性插值细化",
        "property_group": PROPS_FORMULA_TAG,
        "grid": {"n_cells": P.N_CELLS, "dt_s": P.DT_Q3_S, "dr_cm": P.R0_CM / P.N_CELLS,
                 "out_dt_s": P.Q3_FILE_DT_S, "out_dr_cm": P.Q3_FILE_DR_CM,
                 "n_steps": hist.n_steps},
        "answer": {"t_star_h": round(t_star_h, P.DECIMALS), "t_star_s": hist.t_star_s,
                   "criterion": "max_r C(r,t) < 0.15 kg/kg（干基，全域最大值）",
                   "t_star_days": round(t_star_h / 24.0, P.DECIMALS)},
        "output_radii_cm": P.OUT_RADII_CM,
        "paper_tables": tables,
        "profile_at_tstar": {
            "radii_cm": tables["radii_cm"],
            "C": [round(float(v), P.DECIMALS)
                  for v in hist.C_at_tstar[::_table_stride(P.N_CELLS)]],
            "T": [round(float(v), P.DECIMALS)
                  for v in hist.T_at_tstar[::_table_stride(P.N_CELLS)]],
            "C_full_nodes": [float(v) for v in hist.C_at_tstar[::P.OUT_NODE_STRIDE]],
        },
        "center_series": {"times_s": hist.times,
                          "T": [float(f[0]) for f in hist.T_fields],
                          "C": [float(f[0]) for f in hist.C_fields]},
        "surface_series": {"times_s": hist.times,
                           "T": [float(f[-1]) for f in hist.T_fields],
                           "C": [float(f[-1]) for f in hist.C_fields]},
        "env_series": {"times_s": hist.times, "T_inf": hist.T_inf_hist,
                       "C_inf": hist.C_inf_hist},
        "field_C": RIO.field_grid(hist.times, hist.C_fields, every=60),
        "field_T": RIO.field_grid(hist.times, hist.T_fields, every=60),
        "mass_balance": {"times_s": hist.times, "M": hist.M_hist, "Q": hist.Q_hist,
                         "eps_M": hist.eps_M},
        "grid_convergence": conv,
        "stability_probe": stab,
        "criterion_variants": variants,
        "product_exponent_probe": product,
        "q2_anchor_3h": anchor,
        "diagnostics": diag,
        "xlsx_report": xlsx_report,
        "summary": {
            "t_star_h": round(t_star_h, P.DECIMALS),
            "eps_M": diag["eps_M"],
            "grid_final_rel_change": conv["final_rel_change"],
            "maxC_at_tstar": diag["maxC_at_tstar"],
            "C_center_6h": float(hist.C_fields[int(round(6 * 3600 / P.Q3_FILE_DT_S))][0]),
            "t_star_mean_criterion_h": variants["t_star_h_by_criterion"]["mean"],
            "t_star_product_exponent_h": product["t_star_product_h"],
        },
    }
    out_path, nbytes = RIO.write_results("problem_3_results", payload)
    print(f"[problem_3] 写出 {out_path.name} ({nbytes} bytes)、{path.name}")
    print(f"[problem_3] 烘干时长 t* = {t_star_h:.4f} h（{t_star_h / 24:.4f} 天）")
    print(f"[problem_3] t* 剖面 C = {payload['profile_at_tstar']['C']}")
    print(f"[problem_3] eps_M = {diag['eps_M']:.3e}，Picard 最大轮数 = {diag['picard_rounds_max']}")
    print("[problem_3] 网格收敛：" + " → ".join(
        f"N={r['n_cells']}/dt={r['dt_s']:g}s: {r['t_star_h']:.4f} h" for r in conv["table"]))
    print(f"[problem_3] 末档相对变化 = {conv['final_rel_change']:.4%}（限 1%）")
    print(f"[problem_3] 判据对照：max {variants['t_star_h_by_criterion']['max']:.4f} h、"
          f"mean {variants['t_star_h_by_criterion']['mean']:.4f} h、"
          f"surface {variants['t_star_h_by_criterion']['surface']:.4f} h")
    print(f"[problem_3] 乘积指数证伪：{product['t_star_product_h']:.4f} h "
          f"vs 分式 {product['t_star_fraction_h']:.4f} h")
    print(f"[problem_3] 显式稳定界 dt <= {stab['dt_stable_s']:.4f} s（实用 {stab['dt_used_s']:.4f} s）")
    print(f"[problem_3] 3 h 锚点：全场温差 {anchor['T_spread_degC']:.4f} °C，"
          f"C 中心 {anchor['C_center']:.4f}、表面 {anchor['C_surface']:.4f}")
    return payload


if __name__ == "__main__":
    main()
