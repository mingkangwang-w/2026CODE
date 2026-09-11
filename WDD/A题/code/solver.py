# -*- coding: utf-8 -*-
"""核心求解器：圆柱径向热-质双场，有限体积守恒格式。

固定域（问题1-3）与动域（问题4，eta=r/R(t) 归一化坐标）。
节点 x_i = i*dx, i=0..N-1（固定域 x=r∈[0,R0]；动域 x=η∈[0,1]）。

离散方程（热方程除以 rc=rho*cp，质量方程不除）：
  内部 i=1..N-2: dphi_i = (F_{i+1/2}-F_{i-1/2})/(x_i*dx),  F = x_f*Gam*dphi/dx
  中心 i=0      : dphi_0 = 4*Gam_f[0]*(phi_1-phi_0)/dx^2        (L'Hopital)
  表面 i=N-1（固定域，半控制体 2/(R0*dx)）:
      dphi_s = (2/(R0*dx)) * ( xf*Gam_f*(phi_{N-2}-phi_s)/dx - R0*h*(phi_s-phi_inf) )
  表面 i=N-1（动域，Gam 已含 1/R^2，表面通量 -h*(phi_s-phi_inf)/R）:
      dphi_s = (2/dx) * ( xf*Gam_f*(phi_{N-2}-phi_s)/dx - h*(phi_s-phi_inf)/R(t) )

注意：通量 F 已含 1/dx，散度只再除一个 dx（多除一个 → 等效步长放大 1/dx 倍 → 必炸）。

时间格式：隐式 Backward Euler + Picard 迭代；另备显式用于交叉验证。
动域附加伪对流项 v_i = eta_i*Rdot/R（<=0，迎风=前向差分）。
"""
import numpy as np
from scipy.linalg import solve_banded

from properties import H_CONV, HM_CONV, T0, C0, R0, C_THRESHOLD


def _iface(a):
    return 0.5 * (a[1:] + a[:-1])


def _assemble(N, dx, x, Gam_f, rc, dt, h_bc, fixed, Rnow, v=None):
    """装配隐式步 (I - dt*L) phi = phi_old + rhs_add 的三对角系数。

    Gam_f : 界面输运系数（动域时已除以 R^2），长度 N-1
    rc    : 节点 rho*cp（热方程）或 None（质量方程）
    h_bc  : 表面对流系数（h 或 h_m）
    fixed : True=固定域（R=R0），False=动域（R=Rnow）
    Rnow  : 当前半径（固定域传 R0）
    v     : 伪对流速度（动域，形状 (N,)），固定域 None
    返回 lower, diag, upper, rhs_conv（表面边界对角的 delta 系数，供 rhs 用）
    """
    lower = np.zeros(N - 1)
    diag = np.ones(N)
    upper = np.zeros(N - 1)
    rcp = np.ones(N) if rc is None else rc
    xf = 0.5 * (x[1:] + x[:-1])

    # 内部 i=1..N-2
    a = dt * xf[:-1] * Gam_f[:-1] / (x[1:-1] * dx * dx * rcp[1:-1])
    c = dt * xf[1:] * Gam_f[1:] / (x[1:-1] * dx * dx * rcp[1:-1])
    lower[0:N - 2] = -a          # lower[i-1] 是第 i 行的次对角元（i=1..N-2）
    diag[1:N - 1] += a + c
    upper[1:N - 1] = -c

    # 中心 i=0
    beta = 4.0 * dt * Gam_f[0] / (dx * dx * rcp[0])
    diag[0] += beta
    upper[0] = -beta

    # 表面 i=N-1（半控制体）
    if fixed:
        gam = 2.0 * dt * xf[-1] * Gam_f[-1] / (R0 * dx * dx * rcp[-1])
        dlt = 2.0 * dt * h_bc / (dx * rcp[-1])
    else:
        gam = 2.0 * dt * xf[-1] * Gam_f[-1] / (dx * dx * rcp[-1])
        dlt = 2.0 * dt * h_bc / (Rnow * dx * rcp[-1])
    lower[N - 2] = -gam
    diag[N - 1] += gam + dlt

    # 伪对流（动域）：内部二阶中心差分 v*(phi_{i+1}-phi_{i-1})/(2dx)，
    # 表面一阶后向差分 v*(phi_s-phi_{N-2})/dx
    if v is not None:
        w2 = dt * v / (2.0 * dx)
        upper[1:N - 1] += -w2[1:N - 1]
        lower[0:N - 2] += w2[1:N - 1]
        ws = dt * v[N - 1] / dx
        diag[N - 1] += -ws
        lower[N - 2] += ws
    return lower, diag, upper, dlt


def _solve_tri(lower, diag, upper, rhs):
    ab = np.zeros((3, len(diag)))
    ab[0, 1:] = upper
    ab[1, :] = diag
    ab[2, :-1] = lower
    return solve_banded((1, 1), ab, rhs)


def solve(props, N, dt, t_end, bc_func, method='implicit', picard=2,
          R_func=None, Rdot_func=None, r_out=None, t_out=None,
          stop_at_threshold=False):
    """求解热-质双场，返回时间序列与采样剖面。"""
    fixed = R_func is None
    x = np.linspace(0.0, R0, N) if fixed else np.linspace(0.0, 1.0, N)
    dx = x[1] - x[0]
    xg = x / (R0 if fixed else 1.0)          # 归一化坐标（输出插值用）

    T = np.full(N, T0)
    C = np.full(N, C0)
    nsteps = int(round(t_end / dt))
    t_star = None

    store = r_out is not None and t_out is not None
    T_hist = np.full((len(t_out), len(r_out)), np.nan) if store else None
    C_hist = np.full((len(t_out), len(r_out)), np.nan) if store else None
    i_out = 0
    diag_t, diag_Cc, diag_Cs, diag_Cmax, diag_Tc, diag_Ts = [], [], [], [], [], []
    mass_series = []                                # FV 一致的水分积分 ∫C x dx（单位长）
    w_int = np.full(N, dx); w_int[0] *= 0.5; w_int[-1] *= 0.5

    def sample(tt):
        nonlocal i_out
        while i_out < len(t_out) and t_out[i_out] <= tt + 1e-9:
            Rnow = R0 if fixed else R_func(min(t_out[i_out], t_end))
            eta = r_out / Rnow
            vT = np.interp(np.minimum(eta, 1.0), xg, T)
            vC = np.interp(np.minimum(eta, 1.0), xg, C)
            out = eta > 1.0 + 1e-12
            vT[out] = np.nan
            vC[out] = np.nan
            T_hist[i_out] = vT
            C_hist[i_out] = vC
            i_out += 1

    if store:
        sample(0.0)
    for n in range(nsteps):
        t = n * dt
        Rnow = R0 if fixed else R_func(t)
        v = None if fixed else (xg * Rdot_func(t) / Rnow)
        Tinf, Cinf = bc_func(t)

        if method == 'explicit':
            T, C = _step_explicit(props, T, C, x, dx, fixed, Rnow, dt, Tinf, Cinf, v)
        else:
            T, C = _step_implicit(props, T, C, x, dx, fixed, Rnow, dt, Tinf, Cinf, v, picard)

        assert np.isfinite(T).all() and np.isfinite(C).all(), f'NaN/Inf at t={t}'
        # 物理界限与单调性断言（HC-12；容差防数值毛刺）
        assert C.min() >= -1e-9 and C.max() <= C0 + 1e-9, f'C 越界 at t={t}'
        assert T.min() >= T0 - 1.0 and T.max() <= max(Tinf, T0) + 1.0, f'T 越界 at t={t}'
        assert (np.diff(C) <= 1e-9).all(), f'C 沿 r 非单调 at t={t}'
        diag_t.append(t + dt)
        diag_Cc.append(C[0]); diag_Cs.append(C[-1]); diag_Cmax.append(C.max())
        diag_Tc.append(T[0]); diag_Ts.append(T[-1])
        mass_series.append(float(np.sum(C * x * w_int)))

        if stop_at_threshold and C.max() < C_THRESHOLD:
            t_star = t + dt
            if len(diag_Cc) >= 2 and diag_Cc[-1] < diag_Cc[-2]:
                frac = (diag_Cc[-2] - C_THRESHOLD) / (diag_Cc[-2] - diag_Cc[-1])
                t_star = t + dt * frac
            break
        if store:
            sample(t + dt)

    return dict(
        t_star=t_star, t_end_reached=diag_t[-1] if diag_t else 0.0,
        times=np.array(diag_t), center_C=np.array(diag_Cc), surf_C=np.array(diag_Cs),
        max_C=np.array(diag_Cmax), center_T=np.array(diag_Tc), surf_T=np.array(diag_Ts),
        mass_series=np.array(mass_series),
        T_hist=T_hist, C_hist=C_hist, r_out=r_out, t_out=t_out,
        T_final=T.copy(), C_final=C.copy(), xg=xg, N=N, dt=dt,
    )


def _step_implicit(props, T, C, x, dx, fixed, Rnow, dt, Tinf, Cinf, v, picard):
    """隐式 BE + Picard 迭代：矩阵在最新迭代值处线性化，RHS 恒为 t^n 层。

    (I - dt*L(T^{(k)}, C^{(k)})) phi^{(k+1)} = phi^n + 边界驱动
    Tn/Cn 为上一时间层的值（RHS 基准，迭代中不变）；
    Ti/Ci 为线性化点，每轮迭代刷新，直到 ||ΔT||<1e-6 且 ||ΔC||<1e-8 或达到 picard 轮上限。
    """
    Tn, Cn = T, C
    Ti, Ci = T, C
    for _ in range(max(2, picard)):
        T_prev, C_prev = Ti, Ci
        rc = props.rho(Ci) * props.cp(Ci)
        kf, Df = _iface(props.k(Ci)), _iface(props.D(Ci, Ti))
        if not fixed:
            kf = kf / Rnow**2
            Df = Df / Rnow**2
        lo, dg, up, dlt_h = _assemble(len(x), dx, x, kf, rc, dt, H_CONV, fixed, Rnow, v)
        Ti = _solve_tri(lo, dg, up, Tn + _rhs_bc(dg, dlt_h, Tinf))
        lo, dg, up, dlt_m = _assemble(len(x), dx, x, Df, None, dt, HM_CONV, fixed, Rnow, v)
        Ci = _solve_tri(lo, dg, up, Cn + _rhs_bc(dg, dlt_m, Cinf))
        if (np.abs(Ti - T_prev).max() < 1e-6
                and np.abs(Ci - C_prev).max() < 1e-8):
            break
    return Ti, Ci


def _rhs_bc(diag, dlt, phi_inf):
    rhs = np.zeros_like(diag)
    rhs[-1] = dlt * phi_inf
    return rhs


def _step_explicit(props, T, C, x, dx, fixed, Rnow, dt, Tinf, Cinf, v):
    rc = props.rho(C) * props.cp(C)
    kf, Df = _iface(props.k(C)), _iface(props.D(C, T))
    if not fixed:
        kf = kf / Rnow**2
        Df = Df / Rnow**2
    xf = 0.5 * (x[1:] + x[:-1])
    dT = np.zeros_like(T); dC = np.zeros_like(C)
    Fh = xf * kf * (T[1:] - T[:-1]) / dx
    Fc = xf * Df * (C[1:] - C[:-1]) / dx
    dT[1:-1] = (Fh[1:] - Fh[:-1]) / (x[1:-1] * dx) / rc[1:-1]
    dC[1:-1] = (Fc[1:] - Fc[:-1]) / (x[1:-1] * dx)
    dT[0] = 4 * kf[0] * (T[1] - T[0]) / dx**2 / rc[0]
    dC[0] = 4 * Df[0] * (C[1] - C[0]) / dx**2
    if fixed:
        dT[-1] = (2/(R0*dx)) * (xf[-1]*kf[-1]*(T[-2]-T[-1])/dx - R0*H_CONV*(T[-1]-Tinf)) / rc[-1]
        dC[-1] = (2/(R0*dx)) * (xf[-1]*Df[-1]*(C[-2]-C[-1])/dx - R0*HM_CONV*(C[-1]-Cinf))
    else:
        dT[-1] = (2/dx) * (xf[-1]*kf[-1]*(T[-2]-T[-1])/dx - H_CONV*(T[-1]-Tinf)/Rnow) / rc[-1]
        dC[-1] = (2/dx) * (xf[-1]*Df[-1]*(C[-2]-C[-1])/dx - HM_CONV*(C[-1]-Cinf)/Rnow)
    if v is not None:                          # 伪对流：迎风（显式+中心差分对纯对流无条件不稳定！）
        dT[1:-1] += v[1:-1] * (T[2:] - T[1:-1]) / dx
        dC[1:-1] += v[1:-1] * (C[2:] - C[1:-1]) / dx
        dT[-1] += v[-1] * (T[-1] - T[-2]) / dx
        dC[-1] += v[-1] * (C[-1] - C[-2]) / dx
    return T + dt*dT, C + dt*dC


def cfl_limit(props, N, fixed=True, Rmin=None):
    """显式稳定步长上限估计（中心节点 4Gam/dx^2 主导）。"""
    C = np.full(N, C0); T = np.full(N, T0)
    rc = props.rho(C) * props.cp(C)
    amax = (props.k(C) / rc).max()
    Dmax = props.D(C, T).max()
    dx = (R0 if fixed else 1.0) / (N - 1)
    scale = 1.0
    if not fixed:
        scale = 1.0 / (Rmin**2)
    return 0.9 * dx**2 / (4.0 * max(amax, Dmax) * scale)
