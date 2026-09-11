# -*- coding: utf-8 -*-
"""
问题 3：确定药材烘干所需时间（附录 3 变物性 + 干燥判据）

独立程序，不依赖任何自定义模块，可直接运行：
    python solve_p3.py
输出：
    ../data/result3.xlsx    水分浓度，每 60 s、到中心每 0.1 cm
    _p3.npz                 供绘图脚本使用的求解结果缓存
并在终端打印论文表 5。

------------------------------------------------------------
干燥判据
    "药材各处的水分浓度应低于 0.15 kg/kg"。
    由于中心 r=0 距表面最远、水分最难逸出，全场最大含水率始终出现在中心，
    故判据  max_{0<=r<=R} C(r,t) < 0.15  等价于  C(0,t) < 0.15。
    代码中仍按 max(C) 逐时刻检查，首次满足的时刻即为烘干结束时间 t*。

模型与数值方法
    与问题 2 完全相同的变物性耦合模型（附录 3）与控制体积 / Crank-Nicolson
    格式；不同之处仅在于积分终止条件。
    网格 Δr = 0.005 cm (N=400)，时间步 Δt = 5 s，积分上限 100 h。

参数说明
    附录 3 未给出对流换热系数 h 与对流传质系数 h_m，沿用附录 2 的
    h = 25 W/(m^2.K)、h_m = 8e-7 m/s。
"""
import os

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.linalg import solve_banded

# ==================== 路径 ====================
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), 'data')

# ==================== 物理参数 ====================
R0 = 0.02            # 药材初始半径, m
H_CONV = 25.0        # 对流换热系数, W/(m^2.K)  （附录 3 未给出，沿用附录 2）
HM = 8e-7            # 对流传质系数, m/s       （附录 3 未给出，沿用附录 2）
T_AIR_CONST = 50.0   # 恒温段烘房温度, °C
C_AIR_CONST = 0.050  # 恒温段空气水分浓度, kg/kg
T0_INIT = 28.0       # 药材初始温度, °C
C0_INIT = 2.55       # 药材初始干基含水率, kg/kg
THRESH = 0.15        # 烘干判据阈值, kg/kg


# ==================== 附录 3 变物性 ====================
def rho(C):
    return 650.0 + 128.0 * np.asarray(C, float)


def cp(C):
    C = np.asarray(C, float)
    return 1450.0 + 2736.0 * C / (C + 1.0)


def k_cond(C):
    C = np.asarray(C, float)
    return 0.21 + 0.38 * C / (C + 1.0)


def diffusivity(C, T):
    """水分扩散系数 D(C,T)，m^2/s。T 为摄氏温度，内部换算为开尔文。"""
    C = np.asarray(C, float)
    T = np.asarray(T, float)
    return 2.4e-3 * np.exp(-0.45 / np.maximum(C, 1e-6)) * np.exp(-3850.0 / (T + 273.15))


# ==================== 附件 1：烘房环境 ====================
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


# ==================== Crank-Nicolson 单步 ====================
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

    rM = M * dr
    rL = rM - 0.5 * dr
    denom = rho_v[M] * cp_v[M] * (Rs ** 2 - rL ** 2)
    p = 2.0 * rL * kf[M - 1] / (denom * dr)
    q = 2.0 * Rs * H_CONV / denom
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

    rM = M * dr
    rL = rM - 0.5 * dr
    denom = Rs ** 2 - rL ** 2
    p = 2.0 * rL * Df[M - 1] / (denom * dr)
    q = 2.0 * Rs * HM / denom
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
    求解问题 3，返回 (T_out, C_out, t_out, C_surf, T_end)。
    drying_thresh 非空时，当 max(C) 首次低于该阈值即终止并返回该时刻。
    """
    T_air, C_air, _ = load_room()
    dr = R0 / N
    T = np.full(N + 1, T0_INIT)
    C = np.full(N + 1, C0_INIT)

    out_times = np.asarray(out_times, float)
    out_r = np.asarray(out_r, float)
    out_idx = np.rint(out_r / dr).astype(int)
    n_out = len(out_times)

    T_list, C_list, t_list, Cs_list = [], [], [], []
    out_ptr = 0
    T_end = t_end

    for step in range(1, int(round(t_end / dt)) + 1):
        t_now = (step - 1) * dt
        t_next = step * dt
        Tair0, Tair1 = T_air(t_now), T_air(t_next)
        Cair0, Cair1 = C_air(t_now), C_air(t_next)
        Rs, M = R0, N

        Ta, Ca = T[:M + 1].copy(), C[:M + 1].copy()
        Tnew, Cnew = Ta.copy(), Ca.copy()
        for _ in range(n_iter):
            Cmid = 0.5 * (Ca + Cnew)
            Tmid = 0.5 * (Ta + Tnew)
            Tnew = _heat_cn(Ta, Cmid, Tair0, Tair1, dr, dt, Rs, M)
            Cnew = _moist_cn(Ca, Cmid, Tmid, Cair0, Cair1, dr, dt, Rs, M)

        T[:M + 1] = Tnew
        C[:M + 1] = Cnew

        while out_ptr < n_out and t_next >= out_times[out_ptr] - 0.5 * dt:
            T_list.append(T[out_idx])
            C_list.append(C[out_idx])
            Cs_list.append(C[M])
            t_list.append(out_times[out_ptr])
            out_ptr += 1

        # ---- 干燥判据：全场水分浓度均低于阈值 ----
        if drying_thresh is not None and np.nanmax(C[:M + 1]) < drying_thresh:
            T_end = t_next
            if not t_list or abs(t_list[-1] - t_next) > 1e-9:
                T_list.append(T[out_idx])
                C_list.append(C[out_idx])
                Cs_list.append(C[M])
                t_list.append(t_next)
            break

    return (np.array(T_list), np.array(C_list), np.array(t_list),
            np.array(Cs_list), T_end)


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
    t_end = 360000.0        # 积分上限 100 h

    print('=' * 68)
    print('问题 3  烘干所需时间（附录 3 变物性，判据 C < 0.15 kg/kg）')
    print('=' * 68)

    out_times = np.arange(60.0, t_end + 1e-9, 60.0)     # 每 60 s
    out_r = np.arange(0.0, 0.020001, 0.001)             # 0~2 cm 每 0.1 cm

    T, C, t, C_surf, T_end = simulate(t_end, dt, N, out_times, out_r,
                                      drying_thresh=THRESH)

    print(f'烘干结束时间 t* = {T_end:.1f} s = {T_end/3600:.4f} h '
          f'= {T_end/86400:.2f} 天')
    print(f'结束时刻 max(C) = {np.nanmax(C[-1]):.6f} kg/kg（应 < {THRESH}）')
    print(f'求解步数：{len(t)} 个输出时刻 × {C.shape[1]} 个径向位置')

    # ---------- 论文表 5 ----------
    tbl_r = [0.0, 0.005, 0.010, 0.015, 0.020]
    r_idx = [int(round(rr / 0.001)) for rr in tbl_r]
    tbl_t = list(np.arange(21600.0, T_end + 1e-9, 21600.0)) + [T_end]

    print('-' * 68)
    print('表 5  药材烘干过程的水分浓度 (kg/kg)')
    print('时间/h   ' + ''.join(f'{rr*100:>11.1f}cm' for rr in tbl_r))
    for th in tbl_t:
        i = int(np.argmin(np.abs(t - th)))
        print(f'{th/3600:>7.2f}  ' + ''.join(f'{C[i, j]:>13.4f}' for j in r_idx))
    print('=' * 68)

    # ---------- 写出 result3.xlsx ----------
    dist_header = [round(float(x) * 100.0, 1) for x in out_r]
    path = os.path.join(DATA, 'result3.xlsx')
    write_result_xlsx(path,
                      sheets=[('Sheet1', C)],
                      times=[int(round(x)) for x in t],
                      distances=dist_header)
    print(f'已写出 {path}：{len(t)} 行 × {len(dist_header)} 列')

    # ---------- 缓存供绘图使用 ----------
    cache = os.path.join(HERE, '_p3.npz')
    np.savez(cache, t=t, C=C, T=T, r=out_r, C_surf=C_surf, T_end=T_end)
    print(f'已写出 {cache}')


if __name__ == '__main__':
    main()
