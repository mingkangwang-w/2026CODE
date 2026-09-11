"""问题 1 水分浓度径向剖面（basic#3：多时刻叠加 + 渐变填充）。

本图讲什么：预热段 7 个指定时刻的 C(r) 叠加在同一坐标里。核心现象是"表层陡降 +
中心平台"：Bi_m=3.24 且 tau_mass=8.10e4 s 远大于预热时长 1800 s，故失水只发生在
表层薄壳内，中心 1800 s 时仍停在初值 C0=2.55（表面已降至 1.5104）。

图元：7 条时刻剖面（浅→深渐变表示时间推进）+ 相邻时刻间渐变填充 + C0 参考线
+ 中心平台区标注 + 末时刻表面读数。
数据来源：figures/problem_1_results.json 的 paper_tables.table2_moisture
（7 行 t=100..1800 s）与 field_C（21 节点细剖面，用于画光滑曲线）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, declutter_axes,
                      auto_legend, PALETTE, COLORS, _lighten, out)

res = load('problem_1_results')
# 细网格场用于光滑曲线；表格时刻用于取剖面
radii = np.asarray(res['output_radii_cm'], dtype=float)
ftimes = np.asarray(res['field_C']['times_s'], dtype=float)
fvals = np.asarray(res['field_C']['values'], dtype=float)
tab_times = [float(r['t_s']) for r in res['paper_tables']['table2_moisture']]

C0 = float(res['center_series']['C'][0])
base = PALETTE[0]

fig, ax = plt.subplots(figsize=(6.0, 3.6), layout='constrained')

prev = None
for i, t in enumerate(tab_times):
    j = int(np.argmin(np.abs(ftimes - t)))
    prof = fvals[j]
    # 浅→深表示时间推进：同一色系内部渐变，避免 7 条线各用一色造成噪声
    frac = i / (len(tab_times) - 1)
    col = _lighten(base, 0.68 * (1.0 - frac))
    ax.plot(radii, prof, '-', color=col, lw=1.7, zorder=3 + i,
            label=f'{t:.0f} s')
    if prev is not None:
        ax.fill_between(radii, prev, prof, color=col, alpha=0.13, lw=0, zorder=2)
    prev = prof

ax.axhline(C0, color=COLORS['ref_line'], lw=0.8, ls=':', zorder=1)

last = fvals[int(np.argmin(np.abs(ftimes - tab_times[-1])))]
ax.annotate(f'{last[-1]:.4f}', xy=(radii[-1], last[-1]),
            xytext=(-6, 8), textcoords='offset points', fontsize=FS,
            ha='right', va='bottom', color=base,
            arrowprops=dict(arrowstyle='-', color=base, lw=0.7,
                            shrinkA=0, shrinkB=2))
# 中心平台：给这段区域起名，具体机理留正文
ax.annotate(f'中心平台 $C_0$={C0}', xy=(0.16, C0), xytext=(0.30, C0 - 0.30),
            fontsize=FS, color=COLORS['text'], va='top',
            arrowprops=dict(arrowstyle='->', color=COLORS['ref_line'], lw=0.7))

ax.set_xlabel('半径 $r$ (cm)')
ax.set_ylabel('水分浓度 $C$ (kg/kg)')
ax.set_xlim(radii[0] - 0.05, radii[-1] + 0.05)
ax.set_ylim(float(fvals.min()) - 0.16, C0 + 0.10)
declutter_axes(ax, grid='auto', grid_axis='y')
auto_legend(ax, ncol=2, fontsize=FS)

set_paper_placement(fig, 0.86)
save_fig(fig, out('fig_q1_moist_profiles.png'))
