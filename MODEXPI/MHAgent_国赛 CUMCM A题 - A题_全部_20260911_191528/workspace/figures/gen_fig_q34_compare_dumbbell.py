"""问题 3 与问题 4 达标时刻对比（advanced#2：哑铃图 + 变化率标注）。

本图讲什么：把固定域（问题 3）与收缩域（问题 4）在各径向位置的达标时刻配对成
哑铃。收缩把扩散路径缩短，各位置达标时刻整体左移，总时长由 57.27 h 降到
51.04 h（缩短 10.9%）。最内层（中心）是判据的控制点，也是缩短幅度的决定者。

哑铃口径：对每个无量纲位置 eta=r/R(t)，取该位置含水率首次降到 0.15 以下的时刻，
由各自的 field_C 按时间线性插值求得。用 eta 而非物理半径配对，因为问题 4 的
物理半径随时间变化，只有物质坐标位置在两问间可比。

图元：每个位置一根哑铃（问题 3 端点 + 问题 4 端点 + 连接线）+ 缩短量标注
+ 两问总时长参考线 + 图例。
数据来源：figures/problem_3_results.json 与 problem_4_results.json 的 field_C
（问题 3 的 21 节点为物理半径 r/R0，问题 4 的 21 节点为 eta，两者数值同为 0..1）
及各自 answer.t_star_h（57.2745 / 51.0444）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, declutter_axes,
                      auto_legend, PALETTE, COLORS, out)

C_TH = 0.15


def first_cross_times(times_h, Z, cols):
    """各列首次降到 C_TH 以下的时刻（沿时间线性插值）。"""
    outv = []
    for j in cols:
        series = Z[:, j]
        idx = np.where(series <= C_TH)[0]
        if idx.size == 0:
            outv.append(np.nan)
            continue
        i = int(idx[0])
        if i == 0:
            outv.append(float(times_h[0]))
            continue
        y0, y1 = series[i - 1], series[i]
        w = 0.0 if y0 == y1 else (y0 - C_TH) / (y0 - y1)
        outv.append(float(times_h[i - 1] + w * (times_h[i] - times_h[i - 1])))
    return np.asarray(outv, dtype=float)


p3 = load('problem_3_results')
p4 = load('problem_4_results')

t3 = np.asarray(p3['field_C']['times_s'], dtype=float) / 3600.0
Z3 = np.asarray(p3['field_C']['values'], dtype=float)
t4 = np.asarray(p4['field_C']['times_s'], dtype=float) / 3600.0
Z4 = np.asarray(p4['field_C']['values'], dtype=float)

n = Z3.shape[1]
# 取 5 个无量纲位置：中心到表面均匀分布（两问节点数一致，位置可直接对齐）
cols = [0, (n - 1) // 4, (n - 1) // 2, 3 * (n - 1) // 4, n - 1]
frac = np.asarray(cols, dtype=float) / (n - 1)

a3 = first_cross_times(t3, Z3, cols)
a4 = first_cross_times(t4, Z4, cols)

ts3 = float(p3['answer']['t_star_h'])
ts4 = float(p4['answer']['t_star_h'])

y = np.arange(len(cols))
fig, ax = plt.subplots(figsize=(6.2, 3.5), layout='constrained')

ax.hlines(y, np.minimum(a3, a4), np.maximum(a3, a4), color=COLORS['grid'],
          lw=2.4, zorder=2, capstyle='round')
ax.scatter(a3, y, s=62, color=PALETTE[0], edgecolors='white', linewidths=1.0,
           zorder=5, label=f'问题 3 固定域（$t^*$={ts3:.2f} h）')
ax.scatter(a4, y, s=62, color=PALETTE[3], edgecolors='white', linewidths=1.0,
           zorder=5, label=f'问题 4 收缩域（$t^*$={ts4:.2f} h）')

# 缩短量：放在两端点之间的连接线上方，数值 + 号即可，机理留正文
for i in range(len(cols)):
    mid = 0.5 * (a3[i] + a4[i])
    ax.annotate(f'{a4[i] - a3[i]:+.2f} h', xy=(mid, y[i]), xytext=(0, 7),
                textcoords='offset points', fontsize=FS, ha='center',
                va='bottom', color=COLORS['text'])

ax.set_yticks(y)
ax.set_yticklabels([('中心' if f == 0 else '表面' if f == 1
                     else f'$\\eta$={f:.2f}') for f in frac])
ax.set_xlabel('达标时刻 (h)')
ax.set_ylabel('无量纲位置 $\\eta=r/R(t)$')
ax.set_ylim(-0.6, len(cols) - 0.25)
lo = float(np.nanmin(a4)); hi = float(np.nanmax(a3))
ax.set_xlim(lo - 0.09 * (hi - lo), hi + 0.10 * (hi - lo))
declutter_axes(ax, grid='auto', grid_axis='x')
auto_legend(ax)

set_paper_placement(fig, 0.90)
save_fig(fig, out('fig_q34_compare_dumbbell.png'))
