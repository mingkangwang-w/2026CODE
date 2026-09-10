# -*- coding: utf-8 -*-
"""
图C  常物性模型（问题1，附录2）与变物性模型（问题2，附录3）的对比

问题1 与问题2 并非串联的两个阶段，而是同一物理过程的两个精度层次：
问题1 在 0~1800 s 采用附录2 的常物性线性化，问题2 从 t=0 起采用附录3 的
变物性全耦合模型。二者在 0~1800 s 区间重叠，其差异定量刻画了常物性假设
在预热段引入的误差，也论证了问题2 采用变物性描述的必要性。

本图在同一时间窗内并列两套模型的径向剖面与中心/表面时程差值。
"""
import numpy as np
import matplotlib.pyplot as plt

from _style import setup_style, save_fig, panel_label, PALETTE, DEFAULT_COLORS
import common
from common import simulate

setup_style()
print('[图C] 常物性模型 vs 变物性模型（0~1800 s）')

# ---------------- 求解 ----------------
T_WIN = 1800.0
out_t = np.arange(10.0, T_WIN + 1e-9, 10.0)
out_r = np.arange(0.0, 0.020001, 0.001)
r_cm = out_r * 100.0

print('  求解问题1 模型（附录2 常物性）...')
r1 = simulate(1, T_WIN, 0.5, N=400, out_times=out_t, out_r=out_r)
print('  求解问题2 模型（附录3 变物性）...')
r2 = simulate(2, T_WIN, 0.5, N=400, out_times=out_t, out_r=out_r)

T1, C1 = r1['T_out'], r1['C_out']
T2, C2 = r2['T_out'], r2['C_out']
t = r1['t_out']

sel_t = [600, 1200, 1800]
sel_i = [int(round(x / 10.0)) - 1 for x in sel_t]

for x, i in zip(sel_t, sel_i):
    print(f'  t={x:>5d}s  中心温度 {T1[i,0]:7.3f} vs {T2[i,0]:7.3f} °C '
          f'| 表面水分 {C1[i,-1]:7.4f} vs {C2[i,-1]:7.4f} kg/kg')

# ---------------- 绘图 ----------------
fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.2))

# (a) 温度剖面
ax = axes[0]
for k, (x, i) in enumerate(zip(sel_t, sel_i)):
    ax.plot(r_cm, T1[i], color=DEFAULT_COLORS[k], lw=1.8, ls='-')
    ax.plot(r_cm, T2[i], color=DEFAULT_COLORS[k], lw=1.6, ls='--')
    ax.text(2.02, T1[i, -1], f'{x} s', fontsize=7.5, va='center',
            color=DEFAULT_COLORS[k])
ax.plot([], [], color=PALETTE['neutral_dark'], ls='-', lw=1.8,
        label='问题1：常物性（附录2）')
ax.plot([], [], color=PALETTE['neutral_dark'], ls='--', lw=1.6,
        label='问题2：变物性（附录3）')
ax.set_xlabel('到药材中心的距离 / cm')
ax.set_ylabel('温度 $T$ / °C')
ax.set_xlim(0, 2.25)
ax.legend(fontsize=7.5, loc='upper left')
panel_label(ax, 'a')

# (b) 水分剖面
ax = axes[1]
for k, (x, i) in enumerate(zip(sel_t, sel_i)):
    ax.plot(r_cm, C1[i], color=DEFAULT_COLORS[k], lw=1.8, ls='-')
    ax.plot(r_cm, C2[i], color=DEFAULT_COLORS[k], lw=1.6, ls='--')
ax.plot([], [], color=PALETTE['neutral_dark'], ls='-', lw=1.8,
        label='问题1：常物性')
ax.plot([], [], color=PALETTE['neutral_dark'], ls='--', lw=1.6,
        label='问题2：变物性')
ax.set_xlabel('到药材中心的距离 / cm')
ax.set_ylabel(r'水分浓度 $C$ / (kg$\cdot$kg$^{-1}$)')
ax.set_xlim(0, 2)
ax.legend(fontsize=7.5, loc='lower left')
panel_label(ax, 'b')

# (c) 差值时程
ax = axes[2]
dT_c = T2[:, 0] - T1[:, 0]
dT_s = T2[:, -1] - T1[:, -1]
ax.plot(t, dT_c, color=PALETTE['blue_main'], lw=1.8, label='中心 $\\Delta T$')
ax.plot(t, dT_s, color=PALETTE['blue_secondary'], lw=1.6, ls='--',
        label='表面 $\\Delta T$')
ax.axhline(0, color=PALETTE['neutral_light'], lw=0.9)
ax.set_xlabel('时间 / s')
ax.set_ylabel('温度差 $T_{变} - T_{常}$ / °C', color=PALETTE['blue_main'])
ax.tick_params(axis='y', colors=PALETTE['blue_main'])
ax.set_xlim(0, T_WIN)

ax2 = ax.twinx()
dC_s = C2[:, -1] - C1[:, -1]
ax2.plot(t, dC_s, color=PALETTE['red_main'], lw=1.8, label='表面 $\\Delta C$')
ax2.set_ylabel(r'水分浓度差 $C_{变}-C_{常}$ / (kg$\cdot$kg$^{-1}$)',
               color=PALETTE['red_main'])
ax2.tick_params(axis='y', colors=PALETTE['red_main'])
ax2.spines['right'].set_visible(True)
ax2.spines['right'].set_color(PALETTE['red_main'])
ax2.spines['top'].set_visible(False)

lines = ax.get_lines()[:2] + ax2.get_lines()[:1]
ax.legend(lines, [l.get_label() for l in lines], fontsize=7.5, loc='lower left')
panel_label(ax, 'c')

fig.suptitle('图C  预热阶段常物性模型与变物性模型的差异', y=1.03)
fig.tight_layout()
save_fig(fig, 'figC_p1_vs_p2')
