# -*- coding: utf-8 -*-
"""
问题 4：考虑尺寸收缩的药材烘干时长（附录 4 变物性 + 移动边界）

独立程序，不依赖任何自定义模块，可直接运行：
    python solve_p4.py
输出：
    ../data/result4.xlsx    水分浓度（含"药材表面"列），每 60 s、到中心每 0.1 cm
    _p4.npz                 供绘图脚本使用的求解结果缓存
并在终端打印论文表 6。

------------------------------------------------------------
移动边界处理
    药材失水收缩，半径 R(t) 由附件 2 给定（PCHIP 保单调插值）。
    采用固定网格 + 活动节点数的方式处理：
        Δr = R0/N 固定；活动节点数 M = floor(R(t)/Δr)；
        真实表面与最后一个节点间存在残余薄层 δ = R(t) - M·Δr。
    将残余薄层视为与表面对流阻力串联的导热/扩散热阻，得等效系数

        h_eff   = 1 / (1/h   + δ/k)
        h_m,eff = 1 / (1/h_m + δ/D)

    表面温度/含水率由该串联关系外推：
        T_s = (k/δ·T_M + h·T_air) / (k/δ + h)
        C_s = (D/δ·C_M + h_m·C_air) / (D/δ + h_m)

    随 R(t) 减小，M 逐级下降，超出 M 的节点置为无效（输出为空白）。
    注：该处理忽略了收缩引起的对流输运项，属工程近似。

物性与判据
    物性采用附录 4 经验公式；干燥判据同问题 3（全场 C < 0.15 kg/kg）。
    附录 4 未给出 h 与 h_m，沿用附录 2 的 25 W/(m^2.K) 与 8e-7 m/s。
    网格 Δr = 0.005 cm (N=400)，时间步 Δt = 5 s。
"""
import os

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d, PchipInterpolator
from scipy.linalg import solve_banded

# ==================== 路径 ====================
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), 'data')

# ==================== 物理参数 ====================
R0 = 0.02            # 药材初始半径, m
H_CONV = 25.0        # 对流换热系数, W/(m^2.K)  （附录 4 未给出，沿用附录 2）
HM = 8e-7            # 对流传质系数, m/s       （附录 4 未给出，沿用附录 2）
T_AIR_CONST = 50.0   # 恒温段烘房温度, °C
C_AIR_CONST = 0.050  # 恒温段空气水分浓度, kg/kg
T0_INIT = 28.0       # 药材初始温度, °C
C0_INIT = 2.55       # 药材初始干基含水率, kg/kg
THRESH = 0.15        # 烘干判据阈值, kg/kg


# ==================== 附录 4 变物性 ====================
def rho(C):
    return 760.0 + 90.0 * np.asarray(C, float)


def cp(C):
    C = np.asarray(C, float)
    return 1850.0 + 2150.0 * C / (C + 1.0)


def k_cond(C):
    C = np.asarray(C, float)
    return 0.12 + 0.20 * C / (C + 1.0)


def diffusivity(C, T):
    """水分扩散系数 D(C,T)，m^2/s。T 为摄氏温度，内部换算为开尔文。"""
    C = np.asarray(C, float)
    T = np.asarray(T, float)
    return 4.2e-4 * np.exp(-0.30 / np.maximum(C, 1e-6)) * np.exp(-3850.0 / (T + 273.15))


# ==================== 附件数据 ====================
def load_room():
    """读取附件 1，返回 T_air(t)、C_air(t)；超出数据范围取恒温段常数。"""
    df = pd.read_excel(os.path.join(DATA, '附件1.xlsx'))
    t = df.iloc[:, 0].to_numpy(float)
    T = df.iloc[:, 1].to_numpy(float)
    C = df.iloc[:, 2].to_numpy(float)
    t_end = float(t[-1])
    Tf = interp1d(t, T, kind='linear')
    Cf = interp1d(t, C, kind='linear')

    def T_air(tt):
        tt = np.asarray(tt, float)
        return np.where(tt <= t_end,
                        Tf(np.clip(tt, t[0], t_end)), T_AIR_CONST)

    def C_air(tt):
        tt = np.asarray(tt, float)
        return np.where(tt <= t_end,
                        Cf(np.clip(tt, t[0], t_end)), C_AIR_CONST)

    return T_air, C_air, t_end


def load_radius():
    """读取附件 2 的半径数据，用 PCHIP 保单调插值构造 R(t)（单位 m）。"""
    df = pd.read_excel(os.path.join(DATA, '附件2.xlsx'))
    t = df.iloc[:, 0].to_numpy(float)
    R = df.iloc[:, 1].to_numpy(float) / 100.0        # cm -> m
    return PchipInterpolator(t, R, extrapolate=True), t, R


# ==================== Crank-Nicolson 单步（含移动边界） ====================
def _heat_cn(Tn, Cmid, Tair0, Tair1, dr, dt, Rs, M):
    """传热 C-N 半步：由 T^n 到 T^{n+1}，物性取 Cmid 处之值。"""
    n = M + 1
    rho_v = rho(Cmid)
    cp_v = cp(Cmid)
    k_v = k_cond(Cmid)
    kf = 0.5 * (k_v[:-1] + k_v[1:])
    low = np.zeros(n)
    diag = np.zeros(n)
    up = np.zeros(n)

    g0 = 4.0 * kf[0] / (rho_v[0] * cp_v[0] * dr ** 2)
    diag[0] = -g0
    up[0] = g0

    i = np.arange(1, M)
    w = ((i - 0.5) / i) * kf[i - 1] / (rho_v[i] * cp_v[i] * dr ** 2)
    e = ((i + 0.5) / i) * kf[i] / (rho_v[i] * cp_v[i] * dr ** 2)
    low[i] = w
    diag[i] = -(w + e)
    up[i] = e

    # 表面节点：残余薄层 δ 折算为附加热阻
    rM = M * dr
    rL = rM - 0.5 * dr
    delta = Rs - rM
    kM = k_v[M]
    h_eff = 1.0 / (1.0 / H_CONV + delta / max(kM, 1e-12))
    denom = rho_v[M] * cp_v[M] * (Rs ** 2 - rL ** 2)
    p = 2.0 * rL * kf[M - 1] / (denom * dr)
    q = 2.0 * Rs * h_eff / denom
    low[M] = p
    diag[M] = -(p + q)

    MT = np.zeros(n)
    MT[0] = diag[0] * Tn[0] + up[0] * Tn[1]
    MT[1:-1] = low[1:-1] * Tn[:-2] + diag[1:-1] * Tn[1:-1] + up[1:-1] * Tn[2:]
    MT[-1] = low[-1] * Tn[-2] + diag[-1] * Tn[-1]

    rhs = Tn + 0.5 * dt * MT
    rhs[-1] += 0.5 * dt * q * (Tair1 + Tair0)

    ab = np.zeros((3, n))
    ab[0, 1:] = (-0.5 * dt * up)[:-1]
    ab[1, :] = 1.0 - 0.5 * dt * diag
    ab[2, :-1] = (-0.5 * dt * low)[1:]
    return solve_banded((1, 1), ab, rhs)


def _moist_cn(Cn, Cmid, Tmid, Cair0, Cair1, dr, dt, Rs, M):
    """传质 C-N 半步：由 C^n 到 C^{n+1}，扩散系数取 (Cmid, Tmid) 处之值。"""
    n = M + 1
    D_v = diffusivity(Cmid, Tmid)
    Df = 0.5 * (D_v[:-1] + D_v[1:])
    low = np.zeros(n)
    diag = np.zeros(n)
    up = np.zeros(n)

    g0 = 4.0 * Df[0] / dr ** 2
    diag[0] = -g0
    up[0] = g0

    i = np.arange(1, M)
    w = ((i - 0.5) / i) * Df[i - 1] / dr ** 2
    e = ((i + 0.5) / i) * Df[i] / dr ** 2
    low[i] = w
    diag[i] = -(w + e)
    up[i] = e

    # 表面节点：残余薄层 δ 折算为附加传质阻力
    rM = M * dr
    rL = rM - 0.5 * dr
    delta = Rs - rM
    DM = D_v[M]
    h_eff = 1.0 / (1.0 / HM + delta / max(DM, 1e-20))
    denom = Rs ** 2 - rL ** 2
    p = 2.0 * rL * Df[M - 1] / (denom * dr)
    q = 2.0 * Rs * h_eff / denom
    low[M] = p
    diag[M] = -(p + q)

    MC = np.zeros(n)
    MC[0] = diag[0] * Cn[0] + up[0] * Cn[1]
    MC[1:-1] = low[1:-1] * Cn[:-2] + diag[1:-1] * Cn[1:-1] + up[1:-1] * Cn[2:]
    MC[-1] = low[-1] * Cn[-2] + diag[-1] * Cn[-1]

    rhs = Cn + 0.5 * dt * MC
    rhs[-1] += 0.5 * dt * q * (Cair1 + Cair0)

    ab = np.zeros((3, n))
    ab[0, 1:] = (-0.5 * dt * up)[:-1]
    ab[1, :] = 1.0 - 0.5 * dt * diag
    ab[2, :-1] = (-0.5 * dt * low)[1:]
    return solve_banded((1, 1), ab, rhs)


# ==================== 主求解 ====================
def simulate(t_end, dt, N, out_times, out_r, n_iter=4, drying_thresh=None):
    """
    求解问题 4，返回 (T_out, C_out, t_out, R_out, C_surf, T_end)。
    输出网格为固定物理距离 out_r，超出当前半径的节点填 NaN。
    """
    T_air, C_air, _ = load_room()
    Rspl, _, _ = load_radius()
    dr = R0 / N
    T = np.full(N + 1, T0_INIT)
    C = np.full(N + 1, C0_INIT)

    out_times = np.asarray(out_times, float)
    out_r = np.asarray(out_r, float)
    out_idx = np.rint(out_r / dr).astype(int)
    n_out = len(out_times)

    def snapshot(M):
        idx = np.where(out_idx <= M, out_idx, -1)
        Trow = np.where(idx >= 0, T[np.clip(idx, 0, None)], np.nan)
        Crow = np.where(idx >= 0, C[np.clip(idx, 0, None)], np.nan)
        return Trow, Crow

    def surface_vals(M, Rs, Tair, Cair):
        """由表面薄层的串联阻力关系外推真实表面温度与含水率。"""
        delta = Rs - M * dr
        if delta <= 1e-12:
            return T[M], C[M]
        kM = k_cond(C[:M + 1])[M]
        DM = diffusivity(C[:M + 1], T[:M + 1])[M]
        Ts = (kM / delta * T[M] + H_CONV * Tair) / (kM / delta + H_CONV)
        Cs = (DM / delta * C[M] + HM * Cair) / (DM / delta + HM)
        return Ts, Cs

    T_list, C_list, t_list, R_list, Cs_list = [], [], [], [], []
    out_ptr = 0
    T_end = t_end

    for step in range(1, int(round(t_end / dt)) + 1):
        t_now = (step - 1) * dt
        t_next = step * dt
        Tair0, Tair1 = T_air(t_now), T_air(t_next)
        Cair0, Cair1 = C_air(t_now), C_air(t_next)

        Rs = float(np.clip(float(Rspl(t_next)), 1e-3, R0))
        M = max(int(np.floor(Rs / dr + 1e-12)), 1)

        Ta, Ca = T[:M + 1].copy(), C[:M + 1].copy()
        Tnew, Cnew = Ta.copy(), Ca.copy()
        for _ in range(n_iter):
            Cmid = 0.5 * (Ca + Cnew)
            Tmid = 0.5 * (Ta + Tnew)
            Tnew = _heat_cn(Ta, Cmid, Tair0, Tair1, dr, dt, Rs, M)
            Cnew = _moist_cn(Ca, Cmid, Tmid, Cair0, Cair1, dr, dt, Rs, M)

        T[:M + 1] = Tnew
        C[:M + 1] = Cnew
        T[M + 1:] = np.nan
        C[M + 1:] = np.nan

        while out_ptr < n_out and t_next >= out_times[out_ptr] - 0.5 * dt:
            Trow, Crow = snapshot(M)
            T_list.append(Trow)
            C_list.append(Crow)
            R_list.append(Rs)
            t_list.append(out_times[out_ptr])
            _, Cs = surface_vals(M, Rs, Tair1, Cair1)
            Cs_list.append(Cs)
            out_ptr += 1

        # ---- 干燥判据 ----
        if drying_thresh is not None and np.nanmax(C[:M + 1]) < drying_thresh:
            T_end = t_next
            if not t_list or abs(t_list[-1] - t_next) > 1e-9:
                Trow, Crow = snapshot(M)
                T_list.append(Trow)
                C_list.append(Crow)
                R_list.append(Rs)
                t_list.append(t_next)
                _, Cs = surface_vals(M, Rs, Tair1, Cair1)
                Cs_list.append(Cs)
            break

    return (np.array(T_list), np.array(C_list), np.array(t_list),
            np.array(R_list), np.array(Cs_list), T_end)


# ==================== 写出 xlsx ====================
def write_result_xlsx(path, sheets, times, distances, round_dec=4):
    """按附件 3 模板写出结果文件。"""
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    header = ['时间\\到药材中心的距离'] + list(distances)
    for name, val in sheets:
        ws = wb.create_sheet(name)
        ws.append(header)
        for k, t in enumerate(times):
            row = [t]
            for v in val[k]:
                row.append(None if (v is None or np.isnan(v))
                           else round(float(v), round_dec))
            ws.append(row)
    wb.save(path)


# ==================== 主程序 ====================
def main():
    N = 400                 # 求解网格：Δr = 0.005 cm
    dt = 5.0                # 时间步长, s
    t_end = 540000.0        # 积分上限 150 h

    print('=' * 72)
    print('问题 4  尺寸收缩下的烘干时长（附录 4 变物性，移动边界）')
    print('=' * 72)

    out_times = np.arange(60.0, t_end + 1e-9, 60.0)     # 每 60 s
    out_r = np.arange(0.0, 0.019001, 0.001)             # 固定距离 0~1.9 cm

    T, C, t, R, C_surf, T_end = simulate(t_end, dt, N, out_times, out_r,
                                         drying_thresh=THRESH)

    print(f'烘干结束时间 t* = {T_end:.1f} s = {T_end/3600:.4f} h '
          f'= {T_end/86400:.2f} 天')
    print(f'结束时刻 max(C) = {np.nanmax(C[-1]):.6f} kg/kg（应 < {THRESH}）')
    print(f'结束时刻表面半径 R = {R[-1]*100:.4f} cm '
          f'（初始 {R[0]*100:.4f} cm，收缩 {(1-R[-1]/R[0])*100:.1f}%）')
    print(f'求解步数：{len(t)} 个输出时刻 × {C.shape[1]} 个固定径向位置')

    # ---------- 论文表 6 ----------
    tbl_t = list(np.arange(21600.0, T_end + 1e-9, 21600.0)) + [T_end]
    print('-' * 72)
    print('表 6  药材烘干过程的水分浓度 (kg/kg)')
    print('时间/h       0.0cm       0.5cm       1.0cm       1.5cm     药材表面')
    for th in tbl_t:
        i = int(np.argmin(np.abs(t - th)))
        vals = [C[i, 0], C[i, 5], C[i, 10], C[i, 15], C_surf[i]]
        cells = ''.join('           —' if not np.isfinite(v) else f'{v:>12.4f}'
                        for v in vals)
        print(f'{th/3600:>7.2f}  {cells}')
    print('=' * 72)

    # ---------- 写出 result4.xlsx ----------
    C_full = np.column_stack([C, C_surf])
    dist_header = [round(float(x) * 100.0, 1) for x in out_r] + ['药材表面']
    path = os.path.join(DATA, 'result4.xlsx')
    write_result_xlsx(path,
                      sheets=[('Sheet1', C_full)],
                      times=[int(round(x)) for x in t],
                      distances=dist_header)
    print(f'已写出 {path}：{len(t)} 行 × {len(dist_header)} 列')

    # ---------- 缓存供绘图使用 ----------
    cache = os.path.join(HERE, '_p4.npz')
    np.savez(cache, t=t, C=C, C_surf=C_surf, R=R, r=out_r, T_end=T_end)
    print(f'已写出 {cache}')


if __name__ == '__main__':
    main()
