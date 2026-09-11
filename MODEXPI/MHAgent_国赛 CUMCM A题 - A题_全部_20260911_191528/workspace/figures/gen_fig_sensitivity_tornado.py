"""参数敏感性龙卷风图（competition#2：双向条形按影响幅度排序）。

本图讲什么：把 6 个模型参数各自 ±10% 扰动后 t* 的相对变化画成左右对置条形，
按最大绝对相对变化降序排列。Arrhenius 指数系数（3850）一项独占两个数量级，
其余参数合计不足其十分之一——这解释了为什么标定工作应集中在温度激活项上。
h 的影响接近零，说明该工况下过程受内部扩散控制而非表面换热控制。

图元：以零变化为中轴的对置条形（高扰动 / 低扰动分色）+ 条端相对变化标注
+ 基准参考线与读数 + 线性横轴（保留幅度可比性，小量级由条端读数给出）+ 图例。
数据来源：figures/sensitivity_results.json 的 main_group（base_t_star_h=56.4950，
factor_high=1.1 / factor_low=0.9，n_cells=20、dt=20 s）的 rows 字段
rel_change_high / rel_change_low，顺序取 ranking_by_abs_rel_max。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, declutter_axes,
                      auto_legend, PALETTE, COLORS, out)

res = load('sensitivity_results')
mg = res['main_group']
base = float(mg['base_t_star_h'])
fh = float(mg['factor_high'])
fl = float(mg['factor_low'])

rows = {r['id']: r for r in mg['rows']}
order = list(mg['ranking_by_abs_rel_max'])
# 龙卷风约定：影响最大者置顶，故绘图自下而上排
order = order[::-1]

labels = [rows[k]['label'] for k in order]
hi = np.asarray([float(rows[k]['rel_change_high']) for k in order]) * 100.0
lo = np.asarray([float(rows[k]['rel_change_low']) for k in order]) * 100.0

y = np.arange(len(order))
fig, ax = plt.subplots(figsize=(6.3, 3.8), layout='constrained')

bh = ax.barh(y, hi, height=0.62, color=PALETTE[0], edgecolor='white',
             linewidth=0.6, zorder=3, label=f'参数 $\\times${fh:.1f}')
bl = ax.barh(y, lo, height=0.62, color=PALETTE[3], edgecolor='white',
             linewidth=0.6, zorder=3, label=f'参数 $\\times${fl:.1f}')

ax.axvline(0.0, color=COLORS['ref_line'], lw=1.0, zorder=4)

# 条端读数：正条向右、负条向左，均落在条外空白
for arr in (hi, lo):
    for i, v in enumerate(arr):
        off = 4 if v >= 0 else -4
        ax.annotate(f'{v:+.2f}%', xy=(v, y[i]), xytext=(off, 0),
                    textcoords='offset points', fontsize=FS, va='center',
                    ha='left' if v >= 0 else 'right', color=COLORS['text'])

ax.annotate(f'基准 $t^*$={base:.2f} h', xy=(0.0, y[-1] + 0.52), xytext=(4, 0),
            textcoords='offset points', fontsize=FS, ha='left', va='center',
            color=COLORS['text'])

ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel('$t^*$ 相对变化 (%)')
span = max(hi.max(), abs(lo.min()))
ax.set_xlim(-span * 0.62, span * 1.30)
ax.set_ylim(-0.66, len(order) - 0.14)
declutter_axes(ax, grid='auto', grid_axis='x')
auto_legend(ax)

set_paper_placement(fig, 0.92)
save_fig(fig, out('fig_sensitivity_tornado.png'))
