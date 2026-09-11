"""网格/时间步收敛性验证（competition#1：解序列 + 逐级相对变化双面板）。

本图讲什么：把空间网格与时间步同步加密三级（20/40/80 单元，dt=20/10/5 s），
看 t* 是否收敛。(a) t* 随 dr 减小单调趋于平台；(b) 逐级相对变化由 0.92% 降到
0.45%，落在 1% 容差之下，故取最细一级（dr=0.025 cm、dt=5 s）作为正式结果。
相对变化逐级减半，与一阶隐式格式的预期一致。

图元：(a) t* 对 dr 的折线 + 节点读数 + 采用级高亮 + 反转横轴（自粗到细）；
(b) 相对变化条形 + 1% 容差线 + 条端读数 + 网格配置刻度标签。
数据来源：figures/problem_3_results.json 的 grid_convergence.table
（n_cells 20/40/80、dt_s 20/10/5、dr_cm 0.1/0.05/0.025、
t_star_h 56.4950/57.0168/57.2745、rel_change_vs_coarser null/0.009236/0.004519）
与 grid_convergence.tol=0.01。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, declutter_axes,
                      auto_legend, panel, PALETTE, COLORS, out)

res = load('problem_3_results')
gc = res['grid_convergence']
tab = gc['table']
tol = float(gc['tol'])

dr = np.asarray([float(r['dr_cm']) for r in tab])
dt = np.asarray([float(r['dt_s']) for r in tab])
nc = np.asarray([int(r['n_cells']) for r in tab])
ts = np.asarray([float(r['t_star_h']) for r in tab])
rel = np.asarray([np.nan if r['rel_change_vs_coarser'] is None
                  else float(r['rel_change_vs_coarser']) for r in tab]) * 100.0

fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.1), layout='constrained')

# (a) t* 随空间步长加密的走向
ax = axes[0]
ax.plot(dr, ts, '-o', color=PALETTE[0], lw=1.8, ms=6, mfc='white',
        mew=1.6, zorder=4, label='$t^*$ 收敛序列')
ax.scatter([dr[-1]], [ts[-1]], s=132, facecolors='none',
           edgecolors=COLORS['highlight'], linewidths=1.8, zorder=5,
           label='采用级')
for i in range(len(dr)):
    ax.annotate(f'{ts[i]:.3f}', xy=(dr[i], ts[i]), xytext=(0, -9),
                textcoords='offset points', fontsize=FS, ha='center',
                va='top', color=COLORS['text'])
ax.set_xscale('log')
ax.invert_xaxis()                      # 自左（粗）到右（细）
ax.set_xticks(dr)
ax.set_xticklabels([f'{v:g}' for v in dr])
ax.minorticks_off()
ax.set_xlabel('径向步长 $\\Delta r$ (cm)')
ax.set_ylabel('$t^*$ (h)')
span = ts.max() - ts.min()
ax.set_ylim(ts.min() - 0.55 * span, ts.max() + 0.30 * span)
declutter_axes(ax, grid='auto', grid_axis='y')
auto_legend(ax)
panel(ax, 'a')

# (b) 逐级相对变化与容差
ax = axes[1]
x = np.arange(1, len(tab))              # 首级无更粗一级可比
vals = rel[1:]
bars = ax.bar(x, vals, width=0.52, color=PALETTE[0], edgecolor='white',
              linewidth=0.6, zorder=3)
ax.axhline(tol * 100.0, color=COLORS['highlight'], lw=1.4, ls='--', zorder=4,
           label=f'容差 {tol * 100:.0f}%')
ax.bar_label(bars, labels=[f'{v:.3f}%' for v in vals], padding=3,
             fontsize=FS, color=COLORS['text'])

ax.set_xticks(x)
ax.set_xticklabels([f'{nc[i]}\n$\\Delta t$={dt[i]:g} s' for i in x])
ax.set_xlim(x[0] - 0.72, x[-1] + 0.72)
ax.set_ylim(0.0, max(vals.max(), tol * 100.0) * 1.42)
ax.set_xlabel('网格单元数')
ax.set_ylabel('相对变化 (%)')
declutter_axes(ax, grid='auto', grid_axis='y')
auto_legend(ax)
panel(ax, 'b')

set_paper_placement(fig, 0.96)
save_fig(fig, out('fig_grid_convergence.png'))
