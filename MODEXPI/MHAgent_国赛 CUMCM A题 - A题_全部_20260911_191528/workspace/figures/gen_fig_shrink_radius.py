"""附件 2 半径收缩曲线（basic#3）。

本图讲什么：药材半径 R(t) 从 2.000 cm 收缩到 1.198 cm 的全过程（0-72 h），
并标出收缩停滞点（此后 R 不再变化），说明问题 4 的动边界只在停滞前活跃。

图元：三层渐变填充 + 主折线 + 起止端点标注 + 停滞点箭头标注 + 停滞后区间底纹。
数据来源：user_data/附件2.xlsx（145 行，列「时间」「半径」，步长 1800 s）。
关键数值：R(0)=2.000 cm，R(末)=1.198 cm，停滞点由 R<=R_min+1e-12 首次成立处取出。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _figbase import (FS, save_fig, set_paper_placement, declutter_axes,
                      PALETTE, COLORS, out)

df = pd.read_excel('user_data/附件2.xlsx')
t_h = df['时间'].to_numpy(dtype=float) / 3600.0
R = df['半径'].to_numpy(dtype=float)

R0, R_end = float(R[0]), float(R[-1])
i_stall = int(np.argmax(R <= R_end + 1e-12))
t_stall = float(t_h[i_stall])
total_shrink = (R0 - R_end) / R0 * 100.0

fig, ax = plt.subplots(figsize=(6.4, 3.6))

ax.axvspan(t_stall, t_h[-1], color=PALETTE[2], alpha=0.07, lw=0, zorder=0)

for layer, alpha in enumerate([0.18, 0.10, 0.04]):
    ax.fill_between(t_h, R_end - 0.02 + layer * 0.006, R - layer * 0.006,
                    color=PALETTE[0], alpha=alpha, lw=0, zorder=1)

ax.plot(t_h, R, '-', color=PALETTE[0], lw=1.9, zorder=3)
ax.scatter([t_h[0], t_h[-1]], [R0, R_end], s=40, color=PALETTE[0],
           edgecolor='white', linewidth=1.3, zorder=5)

ax.scatter([t_stall], [R[i_stall]], s=62, marker='*', color=COLORS['highlight'],
           edgecolor='white', linewidth=1.1, zorder=6)
ax.annotate(f'停滞点 {t_stall:.1f} h', xy=(t_stall, R[i_stall]),
            xytext=(t_stall - 22.0, R_end + 0.20),
            fontsize=FS, color=COLORS['highlight'],
            arrowprops=dict(arrowstyle='->', color=COLORS['highlight'], lw=0.9))

ax.annotate(f'{R0:.3f} cm', xy=(t_h[0], R0), xytext=(6, 4),
            textcoords='offset points', fontsize=FS, color=COLORS['text'])
ax.annotate(f'{R_end:.3f} cm', xy=(t_h[-1], R_end), xytext=(-4, 9),
            textcoords='offset points', fontsize=FS, ha='right',
            color=COLORS['text'])
ax.text(0.985, 0.93, f'-{total_shrink:.1f}%', transform=ax.transAxes,
        fontsize=FS, ha='right', va='top', color=PALETTE[0])

ax.set_xlabel('时间 (h)')
ax.set_ylabel('半径 $R(t)$ (cm)')
ax.set_xlim(-1.5, t_h[-1] + 1.5)
ax.set_ylim(R_end - 0.075, R0 + 0.075)

declutter_axes(ax, grid='auto', grid_axis='y')
set_paper_placement(fig, 0.90)
save_fig(fig, out('fig_shrink_radius.png'))
