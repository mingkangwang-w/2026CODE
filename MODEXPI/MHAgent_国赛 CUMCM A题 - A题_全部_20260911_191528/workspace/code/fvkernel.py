# -*- coding: utf-8 -*-
"""守恒型有限体积内核（MODELING_REPORT §6）。

一套内核服务四问：空间离散权重 w_j 与界面通量表达式相邻控制体共享，
时间推进为向后 Euler + Picard，线性系统用 solve_banded((1,1),...) 三对角直接求解。

问题 4 在 eta=r/R(t) 物质坐标下求解：扩散项整体乘 1/R^2、表面项系数为 sigma/R，
不含伪对流项（§0.2 / §9.3：坐标运动项与固相对流项精确相消）。
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_banded

import params as P


def cell_weights(n_cells: int, span: float) -> np.ndarray:
    """控制体权重 w_j = ∫_cell r dr：w0=δ²/8，w_j=jδ²，wN=(S²-(S-δ/2)²)/2。"""
    delta = span / n_cells
    idx = np.arange(n_cells + 1, dtype=float)
    w = idx * delta ** 2
    w[0] = delta ** 2 / 8.0
    w[-1] = (span ** 2 - (span - delta / 2.0) ** 2) / 2.0
    return w


def face_radii(n_cells: int, span: float) -> np.ndarray:
    """内界面位置 r_{j+1/2}，共 n_cells 个（j=0..N-1）。"""
    delta = span / n_cells
    return (np.arange(n_cells, dtype=float) + 0.5) * delta


def node_coords(n_cells: int, span: float) -> np.ndarray:
    return np.linspace(0.0, span, n_cells + 1)


def solve_diffusion_step(phi_old, capacity, gamma, weights, faces, delta, dt,
                         sigma, phi_inf, span, diff_scale=1.0, surf_scale=1.0,
                         interface_mode="mean"):
    """一步向后 Euler 的守恒型有限体积求解（三对角）。

    capacity: 容量项 S_j（质量方程恒为 1）；gamma: 节点扩散系数 Γ_j；
    diff_scale: 扩散项整体因子（物质坐标为 1/R²，固定域为 1）；
    surf_scale: 表面通量因子（物质坐标为 1/R，固定域为 1）。

    interface_mode="mean" 为生产用的守恒型：界面物性取算术平均，相邻控制体共享
    同一个通量表达式，离散守恒因此是恒等式。="node" 是 B-14/P2-C1(d) 的反例通道：
    每个控制体各用自己的节点物性算出流出量，同一界面两侧不再相等，守恒被破坏。
    """
    n = phi_old.size
    if interface_mode == "mean":
        gamma_face = 0.5 * (gamma[:-1] + gamma[1:])      # 界面物性算术平均，相邻控制体共享
        trans_out = trans_in = diff_scale * faces * gamma_face / delta
    elif interface_mode == "node":
        trans_out = diff_scale * faces * gamma[:-1] / delta
        trans_in = diff_scale * faces * gamma[1:] / delta
    else:
        raise ValueError(f"未知 interface_mode: {interface_mode}")
    ab = np.zeros((3, n), dtype=float)
    rhs = capacity * weights * phi_old / dt
    diag = capacity * weights / dt
    diag[:-1] += trans_out
    diag[1:] += trans_in
    ab[0, 1:] = -trans_out                                # 上对角
    ab[2, :-1] = -trans_in                                # 下对角
    surf = surf_scale * span * sigma                      # Robin：[rΓ∂φ/∂r]_R = -R σ (φ_N-φ_inf)
    diag[-1] += surf
    rhs[-1] += surf * phi_inf
    ab[1, :] = diag
    return solve_banded((1, 1), ab, rhs)


def picard_step(T_old, C_old, group, dt, T_inf, C_inf, span, weights, faces, delta,
                diff_scale=1.0, surf_scale=1.0, hm=None, h=None,
                D_kwargs=None, capacity_scale=1.0, interface_mode="mean"):
    """一个时间步的双向强耦合：更新物性 → 解 T → 用新 T 更新 D → 解 C，Picard 迭代。

    返回 (T_new, C_new, n_rounds)。系数取自上一轮迭代值，未知量线性出现。
    """
    hm = P.HM_CONV if hm is None else hm
    h = P.H_CONV if h is None else h
    D_kwargs = D_kwargs or {}
    T_new, C_new = T_old.copy(), C_old.copy()
    rounds = 0
    for _ in range(P.PICARD_ROUNDS):
        rounds += 1
        cap_T = capacity_scale * group.capacity(C_new)
        gamma_T = group.k(C_new)
        T_try = solve_diffusion_step(T_old, cap_T, gamma_T, weights, faces, delta, dt,
                                     h, T_inf, span, diff_scale, surf_scale,
                                     interface_mode=interface_mode)
        gamma_C = group.D(C_new, T_try, **D_kwargs)
        cap_C = np.ones_like(C_old)              # 干基含水率的容量项恒为 1，不再乘绝干密度
        C_try = solve_diffusion_step(C_old, cap_C, gamma_C, weights, faces, delta, dt,
                                     hm, C_inf, span, diff_scale, surf_scale,
                                     interface_mode=interface_mode)
        dT = float(np.max(np.abs(T_try - T_new)))
        dC = float(np.max(np.abs(C_try - C_new)))
        T_new, C_new = T_try, C_try
        if dT < P.PICARD_TOL_T and dC < P.PICARD_TOL_C:
            break
    return T_new, C_new, rounds


def domain_moisture(C, weights, span):
    """M(t) = (2/S²)Σ w_j C_j，面体比归一后与累计流出同量纲。"""
    return 2.0 / span ** 2 * float(np.dot(weights, C))


def outflow_increment(C_surface, C_inf, radius_m, dt, hm=None):
    """dQ = (2 h_m / R) (C_R - C_inf) dt，取隐式时刻的表面值。"""
    hm = P.HM_CONV if hm is None else hm
    return 2.0 * hm / radius_m * (C_surface - C_inf) * dt


def mass_residual(M_now: float, Q_now: float) -> float:
    """eps_M = |(C0 - M) - Q| / max(Q, 1e-30)（§6.4）。"""
    return abs((P.C0 - M_now) - Q_now) / max(Q_now, 1e-30)


def refine_threshold_crossing(t_prev, max_prev, t_now, max_now, threshold=None):
    """阈值首达时刻的线性插值细化（MC-06），不取网格点整数倍。"""
    threshold = P.C_TH if threshold is None else threshold
    if max_now == max_prev:
        return t_now
    frac = (max_prev - threshold) / (max_prev - max_now)
    return t_prev + frac * (t_now - t_prev)


def explicit_stability_dt(delta, D_max, alpha_max):
    """显式格式稳定步长 0.9*min(dr²/(2 D_max), dr²/(2 alpha_max))（B-18）。"""
    return 0.9 * min(delta ** 2 / (2.0 * D_max), delta ** 2 / (2.0 * alpha_max))


def operator_row_bound_dt(capacity, gamma, weights, faces, delta, sigma, span,
                          safety=0.9):
    """显式格式的算子行和界：dt <= safety / max_j (Σ|a_jk| / (S_j w_j))。

    B-18 的 dr²/(2Γ) 是内部节点的经典界；r=0 的半控制体权重为 δ²/8（而非 δ²），
    其系数比内部节点大一倍，故真实稳定界更紧。取两者较小值才不会溢出。
    """
    gamma_face = 0.5 * (gamma[:-1] + gamma[1:])
    trans = faces * gamma_face / delta
    row = np.zeros_like(weights)
    row[:-1] += trans
    row[1:] += trans
    row[-1] += span * sigma
    return safety / float(np.max(row / (capacity * weights)))


def _kernel_self_check() -> dict:
    """内核层守恒性：权重求和、零通量闭合、纯内部再分布守恒。"""
    n, span = P.N_CELLS, P.R0_M
    delta = span / n
    w = cell_weights(n, span)
    faces = face_radii(n, span)
    if abs(float(w.sum()) - span ** 2 / 2.0) > 1e-18:
        raise AssertionError(f"Σw_j={w.sum()} != R²/2={span ** 2 / 2.0}")
    if abs(float(faces[0]) - delta / 2.0) > 1e-18:
        raise AssertionError("内界面首点应为 δ/2")

    # hm=0 保留 D：只有内部再分布，总水分严格守恒，C 趋于均匀
    C = P.C0 * (1.0 + 0.3 * np.cos(np.pi * node_coords(n, span) / span))
    M_ini = domain_moisture(C, w, span)
    gamma = np.full(n + 1, 1e-8)
    cap = np.ones(n + 1)
    spread_ini = float(C.max() - C.min())
    for _ in range(200):
        C = solve_diffusion_step(C, cap, gamma, w, faces, delta, 10.0, 0.0, 0.0, span)
    M_end = domain_moisture(C, w, span)
    drift_redistribution = abs(M_end / M_ini - 1.0)
    if drift_redistribution >= 1e-6:
        raise AssertionError(f"hm=0 内部再分布漂移 {drift_redistribution:.3e} 未守恒")
    if not float(C.max() - C.min()) < spread_ini:
        raise AssertionError("纯扩散未使剖面趋于均匀")

    # T_inf=T0 且 C_inf=C0：两场恒定不变
    C_flat = np.full(n + 1, P.C0)
    C_hold = solve_diffusion_step(C_flat, cap, gamma, w, faces, delta, 10.0,
                                  P.HM_CONV, P.C0, span)
    hold_dev = float(np.max(np.abs(C_hold - P.C0))) / P.C0
    if hold_dev > 1e-14:
        raise AssertionError(f"环境=初值时水分场应恒定，实测相对偏差 {hold_dev:.3e}")
    return {
        "weight_sum_vs_R2_half": float(w.sum()) - span ** 2 / 2.0,
        "drift_hm_zero": drift_redistribution,
        "spread_before": spread_ini,
        "spread_after": float(C.max() - C.min()),
        "hold_case_rel_dev": hold_dev,
    }


if __name__ == "__main__":
    for key, val in _kernel_self_check().items():
        print(f"  {key} = {val:.6e}")
    print("[fvkernel] 守恒型有限体积内核 OK")
