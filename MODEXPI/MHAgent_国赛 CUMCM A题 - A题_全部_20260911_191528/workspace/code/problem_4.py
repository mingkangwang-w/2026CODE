# -*- coding: utf-8 -*-
"""问题 4：收缩动边界（附件 2 的 R(t)）+ 附录 4 物性，物质坐标 eta=r/R(t) 求解。

物性组是附录 4：rho=760+90C、cp=1850+2150C/(C+1)、k=0.12+0.20C/(C+1)，
D = 4.2e-4*exp(-0.30/C)*exp(-3850/T_K)。求解全程只绑定 PR.APPENDIX4；
附录 3 只在 validate_capability 里作为"两组物性确实不同"的对照量出现，
不参与任何求解路径。

方程形式（§5.4）：dC/dt = (1/R²)·(1/eta)·d_eta(eta·D·d_eta C)，无 dR/dt 对流项。
这不是省略：坐标运动项与固相对流项 u_s=(r/R)dR/dt 在变换中精确相消，
收缩效应完全经扩散项的 1/R² 与表面项的 1/R 进入（§5.4 推导，§9.3 实测）。
把该项额外加回去的反例通道在 solver.simulate_material(pseudo_convection=True)，
默认关闭——它与 fvkernel 的 interface_mode="node" 同属"故意破坏守恒的对照通道"，
放在方程所在的模块里，紧邻它所扰动的那套离散。
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

PROPS = PR.APPENDIX4
PROPS_FORMULA_TAG = f"附录4 变物性 {P.FORMULA_PROPS_A4}; {P.FORMULA_D_A4}"
Q4_SHEET = "Sheet1"
FROZEN_CELLS = 40
FROZEN_DT_S = 10.0
CONSTRUCT_T_END_S = 2.0e5
CONSTRUCT_OUT_DT_S = 2.0e4
CONSTRUCT_AMPLITUDE = 0.3
CONSTRUCT_DRIFT_LIMIT = 1e-6
PSEUDO_DRIFT_MIN = 1e-3
# B-06 在问题 4 的容差：温度取 2e-3 而非问题 1/2/3 的 1e-3。
# 理由是实测的截断误差常数更大，不是实现问题——附录 4 的 k=0.12+0.20C/(C+1)
# 比附录 3 的 0.21+0.38C/(C+1) 小一半，热边界层相对网格更薄，三点单侧重建的
# O(δ²) 误差常数随之变大。ROBIN_ORDER_CELLS 通道实测（3 h 锚点，dt=2.5 s）：
#   N=20 1.4609e-2 → 40 4.3486e-3 → 80 1.2118e-3 → 160 3.2239e-4
#   收敛阶 1.75 → 1.84 → 1.91（趋于 2）
# 即 N=80 的 1.21e-3 是纯截断误差。这条容差仍可证伪：符号写反或权重写错
# 不会给出 O(δ²) 收敛，故本文件把收敛表一并算出并断言其阶数。
ROBIN_TOL_T_Q4 = 2e-3
ROBIN_TOL_C_Q4 = 1e-2
ROBIN_ORDER_CELLS = (20, 40, 80)
ROBIN_ORDER_DT_S = 2.5
ROBIN_ORDER_MIN = 1.5

# ---- CAPABILITY_CHECKLIST P4-C1(c) 的已知偏离（不隐藏，随结果一起交付）----
DEVIATION_P4_C1c = {
    "capability": "P4-C1(c)",
    "checklist_demands": "eta 坐标方程保留伪对流项 (eta*dR/dt/R)*dC/deta；"
                         "关闭该项后守恒残差至少变差一个量级",
    "this_code_does": "不保留该项（物质坐标形式），并把附加该项作为反例通道",
    "why": "坐标运动项与固相对流项精确相消（§5.4）。附加该项等于把同一物理"
           "输运计两次，故它不是被省略而是本就不存在。",
    "measured_constructive_test": {
        "setup": "D=0、h_m=0、非均匀初值 C0(1+0.3cos(pi*eta))、积到 2e5 s；"
                 "此时没有任何物理机制能改变总水分，漂移全部来自格式",
        "material_coords_drift_reported": 0.0,
        "pseudo_convection_drift_reported": 0.231256,
    },
    "measured_real_case": {
        "setup": "N=40、dt=10 s 真实工况",
        "material_t_star_h_reported": 50.9690,
        "material_eps_M_reported": 4.38e-15,
        "pseudo_t_star_h_reported": 52.5333,
        "pseudo_eps_M_reported": 0.2542,
    },
    # 反例侧数值的可复现性说明：伪对流项是"本不该存在的项"，它的漂移量完全取决于
    # 怎么离散它（本通道用显式算子分裂 + 内点中心差商；§9.3 用的是另一种离散）。
    # 因此反例侧只有"量级/方向"是可复现的断言，绝对值不是物理常数，不做逐位对账。
    # 生产侧（物质坐标）反过来必须逐位复现，因为它是唯一确定的方程离散。
    "counterexample_reproducibility": (
        "反例通道的绝对漂移量随离散方式变化（本通道 0.1304 vs §9.3 的 0.2313，"
        "同量级同方向）；可复现的断言是'漂移 ≥ 1e-3 且比物质坐标差 10 个量级以上'，"
        "而非某个具体数值。t* 的移动方向亦随离散而变（本通道 48.78 h、§9.3 52.53 h），"
        "故不对反例 t* 作方向性断言——结论只依赖守恒被破坏这一事实。"),
    "conclusion": "实测方向与该子条要求相反：保留该项使守恒残差恶化 13 个量级以上"
                  "（本次 eps_M 比 1.35e13 倍）。按 §14 采用物质坐标形式，"
                  "并建议把该子条的对照方向反转。",
    "counterexample_channel": "solver.simulate_material(pseudo_convection=True)",
    "other_subitems": "P4-C1 的 (a)(b)(d) 三条照单全部满足，未偏离。",
    "documented_in": "MODELING_REPORT.md §0.2 / §5.4 / §9.3 / §14",
}

# 上面那些 *_reported 是 §9.3 的报告锚点。只把锚点和实测并排存进 JSON
# 等于宣称"复现了"却没查过——故本次运行必须逐项落在锚点附近，
# 由 reconcile_deviation() 硬断言。容差集中在此便于审计核对口径。
DEVIATION_TOL = {
    # 生产侧（物质坐标）：方程离散唯一确定，逐位对账
    "material_t_star_h_abs": 0.30,        # 与台账 bd_tstar_q4_range 同口径
    "material_drift_max": CONSTRUCT_DRIFT_LIMIT,
    # 机器精度量级的 eps_M 不做相对核对：4.38e-15 本身是舍入噪声，
    # 换网格/换平台不可能逐位复现，可验证的只有"仍属机器精度类"。
    "material_eps_M_max": 1e-12,
    # 反例侧：只核对量级与恶化倍数（理由见 counterexample_reproducibility）
    "pseudo_drift_min": PSEUDO_DRIFT_MIN,
    "pseudo_eps_M_min": 1e-3,
    "pseudo_over_material_ratio_min": 1e10,
}


def reconcile_deviation(construct, construct_pseudo, pseudo):
    """把 P4-C1(c) 偏离的报告锚点与本次实测逐项对账，越界即 raise。"""
    checks = []

    def _chk(name, measured, reference, tol, kind, note=""):
        """kind: abs/max = 与报告锚点逐位对账；min = 只核对量级下限（反例侧）。"""
        measured = float(measured)
        if kind == "abs":
            gap = abs(measured - reference)
            ok = gap <= tol
        elif kind == "max":
            gap, ok = measured, measured <= tol
        else:                                    # "min"
            gap, ok = measured, measured >= tol
        checks.append({"item": name, "measured": measured,
                       "reference": float(reference), "tol": float(tol),
                       "kind": kind, "gap": float(gap), "ok": bool(ok),
                       "note": note})
        if not ok:
            raise AssertionError(
                f"P4-C1(c) 偏离对账失败：{name} 实测 {measured:.6g}，"
                f"判据 {kind} 参照 {reference:.6g} / 阈值 {tol:.3g}（差 {gap:.3g}）。"
                "偏离说明只有在实测支持时才站得住——请查实测，不要放宽阈值。")

    ct = DEVIATION_P4_C1c["measured_constructive_test"]
    rc = DEVIATION_P4_C1c["measured_real_case"]
    # 生产侧：逐位对账（方程离散唯一）
    _chk("构造性守恒·物质坐标漂移", construct["drift"],
         ct["material_coords_drift_reported"], DEVIATION_TOL["material_drift_max"], "max",
         "物质坐标下总量恒等，漂移应为机器精度")
    _chk("真实工况·物质坐标 t*", pseudo["material_t_star_h"],
         rc["material_t_star_h_reported"], DEVIATION_TOL["material_t_star_h_abs"], "abs",
         "生产路径，须复现 §9.3 锚点")
    _chk("真实工况·物质坐标 eps_M", pseudo["material_eps_M"],
         rc["material_eps_M_reported"], DEVIATION_TOL["material_eps_M_max"], "max",
         "只核对量级类别：机器精度量不可能逐位复现")
    # 反例侧：只核对量级与恶化倍数（绝对值随离散而变，非物理常数）
    _chk("构造性守恒·伪对流漂移量级", construct_pseudo["drift"],
         ct["pseudo_convection_drift_reported"], DEVIATION_TOL["pseudo_drift_min"], "min",
         f"§9.3 为 {ct['pseudo_convection_drift_reported']:.4f}，本通道离散不同，同量级同方向")
    _chk("真实工况·伪对流 eps_M 量级", pseudo["pseudo_eps_M"],
         rc["pseudo_eps_M_reported"], DEVIATION_TOL["pseudo_eps_M_min"], "min",
         f"§9.3 为 {rc['pseudo_eps_M_reported']:.4f}，同量级")
    _chk("伪对流/物质坐标 eps_M 倍数", pseudo["eps_M_ratio"],
         DEVIATION_TOL["pseudo_over_material_ratio_min"],
         DEVIATION_TOL["pseudo_over_material_ratio_min"], "min",
         "这是偏离说明真正依赖的断言：保留该项使守恒恶化 10 个量级以上")

    return {**DEVIATION_P4_C1c,
            "measured_this_run": {
                "construct_drift_material": float(construct["drift"]),
                "construct_drift_pseudo": float(construct_pseudo["drift"]),
                "construct_drift_ratio": float(pseudo["construct_drift_ratio"]),
                "material_t_star_h": float(pseudo["material_t_star_h"]),
                "material_eps_M": float(pseudo["material_eps_M"]),
                "pseudo_t_star_h": float(pseudo["pseudo_t_star_h"]),
                "pseudo_eps_M": float(pseudo["pseudo_eps_M"]),
                "eps_M_ratio": float(pseudo["eps_M_ratio"]),
            },
            "reconciliation": checks,
            "reconciled": all(c["ok"] for c in checks)}


def radius_interpolator():
    """附件 2 的 R(t) 插值器：数据段内线性插值，段外取端点常值（§5.5）。

    left=R0 保证 R(0)=0.02 m；right=R_min 保证 t > 259200 s 时不做线性外推
    （外推会给出负半径）。附件 2 半径量化到 0.001 cm，故 Ṙ 本身带量化噪声——
    这也是物质坐标形式回避 Ṙ 的一个附带好处（§5.4）。
    """
    rad = data_io.get_radius()
    if abs(rad.R_start_m - P.R0_M) > 1e-12:
        raise AssertionError(f"P4-C1(a)：附件 2 起始半径 {rad.R_start_m} ≠ {P.R0_M}")
    if abs(rad.R_min_m - P.R_MIN_REF_M) > 1e-9:
        raise AssertionError(f"P4-C1(a)：附件 2 最小半径 {rad.R_min_m} ≠ {P.R_MIN_REF_M}")
    return rad


def run(n_cells=None, dt=None, out_dt_s=None, D_kwargs=None, hm=None, h=None,
        t_end_s=None, radius_fn=None, pseudo_convection=False):
    """生产求解：附录 4 变物性 + 附件 2 收缩，积到 max_eta C 首次低于 0.15。"""
    n_cells = P.N_CELLS if n_cells is None else n_cells
    dt = P.DT_Q4_S if dt is None else dt
    out_dt_s = P.Q4_FILE_DT_S if out_dt_s is None else out_dt_s
    env = data_io.get_env()
    rad = radius_interpolator()
    fn = rad.R_scalar if radius_fn is None else radius_fn
    hist = SV.simulate_material(PROPS, dt, env, fn, n_cells=n_cells, t_end_s=t_end_s,
                                out_dt_s=out_dt_s, stop_at_threshold=True,
                                D_kwargs=D_kwargs, hm=hm, h=h,
                                pseudo_convection=pseudo_convection)
    return hist, env, rad


def solve_tstar_h(n_cells, dt, **kwargs) -> float:
    """轻量通道：只要 t*(h)，输出网格放粗以省内存。"""
    hist, _, _ = run(n_cells=n_cells, dt=dt, out_dt_s=3600.0, **kwargs)
    return hist.t_star_s / P.SECONDS_PER_HOUR


def eta_nodes(n_cells) -> np.ndarray:
    return np.linspace(0.0, SV.ETA_SPAN, n_cells + 1)


def on_output_grid(times_s, out_dt_s=None):
    """滤掉阈值那步的离网采样，保证 xlsx A 列严格等距。"""
    out_dt_s = P.Q4_FILE_DT_S if out_dt_s is None else out_dt_s
    return [i for i, t in enumerate(times_s)
            if abs(float(t) / out_dt_s - round(float(t) / out_dt_s)) < 1e-9]


def paper_table6(hist, rad, n_cells=None):
    """表 6：行为 6,12,… h 加烘干结束行；列为 0,0.5,… 等距 + 末列「药材表面」。

    末列取 eta=1（即 r=R(t)），其对应半径随行变化——这是 P4-C2 的要点：
    表面不是固定 2 cm。等距列在超出该时刻 R(t) 后留 None（域外不给数值）。
    """
    n_cells = P.N_CELLS if n_cells is None else n_cells
    t_star_h = hist.t_star_s / P.SECONDS_PER_HOUR
    nodes = eta_nodes(n_cells)
    fixed_cm = [i * P.Q4_TABLE_DR_CM
                for i in range(int(round(P.R0_CM / P.Q4_TABLE_DR_CM)) + 1)]
    times = np.array(hist.times)
    rows = []
    n_full = int(np.floor(t_star_h / P.Q4_TABLE_DT_H))
    for m in range(1, n_full + 1):
        t_s = m * P.Q4_TABLE_DT_H * P.SECONDS_PER_HOUR
        idx = int(np.argmin(np.abs(times - t_s)))
        if abs(times[idx] - t_s) > 1e-9:
            raise AssertionError(f"表 6 整点行 {m * 6} h 不在输出网格上")
        C_row = np.asarray(hist.C_fields[idx], dtype=float)
        R_m = float(hist.radii_m[idx])
        rows.append({"label": f"{m * int(P.Q4_TABLE_DT_H)}", "t_h": float(t_s / P.SECONDS_PER_HOUR),
                     "values": SV.eta_to_radius_row(C_row, R_m, fixed_cm, nodes),
                     "surface_value": float(C_row[-1]),
                     "surface_radius_cm": R_m * P.CM_PER_M,
                     "center_value": float(C_row[0])})
    C_star = np.asarray(hist.C_at_tstar, dtype=float)
    R_star = float(hist.R_at_tstar_m)
    rows.append({"label": P.Q4_TABLE_LAST_ROW, "t_h": t_star_h,
                 "values": SV.eta_to_radius_row(C_star, R_star, fixed_cm, nodes),
                 "surface_value": float(C_star[-1]),
                 "surface_radius_cm": R_star * P.CM_PER_M,
                 "center_value": float(C_star[0])})
    return {"table6_moisture": rows, "fixed_radii_cm": fixed_cm,
            "last_col_label": P.Q4_TABLE_LAST_COL, "n_full_rows": n_full}


def frozen_radius_probe():
    """收缩效应的量化对照：把 R 冻结在 2 cm，t* 应显著变长（§7.4）。"""
    t_shrink = solve_tstar_h(FROZEN_CELLS, FROZEN_DT_S)
    t_frozen = solve_tstar_h(FROZEN_CELLS, FROZEN_DT_S, radius_fn=lambda t: P.R0_M)
    return {"n_cells": FROZEN_CELLS, "dt_s": FROZEN_DT_S,
            "t_star_shrinking_h": t_shrink, "t_star_frozen_h": t_frozen,
            "speedup": t_frozen / t_shrink,
            "compression": t_shrink / t_frozen}


def construct_conservation_probe(pseudo_convection=False):
    """B-16 构造性守恒：D=0、h_m=0、非均匀初值，总量应逐位不变。

    关掉扩散与表面通量后，物质坐标形式里没有任何机制改变总水分，
    故 M_end/M_ini − 1 必须是机器精度。打开伪对流反例通道时该恒等式被破坏，
    漂移量即"附加该项引入的凭空产湿/失湿"。
    """
    env = data_io.get_env()
    rad = radius_interpolator()
    nodes = eta_nodes(FROZEN_CELLS)
    C_init = P.C0 * (1.0 + CONSTRUCT_AMPLITUDE * np.cos(np.pi * nodes))
    hist = SV.simulate_material(PROPS, FROZEN_DT_S, env, rad.R_scalar,
                                n_cells=FROZEN_CELLS, t_end_s=CONSTRUCT_T_END_S,
                                out_dt_s=CONSTRUCT_OUT_DT_S, stop_at_threshold=False,
                                D_kwargs={"pre_scale": 0.0}, hm=0.0,
                                C_init_profile=C_init,
                                pseudo_convection=pseudo_convection)
    M_ini, M_end = float(hist.M_hist[0]), float(hist.M_hist[-1])
    # 本通道不报 eps_M：h_m=0 使累计流出 Q 恒为 0，而 eps_M 的定义要除以
    # max(Q,1e-30)，得到的是 1e29 量级的无意义数。本通道的守恒判据是 drift
    # 本身（总量应逐位不变），它不依赖 Q。
    return {"M_ini": M_ini, "M_end": M_end,
            "drift": abs(M_end / M_ini - 1.0),
            "eps_M_not_applicable": "h_m=0 → Q≡0，eps_M 的分母无定义；本通道用 drift 判守恒",
            "pseudo_convection": bool(pseudo_convection),
            "t_end_s": CONSTRUCT_T_END_S, "amplitude": CONSTRUCT_AMPLITUDE}


def pseudo_convection_real_probe():
    """真实工况下的伪对流对照：t* 与 eps_M 各自变成什么（§9.3）。"""
    base = run(n_cells=FROZEN_CELLS, dt=FROZEN_DT_S, out_dt_s=3600.0)[0]
    alt = run(n_cells=FROZEN_CELLS, dt=FROZEN_DT_S, out_dt_s=3600.0,
              pseudo_convection=True)[0]
    return {"n_cells": FROZEN_CELLS, "dt_s": FROZEN_DT_S,
            "material_t_star_h": base.t_star_s / P.SECONDS_PER_HOUR,
            "material_eps_M": float(base.eps_M[-1]),
            "pseudo_t_star_h": alt.t_star_s / P.SECONDS_PER_HOUR,
            "pseudo_eps_M": float(alt.eps_M[-1]),
            "eps_M_ratio": float(alt.eps_M[-1]) / max(float(base.eps_M[-1]), 1e-30)}


def shrinkage_prediction_probe(rad):
    """P4-C4：由 C 正向预测 R，与附件 2 实测比对三种假设组合（§9.5）。

    正向预测：给定 C 算体积比再算半径。绝不反演（由 R 反解 C 在 rho 线性形式下
    会给出非物理负含水率）。三组：附录4+仅径向、附录3+仅径向、附录4+各向同性。
    """
    C_grid = np.linspace(P.C_INF_PLATEAU_REF, P.C0, 200)
    combos = {
        "附录4+仅径向": (PR.APPENDIX4, PR.predict_radius_radial_only),
        "附录3+仅径向": (PR.APPENDIX3, PR.predict_radius_radial_only),
        "附录4+各向同性": (PR.APPENDIX4, PR.predict_radius_isotropic),
    }
    R_meas_min_cm = rad.R_min_m * P.CM_PER_M
    out = {}
    for name, (grp, fn) in combos.items():
        R_pred_end_m = float(fn(P.C_INF_PLATEAU_REF, grp))
        R_pred_end_cm = R_pred_end_m * P.CM_PER_M
        dev = abs(R_pred_end_cm - R_meas_min_cm) / R_meas_min_cm
        preds = np.array([float(fn(c, grp)) for c in C_grid])
        if not np.all(preds > 0.0):
            raise AssertionError(f"P4-C4：{name} 预测出非正半径")
        out[name] = {"R_pred_at_Cinf_cm": R_pred_end_cm,
                     "R_measured_min_cm": R_meas_min_cm,
                     "rel_dev": dev,
                     "monotone_in_C": bool(np.all(np.diff(preds) >= -1e-15))}
    return {"combos": out, "best": min(out, key=lambda k: out[k]["rel_dev"]),
            "direction": "forward: C -> R（不反演）"}


def robin_residuals(hist, n_cells=None):
    """B-06 在物质坐标上的落点，两段式（理由同问题 3，见 _tmp/problem_3_check.md）。

    eta 坐标下表面梯度是 ∂C/∂eta，物理通量为 (D/R)∂C/∂eta，故 gamma 取 D/R。
    """
    n_cells = P.N_CELLS if n_cells is None else n_cells
    delta = SV.ETA_SPAN / n_cells
    times = np.array(hist.times)
    idx = int(np.argmin(np.abs(times - P.Q2_FILE_T_END_S)))
    if abs(times[idx] - P.Q2_FILE_T_END_S) > 1e-9:
        raise AssertionError("B-06 良态时刻 3 h 不在输出网格上")
    out = {}
    for tag, i in (("anchor_3h", idx), ("tstar", len(times) - 1)):
        T = np.asarray(hist.T_fields[i], dtype=float)
        C = np.asarray(hist.C_fields[i], dtype=float)
        R_m = float(hist.radii_m[i])
        T_inf, C_inf = float(hist.T_inf_hist[i]), float(hist.C_inf_hist[i])
        D_surf = float(PROPS.D(np.array([C[-1]]), np.array([T[-1]]))[0])
        k_surf = float(PROPS.k(C[-1]))
        gT = (3.0 * T[-1] - 4.0 * T[-2] + T[-3]) / (2.0 * delta)
        gC = (3.0 * C[-1] - 4.0 * C[-2] + C[-3]) / (2.0 * delta)
        drive_T, drive_C = abs(T[-1] - T_inf), abs(C[-1] - C_inf)
        aT = abs(-(k_surf / R_m) * gT - P.H_CONV * (T[-1] - T_inf))
        aC = abs(-(D_surf / R_m) * gC - P.HM_CONV * (C[-1] - C_inf))
        layer_m = D_surf / P.HM_CONV
        out[tag] = {"t_h": float(times[i]) / P.SECONDS_PER_HOUR, "R_m": R_m,
                    "drive_T_degC": drive_T, "drive_C": drive_C,
                    "abs_res_T_W_m2": aT, "abs_res_C_kg_m2s": aC,
                    "rel_res_T": aT / (P.H_CONV * drive_T + 1e-12),
                    "rel_res_C": aC / (P.HM_CONV * drive_C + 1e-12),
                    "D_surface_m2_s": D_surf,
                    "Bi_m": P.HM_CONV * R_m / D_surf,
                    "layer_over_cell": layer_m / (delta * R_m)}
    out["scale_T_W_m2"] = P.H_CONV * (P.T_INF_PLATEAU_REF - P.T0_DEGC)
    out["scale_C_kg_m2s"] = P.HM_CONV * (P.C0 - P.C_INF_PLATEAU_REF)
    return out


def robin_order_probe():
    """实测 3 h 锚点 Robin 重建残差的收敛阶，为 ROBIN_TOL_T_Q4 提供可证伪依据。

    若离散写错（符号、权重、界面物性），残差不会以 O(δ²) 收敛——本通道把
    "容差放宽到 2e-3"从裸判断变成带收敛证据的判断。
    """
    env = data_io.get_env()
    rad = radius_interpolator()
    rows, prev = [], None
    for n in ROBIN_ORDER_CELLS:
        hist = SV.simulate_material(PROPS, ROBIN_ORDER_DT_S, env, rad.R_scalar,
                                    n_cells=n, t_end_s=P.Q2_FILE_T_END_S,
                                    out_dt_s=P.Q2_FILE_T_END_S,
                                    stop_at_threshold=False)
        a = robin_residuals(hist, n_cells=n)["anchor_3h"]
        order = None if prev is None else float(np.log2(prev / a["rel_res_T"]))
        rows.append({"n_cells": n, "rel_res_T": a["rel_res_T"],
                     "rel_res_C": a["rel_res_C"], "order_T": order,
                     "layer_over_cell": a["layer_over_cell"]})
        prev = a["rel_res_T"]
    orders = [r["order_T"] for r in rows if r["order_T"] is not None]
    if not orders or min(orders) < ROBIN_ORDER_MIN:
        raise AssertionError(
            f"B-06：Robin 重建残差收敛阶 {orders} 未达 {ROBIN_ORDER_MIN}，"
            "说明残差不是截断误差而是离散实现问题——此时放宽容差是掩盖错误")
    return {"table": rows, "orders": orders, "min_order": float(min(orders)),
            "dt_s": ROBIN_ORDER_DT_S,
            "why": "为 ROBIN_TOL_T_Q4=2e-3 提供收敛证据；阶数趋于 2 即纯截断误差"}


def validate_constraints(hist, env, rad, tables, xlsx_report, construct, pseudo,
                         robin_order):
    """B-05/06/09/10/11/12/14/15/16/19/20/21/26/27/28/29 在问题 4 的落点，全硬断言。"""
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
        raise AssertionError("B-11：C 沿 eta 非单调非增")
    if hist.n_center_violations != 0 or hist.argmax_max != 0:
        raise AssertionError(f"bd_center_is_wettest：argmax = {hist.argmax_max}，"
                             f"max−C[0] = {hist.max_center_deficit:.3e}")
    C_star = np.asarray(hist.C_at_tstar, dtype=float)
    if not abs(float(C_star.max()) - P.C_TH) < 1e-4:
        raise AssertionError(f"B-05：t* 处 max C = {C_star.max()} 偏离阈值超 1e-4")
    if int(np.argmax(C_star)) != 0:
        raise AssertionError("B-05：t* 处最湿点不在中心")
    eps_final = float(hist.eps_M[-1])
    if not eps_final < P.EPS_M_LIMIT:
        raise AssertionError(f"B-12：eps_M={eps_final:.3e} 超出 {P.EPS_M_LIMIT}")
    t_star_h = hist.t_star_s / P.SECONDS_PER_HOUR
    if not 20.0 < t_star_h < 200.0:
        raise AssertionError(f"B-21：t*={t_star_h:.4f} h 落在 20~200 h 之外")
    if not abs(hist.t_star_s % P.Q4_FILE_DT_S) > 1e-9:
        raise AssertionError(f"B-20：t*={hist.t_star_s} s 未经插值细化")
    # B-14：半径来自附件 2 实测，单调非增，端点与实测一致
    if abs(float(hist.radii_m[0]) - P.R0_M) > 1e-12:
        raise AssertionError(f"B-14：R(0)={hist.radii_m[0]} ≠ {P.R0_M}")
    radii = np.array(hist.radii_m, dtype=float)
    if not (np.diff(radii) <= 1e-15).all():
        raise AssertionError("B-14：R(t) 出现回升")
    if not radii.min() >= P.R_MIN_REF_M - 1e-12:
        raise AssertionError(f"B-14：R 最小值 {radii.min()} 低于附件 2 的 {P.R_MIN_REF_M}")
    if abs(radii.min() - P.R_MIN_REF_M) > 1e-9 and t_star_h * 3600.0 > rad.t_reach_min_s:
        raise AssertionError("B-14：t* 已过收缩平台但 R 未取到附件 2 末值")
    # B-16：构造性守恒（物质坐标形式下总量恒等）
    if not construct["drift"] < CONSTRUCT_DRIFT_LIMIT:
        raise AssertionError(f"B-16：构造性守恒漂移 {construct['drift']:.3e} "
                             f"超出 {CONSTRUCT_DRIFT_LIMIT}")
    # B-15 的运行侧证据：伪对流反例通道确实破坏守恒（静态侧由本文件无该项保证）
    if not pseudo["construct_drift_pseudo"] > PSEUDO_DRIFT_MIN:
        raise AssertionError(
            f"B-15：伪对流通道漂移 {pseudo['construct_drift_pseudo']:.3e} 未超过 "
            f"{PSEUDO_DRIFT_MIN}，对照失去判别力")
    rob = robin_residuals(hist, n_cells=C_all.shape[1] - 1)
    anc, fin = rob["anchor_3h"], rob["tstar"]
    if not anc["layer_over_cell"] > 1.0:
        raise AssertionError(f"B-06：3 h 边界层/网格 {anc['layer_over_cell']:.3f} ≤ 1")
    if not anc["rel_res_T"] < ROBIN_TOL_T_Q4:
        raise AssertionError(f"B-06：3 h 温度相对残差 {anc['rel_res_T']:.3e} 超 "
                             f"{ROBIN_TOL_T_Q4}")
    if not anc["rel_res_C"] < ROBIN_TOL_C_Q4:
        raise AssertionError(f"B-06：3 h 水分相对残差 {anc['rel_res_C']:.3e} 超 "
                             f"{ROBIN_TOL_C_Q4}")
    # 容差本身的合法性由收敛阶担保：阶数趋 2 才允许用放宽后的常数
    if robin_order["min_order"] < ROBIN_ORDER_MIN:
        raise AssertionError("B-06：收敛阶不足，放宽容差不成立")
    if not fin["abs_res_T_W_m2"] < 1e-6 * rob["scale_T_W_m2"]:
        raise AssertionError(f"B-06：t* 温度绝对残差 {fin['abs_res_T_W_m2']:.3e} W/m² 过大")
    if not fin["abs_res_C_kg_m2s"] < 1e-2 * rob["scale_C_kg_m2s"]:
        raise AssertionError(f"B-06：t* 水分绝对残差 {fin['abs_res_C_kg_m2s']:.3e} 过大")
    # B-09：面半径从 0.5δ 起 → eta=0 无通量面（结构性）
    faces = FV.face_radii(C_all.shape[1] - 1, SV.ETA_SPAN)
    d_eta = SV.ETA_SPAN / (C_all.shape[1] - 1)
    if abs(faces[0] - 0.5 * d_eta) > 1e-15:
        raise AssertionError("B-09：eta 面半径不从 0.5δ 起")
    sym_C = SV.center_symmetry(C_star, SV.ETA_SPAN, n_cells=C_all.shape[1] - 1)
    if not sym_C["ratio"] < 1e-2:
        raise AssertionError(f"B-09：t* 水分中心对称比值 {sym_C['ratio']:.3e} 超 1e-2")
    if xlsx_report[Q4_SHEET]["dt_s"] != P.Q4_FILE_DT_S:
        raise AssertionError("B-29：result4.xlsx 步长不为 60 s")
    if len(xlsx_report["sheets"]) != 1:
        raise AssertionError("B-28：result4.xlsx 不是单工作表")
    return {"eps_M": eps_final, "t_star_h": t_star_h, "t_star_s": hist.t_star_s,
            "R_at_tstar_cm": float(hist.R_at_tstar_m) * P.CM_PER_M,
            "robin_detail": rob, "center_sym_C": sym_C,
            "T_range": [float(T_all.min()), float(T_all.max())],
            "C_range": [float(C_all.min()), float(C_all.max())],
            "R_range_cm": [float(radii.min()) * P.CM_PER_M,
                           float(radii.max()) * P.CM_PER_M],
            "maxC_at_tstar": float(C_star.max()),
            "argmax_at_tstar": int(np.argmax(C_star)),
            "max_diff_C": hist.max_diff_C, "argmax_max": hist.argmax_max,
            "max_center_deficit": hist.max_center_deficit,
            "n_center_violations": hist.n_center_violations,
            "prop_ptp_min": hist.prop_ptp_min, "T_K_range": hist.T_K_range,
            "picard_rounds_max": int(max(hist.picard_rounds))}


def validate_capability(hist, rad, tables, xlsx_report, frozen, construct,
                        pseudo, shrink, t_star_q3_h):
    """CAPABILITY_CHECKLIST P4-C1 ~ P4-C4 的 falsifiable_check。

    P4-C1(c) 按 MODELING_REPORT §14 的偏离说明处理：该子条要求"保留伪对流项、
    关闭后守恒变差一个量级"，实测方向相反——本函数照实断言实测方向
    （物质坐标守恒到机器精度，附加伪对流项后漂移放大），并把两侧数值都存进结果，
    使偏离本身可被审计复算，而不是悄悄跳过该子条。
    """
    t_star_h = hist.t_star_s / P.SECONDS_PER_HOUR
    # P4-C1(a)：域上界是时变半径而非常数 2 cm
    if not rad.R_min_m < P.R0_M - 1e-6:
        raise AssertionError("P4-C1(a)：附件 2 半径未收缩，收缩效应缺失")
    radii = np.array(hist.radii_m, dtype=float)
    if not float(radii.max() - radii.min()) > 1e-4:
        raise AssertionError("P4-C1(a)：求解过程中 R 几乎不变，域上界形同常数")
    if not frozen["speedup"] > 1.0:
        raise AssertionError("P4-C1(a)：冻结半径未变慢，1/R² 放大未起作用")
    # P4-C1(b)：物性是附录 4，不是附录 3
    if abs(float(PROPS.rho(np.array([0.0]))[0]) - 760.0) > 1e-9:
        raise AssertionError("P4-C1(b)：rho(0) ≠ 760，未使用附录 4 密度")
    if abs(float(PROPS.rho(np.array([1.0]))[0]) - 850.0) > 1e-9:
        raise AssertionError("P4-C1(b)：rho(1) ≠ 850，密度斜率不是 90")
    if abs(float(PR.APPENDIX3.rho(np.array([0.0]))[0]) - 650.0) > 1e-9:
        raise AssertionError("P4-C1(b)：附录 3 对照组自身不符，无法判混用")
    # P4-C1(c)（方向按 §14 反转）：物质坐标守恒到机器精度；附加伪对流项后漂移放大
    if not construct["drift"] < CONSTRUCT_DRIFT_LIMIT:
        raise AssertionError("P4-C1(c)：物质坐标形式未达到构造性守恒")
    if not pseudo["construct_drift_pseudo"] > construct["drift"] * 10.0:
        raise AssertionError(
            f"P4-C1(c)：伪对流漂移 {pseudo['construct_drift_pseudo']:.3e} 未比物质坐标 "
            f"{construct['drift']:.3e} 差一个量级以上，对照无判别力")
    if not pseudo["eps_M_ratio"] > 10.0:
        raise AssertionError("P4-C1(c)：真实工况下伪对流的 eps_M 未显著恶化")
    # P4-C1(d)：方向性差异——附录 4 的 D 更小（拖慢）vs 收缩 1/R² 放大（加快）
    D4 = float(PROPS.D(np.array([P.C0]), np.array([P.T_INF_PLATEAU_REF]))[0])
    D3 = float(PR.APPENDIX3.D(np.array([P.C0]), np.array([P.T_INF_PLATEAU_REF]))[0])
    if not D4 < D3:
        raise AssertionError("P4-C1(d)：附录 4 的 D 未小于附录 3，方向性解释不成立")
    if not t_star_h < t_star_q3_h:
        raise AssertionError(
            f"P4-C1(d)：t*_Q4={t_star_h:.4f} h 未短于 t*_Q3={t_star_q3_h:.4f} h，"
            "收缩加速未压过 D 减小的拖慢")
    # P4-C2：表 6 末列为「药材表面」，半径随行变化且与附件 2 一致
    rows = tables["table6_moisture"]
    if tables["last_col_label"] != P.Q4_TABLE_LAST_COL:
        raise AssertionError(f"P4-C2：末列标签 {tables['last_col_label']} 不是"
                             f"「{P.Q4_TABLE_LAST_COL}」")
    surf_radii = [r["surface_radius_cm"] for r in rows]
    if len(set(round(v, 6) for v in surf_radii)) < 2:
        raise AssertionError("P4-C2：末列半径不随行变化，被写成了固定值")
    if any(abs(v - P.R0_CM) < 1e-9 for v in surf_radii[1:]):
        raise AssertionError("P4-C2：末列半径出现固定 2 cm")
    for r in rows:
        R_ref_cm = rad.R_scalar(r["t_h"] * P.SECONDS_PER_HOUR) * P.CM_PER_M
        if abs(r["surface_radius_cm"] - R_ref_cm) > 1e-4:
            raise AssertionError(
                f"P4-C2：{r['label']} 行末列半径 {r['surface_radius_cm']:.6f} 与附件 2 的 "
                f"{R_ref_cm:.6f} cm 偏差超 1e-4")
        for r_cm, v in zip(tables["fixed_radii_cm"], r["values"]):
            if r_cm > r["surface_radius_cm"] + 1e-12 and v is not None:
                raise AssertionError(
                    f"P4-C2：{r['label']} 行 r={r_cm} cm 已在域外却给出数值 {v}")
            if r_cm <= r["surface_radius_cm"] + 1e-12 and v is None:
                raise AssertionError(f"P4-C2：{r['label']} 行 r={r_cm} cm 在域内却留空")
    if P.Q4_TABLE_LAST_ROW not in rows[-1]["label"]:
        raise AssertionError("P4-C2：表 6 末行未标注烘干结束")
    if tables["n_full_rows"] != int(np.floor(t_star_h / P.Q4_TABLE_DT_H)):
        raise AssertionError("P4-C2：表 6 整点行数不等于 floor(t*/6)")
    # P4-C3：交付结构
    if xlsx_report[Q4_SHEET]["n_cols"] != P.N_OUT_COLS:
        raise AssertionError("P4-C3：result4.xlsx 列数不为 21")
    if xlsx_report[Q4_SHEET]["t_first"] != 0:
        raise AssertionError("P4-C3：result4.xlsx A 列未从 0 s 开始")
    if not xlsx_report[Q4_SHEET]["t_last"] <= hist.t_star_s:
        raise AssertionError("P4-C3：result4.xlsx 覆盖超过 t*")
    if hist.t_star_s - xlsx_report[Q4_SHEET]["t_last"] >= P.Q4_FILE_DT_S:
        raise AssertionError("P4-C3：result4.xlsx 未覆盖到 t* 前最后一个网格点")
    # P4-C4：三组正向预测对照，附录4+仅径向最优
    if shrink["best"] != "附录4+仅径向":
        raise AssertionError(f"P4-C4：最优组合是 {shrink['best']}，非附录4+仅径向")
    devs = {k: v["rel_dev"] for k, v in shrink["combos"].items()}
    for name, ref in (("附录4+仅径向", 0.0329), ("附录3+仅径向", 0.1073),
                      ("附录4+各向同性", 0.2122)):
        if abs(devs[name] - ref) > 0.005:
            raise AssertionError(f"P4-C4：{name} 偏差 {devs[name]:.4f} 与 §9.5 的 {ref} 不符")
    if shrink["direction"] != "forward: C -> R（不反演）":
        raise AssertionError("P4-C4：预测方向标注不是正向")
    return {"t_star_q4_h": t_star_h, "t_star_q3_h": t_star_q3_h,
            "D_app4_at_C0_50C": D4, "D_app3_at_C0_50C": D3,
            "D_ratio_app4_over_app3": D4 / D3,
            "shrink_deviations": devs}


def main():
    print("[problem_4] 生产求解开始（N=80, dt=5 s，物质坐标 + 附件 2 收缩）…", flush=True)
    hist, env, rad = run()
    t_star_h = hist.t_star_s / P.SECONDS_PER_HOUR
    print(f"[problem_4] t* = {t_star_h:.4f} h（{hist.n_steps} 步）", flush=True)

    tables = paper_table6(hist, rad)
    print("[problem_4] 冻结半径对照…", flush=True)
    frozen = frozen_radius_probe()
    print("[problem_4] 构造性守恒与伪对流证伪…", flush=True)
    construct = construct_conservation_probe(pseudo_convection=False)
    construct_pseudo = construct_conservation_probe(pseudo_convection=True)
    real_pseudo = pseudo_convection_real_probe()
    pseudo = dict(real_pseudo)
    pseudo["construct_drift_material"] = construct["drift"]
    pseudo["construct_drift_pseudo"] = construct_pseudo["drift"]
    pseudo["construct_drift_ratio"] = (construct_pseudo["drift"]
                                       / max(construct["drift"], 1e-30))
    deviation = reconcile_deviation(construct, construct_pseudo, pseudo)
    print("[problem_4] Robin 残差收敛阶实测…", flush=True)
    robin_order = robin_order_probe()
    shrink = shrinkage_prediction_probe(rad)

    keep = on_output_grid(hist.times)
    nodes = eta_nodes(len(hist.C_fields[0]) - 1)
    xlsx_times = [hist.times[i] for i in keep]
    C_rows = [SV.eta_to_radius_row(np.asarray(hist.C_fields[i], dtype=float),
                                   float(hist.radii_m[i]), P.OUT_RADII_CM, nodes)
              for i in keep]
    path = XW.write_single_sheet_result(P.OUTPUT_DIR / "result4.xlsx", xlsx_times,
                                       P.OUT_RADII_CM, C_rows, sheet_name=Q4_SHEET)
    xlsx_report = XW.verify_written(path, [Q4_SHEET], P.Q4_FILE_DT_S, P.N_OUT_COLS)

    import json
    q3 = json.loads((P.FIGURES_DIR / "problem_3_results.json").read_text(encoding="utf-8"))
    t_star_q3_h = float(q3["answer"]["t_star_h"])

    diag = validate_constraints(hist, env, rad, tables, xlsx_report,
                                construct, pseudo, robin_order)
    cap = validate_capability(hist, rad, tables, xlsx_report, frozen, construct,
                              pseudo, shrink, t_star_q3_h)

    every = max(1, len(keep) // 200)
    payload = {
        "problem": 4,
        "title": "收缩动边界下的烘干时长（附件 2 的 R(t) + 附录 4 物性，物质坐标）",
        "method": "物质坐标 eta=r/R(t) + 守恒型有限体积 + 向后 Euler + Picard 强耦合；"
                  "扩散项乘 1/R²、表面项乘 1/R；无 dR/dt 伪对流项（坐标运动与固相对流精确相消）",
        "property_group": PROPS_FORMULA_TAG,
        "grid": {"n_cells": len(hist.C_fields[0]) - 1, "dt_s": P.DT_Q4_S,
                 "eta_span": SV.ETA_SPAN, "out_dt_s": P.Q4_FILE_DT_S,
                 "picard_rounds_max": diag["picard_rounds_max"]},
        "answer": {"t_star_h": round(t_star_h, 4), "t_star_s": hist.t_star_s,
                   "t_star_days": round(t_star_h / 24.0, 4),
                   "R_at_tstar_cm": diag["R_at_tstar_cm"],
                   "criterion": "max_eta C(eta,t) < 0.15 kg/kg（干基，全域最大值）"},
        "output_radii_cm": list(P.OUT_RADII_CM),
        "paper_tables": tables,
        "profile_at_tstar": {"eta": nodes.tolist(),
                             "C": np.asarray(hist.C_at_tstar, dtype=float).tolist(),
                             "T": np.asarray(hist.T_at_tstar, dtype=float).tolist(),
                             "R_cm": diag["R_at_tstar_cm"]},
        "center_series": {"times_s": [float(hist.times[i]) for i in keep],
                          "C": [float(hist.C_fields[i][0]) for i in keep],
                          "T": [float(hist.T_fields[i][0]) for i in keep]},
        "surface_series": {"times_s": [float(hist.times[i]) for i in keep],
                           "C": [float(hist.C_fields[i][-1]) for i in keep],
                           "T": [float(hist.T_fields[i][-1]) for i in keep]},
        "radius_series": {"times_s": [float(hist.times[i]) for i in keep],
                          "R_cm": [float(hist.radii_m[i]) * P.CM_PER_M for i in keep]},
        "env_series": {"times_s": [float(hist.times[i]) for i in keep],
                       "T_inf": [float(hist.T_inf_hist[i]) for i in keep],
                       "C_inf": [float(hist.C_inf_hist[i]) for i in keep]},
        "field_C": RIO.field_grid([hist.times[i] for i in keep],
                                  [hist.C_fields[i] for i in keep], every),
        "field_T": RIO.field_grid([hist.times[i] for i in keep],
                                  [hist.T_fields[i] for i in keep], every),
        "mass_balance": {"times_s": [float(hist.times[i]) for i in keep],
                         "M": [float(hist.M_hist[i]) for i in keep],
                         "Q": [float(hist.Q_hist[i]) for i in keep],
                         "eps_M": [float(hist.eps_M[i]) for i in keep]},
        "frozen_radius_probe": frozen,
        "construct_conservation": construct,
        "construct_conservation_pseudo": construct_pseudo,
        "pseudo_convection_probe": pseudo,
        "deviation_P4_C1c": deviation,
        "robin_order_probe": robin_order,
        "shrinkage_prediction": shrink,
        "capability": cap,
        "diagnostics": diag,
        "xlsx_report": xlsx_report,
        "summary": {"t_star_h": round(t_star_h, 4),
                    "R_at_tstar_cm": diag["R_at_tstar_cm"],
                    "eps_M": diag["eps_M"],
                    "shrink_speedup": frozen["speedup"],
                    "t_star_q3_h": t_star_q3_h,
                    "D_ratio_app4_over_app3": cap["D_ratio_app4_over_app3"]},
    }
    out_path, nbytes = RIO.write_results("problem_4_results", payload)
    print(f"[problem_4] 写出 {out_path.name} ({nbytes} bytes)、result4.xlsx", flush=True)
    print(f"[problem_4] 烘干时长 t* = {t_star_h:.4f} h（{t_star_h / 24.0:.4f} 天），"
          f"R(t*) = {diag['R_at_tstar_cm']:.4f} cm", flush=True)
    prof = np.asarray(hist.C_at_tstar, dtype=float)
    show = [float(prof[int(round(f * (prof.size - 1)))]) for f in (0, .25, .5, .75, 1)]
    print(f"[problem_4] t* 剖面 C(eta=0,.25,.5,.75,1) = "
          f"{[round(v, 4) for v in show]}", flush=True)
    print(f"[problem_4] eps_M = {diag['eps_M']:.3e}，Picard 最大轮数 = "
          f"{diag['picard_rounds_max']}", flush=True)
    print(f"[problem_4] 冻结半径 {frozen['t_star_frozen_h']:.4f} h vs 收缩 "
          f"{frozen['t_star_shrinking_h']:.4f} h → 加速 {frozen['speedup']:.4f} 倍"
          f"（压缩到 {frozen['compression']:.1%}）", flush=True)
    print(f"[problem_4] 构造性守恒漂移：物质坐标 {construct['drift']:.3e} vs "
          f"伪对流 {construct_pseudo['drift']:.3e}", flush=True)
    print(f"[problem_4] 真实工况：物质坐标 {pseudo['material_t_star_h']:.4f} h / "
          f"eps_M {pseudo['material_eps_M']:.3e}；伪对流 "
          f"{pseudo['pseudo_t_star_h']:.4f} h / eps_M {pseudo['pseudo_eps_M']:.3e}",
          flush=True)
    print(f"[problem_4] 收缩假设正向预测偏差："
          f"{ {k: round(v, 4) for k, v in cap['shrink_deviations'].items()} }", flush=True)
    print(f"[problem_4] D(C0,50℃)：附录4 {cap['D_app4_at_C0_50C']:.4e} vs 附录3 "
          f"{cap['D_app3_at_C0_50C']:.4e}（比 {cap['D_ratio_app4_over_app3']:.4f}）",
          flush=True)
    return payload


if __name__ == "__main__":
    main()
