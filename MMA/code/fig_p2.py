# -*- coding: utf-8 -*-
"""问题2 数据图：温度/水分剖面、中心/表面时程、变物性曲线。"""
import numpy as np
import matplotlib.pyplot as plt
from common import load_room, props
from figstyle import setup_style, save_fig, panel_label, DEFAULT_COLORS, PALETTE

setup_style()
d = np.load('/home/user/workspace/code/_p2.npz')
t = d['t']; T = d['T']; C = d['C']; r_cm = d['r'] * 100.0
T_air, C_air, _ = load_room()

# ---------- 图3：剖面 ----------
sel = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
sel_i = [int(round(x * 3600.0)) - 1 for x in sel]
labels = [f'{x} h' for x in sel]

fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
ax = axes[0]
for k, i in enumerate(sel_i):
    ax.plot(r_cm, T[i], color=DEFAULT_COLORS[k], label=labels[k], lw=1.6)
ax.set_xlabel('到药材中心的距离 / cm'); ax.set_ylabel('温度 $T$ / °C')
ax.set_xlim(0, 2); ax.legend(ncol=1, fontsize=7.5, loc='lower right')
panel_label(ax, 'a')

ax = axes[1]
for k, i in enumerate(sel_i):
    ax.plot(r_cm, C[i], color=DEFAULT_COLORS[k], label=labels[k], lw=1.6)
ax.set_xlabel('到药材中心的距离 / cm'); ax.set_ylabel('水分浓度 $C$ / (kg·kg$^{-1}$)')
ax.set_xlim(0, 2); ax.legend(ncol=1, fontsize=7.5, loc='upper right')
panel_label(ax, 'b')
fig.suptitle('图3  3 小时内温度与水分浓度沿径向的分布', y=1.02)
save_fig(fig, 'fig3_p2_profiles')

# ---------- 图4：中心/表面时程 ----------
th = t / 3600.0
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
ax = axes[0]
ax.plot(th, T_air(t), color=PALETTE['neutral_mid'], ls='--', lw=1.4, label='烘房温度')
ax.plot(th, T[:, 20], color=PALETTE['red_main'], lw=1.8, label='表面 ($r=2$ cm)')
ax.plot(th, T[:, 0], color=PALETTE['blue_main'], lw=1.8, label='中心 ($r=0$)')
ax.set_xlabel('时间 / h'); ax.set_ylabel('温度 / °C'); ax.legend(fontsize=8)
panel_label(ax, 'a')

ax = axes[1]
ax.plot(th, C[:, 0], color=PALETTE['blue_main'], lw=1.8, label='中心 ($r=0$)')
ax.plot(th, C[:, 20], color=PALETTE['red_main'], lw=1.8, label='表面 ($r=2$ cm)')
ax.plot(th, C_air(t), color=PALETTE['neutral_mid'], ls='--', lw=1.4, label='空气水分浓度')
ax.set_xlabel('时间 / h'); ax.set_ylabel('水分浓度 / (kg·kg$^{-1}$)'); ax.legend(fontsize=8)
panel_label(ax, 'b')
fig.suptitle('图4  中心与表面温度、水分浓度随时间的演化', y=1.02)
save_fig(fig, 'fig4_p2_timeseries')

# ---------- 图5：变物性曲线（附录3） ----------
rho, cp, k, D = props(2)
Cv = np.linspace(0.0, 3.0, 200)
T50 = np.full_like(Cv, 50.0)
fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.6))
axes[0].plot(Cv, rho(Cv), color=DEFAULT_COLORS[0])
axes[0].set_xlabel('$C$'); axes[0].set_ylabel('$\\rho$ / (kg·m$^{-3}$)')
axes[1].plot(Cv, cp(Cv), color=DEFAULT_COLORS[1])
axes[1].set_xlabel('$C$'); axes[1].set_ylabel('$c_p$ / (J·kg$^{-1}$·K$^{-1}$)')
axes[2].plot(Cv, k(Cv), color=DEFAULT_COLORS[2])
axes[2].set_xlabel('$C$'); axes[2].set_ylabel('$k$ / (W·m$^{-1}$·K$^{-1}$)')
axes[3].plot(Cv, D(Cv, T50) * 1e9, color=DEFAULT_COLORS[3])
axes[3].set_xlabel('$C$'); axes[3].set_ylabel('$D$ / (10$^{-9}$ m$^2$·s$^{-1}$)')
for a, lbl in zip(axes, list('abcd')):
    panel_label(a, lbl, x=-0.28)
fig.suptitle('图5  附录3 物性参数随水分浓度的变化', y=1.02)
fig.tight_layout()
save_fig(fig, 'fig5_p2_properties')
print('fig_p2 done')
