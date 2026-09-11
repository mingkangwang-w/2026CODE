"""问题 1 数值解 vs Bessel 级数半解析解（competition#4：预测-实际 + 残差分布）。

本图讲什么：常物性下温度场存在 Bessel 级数半解析解（2000 模态），把它当作参照
量化有限体积格式的离散误差。7 个时刻 × 5 个半径共 35 个配对点全部落在 y=x 上，
最大绝对偏差 0.002062 K，相对温升量级（8.79 K）是 2.3e-4，说明格式误差不构成
问题 1 结论的不确定性来源。

面板：(a) 数值 vs 半解析散点 + y=x 参照线 + 最大偏差点标注；
      (b) 逐时刻最大绝对偏差（柱），显示偏差随时间的量级。
数据来源：figures/problem_1_results.json 的 analytic_validation.detail
（7 个时刻各含 numeric/analytic 两组 5 个值与 max_abs_dev）与 n_modes / Bi_h。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, declutter_axes,
                      panel, auto_legend, PALETTE, COLORS, out)

res = load('problem_1_results')
av = res['analytic_validation']
detail = av['detail']
keys = sorted(detail.keys(), key=lambda s: float(s.rstrip('s')))

num, ana, tags = [], [], []
devs = []
for k in keys:
    d = detail[k]
    num.extend(d['numeric'])
    ana.extend(d['analytic'])
    tags.extend([float(k.rstrip('s'))] * len(d['numeric']))
    devs.append(float(d['max_abs_dev']))
num = np.asarray(num); ana = np.asarray(ana); tags = np.asarray(tags)
devs = np.asarray(devs)
tvals = np.asarray([float(k.rstrip('s')) for k in keys])

fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.1), layout='constrained',
                         gridspec_kw={'width_ratios': [1.15, 1.0]})

# ── (a) 预测 vs 实际 ──
ax = axes[0]
lo = min(num.min(), ana.min()); hi = max(num.max(), ana.max())
pad = 0.06 * (hi - lo)
ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], '--',
        color=COLORS['ref_line'], lw=1.0, zorder=2, label='$y=x$')
sc = ax.scatter(ana, num, c=tags, cmap='YlOrRd', s=26, edgecolors='white',
                linewidths=0.6, zorder=4)
ax.set_xlabel('半解析解 $T$ (°C)')
ax.set_ylabel('数值解 $T$ (°C)')
ax.set_xlim(lo - pad, hi + pad)
ax.set_ylim(lo - pad, hi + pad)
ax.set_aspect('equal', adjustable='box')
declutter_axes(ax, grid='auto', grid_axis='both')
panel(ax, '(a)')
auto_legend(ax, fontsize=FS)

cb = fig.colorbar(sc, ax=ax, pad=0.02, aspect=26)
cb.set_label('时间 $t$ (s)')
cb.outline.set_linewidth(0.4)
cb.outline.set_edgecolor(COLORS['grid'])

# ── (b) 逐时刻最大绝对偏差 ──
ax = axes[1]
bars = ax.bar(np.arange(len(tvals)), devs * 1e3, width=0.66,
              color=PALETTE[:len(tvals)], edgecolor='white', linewidth=0.9,
              zorder=3)
ax.set_xticks(np.arange(len(tvals)))
ax.set_xticklabels([f'{v:.0f}' for v in tvals])
ax.set_xlabel('时间 $t$ (s)')
ax.set_ylabel('最大偏差 (mK)')
ax.bar_label(bars, fmt='%.2f', padding=2, fontsize=FS, color=COLORS['text'])
ax.set_ylim(0, devs.max() * 1e3 * 1.28)
declutter_axes(ax, grid='auto', grid_axis='y')
panel(ax, '(b)')

set_paper_placement(fig, 0.94)
save_fig(fig, out('fig_q1_analytic_validation.png'))
