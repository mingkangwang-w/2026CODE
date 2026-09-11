# -*- coding: utf-8 -*-
"""
问题 4：考虑尺寸收缩的药材烘干时长（附录 4 变物性 + 参考坐标移动边界）

独立程序，不依赖任何自定义模块，可直接运行：
    python solve_p4.py
输出：
    ../data/result4.xlsx    水分浓度（含"药材表面"列），每 60 s、到中心每 0.1 cm
    _p4.npz                 供绘图脚本使用的求解结果缓存
并在终端打印论文表 6 与质量守恒校核。

============================================================
移动边界的处理：参考坐标（Lagrange / 材料坐标）
============================================================
药材失水时各层按比例收缩（仿射收缩），材料点向内移动。若仍在【固定物理
坐标 r】上求解，控制方程必须保留材料对流项

        ∂C/∂t + u_r ∂C/∂r = (1/r) ∂/∂r ( r D ∂C/∂r ),    u_r = r Ṙ/R

若略去该对流项并让计算域随 R(t) 收缩、逐层删除网格节点，则每个被删除的
节点所携带的水分会直接脱离计算域——这部分水分并未经过表面蒸发，属于
非物理的质量损失（实测约占总水分的 26.7%）。

本文改用【参考坐标 r0】（材料坐标）求解，从根本上避免该问题。记

        λ(t) = R(t)/R0 ,        r = λ · r0 ,      0 ≤ r0 ≤ R0

将控制方程变换到参考坐标（∂/∂r = (1/λ)∂/∂r0，材料导数 ∂C/∂t|_r0）：

        ∂C/∂t|_r0 = (1/λ²) · (1/r0) ∂/∂r0 ( r0 D ∂C/∂r0 )
        ∂T/∂t|_r0 = (1/λ²) · (1/(ρcp r0)) ∂/∂r0 ( r0 k ∂T/∂r0 )

表面边界 r0 = R0 处，由 -D ∂C/∂r|_R = h_m (C - C_air) 与
∂C/∂r|_R = (1/λ) ∂C/∂r0|_R0 得

        -D ∂C/∂r0|_R0 = λ h_m (C - C_air)          （传热同理，h_m → h）

参考坐标下的三大优势：
  1. 网格固定在 r0 = i·Δr0，节点数 N 恒定，**永不删节点** —— 质量严格守恒；
  2. 表面节点 N 恰好位于真实表面（r0 = R0 映射到 r = R(t)），
     无需残余薄层 δ、无需等效系数 h_eff = 1/(1/h + δ/k)、无需表面外推；
  3. 内部节点离散格式与固定网格完全一致，仅整体多乘 1/λ²。

离散（有限体积，A_N 为表面半控制体的参考体积）：

    内部节点 i=1..N-1 :  dC_i/dt = (1/λ²)[ w_i(C_{i-1}-C_i) + e_i(C_{i+1}-C_i) ]
    中心节点 i=0      :  dC_0/dt = (1/λ²)·(4D_{1/2}/Δr0²)(C_1-C_0)
    表面节点 i=N      :  dC_N/dt = (1/λ²)·p_N(C_{N-1}-C_N) - q_N(C_N-C_air)

    w_i = ((i-1/2)/i)·D_{i-1/2}/Δr0² ,  e_i = ((i+1/2)/i)·D_{i+1/2}/Δr0²
    p_N = r0L·D_{N-1/2}/(A_N·Δr0)     ,  q_N = R0·h_m/(λ·A_N)
    r0L = (N-1/2)Δr0 ,  A_N = (R0² - r0L²)/2

注意 λ² 只作用于扩散项 p_N；对流项 q_N 只含 1/λ。时间推进仍用
Crank-Nicolson + 固定点迭代（4 次）。

============================================================
质量守恒的积分形式
============================================================
对参考坐标方程以 r0 dr0 加权积分，并用表面边界条件，得

        dJ/dt = -(R0/λ) · h_m · (C_N - C_air),      J(t) = ∫_0^R0 C(r0,t) r0 dr0

程序在结束时校核该恒等式（见终端输出"质量守恒校核"）。
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


# ==================== 参考坐标下的 Crank-Nicolson 单步 ====================
def _build_ops(low, diag, up, q_surf, capN, lam, A_N, N):
    """
    把 λ 因子施加到算子上，返回 (low, diag, up, qN)。

    扩散项整体乘 1/λ²；表面节点额外扣除对流项 qN（只含 1/λ，并除以容积
    系数 capN——传热为 ρc_p、传质为 1，使两项量纲一致）。
    对方程  du_i/dt = low_i·u_{i-1} + diag_i·u_i + up_i·u_{i+1} + qN·u_air
    """
    lo, di, u = low / lam ** 2, diag / lam ** 2, up / lam ** 2
    qN = R0 * q_surf / (capN * lam * A_N)
    di[N] -= qN
    return lo, di, u, qN


def _cn_step(un, u_air0, u_air1, lam, dr, dt, N, A_N, r0L, coef, q_surf, kind):
    """
    单个 Crank-Nicolson 半步（参考坐标）。

    kind='heat' : coef=(rho, cp, k)，u 为温度，q_surf=h
    kind='mass' : coef=D，            u 为含水率，q_surf=h_m
    """
    n = N + 1
    low = np.zeros(n)
    diag = np.zeros(n)
    up = np.zeros(n)

    if kind == 'heat':
        rho_v, cp_v, k_v = coef
        f_v = k_v
        cap = rho_v * cp_v                       # 容积热容
    else:
        f_v = coef                               # D
        cap = np.ones(n)

    ff = 0.5 * (f_v[:-1] + f_v[1:])              # 界面系数（参考坐标等距）

    # 中心节点（对称，半控制体）
    g0 = 4.0 * ff[0] / (cap[0] * dr ** 2)
    diag[0], up[0] = -g0, g0

    # 内部节点
    i = np.arange(1, N)
    w = ((i - 0.5) / i) * ff[i - 1] / (cap[i] * dr ** 2)
    e = ((i + 0.5) / i) * ff[i] / (cap[i] * dr ** 2)
    low[i], diag[i], up[i] = w, -(w + e), e

    # 表面节点
    pN = r0L * ff[N - 1] / (cap[N] * A_N * dr)
    low[N], diag[N] = pN, -pN

    lo, di, u, qN = _build_ops(low, diag, up, q_surf, cap[N], lam, A_N, N)

    Mu = np.zeros(n)
    Mu[0] = di[0] * un[0] + u[0] * un[1]
    Mu[1:-1] = lo[1:-1] * un[:-2] + di[1:-1] * un[1:-1] + u[1:-1] * un[2:]
    Mu[-1] = lo[-1] * un[-2] + di[-1] * un[-1]

    rhs = un + 0.5 * dt * Mu
    rhs[-1] += 0.5 * dt * qN * (u_air1 + u_air0)

    ab = np.zeros((3, n))
    ab[0, 1:] = (-0.5 * dt * u)[:-1]
    ab[1, :] = 1.0 - 0.5 * dt * di
    ab[2, :-1] = (-0.5 * dt * lo)[1:]
    return solve_banded((1, 1), ab, rhs)


# ==================== 主求解 ====================
def simulate(t_end, dt, N, out_times, out_r, n_iter=4, drying_thresh=None):
    """
    参考坐标（Lagrange）求解问题 4。

    返回 (T_out, C_out, t_out, R_out, C_surf, T_end, balance)
      T_out/C_out : 已插值到【物理距离】out_r 上的场（超出当前半径处为 NaN）
      C_surf      : 真实表面含水率 C(r0=R0)
      balance     : 质量守恒校核字典
    """
    T_air, C_air, _ = load_room()
    Rspl, _, _ = load_radius()
    dr = R0 / N

    r0L = (N - 0.5) * dr
    A_N = 0.5 * (R0 ** 2 - r0L ** 2)

    T = np.full(N + 1, T0_INIT)
    C = np.full(N + 1, C0_INIT)

    out_times = np.asarray(out_times, float)
    out_r = np.asarray(out_r, float)
    n_out = len(out_times)

    def to_physical(field, lam):
        """把参考坐标解插值到给定的物理距离 out_r（线性插值）。"""
        xi = out_r / (lam * dr)                  # 物理距离对应的参考节点号
        res = np.full(len(out_r), np.nan)
        ok = xi <= N + 1e-12
        xv = xi[ok]
        i0 = np.clip(np.floor(xv).astype(int), 0, N - 1)
        frac = xv - i0
        res[ok] = field[i0] * (1.0 - frac) + field[i0 + 1] * frac
        return res

    T_list, C_list, t_list, R_list, Cs_list = [], [], [], [], []

    # 质量守恒记账：J = ∫ C r0 dr0
    # 控制体积必须与离散算子严格一致：
    #   中心节点 0 : ∫_0^{Δr/2} r dr        = Δr²/8
    #   内部节点 i : ∫_{(i-1/2)Δr}^{(i+1/2)Δr} r dr = i·Δr² = r0_i·Δr
    #   表面节点 N : A_N = (R0² - r0L²)/2
    r0 = np.arange(N + 1) * dr
    vol = r0 * dr
    vol[0] = dr ** 2 / 8.0
    vol[N] = A_N

    def inventory(field):
        return float(np.sum(field * vol))

    def flux_rate(C_now, C_prev, cair_now, cair_prev, lam_):
        """表面流出率（与 CN 离散一致的梯形形式）。"""
        return 0.5 * (R0 / lam_) * HM * (
            (C_now - cair_now) + (C_prev - cair_prev))

    J0 = inventory(C)
    flux_cum = 0.0
    out_ptr = 0
    T_end = t_end
    C_air_prev = float(C_air(0.0))          # 与 CN 同阶的梯形累加所需的上一步值
    bal_max = dict(rel=0.0, resid=0.0, t=0.0, J=0.0, expected=0.0)

    for step in range(1, int(round(t_end / dt)) + 1):
        t_now = (step - 1) * dt
        t_next = step * dt
        Tair0, Tair1 = T_air(t_now), T_air(t_next)
        Cair0, Cair1 = C_air(t_now), C_air(t_next)

        lam0 = float(np.clip(float(Rspl(t_now)) / R0, 1e-3, 1.0))
        lam1 = float(np.clip(float(Rspl(t_next)) / R0, 1e-3, 1.0))
        lam = 0.5 * (lam0 + lam1)

        Ta, Ca = T.copy(), C.copy()
        Tnew, Cnew = Ta.copy(), Ca.copy()

        for _ in range(n_iter):
            Cmid = 0.5 * (Ca + Cnew)
            Tmid = 0.5 * (Ta + Tnew)

            Tnew = _cn_step(Ta, Tair0, Tair1, lam, dr, dt, N, A_N, r0L,
                            (rho(Cmid), cp(Cmid), k_cond(Cmid)), H_CONV, 'heat')
            Cnew = _cn_step(Ca, Cair0, Cair1, lam, dr, dt, N, A_N, r0L,
                            diffusivity(Cmid, Tmid), HM, 'mass')

        C_old = C
        T, C = Tnew, Cnew

        # ---- 质量守恒累计：dJ/dt = -(R0/λ)·h_m·(C_N - C_air) ----
        flux_cum += flux_rate(C[N], C_old[N], float(Cair1), C_air_prev, lam) * dt
        C_air_prev = float(Cair1)

        # 全程记录守恒偏差（不仅看终点，避免中途误差相互抵消）
        J_now = inventory(C)
        rhs_now = J0 - flux_cum
        denom = max(abs(J0 - J_now), 1e-30)
        resid_rel = abs(J_now - rhs_now) / denom
        if resid_rel > bal_max['rel']:
            bal_max.update(rel=resid_rel, resid=abs(J_now - rhs_now),
                           t=t_next, J=J_now, expected=rhs_now)

        while out_ptr < n_out and t_next >= out_times[out_ptr] - 0.5 * dt:
            T_list.append(to_physical(T, lam))
            C_list.append(to_physical(C, lam))
            Cs_list.append(float(C[N]))          # 真实表面，无需外推
            R_list.append(lam * R0)
            t_list.append(out_times[out_ptr])
            out_ptr += 1

        if drying_thresh is not None and np.nanmax(C) < drying_thresh:
            T_end = t_next
            if not t_list or abs(t_list[-1] - t_next) > 1e-9:
                T_list.append(to_physical(T, lam))
                C_list.append(to_physical(C, lam))
                Cs_list.append(float(C[N]))
                R_list.append(lam * R0)
                t_list.append(t_next)
            break

    J_end = inventory(C)
    balance = dict(J0=J0, J_end=J_end, flux=flux_cum,
                   residual=abs(J0 - J_end - flux_cum),
                   rel=abs(J0 - J_end - flux_cum) / max(abs(J0 - J_end), 1e-30),
                   max_rel=bal_max['rel'], max_resid=bal_max['resid'],
                   max_t=bal_max['t'])

    return (np.array(T_list), np.array(C_list), np.array(t_list),
            np.array(R_list), np.array(Cs_list), T_end, balance)


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
    N = 400                 # 参考网格：Δr0 = 0.005 cm，全程固定不删节点
    dt = 5.0                # 时间步长, s
    t_end = 540000.0        # 积分上限 150 h

    print('=' * 76)
    print('问题 4  尺寸收缩下的烘干时长（附录 4 + 参考坐标移动边界）')
    print('=' * 76)

    out_times = np.arange(60.0, t_end + 1e-9, 60.0)     # 每 60 s
    out_r = np.arange(0.0, 0.019001, 0.001)             # 物理距离 0~1.9 cm

    T, C, t, R, C_surf, T_end, bal = simulate(t_end, dt, N, out_times, out_r,
                                              drying_thresh=THRESH)

    print(f'烘干结束时间 t* = {T_end:.1f} s = {T_end/3600:.4f} h '
          f'= {T_end/86400:.2f} 天')
    print(f'结束时刻 max(C) = {np.nanmax(C[-1]):.6f} kg/kg（应 < {THRESH}）')
    print(f'结束时刻表面半径 R = {R[-1]*100:.4f} cm '
          f'（初始 {R[0]*100:.4f} cm，收缩 {(1-R[-1]/R[0])*100:.1f}%）')
    print(f'求解步数：{len(t)} 个输出时刻 × {C.shape[1]} 个物理距离')

    # ---------- 质量守恒校核 ----------
    print('-' * 76)
    print('质量守恒校核   dJ/dt = -(R0/λ)·h_m·(C_N - C_air),   J = ∫ C r0 dr0')
    print(f'  初始 J0            = {bal["J0"]:.10e}')
    print(f'  结束 J_end         = {bal["J_end"]:.10e}')
    print(f'  表面累计流出通量   = {bal["flux"]:.10e}')
    print(f'  终点闭合残差       = {bal["residual"]:.4e}'
          f'  （相对 {bal["rel"]*100:.6f}%）')
    print(f'  全程最大闭合残差   = {bal["max_resid"]:.4e}'
          f'  （相对 {bal["max_rel"]*100:.6f}%，出现在 t={bal["max_t"]:.0f} s）')

    # ---------- 论文表 6 ----------
    tbl_t = list(np.arange(21600.0, T_end + 1e-9, 21600.0)) + [T_end]
    print('-' * 76)
    print('表 6  药材烘干过程的水分浓度 (kg/kg)')
    print('时间/h       0.0cm       0.5cm       1.0cm       1.5cm     药材表面')
    for th in tbl_t:
        i = int(np.argmin(np.abs(t - th)))
        vals = [C[i, 0], C[i, 5], C[i, 10], C[i, 15], C_surf[i]]
        cells = ''.join('           —' if not np.isfinite(v) else f'{v:>12.4f}'
                        for v in vals)
        print(f'{th/3600:>7.2f}  {cells}')
    print('=' * 76)

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
