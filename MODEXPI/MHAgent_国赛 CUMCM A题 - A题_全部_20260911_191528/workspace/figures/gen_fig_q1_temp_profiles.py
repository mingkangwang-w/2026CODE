"""问题 1 温度径向剖面分面图（basic#12）。

本图讲什么：预热段 0-1800 s 内 7 个指定时刻的温度径向剖面 T(r)，按时刻分面，
显示热量自表面向中心推进、表面先升温、中心滞后（Bi_h=1.389 的典型薄层响应）。

面板：(a)-(f) 为 300/600/900/1200/1500/1800 s 六个时刻的 T(r)；每面板含该时刻剖面、
上一时刻剖面（淡色对照）、初温参考线、中心与表面读数。100 s 剖面作为所有面板的最底层淡色底衬。

数据来源：figures/problem_1_results.json 的 paper_tables.table1_temperature
（7 行，t=100..1800 s，各 5 个半径 0/0.5/1/1.5/2 cm）与 table_radii_cm。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, declutter_axes,
                      consolidate_shared_legends, PALETTE, COLORS, out)

res = load('problem_1_results')
radii = np.asarray(res['table_radii_cm'], dtype=float)
rows = res['paper_tables']['table1_temperature']
times = [float(r['t_s']) for r in rows]
vals = [np.asarray(r['values'], dtype=float) for r in rows]
T0 = float(res['summary']['T0_degC']) if 'T0_degC' in res.get('summary', {}) \
    else float(min(v.min() for v in vals))

base_t, base_v = times[0], vals[0]
show = list(range(1, len(times)))

fig, axes = plt.subplots(2, 3, figsize=(6.4, 3.9), layout='constrained',
                         sharex=True, sharey=True)

for k, ax in zip(show, axes.flat):
    ax.plot(radii, base_v, '-', color=COLORS['grid'], lw=1.0, zorder=1,
            label=f'{base_t:.0f} s')
    if k - 1 >= 1:
        ax.plot(radii, vals[k - 1], '--', color=PALETTE[2], lw=1.1, zorder=2,
                label='前一时刻')
    ax.plot(radii, vals[k], 'o-', color=PALETTE[0], lw=1.8, ms=3.4,
            markeredgecolor='white', markeredgewidth=0.7, zorder=4,
            label='本时刻')
    ax.fill_between(radii, base_v, vals[k], color=PALETTE[0], alpha=0.10, lw=0,
                    zorder=1)
    ax.axhline(T0, color=COLORS['ref_line'], lw=0.7, ls=':', zorder=1)
    ax.set_title(f'({chr(96 + k)}) {times[k]:.0f} s', fontsize=FS, loc='left',
                 pad=3)
    # 表面读数放到曲线上方左侧的空白区：曲线自左下升来，其上方无图元
    ax.annotate(f'{vals[k][-1]:.2f}', xy=(radii[-1], vals[k][-1]),
                xytext=(-4, 6), textcoords='offset points', fontsize=FS,
                ha='right', va='bottom', color=PALETTE[0])
    # 中心读数放到中心点上方的楔形空白：曲线向右上升，正上方无图元
    ax.annotate(f'{vals[k][0]:.2f}', xy=(radii[0], vals[k][0]),
                xytext=(2, 5), textcoords='offset points', fontsize=FS,
                ha='left', va='bottom', color=PALETTE[0])
    declutter_axes(ax, grid='auto', grid_axis='y')

for ax in axes[1, :]:
    ax.set_xlabel('半径 $r$ (cm)')
for ax in axes[:, 0]:
    ax.set_ylabel('温度 (°C)')

axes[0, 0].set_xlim(radii[0] - 0.08, radii[-1] + 0.08)
lo = min(v.min() for v in vals)
hi = max(v.max() for v in vals)
axes[0, 0].set_ylim(lo - 0.6, hi + 1.9)

consolidate_shared_legends(fig, list(axes.flat), where='top', ncol=3,
                           fontsize=FS)
set_paper_placement(fig, 0.90)
save_fig(fig, out('fig_q1_temp_profiles.png'))
