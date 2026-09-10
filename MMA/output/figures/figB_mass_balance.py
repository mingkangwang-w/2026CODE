# -*- coding: utf-8 -*-
"""
图B  质量守恒校验：数值解可信度的直接证据

对单位长度圆柱，把水分方程 ∂C/∂t = (1/r)∂/∂r(r D ∂C/∂r) 在 [0,R] 上做
截面积分（乘 2π r dr 并除以常数干物质密度 ρ_dry），得到积分形式的守恒律：

    d/dt ∫_0^R C(r,t) r dr = - R * h_m [ C_s(t) - C_air(t) ]

因此任意时刻应有

    储存项  S(t) = ∫_0^R [C_0 - C(r,t)] r dr        （内部水分减少量）
    通量项  F(t) = R ∫_0^t h_m [C_s - C_air] dτ     （表面累计蒸发量）
    S(t) ≡ F(t)

二者的相对偏差反映时间/空间离散与耦合迭代的综合误差。收敛性检验只能说明
解收敛到某个极限，而守恒校验才能说明收敛到的是正确的解。
"""
import numpy as np
import matplotlib.pyplot as plt

from _style import setup_style, save_fig, panel_label, npz, trapz, PALETTE
import common

setup_style()
print('[图B] 质量守恒校验')

# ---------------- 数据 ----------------
d = npz('_p3')
t = d['t']
C = d['C']
C_surf = d['C_surf']
r = d['r']
T_end = float(d['T_end'])
th = t / 3600.0

R0 = common.R0
hm = common.hm
C0 = common.C0_INIT
_, C_air_f, _ = common.load_room()
C_air = np.asarray(C_air_f(t), float)

# 储存项：∫ (C0 - C) r dr
storage = trapz((C0 - C) * r[None, :], r, axis=1)

# 通量项：R * ∫ h_m (C_s - C_air) dτ  （累计梯形积分）
integrand = hm * (C_surf - C_air)
cum = np.concatenate([[0.0], np.cumsum(0.5 * (integrand[1:] + integrand[:-1]) * np.diff(t))])
# 补上 t=0 到 t[0] 的一小段（初始表面浓度即 C0）
cum += 0.5 * (hm * (C0 - float(C_air_f(0.0))) + integrand[0]) * t[0]
flux = R0 * cum

# 归一化基准：初始总水分 ∫ C0 r dr = C0 R^2 / 2
base = C0 * R0 ** 2 / 2.0
S = storage / base * 100.0          # 已脱除水分占初始总量的百分比
F = flux / base * 100.0

denom = np.maximum(np.abs(S), 1e-12)
rel_err = np.abs(S - F) / denom * 100.0        # 相对误差 %

print(f'  终点已脱除水分: 储存项 {S[-1]:.4f}% , 通量项 {F[-1]:.4f}%')
print(f'  相对误差: 最大 {np.nanmax(rel_err[10:]):.3e}% , 终点 {rel_err[-1]:.3e}%')

# ---------------- 绘图 ----------------
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))

# (a) 两条曲线叠合
ax = axes[0]
ax.plot(th, S, color=PALETTE['blue_main'], lw=2.4,
        label='储存项：内部水分减少量')
ax.plot(th[::40], F[::40], 'o', ms=4.2, mfc='none', mew=1.2,
        color=PALETTE['red_main'], label='通量项：表面累计蒸发量')
ax.set_xlabel('时间 / h')
ax.set_ylabel('已脱除水分占初始总量的比例 / %')
ax.set_xlim(0, T_end / 3600.0)
ax.set_ylim(0, 105)
ax.legend(fontsize=8, loc='lower right')
panel_label(ax, 'a')

# (b) 相对误差
ax = axes[1]
ax.semilogy(th[3:], rel_err[3:], color=PALETTE['green'], lw=1.6)
ax.set_xlabel('时间 / h')
ax.set_ylabel('两者相对偏差 / %')
ax.set_xlim(0, T_end / 3600.0)
ax.axhline(1e-2, color=PALETTE['neutral_dark'], ls='--', lw=1.1)
ax.text(T_end / 3600.0 * 0.98, 1.2e-2, r'$10^{-2}\%$ 参考线',
        fontsize=8, ha='right', color=PALETTE['neutral_dark'])
ax.set_title(f'终点相对偏差 {rel_err[-1]:.2e}%', fontsize=8.5,
             color=PALETTE['neutral_dark'])
panel_label(ax, 'b')

fig.suptitle('图B  水分质量守恒校验', y=1.03)
fig.tight_layout()
save_fig(fig, 'figB_mass_balance')
