# -*- coding: utf-8 -*-
"""问题3 数据图：干燥过程水分剖面、中心/表面时程、干燥速率。"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from figstyle import setup_style, save_fig, panel_label, PALETTE

setup_style()
d = np.load('/home/user/workspace/code/_p3.npz')
t = d['t']; C = d['C']; T = d['T']; r_cm = d['r'] * 100.0
C_surf = d['C_surf']; T_end = d['T_end']
th = t / 3600.0

# ---------- 图6：水分剖面（hero） ----------
sel = [6, 12, 18, 24, 30, 36, 42, 48, 54]
sel_i = [int(np.argmin(np.abs(t - x * 3600))) for x in sel]
cmap = plt.get_cmap('viridis')
norm = Normalize(0, T_end / 3600.0)

fig, ax = plt.subplots(figsize=(4.2, 3.4))
for x, i in zip(sel, sel_i):
    ax.plot(r_cm, C[i], color=cmap(norm(x)), lw=1.6)
# 结束时刻
i_end = len(t) - 1
ax.plot(r_cm, C[i_end], color=PALETTE['red_main'], lw=2.0, label=f'结束 {T_end/3600:.1f} h')
ax.axhline(0.15, color=PALETTE['neutral_dark'], ls='--', lw=1.2)
ax.text(0.02, 0.153, '干燥终点阈值 $C=0.15$', fontsize=8, va='bottom')
ax.set_xlabel('到药材中心的距离 / cm')
ax.set_ylabel('水分浓度 $C$ / (kg·kg$^{-1}$)')
ax.set_xlim(0, 2); ax.set_ylim(0, 1.7)
sm = ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
cb = fig.colorbar(sm, ax=ax, pad=0.02); cb.set_label('时间 / h', fontsize=8)
fig.suptitle('图6  干燥过程中水分浓度沿径向的演化', y=1.02)
save_fig(fig, 'fig6_p3_profiles')

# ---------- 图7：中心/表面时程 + 阈值 ----------
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
ax = axes[0]
ax.plot(th, C[:, 0], color=PALETTE['blue_main'], lw=1.8, label='中心 ($r=0$)')
ax.plot(th, C[:, 10], color=PALETTE['teal'], lw=1.5, label='$r=1$ cm')
ax.plot(th, C_surf, color=PALETTE['red_main'], lw=1.8, label='表面 ($r=2$ cm)')
ax.axhline(0.15, color=PALETTE['neutral_dark'], ls='--', lw=1.2)
ax.axvline(T_end / 3600.0, color=PALETTE['red_main'], ls=':', lw=1.4)
ax.annotate(f'干燥结束\n{np.round(T_end/3600,2)} h', xy=(T_end/3600.0, 0.15),
            xytext=(T_end/3600.0 - 30, 0.8), fontsize=8,
            arrowprops=dict(arrowstyle='->', lw=1.0, color=PALETTE['red_main']))
ax.set_xlabel('时间 / h'); ax.set_ylabel('水分浓度 / (kg·kg$^{-1}$)')
ax.legend(fontsize=8); ax.set_xlim(0, T_end/3600*1.05)
panel_label(ax, 'a')

# 对数纵轴强调尾部
ax = axes[1]
ax.semilogy(th, C[:, 0], color=PALETTE['blue_main'], lw=1.8, label='中心')
ax.semilogy(th, C_surf, color=PALETTE['red_main'], lw=1.8, label='表面')
ax.axhline(0.15, color=PALETTE['neutral_dark'], ls='--', lw=1.2)
ax.axvline(T_end / 3600.0, color=PALETTE['red_main'], ls=':', lw=1.4)
ax.set_xlabel('时间 / h'); ax.set_ylabel('水分浓度（对数）/ (kg·kg$^{-1}$)')
ax.legend(fontsize=8); ax.set_xlim(0, T_end/3600*1.05)
panel_label(ax, 'b')
fig.suptitle('图7  中心与表面水分浓度随时间的变化', y=1.02)
save_fig(fig, 'fig7_p3_drying')

# ---------- 图8：干燥速率 ----------
# 平均含水率（质量加权）与干燥速率
Cbar = np.trapz(C * r_cm[None, :], r_cm, axis=1) / np.trapz(r_cm, r_cm)
rate = -np.gradient(Cbar, th)
fig, ax = plt.subplots(figsize=(4.6, 3.2))
ax.plot(th, rate, color=PALETTE['blue_main'], lw=1.8)
ax.set_xlabel('时间 / h'); ax.set_ylabel('干燥速率 $-d\\bar{C}/dt$ / (kg·kg$^{-1}$·h$^{-1}$)')
ax.axvline(T_end/3600, color=PALETTE['red_main'], ls=':', lw=1.4)
ax.set_xlim(0, T_end/3600*1.02)
# 标注阶段
ax.annotate('预热与\n恒速段', xy=(3, rate[int(np.argmin(np.abs(th-3)))]),
            xytext=(6, 0.24), fontsize=8, arrowprops=dict(arrowstyle='->'))
ax.annotate('降速段', xy=(30, rate[int(np.argmin(np.abs(th-30)))]),
            xytext=(36, 0.06), fontsize=8, arrowprops=dict(arrowstyle='->'))
fig.suptitle('图8  干燥速率随时间的变化', y=1.02)
save_fig(fig, 'fig8_p3_rate')
print('fig_p3 done')
