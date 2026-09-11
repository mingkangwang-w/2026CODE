"""附件 1 烘房环境双轴图（basic#10）。

本图讲什么：烘房热风的温度 T_inf(t) 与水分浓度 C_inf(t) 在 0-14400 s 内的同步演化，
并标出 t=10800 s 之后进入恒温恒湿平台段（后续四问的边界条件即取自该平台）。

图元：左轴 = 温度（30 min 分箱增温柱，基线锚在初始 28 度 + 逐点实测折线 + 三层渐变填充）；
      右轴 = 水分浓度折线 + 峰值高亮；竖线 = 平台起点 10800 s；文字仅数值/短锚点。

数据来源：user_data/附件1.xlsx（241 行，列「时间」「温度」「水分浓度」，步长 60 s）。
关键数值：初始 28.000 度；平台起点 10800 s；平台均值由本脚本按 t>=10800 s 实测算出。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _figbase import (FS, save_fig, set_paper_placement, declutter_axes,
                      PALETTE, COLORS, _lighten, out)

PLATEAU_START_S = 10800.0

df = pd.read_excel('user_data/附件1.xlsx')
t_s = df['时间'].to_numpy(dtype=float)
T = df['温度'].to_numpy(dtype=float)
C = df['水分浓度'].to_numpy(dtype=float)
t_h = t_s / 3600.0

T0 = float(T[0])
plateau = t_s >= PLATEAU_START_S
T_bar = float(np.mean(T[plateau]))
C_bar = float(np.mean(C[plateau]))

# 30 min 分箱平均增温，柱基线锚在初始温度（浮动柱 = 增量，位置 = 绝对温度）
BIN_S = 1800.0
edges = np.arange(0.0, t_s[-1] + BIN_S, BIN_S)
idx = np.clip(np.digitize(t_s, edges) - 1, 0, len(edges) - 2)
centers, heights = [], []
for k in range(len(edges) - 1):
    sel = idx == k
    if not np.any(sel):
        continue
    centers.append(0.5 * (edges[k] + edges[k + 1]) / 3600.0)
    heights.append(float(np.mean(T[sel])) - T0)
centers = np.asarray(centers)
heights = np.asarray(heights)

fig, ax1 = plt.subplots(figsize=(6.4, 3.6))
ax2 = ax1.twinx()

ax1.bar(centers, heights, width=BIN_S / 3600.0 * 0.78, bottom=T0,
        color=_lighten(PALETTE[0], 0.45), edgecolor=PALETTE[0],
        linewidth=0.9, zorder=2, label='30 min 均温')
ax1.axhline(T0, color=COLORS['ref_line'], lw=0.7, ls=':', zorder=1)

ax1.plot(t_h, T, '-', color=PALETTE[0], lw=1.7, zorder=5, label='实测温度')
for layer, alpha in enumerate([0.16, 0.09, 0.04]):
    ax1.fill_between(t_h, T0 + layer * 0.4, T - layer * 0.4,
                     color=PALETTE[0], alpha=alpha, lw=0, zorder=1)

ax2.plot(t_h, C, '-', color=PALETTE[1], lw=1.7, zorder=5, label='实测水分浓度')
pk = int(np.argmax(C))
ax2.scatter(t_h[pk], C[pk], s=42, color=PALETTE[1], edgecolor='white',
            linewidth=1.3, zorder=6)

ax1.set_xlim(-0.15, t_h[-1] + 0.15)
ax1.set_ylim(T0 - 1.0, T.max() + 3.6)
ax2.set_ylim(C.min() - 0.0035, C.max() + 0.0128)

t_pl_h = PLATEAU_START_S / 3600.0
ax1.axvline(t_pl_h, color=COLORS['highlight'], lw=1.1, ls='--', zorder=4)
ax1.annotate(f'平台起点 {t_pl_h:.0f} h', xy=(t_pl_h, T.max() + 1.5),
             xytext=(t_pl_h - 2.6, T.max() + 2.6),
             fontsize=FS, color=COLORS['highlight'], va='center',
             arrowprops=dict(arrowstyle='->', color=COLORS['highlight'], lw=0.9))
ax1.text(t_h[-1] - 0.08, T.max() + 2.9, f'{T_bar:.4f} °C\n{C_bar:.5f} kg/kg',
         fontsize=FS, ha='right', va='top', color=COLORS['text'], linespacing=1.35)

ax1.set_xlabel('时间 (h)')
ax1.set_ylabel('热风温度 (°C)', color=PALETTE[0])
ax2.set_ylabel('水分浓度 (kg/kg)', color=PALETTE[1])
ax1.tick_params(axis='y', labelcolor=PALETTE[0])
ax2.tick_params(axis='y', labelcolor=PALETTE[1])

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, frameon=False, fontsize=FS, labelspacing=0.32,
           handlelength=1.5, loc='lower right')

declutter_axes(ax1, grid=False)
ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)
set_paper_placement(fig, 0.90)
save_fig(fig, out('fig_oven_input.png'))
