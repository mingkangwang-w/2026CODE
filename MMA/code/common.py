# -*- coding: utf-8 -*-
"""
2026 CUMCM A题「药材的烘干问题」共享求解模块。

物理模型：长圆柱药材（一维径向），耦合非稳态热传导与水分扩散。
    rho*cp*dT/dt = (1/r) d/dr (r*k*dT/dr)          (0 < r < R)
    dC/dt        = (1/r) d/dr (r*D*dC/dr)          (0 < r < R)
    对称边界  r=0 : dT/dr=0, dC/dr=0
    表面边界  r=R : -k*dT/dr = h(T-T_air),  -D*dC/dr = h_m(C-C_air)
数值方法：节点型控制体积有限差分 + Crank-Nicolson 隐式时间推进，
    传热/传质耦合采用固定点迭代。
"""
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d, PchipInterpolator
from scipy.linalg import solve_banded

DATA = '/home/user/workspace/data'
R0 = 0.02          # 初始半径 m (2 cm)
h_conv = 25.0      # 对流传热系数 W/(m2.K)
hm = 8e-7          # 对流传质系数 m/s
T_AIR_CONST = 50.0  # 恒温干燥阶段烘房温度 °C
C_AIR_CONST = 0.050 # 恒温干燥阶段空气水分浓度 kg/kg
T0_INIT = 28.0     # 药材初始温度 °C
C0_INIT = 2.55     # 药材初始干基含水率 kg/kg


def load_room():
    """加载附件1：烘房温度与空气水分浓度（0~14400s），之后恒温段取常数。"""
    df = pd.read_excel(f'{DATA}/附件1.xlsx')
    t = df['时间'].to_numpy(float)          # s
    T = df['温度'].to_numpy(float)          # °C
    C = df['水分浓度'].to_numpy(float)      # kg/kg
    t_end = float(t[-1])
    Tf = interp1d(t, T, kind='linear')
    Cf = interp1d(t, C, kind='linear')

    def T_air(tt):
        tt = np.asarray(tt, float)
        return np.where(tt <= t_end, Tf(np.clip(tt, t[0], t_end)), T_AIR_CONST)

    def C_air(tt):
        tt = np.asarray(tt, float)
        return np.where(tt <= t_end, Cf(np.clip(tt, t[0], t_end)), C_AIR_CONST)

    return T_air, C_air, t_end


def load_radius():
    """加载附件2：药材半径随时间（三次样条插值），返回 (spline, t, R_m)。"""
    df = pd.read_excel(f'{DATA}/附件2.xlsx')
    t = df['时间'].to_numpy(float)          # s
    R = df['半径'].to_numpy(float) / 100.0  # cm -> m
    Rspl = PchipInterpolator(t, R, extrapolate=True)
    return Rspl, t, R


def props(problem):
    """返回物性经验公式 rho(C), cp(C), k(C), D(C,T[°C])。"""
    if problem == 1:  # 附录2 常物性
        rho = lambda C: np.full_like(np.asarray(C, float), 820.0)
        cp = lambda C: np.full_like(np.asarray(C, float), 2600.0)
        k = lambda C: np.full_like(np.asarray(C, float), 0.36)
        D = lambda C, T: 7e-9 * np.exp(-0.89 / np.maximum(np.asarray(C, float), 1e-6))
    elif problem in (2, 3):  # 附录3
        def rho(C):
            C = np.asarray(C, float); return 650.0 + 128.0 * C
        def cp(C):
            C = np.asarray(C, float); return 1450.0 + 2736.0 * C / (C + 1.0)
        def k(C):
            C = np.asarray(C, float); return 0.21 + 0.38 * C / (C + 1.0)
        def D(C, T):
            C = np.asarray(C, float); T = np.asarray(T, float)
            return 2.4e-3 * np.exp(-0.45 / np.maximum(C, 1e-6)) * np.exp(-3850.0 / (T + 273.15))
    elif problem == 4:  # 附录4
        def rho(C):
            C = np.asarray(C, float); return 760.0 + 90.0 * C
        def cp(C):
            C = np.asarray(C, float); return 1850.0 + 2150.0 * C / (C + 1.0)
        def k(C):
            C = np.asarray(C, float); return 0.12 + 0.20 * C / (C + 1.0)
        def D(C, T):
            C = np.asarray(C, float); T = np.asarray(T, float)
            return 4.2e-4 * np.exp(-0.30 / np.maximum(C, 1e-6)) * np.exp(-3850.0 / (T + 273.15))
    else:
        raise ValueError('problem must be 1,2,3,4')
    return rho, cp, k, D


def _heat_cn(Tn, Cmid, Tair0, Tair1, dr, dt, Rs, M, rho, cp, k):
    """单个 Crank-Nicolson 传热半步：由 T^n -> T^{n+1}（系数用 Cmid）。"""
    n = M + 1
    rho_v = rho(Cmid); cp_v = cp(Cmid); k_v = k(Cmid)
    kf = 0.5 * (k_v[:-1] + k_v[1:])          # 面导热系数，长度 M
    low = np.zeros(n); diag = np.zeros(n); up = np.zeros(n)
    # 中心节点 0（对称）
    g0 = 4.0 * kf[0] / (rho_v[0] * cp_v[0] * dr ** 2)
    diag[0] = -g0; up[0] = g0
    # 内部节点 1..M-1（均匀网格）
    i = np.arange(1, M)
    w = ((i - 0.5) / i) * kf[i - 1] / (rho_v[i] * cp_v[i] * dr ** 2)
    e = ((i + 0.5) / i) * kf[i] / (rho_v[i] * cp_v[i] * dr ** 2)
    low[i] = w; diag[i] = -(w + e); up[i] = e
    # 表面节点 M（Robin 边界 + 移动边界 δ 插值）
    rM = M * dr
    rL = rM - 0.5 * dr                       # 左界面
    delta = Rs - rM                          # 最后半格宽度（固定网格时为0）
    kM = k_v[M]
    h_eff = 1.0 / (1.0 / h_conv + delta / max(kM, 1e-12))
    denom = rho_v[M] * cp_v[M] * (Rs ** 2 - rL ** 2)
    p = 2.0 * rL * kf[M - 1] / (denom * dr)
    q = 2.0 * Rs * h_eff / denom
    low[M] = p; diag[M] = -(p + q)
    # M 矩阵作用于 T^n
    MT = np.zeros(n)
    MT[0] = diag[0] * Tn[0] + up[0] * Tn[1]
    MT[1:-1] = low[1:-1] * Tn[:-2] + diag[1:-1] * Tn[1:-1] + up[1:-1] * Tn[2:]
    MT[-1] = low[-1] * Tn[-2] + diag[-1] * Tn[-1]
    rhs = Tn + 0.5 * dt * MT
    rhs[-1] += 0.5 * dt * q * (Tair1 + Tair0)
    # A = I - 0.5 dt M
    A_low = -0.5 * dt * low; A_diag = 1.0 - 0.5 * dt * diag; A_up = -0.5 * dt * up
    ab = np.zeros((3, n))
    ab[0, 1:] = A_up[:-1]; ab[1, :] = A_diag; ab[2, :-1] = A_low[1:]
    return solve_banded((1, 1), ab, rhs)


def _moist_cn(Cn, Cmid, Tmid, Cair0, Cair1, dr, dt, Rs, M, D):
    """单个 Crank-Nicolson 传质半步：由 C^n -> C^{n+1}（系数用 Cmid,Tmid）。"""
    n = M + 1
    D_v = D(Cmid, Tmid)
    Df = 0.5 * (D_v[:-1] + D_v[1:])
    low = np.zeros(n); diag = np.zeros(n); up = np.zeros(n)
    g0 = 4.0 * Df[0] / dr ** 2
    diag[0] = -g0; up[0] = g0
    i = np.arange(1, M)
    w = ((i - 0.5) / i) * Df[i - 1] / dr ** 2
    e = ((i + 0.5) / i) * Df[i] / dr ** 2
    low[i] = w; diag[i] = -(w + e); up[i] = e
    rM = M * dr
    rL = rM - 0.5 * dr
    delta = Rs - rM
    DM = D_v[M]
    h_eff = 1.0 / (1.0 / hm + delta / max(DM, 1e-20))
    denom = Rs ** 2 - rL ** 2
    p = 2.0 * rL * Df[M - 1] / (denom * dr)
    q = 2.0 * Rs * h_eff / denom
    low[M] = p; diag[M] = -(p + q)
    MC = np.zeros(n)
    MC[0] = diag[0] * Cn[0] + up[0] * Cn[1]
    MC[1:-1] = low[1:-1] * Cn[:-2] + diag[1:-1] * Cn[1:-1] + up[1:-1] * Cn[2:]
    MC[-1] = low[-1] * Cn[-2] + diag[-1] * Cn[-1]
    rhs = Cn + 0.5 * dt * MC
    rhs[-1] += 0.5 * dt * q * (Cair1 + Cair0)
    A_low = -0.5 * dt * low; A_diag = 1.0 - 0.5 * dt * diag; A_up = -0.5 * dt * up
    ab = np.zeros((3, n))
    ab[0, 1:] = A_up[:-1]; ab[1, :] = A_diag; ab[2, :-1] = A_low[1:]
    return solve_banded((1, 1), ab, rhs)


def simulate(problem, t_end, dt, N=200, out_times=None, out_r=None,
             n_iter=4, shrink=False, drying_thresh=None, verbose=False):
    """
    求解烘干过程。
    problem : 1/2/3/4
    t_end   : 总时长 s
    dt      : 时间步长 s
    N       : 求解网格区间数（节点数 N+1）
    out_times : 输出时间点数组（s）
    out_r     : 输出径向距离数组（m）
    shrink    : 是否启用半径收缩（问题4）
    drying_thresh : 若给定，则当 max(C) < 该值时提前停止，返回结束时间
    返回 dict(T_out, C_out, R_out, t_out, T_end)
    """
    rho, cp, k, D = props(problem)
    T_air, C_air, t_pre = load_room()
    Rspl, _, _ = load_radius()
    dr = R0 / N
    T = np.full(N + 1, T0_INIT)
    C = np.full(N + 1, C0_INIT)

    nsteps = int(round(t_end / dt))
    if out_times is None:
        out_times = np.arange(0.0, t_end + 0.5 * dt, dt)
    out_times = np.asarray(out_times, float)

    # 输出网格：固定距离 + 表面列
    if out_r is None:
        out_r = np.arange(0.0, R0 + 1e-9, 0.001)
    out_r = np.asarray(out_r, float)
    out_idx = np.rint(out_r / dr).astype(int)

    n_out = len(out_times)

    def snapshot(T, C, M):
        """把当前解插值到 out_r 网格（超出表面的点填 NaN）。"""
        idx = np.where(out_idx <= M, out_idx, -1)
        Trow = np.where(idx >= 0, T[np.clip(idx, 0, None)], np.nan)
        Crow = np.where(idx >= 0, C[np.clip(idx, 0, None)], np.nan)
        return Trow, Crow

    def surface_vals(T, C, M, Rs, Tair, Cair):
        """表面温度/水分（移动边界时按 Robin 关系由最后节点外推）。"""
        if not shrink:
            return T[M], C[M]
        delta = Rs - M * dr
        if delta <= 1e-12:
            return T[M], C[M]
        kM = k(C[:M + 1])[M]
        DM = D(C[:M + 1], T[:M + 1])[M]
        Ts = (kM / delta * T[M] + h_conv * Tair) / (kM / delta + h_conv)
        Cs = (DM / delta * C[M] + hm * Cair) / (DM / delta + hm)
        return Ts, Cs

    T_list, C_list, R_list, t_list = [], [], [], []
    Ts_list, Cs_list = [], []
    out_ptr = 0
    T_end = t_end

    for step in range(1, nsteps + 1):
        t_now = (step - 1) * dt
        t_next = step * dt
        Tair0 = T_air(t_now); Tair1 = T_air(t_next)
        Cair0 = C_air(t_now); Cair1 = C_air(t_next)
        Rs = float(Rspl(t_next)) if shrink else R0
        Rs = float(np.clip(Rs, 1e-3, R0))
        M = int(np.floor(Rs / dr + 1e-12))
        M = max(M, 1)
        Ta = T[:M + 1].copy(); Ca = C[:M + 1].copy()
        Tnew = Ta.copy(); Cnew = Ca.copy()
        for _ in range(n_iter):
            Cmid = 0.5 * (Ca + Cnew)
            Tmid = 0.5 * (Ta + Tnew)
            Tnew = _heat_cn(Ta, Cmid, Tair0, Tair1, dr, dt, Rs, M, rho, cp, k)
            Cnew = _moist_cn(Ca, Cmid, Tmid, Cair0, Cair1, dr, dt, Rs, M, D)
        T[:M + 1] = Tnew
        C[:M + 1] = Cnew
        T[M + 1:] = np.nan
        C[M + 1:] = np.nan

        # 记录排定输出
        while out_ptr < n_out and t_next >= out_times[out_ptr] - 0.5 * dt:
            Trow, Crow = snapshot(T, C, M)
            T_list.append(Trow); C_list.append(Crow)
            R_list.append(Rs); t_list.append(out_times[out_ptr])
            Ts, Cs = surface_vals(T, C, M, Rs, Tair1, Cair1)
            Ts_list.append(Ts); Cs_list.append(Cs)
            out_ptr += 1

        # 干燥判据
        if drying_thresh is not None:
            cmax = np.nanmax(C[:M + 1])
            if cmax < drying_thresh:
                T_end = t_next
                if not t_list or abs(t_list[-1] - t_next) > 1e-9:
                    Trow, Crow = snapshot(T, C, M)
                    T_list.append(Trow); C_list.append(Crow)
                    R_list.append(Rs); t_list.append(t_next)
                    Ts, Cs = surface_vals(T, C, M, Rs, Tair1, Cair1)
                    Ts_list.append(Ts); Cs_list.append(Cs)
                break

    T_out = np.array(T_list); C_out = np.array(C_list)
    R_out = np.array(R_list); t_out = np.array(t_list)
    T_surf = np.array(Ts_list); C_surf = np.array(Cs_list)
    return dict(T_out=T_out, C_out=C_out, R_out=R_out, t_out=t_out,
                T_end=T_end, T_surf=T_surf, C_surf=C_surf)


def write_result_xlsx(path, sheets, times, distances, round_dec=4):
    """
    写结果 xlsx。sheets: list[(sheet_name, 2D array)]；
    distances: 列头（距离 cm 数值或 '药材表面'）。
    """
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    header = ['时间\\到药材中心的距离'] + list(distances)
    for (name, val) in sheets:
        ws = wb.create_sheet(name)
        ws.append(header)
        for k, t in enumerate(times):
            row = [t]
            for v in val[k]:
                row.append(None if (v is None or (isinstance(v, float) and np.isnan(v))) else round(float(v), round_dec))
            ws.append(row)
    wb.save(path)
