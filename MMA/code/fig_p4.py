# -*- coding: utf-8 -*-
"""问题4 数据图：半径收缩、水分剖面（收缩域）、问题3/4 对比。"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from common import load_radius
from figstyle import setup_style, save_fig, panel_label, PALETTE

setup_style()
d4 = np.load('/home/user/workspace/code/_p4.npz')
t4 = d4['t']; C4 = d4['C']; C_surf4 = d4['C_surf']; R4 = d4['R']; T_end4 = d4['T_end']
r4_cm = d4['r'] * 100.0
d3 = np.load('/home/user/workspace/code/_p3.npz')
t3 = d3['t']; C3 = d3['C']; T_end3 = d3['T_end']

Rspl, tR, RR = load_radius()

# ---------- 图9 ----------
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.1))

# (a) 半径收缩
ax = axes[0]
tr_cont = np.linspace(0, T_end4, 200)
ax.plot(tr_cont / 3600, Rspl(tr_cont) * 100, color=PALETTE['blue_main'], lw=1.8, label='三次样条拟合')
ax.plot(tR / 3600, RR * 100, 'o', ms=3, color=PALETTE['red_main'], label='附件2实测')
ax.set_xlabel('时间 / h'); ax.set_ylabel('半径 / cm')
ax.legend(fontsize=7.5)
panel_label(ax, 'a')

# (b) 水分剖面（收缩域）
ax = axes[1]
sel = [6, 12, 18, 24, 30, 36, 42, 48]
cmap = plt.get_cmap('viridis'); norm = Normalize(0, 52)
for x in sel:
    i = int(np.argmin(np.abs(t4 - x * 3600)))
    rr = r4_cm[r4_cm <= R4[i] * 100]
    cc = C4[i, :len(rr)]
    ax.plot(rr, cc, color=cmap(norm(x)), lw=1.5)
ax.plot(R4[-1] * 100, C_surf4[-1], 'o', color=PALETTE['red_main'], ms=5, label='结束表面')
ax.set_xlabel('到药材中心的距离 / cm'); ax.set_ylabel('水分浓度 / (kg·kg$^{-1}$)')
ax.set_xlim(0, 2)
sm = ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
cb = fig.colorbar(sm, ax=ax, pad=0.02); cb.set_label('时间 / h', fontsize=8)
panel_label(ax, 'b')

# (c) 问题3 vs 问题4 中心水分
ax = axes[2]
ax.plot(t3 / 3600, C3[:, 0], color=PALETTE['blue_main'], lw=1.8, label='问题3（定半径）')
ax.plot(t4 / 3600, C4[:, 0], color=PALETTE['red_main'], lw=1.8, label='问题4（收缩）')
ax.axhline(0.15, color=PALETTE['neutral_dark'], ls='--', lw=1.1)
ax.axvline(T_end3 / 3600, color=PALETTE['blue_main'], ls=':', lw=1.2)
ax.axvline(T_end4 / 3600, color=PALETTE['red_main'], ls=':', lw=1.2)
ax.set_xlabel('时间 / h'); ax.set_ylabel('中心水分浓度 / (kg·kg$^{-1}$)')
ax.legend(fontsize=7.5); ax.set_xlim(0, 60)
panel_label(ax, 'c')
fig.suptitle('图9  尺寸收缩对干燥过程的影响', y=1.02)
save_fig(fig, 'fig9_p4_shrinkage')
print('fig_p4 done')
