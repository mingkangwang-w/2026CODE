# -*- coding: utf-8 -*-
"""四问共用的时间推进驱动（MODELING_REPORT §5、§6）。

simulate_fixed    ：固定域 [0,R0]，服务问题 1/2/3（差异只在物性组与终止条件）。
simulate_material ：物质坐标 eta=r/R(t)，服务问题 4；扩散项乘 1/R²、表面项乘 1/R。
两者共用 fvkernel 的同一套权重与界面通量表达式，故守恒残差在离散层面是恒等式。
"""
from __future__ import annotations

import numpy as np

import fvkernel as FV
import params as P


class RunHistory:
    """采样输出与逐步诊断的容器。字段命名对齐 MODELING_REPORT §7 的锚点。"""

    def __init__(self) -> None:
        self.times: list[float] = []
        self.T_fields: list[np.ndarray] = []
        self.C_fields: list[np.ndarray] = []
        self.radii_m: list[float] = []
        self.eps_M: list[float] = []
        self.M_hist: list[float] = []
        self.Q_hist: list[float] = []
        self.T_inf_hist: list[float] = []
        self.C_inf_hist: list[float] = []
        self.step_times: list[float] = []
        self.step_maxC: list[float] = []
        self.picard_rounds: list[int] = []
        self.t_star_s: float | None = None
        self.C_at_tstar: np.ndarray | None = None
        self.T_at_tstar: np.ndarray | None = None
        self.R_at_tstar_m: float | None = None
        self.argmax_max: int = 0
        self.max_diff_C: float = -np.inf
        self.max_center_deficit: float = -np.inf
        self.n_center_violations: int = 0
        self.n_steps: int = 0
        # P2-C1(b)：逐步记录变物性沿 r 的极差，min 为 0 即说明物性被冻结成初值
        self.prop_ptp_min: dict[str, float] = {}
        self.T_K_range: list[float] = [np.inf, -np.inf]

    def record(self, t, T, C, radius, M, Q, T_inf, C_inf) -> None:
        self.times.append(float(t))
        self.T_fields.append(T.copy())
        self.C_fields.append(C.copy())
        self.radii_m.append(float(radius))
        self.M_hist.append(float(M))
        self.Q_hist.append(float(Q))
        self.eps_M.append(FV.mass_residual(M, Q))
        self.T_inf_hist.append(float(T_inf))
        self.C_inf_hist.append(float(C_inf))

    def as_arrays(self) -> dict:
        return {
            "times_s": np.array(self.times),
            "T": np.array(self.T_fields),
            "C": np.array(self.C_fields),
            "radii_m": np.array(self.radii_m),
            "eps_M": np.array(self.eps_M),
        }


NODE_NOISE_FLOOR = 1e-12   # 节点间舍入噪声上界（C0=2.55 的 ulp 约 4e-16，累积后仍远低于此）


def _track_profile(hist: RunHistory, C: np.ndarray, group=None, T=None,
                   D_kwargs=None) -> None:
    """全时程记录 bd_center_is_wettest / B-11 所需的度量（附带物性诊断）。

    初值均匀时全场在 1e-16 内相等，裸 argmax 由舍入噪声决定（会指向任意内部节点），
    故以 center_deficit = max_r C - C[0] 为判据：只有当某节点确实比中心高出
    NODE_NOISE_FLOOR 以上时才记 argmax 与违例计数。边界符号写错会让表面比中心湿
    O(0.1)，仍能被这一形式否证。
    """
    deficit = float(C.max() - C[0])
    hist.max_center_deficit = max(hist.max_center_deficit, deficit)
    hist.max_diff_C = max(hist.max_diff_C, float(np.max(np.diff(C))))
    if deficit > NODE_NOISE_FLOOR:
        hist.argmax_max = max(hist.argmax_max, int(np.argmax(C)))
        hist.n_center_violations += 1
    if group is not None:
        _track_properties(hist, group, C, T, D_kwargs)


def _track_properties(hist: RunHistory, group, C, T, D_kwargs=None) -> None:
    """P2-C1(a)(b)：记录物性沿 r 的极差最小值与运行时 T_K 区间。

    物性若被冻结为初值，则 ptp 恒为 0；D 的 Arrhenius 若误用摄氏值，
    T_K_range 会落到 273 以下，两者都可被 problem_2 的断言抓住。
    """
    fields = {"rho": group.rho(C), "cp": group.cp(C), "k": group.k(C),
              "D": group.D(C, T, **(D_kwargs or {}))}
    for name, arr in fields.items():
        ptp = float(np.ptp(np.asarray(arr, dtype=float)))
        prev = hist.prop_ptp_min.get(name)
        hist.prop_ptp_min[name] = ptp if prev is None else min(prev, ptp)
    T_K = np.asarray(T, dtype=float) + P.KELVIN_OFFSET
    hist.T_K_range[0] = min(hist.T_K_range[0], float(T_K.min()))
    hist.T_K_range[1] = max(hist.T_K_range[1], float(T_K.max()))


def simulate_fixed(group, dt, env, n_cells=None, t_end_s=None, out_dt_s=None,
                   stop_at_threshold=False, D_kwargs=None, hm=None, h=None,
                   radius_m=None, C0=None, T0=None, interface_mode="mean"):
    """固定域求解。stop_at_threshold=True 时积分到 max_r C 首次低于阈值。"""
    n_cells = P.N_CELLS if n_cells is None else n_cells
    span = P.R0_M if radius_m is None else radius_m
    C_init = P.C0 if C0 is None else C0
    T_init = P.T0_DEGC if T0 is None else T0
    hm = P.HM_CONV if hm is None else hm
    delta = span / n_cells
    weights = FV.cell_weights(n_cells, span)
    faces = FV.face_radii(n_cells, span)
    T = np.full(n_cells + 1, float(T_init))
    C = np.full(n_cells + 1, float(C_init))
    if np.ndim(C_init) > 0:
        C = np.array(C_init, dtype=float)

    hist = RunHistory()
    Q_acc = 0.0
    t = 0.0
    hist.record(t, T, C, span, FV.domain_moisture(C, weights, span), Q_acc,
                env.T_inf_scalar(t), env.C_inf_scalar(t))
    _track_profile(hist, C)          # 初值均匀，物性极差本应为 0，不计入 prop_ptp_min
    hist.step_times.append(t)
    hist.step_maxC.append(float(C.max()))

    limit_s = P.T_MAX_HOURS * P.SECONDS_PER_HOUR if t_end_s is None else t_end_s
    out_dt_s = limit_s if out_dt_s is None else out_dt_s
    out_stride = int(round(out_dt_s / dt))
    if abs(out_stride * dt - out_dt_s) > 1e-12:
        raise AssertionError(f"输出步长 {out_dt_s} 不是计算步长 {dt} 的整数倍")
    step = 0
    while t < limit_s - 1e-9:
        t_next = t + dt
        T_inf = env.T_inf_scalar(t_next)          # 环境驱动取隐式时刻值
        C_inf = env.C_inf_scalar(t_next)
        T_new, C_new, rounds = FV.picard_step(T, C, group, dt, T_inf, C_inf, span,
                                              weights, faces, delta, hm=hm, h=h,
                                              D_kwargs=D_kwargs,
                                              interface_mode=interface_mode)
        Q_acc += FV.outflow_increment(float(C_new[-1]), C_inf, span, dt, hm=hm)
        max_prev = float(C.max())
        T, C = T_new, C_new
        t = t_next
        step += 1
        hist.picard_rounds.append(rounds)
        _track_profile(hist, C, group, T, D_kwargs)
        hist.step_times.append(t)
        max_now = float(C.max())
        hist.step_maxC.append(max_now)
        if step % out_stride == 0:
            hist.record(t, T, C, span, FV.domain_moisture(C, weights, span), Q_acc,
                        T_inf, C_inf)
        if stop_at_threshold and max_now < P.C_TH:
            hist.t_star_s = FV.refine_threshold_crossing(t - dt, max_prev, t, max_now)
            hist.C_at_tstar = C.copy()
            hist.T_at_tstar = T.copy()
            hist.R_at_tstar_m = span
            if step % out_stride != 0:
                hist.record(t, T, C, span, FV.domain_moisture(C, weights, span), Q_acc,
                            T_inf, C_inf)
            break
    hist.n_steps = step
    if stop_at_threshold and hist.t_star_s is None:
        raise AssertionError(f"积分至 {limit_s / P.SECONDS_PER_HOUR:.2f} h 仍未达标，检查物性或边界")
    return hist


ETA_SPAN = 1.0        # 物质坐标 eta = r/R(t) 的区间上界


def _add_pseudo_convection(C_in, R_now, R_next, dt, delta):
    """反例通道：显式附加 −(eta·Ṙ/R)·∂C/∂eta（仅供证伪对照，生产不调用）。

    内点取中心差商、两端取单侧差商；eta=0 处该项系数为 0，故只影响 eta>0。
    """
    C_out = np.array(C_in, dtype=float)
    eta = np.linspace(0.0, ETA_SPAN, C_out.size)
    Rdot = (R_next - R_now) / dt
    grad = np.empty_like(C_out)
    grad[1:-1] = (C_out[2:] - C_out[:-2]) / (2.0 * delta)
    grad[0] = (C_out[1] - C_out[0]) / delta
    grad[-1] = (C_out[-1] - C_out[-2]) / delta
    return C_out - dt * (eta * Rdot / R_next) * grad


def simulate_material(group, dt, env, radius_fn, n_cells=None, t_end_s=None,
                      out_dt_s=None, stop_at_threshold=True, D_kwargs=None,
                      hm=None, h=None, C_init_profile=None,
                      pseudo_convection=False):
    """物质坐标 eta=r/R(t) 求解（问题 4）。

    扩散项整体乘 1/R²(t)、表面项系数为 sigma/R(t)；无含 dR/dt 的对流项——
    坐标运动项与固相对流项精确相消（MODELING_REPORT §0.2、§5.4、§9.3）。

    pseudo_convection=True 是**故意破坏守恒的反例通道**（与 fvkernel 的
    interface_mode="node" 同一用途）：在物质坐标解之上再附加一项
    −(eta·Ṙ/R)·∂C/∂eta 显式源，即上游主张、CAPABILITY_CHECKLIST P4-C1(c)
    要求"保留"的伪对流项。生产路径默认 False，只有证伪对照才打开它，
    用来量化"附加此项后守恒漂移多少"。
    """
    n_cells = P.N_CELLS if n_cells is None else n_cells
    hm = P.HM_CONV if hm is None else hm
    delta = ETA_SPAN / n_cells
    weights = FV.cell_weights(n_cells, ETA_SPAN)
    faces = FV.face_radii(n_cells, ETA_SPAN)
    T = np.full(n_cells + 1, P.T0_DEGC)
    C = np.full(n_cells + 1, P.C0) if C_init_profile is None \
        else np.array(C_init_profile, dtype=float)

    hist = RunHistory()
    Q_acc = 0.0
    t = 0.0
    R_now = float(radius_fn(t))
    hist.record(t, T, C, R_now, FV.domain_moisture(C, weights, ETA_SPAN), Q_acc,
                env.T_inf_scalar(t), env.C_inf_scalar(t))
    _track_profile(hist, C)          # 初值均匀，物性极差本应为 0，不计入 prop_ptp_min
    hist.step_times.append(t)
    hist.step_maxC.append(float(C.max()))

    limit_s = P.T_MAX_HOURS * P.SECONDS_PER_HOUR if t_end_s is None else t_end_s
    out_dt_s = limit_s if out_dt_s is None else out_dt_s
    out_stride = int(round(out_dt_s / dt))
    if abs(out_stride * dt - out_dt_s) > 1e-12:
        raise AssertionError(f"输出步长 {out_dt_s} 不是计算步长 {dt} 的整数倍")
    step = 0
    while t < limit_s - 1e-9:
        t_next = t + dt
        T_inf = env.T_inf_scalar(t_next)
        C_inf = env.C_inf_scalar(t_next)
        R_next = float(radius_fn(t_next))
        diff_scale = 1.0 / R_next ** 2          # 收缩通过 1/R² 唯一地进入方程
        surf_scale = 1.0 / R_next               # 表面项 sigma/R
        T_new, C_new, rounds = FV.picard_step(T, C, group, dt, T_inf, C_inf, ETA_SPAN,
                                              weights, faces, delta,
                                              diff_scale=diff_scale, surf_scale=surf_scale,
                                              hm=hm, h=h, D_kwargs=D_kwargs)
        if pseudo_convection:
            C_new = _add_pseudo_convection(C_new, R_now, R_next, dt, delta)
        Q_acc += FV.outflow_increment(float(C_new[-1]), C_inf, R_next, dt, hm=hm)
        max_prev = float(C.max())
        T, C, R_now = T_new, C_new, R_next
        t = t_next
        step += 1
        hist.picard_rounds.append(rounds)
        _track_profile(hist, C, group, T, D_kwargs)
        hist.step_times.append(t)
        max_now = float(C.max())
        hist.step_maxC.append(max_now)
        if step % out_stride == 0:
            hist.record(t, T, C, R_now, FV.domain_moisture(C, weights, ETA_SPAN), Q_acc,
                        T_inf, C_inf)
        if stop_at_threshold and max_now < P.C_TH:
            hist.t_star_s = FV.refine_threshold_crossing(t - dt, max_prev, t, max_now)
            hist.C_at_tstar = C.copy()
            hist.T_at_tstar = T.copy()
            hist.R_at_tstar_m = float(radius_fn(hist.t_star_s))
            if step % out_stride != 0:
                hist.record(t, T, C, R_now, FV.domain_moisture(C, weights, ETA_SPAN),
                            Q_acc, T_inf, C_inf)
            break
    hist.n_steps = step
    if stop_at_threshold and hist.t_star_s is None:
        raise AssertionError(f"积分至 {limit_s / P.SECONDS_PER_HOUR:.2f} h 仍未达标，检查收缩或物性")
    return hist


def robin_flux_residual(field, gamma, span, sigma, phi_inf, n_cells=None):
    """B-06：用三点单侧差商独立重建表面梯度，与 Robin 条件对账。"""
    n_cells = P.N_CELLS if n_cells is None else n_cells
    delta = span / n_cells
    grad = (3.0 * field[-1] - 4.0 * field[-2] + field[-3]) / (2.0 * delta)
    drive = sigma * abs(field[-1] - phi_inf)
    return abs(-gamma[-1] * grad - sigma * (field[-1] - phi_inf)) / (drive + 1e-12)


def center_symmetry(field, span, n_cells=None):
    """B-09：中心零通量的可证伪度量。

    r=0 的面积因子恒为 0，故该处通量在离散层面结构性为零（无需虚拟节点）。
    真正可被否证的是对称性本身：把三点单侧差商重建的中心梯度与表面梯度相比，
    对称解应给出量级悬殊的比值；若边界符号或权重写错，两者会同量级。
    """
    n_cells = P.N_CELLS if n_cells is None else n_cells
    delta = span / n_cells
    grad_center = (-3.0 * field[0] + 4.0 * field[1] - field[2]) / (2.0 * delta)
    grad_surface = (3.0 * field[-1] - 4.0 * field[-2] + field[-3]) / (2.0 * delta)
    ratio = abs(grad_center) / (abs(grad_surface) + 1e-30)
    return {"grad_center": float(grad_center), "grad_surface": float(grad_surface),
            "ratio": float(ratio)}


def sample_columns(field_2d, stride=None):
    """按节点步长抽取输出列（N=80、0.1 cm 时恰为每第 4 个节点，无需径向插值）。"""
    stride = P.OUT_NODE_STRIDE if stride is None else stride
    return np.asarray(field_2d)[..., ::stride]


def eta_to_radius_row(C_row, radius_m, out_radii_cm, eta_nodes):
    """问题 4：把 eta 剖面插到固定物理半径列上，超出 R(t) 的列返回 None（域外留空）。"""
    vals = []
    R_cm = radius_m * P.CM_PER_M
    for r_cm in out_radii_cm:
        if r_cm > R_cm + 1e-12:
            vals.append(None)
        else:
            vals.append(float(np.interp(r_cm / R_cm, eta_nodes, C_row)))
    return vals


def explicit_cross_check(group, dt_target, env, t_end_s, n_cells=None):
    """§6.2 的显式小步长交叉验证通道（仅验证用，主方案仍为向后 Euler）。"""
    n_cells = P.N_CELLS if n_cells is None else n_cells
    span, delta = P.R0_M, P.R0_M / n_cells
    weights = FV.cell_weights(n_cells, span)
    faces = FV.face_radii(n_cells, span)
    T = np.full(n_cells + 1, P.T0_DEGC)
    C = np.full(n_cells + 1, P.C0)
    alpha_max = float(np.max(group.k(C) / group.capacity(C)))
    D_max = float(np.max(group.D(C, T)))
    dt_stable = FV.explicit_stability_dt(delta, D_max, alpha_max)
    dt_row = min(FV.operator_row_bound_dt(group.capacity(C), group.k(C), weights, faces,
                                          delta, P.H_CONV, span),
                 FV.operator_row_bound_dt(np.ones_like(C), group.D(C, T), weights, faces,
                                          delta, P.HM_CONV, span))
    dt = min(dt_target, dt_stable, dt_row)
    n_steps = int(np.ceil(t_end_s / dt))
    dt = t_end_s / n_steps
    for i in range(n_steps):
        t_mid = i * dt
        T_inf, C_inf = env.T_inf_scalar(t_mid), env.C_inf_scalar(t_mid)
        for field, gamma, cap, sigma, phi_inf in (
                (T, group.k(C), group.capacity(C), P.H_CONV, T_inf),
                (C, group.D(C, T), np.ones_like(C), P.HM_CONV, C_inf)):
            gface = 0.5 * (gamma[:-1] + gamma[1:])
            flux = faces * gface * np.diff(field) / delta
            div = np.zeros_like(field)
            div[:-1] += flux
            div[1:] -= flux
            div[-1] += -span * sigma * (field[-1] - phi_inf)
            field += dt * div / (cap * weights)
    if not (np.isfinite(T).all() and np.isfinite(C).all()):
        raise AssertionError("显式交叉验证出现非有限值")
    return {"dt_used_s": dt, "dt_stable_s": dt_stable, "dt_row_bound_s": dt_row,
            "n_steps": n_steps, "T_final": T, "C_final": C}
