# -*- coding: utf-8 -*-
"""问题1 数据图：温度/水分剖面 + 时空热力图。"""
import numpy as np
import matplotlib.pyplot as plt
from common import simulate
from figstyle import setup_style, save_fig, panel_label, DEFAULT_COLORS

setup_style()
r_cm = np.arange(0.0, 0.020001, 0.001) * 100.0

# 一次求解，输出每 20s、0.1cm 网格
out_times = np.arange(20.0, 1801.0, 20.0)
res = simulate(1, 1800.0, 0.5, N=400, out_times=out_times,
               out_r=np.arange(0.0, 0.020001, 0.001))
T = res['T_out']; C = res['C_out']; t = res['t_out']

# ---------- 图1：温度/水分剖面 ----------
sel_t = [100, 300, 600, 900, 1200, 1500, 1800]
sel_i = [int(round(x / 20.0)) - 1 for x in sel_t]
labels = [f'{x} s' for x in sel_t]

fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.1))
ax = axes[0]
for k, i in enumerate(sel_i):
    ax.plot(r_cm, T[i], color=DEFAULT_COLORS[k], label=labels[k], lw=1.6)
ax.set_xlabel('到药材中心的距离 / cm'); ax.set_ylabel('温度 $T$ / °C')
ax.set_xlim(0, 2); ax.legend(ncol=1, fontsize=7.5, loc='center right')
panel_label(ax, 'a')

ax = axes[1]
for k, i in enumerate(sel_i):
    ax.plot(r_cm, C[i], color=DEFAULT_COLORS[k], label=labels[k], lw=1.6)
ax.set_xlabel('到药材中心的距离 / cm'); ax.set_ylabel('水分浓度 $C$ / (kg·kg$^{-1}$)')
ax.set_xlim(0, 2); ax.legend(ncol=1, fontsize=7.5, loc='upper right')
panel_label(ax, 'b')
fig.suptitle('图1  预热平衡阶段温度与水分浓度沿径向的分布', y=1.02)
save_fig(fig, 'fig1_p1_profiles')

# ---------- 图2：时空热力图 ----------
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3))
for ax, data, name, cmap, vmin, vmax, cblabel in [
    (axes[0], T.T, '温度', 'inferno', 28, 38, '温度 / °C'),
    (axes[1], C.T, '水分', 'YlOrBr', 1.5, 2.56, '水分浓度 / (kg·kg$^{-1}$)')]:
    im = ax.imshow(data, aspect='auto', origin='lower', cmap=cmap,
                   vmin=vmin, vmax=vmax,
                   extent=[t[0], t[-1], r_cm[0], r_cm[-1]])
    ax.set_xlabel('时间 / s'); ax.set_ylabel('距离 / cm')
    cb = fig.colorbar(im, ax=ax, pad=0.02); cb.set_label(cblabel, fontsize=8)
    cb.ax.tick_params(labelsize=7.5)
panel_label(axes[0], 'a'); panel_label(axes[1], 'b')
fig.suptitle('图2  预热阶段温度与水分浓度的时空演化', y=1.02)
save_fig(fig, 'fig2_p1_spacetime')
print('fig_p1 done')
