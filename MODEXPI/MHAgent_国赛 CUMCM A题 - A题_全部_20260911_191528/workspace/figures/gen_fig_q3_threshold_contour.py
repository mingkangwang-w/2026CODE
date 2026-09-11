"""问题 3 干燥前沿等高线（competition#14：等高线 + 判据等值线加粗）。

本图讲什么：C(r,t) 在 r-t 平面上的等值线族，其中 C=0.15 那一条就是"干燥前沿"。
前沿自表面向中心推进，抵达中心（r=0）的时刻即 t*=57.27 h——这给出终点判据的
几何解释：判据不是某个平均量达标，而是最后一个未达标点（中心）达标。
等值线在末段明显变疏，对应 D 随 C 下降而坍塌造成的减速。

图元：多条 C 等值线（细）+ C=0.15 判据等值线（加粗高亮）+ 前沿抵达中心的
t* 标注 + 填充色阶 + 色条。
数据来源：figures/problem_3_results.json 的 field_C（59 时刻 × 21 半径节点）、
answer.t_star_h=57.2745。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, PALETTE,
                      COLORS, out)

res = load('problem_3_results')
r = np.asarray(res['output_radii_cm'], dtype=float)
t = np.asarray(res['field_C']['times_s'], dtype=float) / 3600.0
Z = np.asarray(res['field_C']['values'], dtype=float)
t_star = float(res['answer']['t_star_h'])
C_th = 0.15

RR, TT = np.meshgrid(r, t)

fig, ax = plt.subplots(figsize=(6.0, 3.8), layout='constrained')

cf = ax.contourf(RR, TT, Z, levels=np.linspace(Z.min(), Z.max(), 20),
                 cmap='YlGnBu', alpha=0.92)
# 2.0 与 2.4 两条线在 t<3 h 内相距不足 1 h，标签会挤压，故舍去最上一级
levels = [0.3, 0.5, 0.8, 1.2, 1.6, 2.0]
cs = ax.contour(RR, TT, Z, levels=levels, colors=[COLORS['text']],
                linewidths=0.6, alpha=0.55)
ax.clabel(cs, inline=True, fontsize=8, fmt='%.1f')

# 判据等值线：本图主角，单独加粗高亮
cth = ax.contour(RR, TT, Z, levels=[C_th], colors=[COLORS['highlight']],
                 linewidths=2.2, zorder=8)

ax.axhline(t_star, color=COLORS['ref_line'], lw=1.0, ls=':', zorder=7)
ax.annotate(f'$t^*$={t_star:.2f} h', xy=(r[-1], t_star), xytext=(-5, 7),
            textcoords='offset points', fontsize=FS, ha='right', va='bottom',
            color=COLORS['text'])
# 给判据前沿起名
ax.annotate(f'干燥前沿 $C$={C_th}', xy=(r[6], t_star * 0.90),
            xytext=(0.72, t_star * 0.55), fontsize=FS,
            color=COLORS['highlight'], ha='left', va='top',
            arrowprops=dict(arrowstyle='->', color=COLORS['highlight'],
                            lw=0.9))

ax.set_xlabel('半径 $r$ (cm)')
ax.set_ylabel('时间 $t$ (h)')
ax.set_xlim(r[0], r[-1])
ax.set_ylim(t[0], t[-1])

cb = fig.colorbar(cf, ax=ax, pad=0.02, aspect=24)
cb.set_label('水分浓度 $C$ (kg/kg)')
cb.outline.set_linewidth(0.4)
cb.outline.set_edgecolor(COLORS['grid'])

set_paper_placement(fig, 0.86)
save_fig(fig, out('fig_q3_threshold_contour.png'))
