# -*- coding: utf-8 -*-
"""
问题 1：预热平衡阶段药材温度与水分浓度的演化（附录 2 常物性）

独立程序，不依赖任何自定义模块，可直接运行：
    python solve_p1.py
输出：
    ../data/result1.xlsx    温度 / 水分浓度，每 1 s、到中心每 0.1 cm
并在终端打印论文表 1、表 2。

------------------------------------------------------------
物理模型
    长圆柱药材（R = 2 cm，长 25 cm，长径比 12.5，忽略端面效应），
    一维径向非稳态热传导与水分扩散耦合：

        rho*cp*dT/dt = (1/r) d/dr ( r*k*dT/dr )
        dC/dt        = (1/r) d/dr ( r*D(C)*dC/dr )        0 < r < R

    对称边界  r=0 : dT/dr = 0,  dC/dr = 0
    表面边界  r=R : -k*dT/dr = h (T - T_air(t))
                    -D*dC/dr = h_m (C - C_air(t))

    初始条件  T(r,0) = 28 °C,  C(r,0) = 2.55 kg/kg
    烘房环境  T_air(t)、C_air(t) 由附件 1 线性插值给出。

数值方法
    节点型控制体积法空间离散 + Crank-Nicolson 隐式时间推进，
    每步解三对角方程组；D 依赖 C 造成的非线性不做迭代。
    网格 Δr = 0.005 cm (N=400)，时间步 Δt = 0.5 s。
"""
import os

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.linalg import solve_banded

# ==================== 路径 ====================
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), 'data')

# ==================== 物理参数（附录 2） ====================
R0 = 0.02            # 药材初始半径, m
H_CONV = 25.0        # 对流换热系数, W/(m^2.K)
HM = 8e-7            # 对流传质系数, m/s
T0_INIT = 28.0       # 药材初始温度, °C
C0_INIT = 2.55       # 药材初始干基含水率, kg/kg

# 附录 2 常物性
RHO = 820.0          # kg/m^3
CP = 2600.0          # J/(kg.K)
K_COND = 0.36        # W/(m.K)


def diffusivity(C):
    """附录 2 水分扩散系数 D(C), m^2/s。"""
    return 7e-9 * np.exp(-0.89 / np.maximum(np.asarray(C, float), 1e-6))


# ==================== 附件 1：烘房环境 ====================
def load_room():
    """读取附件 1，返回 T_air(t)、C_air(t) 两个线性插值函数。"""
    df = pd.read_excel(os.path.join(DATA, '附件1.xlsx'))
    t = df.iloc[:, 0].to_numpy(float)
    T = df.iloc[:, 1].to_numpy(float)
    C = df.iloc[:, 2].to_numpy(float)
    Tf = interp1d(t, T, kind='linear')
    Cf = interp1d(t, C, kind='linear')
    return Tf, Cf, float(t[-1])


# ==================== Crank-Nicolson 单步 ====================
def _heat_cn(Tn, Cmid, Tair0, Tair1, dr, dt, Rs, M):
    """传热 C-N 半步：由 T^n 到 T^{n+1}，系数用 Cmid 处的常物性。"""
    n = M + 1
    low = np.zeros(n)
    diag = np.zeros(n)
    up = np.zeros(n)

    # 中心节点 0（对称，半控制体）
    g0 = 4.0 * K_COND / (RHO * CP * dr ** 2)
    diag[0] = -g0
    up[0] = g0

    # 内部节点 1..M-1
    i = np.arange(1, M)
    w = ((i - 0.5) / i) * K_COND / (RHO * CP * dr ** 2)
    e = ((i + 0.5) / i) * K_COND / (RHO * CP * dr ** 2)
    low[i] = w
    diag[i] = -(w + e)
    up[i] = e

    # 表面节点 M（Robin 边界）
    rM = M * dr
    rL = rM - 0.5 * dr
    denom = RHO * CP * (Rs ** 2 - rL ** 2)
    p = 2.0 * rL * K_COND / (denom * dr)
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


def _moist_cn(Cn, Cmid, Cair0, Cair1, dr, dt, Rs, M):
    """传质 C-N 半步：由 C^n 到 C^{n+1}，扩散系数用 Cmid 处的 D(C)。"""
    n = M + 1
    D_v = diffusivity(Cmid)
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
def simulate(t_end, dt, N, out_times, out_r, n_iter=4):
    """
    求解问题 1，返回 (T_out, C_out, t_out)。

    D 依赖 C 造成非线性，每个时间步内做 n_iter 次固定点迭代：
    用 C 的平均值（Cmid）计算扩散系数，交替推进 T 与 C。
    """
    T_air, C_air, _ = load_room()
    dr = R0 / N
    T = np.full(N + 1, T0_INIT)
    C = np.full(N + 1, C0_INIT)

    out_times = np.asarray(out_times, float)
    out_r = np.asarray(out_r, float)
    out_idx = np.rint(out_r / dr).astype(int)
    n_out = len(out_times)

    T_list, C_list, t_list = [], [], []
    out_ptr = 0

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
            Tnew = _heat_cn(Ta, Cmid, Tair0, Tair1, dr, dt, Rs, M)
            Cnew = _moist_cn(Ca, Cmid, Cair0, Cair1, dr, dt, Rs, M)

        T[:M + 1] = Tnew
        C[:M + 1] = Cnew

        while out_ptr < n_out and t_next >= out_times[out_ptr] - 0.5 * dt:
            T_list.append(T[out_idx])
            C_list.append(C[out_idx])
            t_list.append(out_times[out_ptr])
            out_ptr += 1

    return np.array(T_list), np.array(C_list), np.array(t_list)


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
    dt = 0.5                # 时间步长, s
    t_end = 1800.0          # 30 min

    print('=' * 68)
    print('问题 1  预热平衡阶段（附录 2 常物性）')
    print('=' * 68)

    out_times = np.arange(1.0, t_end + 1e-9, 1.0)       # 每秒
    out_r = np.arange(0.0, 0.020001, 0.001)             # 0~2 cm 每 0.1 cm

    T, C, t = simulate(t_end, dt, N, out_times, out_r)
    print(f'求解完成：{len(t)} 个时刻 × {T.shape[1]} 个径向位置')

    # ---------- 论文表 1 / 表 2 ----------
    tbl_t = [100, 300, 600, 900, 1200, 1500, 1800]
    tbl_r = [0.0, 0.005, 0.010, 0.015, 0.020]
    r_idx = [int(round(rr / 0.001)) for rr in tbl_r]

    print('-' * 68)
    print('表 1  30 分钟内药材的温度 (°C)')
    print('时间/s   ' + ''.join(f'{rr*100:>11.1f}cm' for rr in tbl_r))
    for tt in tbl_t:
        i = int(round(tt)) - 1
        print(f'{tt:>7d}  ' + ''.join(f'{T[i, j]:>13.4f}' for j in r_idx))

    print('-' * 68)
    print('表 2  30 分钟内药材的水分浓度 (kg/kg)')
    print('时间/s   ' + ''.join(f'{rr*100:>11.1f}cm' for rr in tbl_r))
    for tt in tbl_t:
        i = int(round(tt)) - 1
        print(f'{tt:>7d}  ' + ''.join(f'{C[i, j]:>13.4f}' for j in r_idx))
    print('=' * 68)

    # ---------- 写出 result1.xlsx ----------
    dist_header = [round(float(x) * 100.0, 1) for x in out_r]
    path = os.path.join(DATA, 'result1.xlsx')
    write_result_xlsx(path,
                      sheets=[('温度', T), ('水分浓度', C)],
                      times=[int(x) for x in t],
                      distances=dist_header)
    print(f'已写出 {path}：{len(t)} 行 × {len(dist_header)} 列')


if __name__ == '__main__':
    main()
