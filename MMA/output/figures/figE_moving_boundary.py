# -*- coding: utf-8 -*-
"""
图E  问题4 收缩域内水分浓度的时空演化

在 (t, r) 平面以填色图给出 C(r,t)，并叠加由附件2 插值得到的实时半径 R(t)
作为计算域的移动上边界；R(t) 以外为已收缩掉的区域，留白处理。
另叠加 C = 0.15 等值线，即"干燥前沿"，可直观看到前沿由表面向中心推进、
同时计算域本身在收缩这一双重效应。

右侧panel给出收缩带来的两个直接后果：扩散路径缩短、表面积减小。
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

from _style import setup_style, save_fig, panel_label, npz, PALETTE
import common

setup_style()
print('[图E] 问题4 移动边界时空云图')

# ---------------- 数据 ----------------
d = npz('_p4')
t = d['t']
C = d['C']                    # (nt, 20)  r = 0 ~ 1.9 cm
C_surf = d['C_surf']
R = d['R']                    # m
r = d['r']
T_end = float(d['T_end'])
th = t / 3600.0
r_cm = r * 100.0
R_cm = R * 100.0

Cm = np.ma.masked_invalid(C)

print(f'  干燥结束时间 {T_end/3600:.2f} h , 结束半径 {R_cm[-1]:.3f} cm')
print(f'  半径收缩 {R_cm[0]:.3f} -> {R_cm[-1]:.3f} cm （体积降至 {(R_cm[-1]/R_cm[0])**2*100:.1f}%）')

# ---------------- 绘图 ----------------
fig = plt.figure(figsize=(10.4, 3.4))
gs = fig.add_gridspec(1, 3, width_ratios=[1.55, 1.0, 1.0], wspace=0.42)

# (a) 时空云图
ax = fig.add_subplot(gs[0, 0])
mesh = ax.pcolormesh(th, r_cm, Cm.T, cmap='YlGnBu', shading='nearest',
                     vmin=0, vmax=2.55)
cb = fig.colorbar(mesh, ax=ax, pad=0.02)
cb.set_label(r'水分浓度 $C$ / (kg$\cdot$kg$^{-1}$)', fontsize=8)
cb.ax.tick_params(labelsize=7.5)

# 移动边界 R(t)
ax.plot(th, R_cm, color='white', lw=2.6)
ax.plot(th, R_cm, color=PALETTE['red_main'], lw=1.5,
        label=r'药材表面 $R(t)$（附件2）')
ax.fill_between(th, R_cm, 2.05, color='white', zorder=2)
ax.text(T_end / 3600 * 0.55, 1.82, '已收缩区域', fontsize=8,
        color=PALETTE['neutral_mid'], zorder=3)

# 干燥前沿 C=0.15 等值线
try:
    cs = ax.contour(th, r_cm, Cm.T, levels=[0.15], colors=[PALETTE['orange']],
                    linewidths=1.6, linestyles='--')
    ax.plot([], [], color=PALETTE['orange'], ls='--', lw=1.6,
            label=r'干燥前沿 $C=0.15$')
except Exception as e:                                   # 等值线可能不存在
    print('  (等值线绘制跳过:', e, ')')

ax.set_xlabel('时间 / h')
ax.set_ylabel('到药材中心的距离 / cm')
ax.set_xlim(0, T_end / 3600.0)
ax.set_ylim(0, 2.05)
ax.legend(fontsize=7.5, loc='upper right', framealpha=0.9)
ax.get_legend().set_frame_on(True)
ax.get_legend().get_frame().set_edgecolor('none')
panel_label(ax, 'a')

# (b) 半径与几何量
ax = fig.add_subplot(gs[0, 1])
ax.plot(th, R_cm, color=PALETTE['blue_main'], lw=1.9, label='半径 $R$')
ax.set_xlabel('时间 / h')
ax.set_ylabel('半径 $R$ / cm', color=PALETTE['blue_main'])
ax.tick_params(axis='y', colors=PALETTE['blue_main'])
ax.set_xlim(0, T_end / 3600.0)

ax2 = ax.twinx()
ax2.plot(th, (R_cm / R_cm[0]) ** 2 * 100, color=PALETTE['green'], lw=1.7, ls='--')
ax2.set_ylabel('截面积相对初始值 / %', color=PALETTE['green'])
ax2.tick_params(axis='y', colors=PALETTE['green'])
ax2.spines['right'].set_visible(True)
ax2.spines['right'].set_color(PALETTE['green'])
ax2.spines['top'].set_visible(False)
ax.text(0.42, 0.55, '截面积（右轴）', transform=ax.transAxes, fontsize=8,
        color=PALETTE['green'])
panel_label(ax, 'b')

# (c) 不同时刻的收缩域剖面
ax = fig.add_subplot(gs[0, 2])
sel = [t_ for t_ in [3, 6, 12, 24, 36, 48, T_end / 3600] if t_ <= T_end / 3600 + 1e-9]
cmap = plt.get_cmap('viridis')
norm = Normalize(0, T_end / 3600.0)
for x in sel:
    i = int(np.argmin(np.abs(th - x)))
    valid = np.isfinite(C[i])
    rr = np.r_[r_cm[valid], R_cm[i]]
    cc = np.r_[C[i, valid], C_surf[i]]
    ax.plot(rr, cc, color=cmap(norm(x)), lw=1.6)
    ax.plot(R_cm[i], C_surf[i], 'o', ms=3.4, color=cmap(norm(x)))
ax.axhline(0.15, color=PALETTE['red_main'], ls='--', lw=1.1)
ax.text(0.05, 0.19, '$C=0.15$', fontsize=7.5, color=PALETTE['red_main'])
ax.set_xlabel('到药材中心的距离 / cm')
ax.set_ylabel(r'水分浓度 / (kg$\cdot$kg$^{-1}$)')
ax.set_xlim(0, 2.05)
sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
sm.set_array([])
cb = fig.colorbar(sm, ax=ax, pad=0.02)
cb.set_label('时间 / h', fontsize=8)
cb.ax.tick_params(labelsize=7.5)
ax.text(0.97, 0.92, '端点为实时表面', transform=ax.transAxes, fontsize=7.5,
        ha='right', color=PALETTE['neutral_mid'])
panel_label(ax, 'c')

fig.suptitle('图E  收缩域内水分浓度的时空演化（问题4）', y=1.04)
save_fig(fig, 'figE_moving_boundary')
