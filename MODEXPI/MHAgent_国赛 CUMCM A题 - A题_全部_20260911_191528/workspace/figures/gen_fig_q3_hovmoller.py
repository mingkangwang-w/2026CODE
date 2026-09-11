"""问题 3 全时程水分场 Hovmöller 图（advanced#29：空间横 + 时间纵向下递增）。

本图讲什么：把 C(r,t) 按 Hovmöller 约定摊开（空间横轴、时间纵轴自上而下递增），
用于凸显"末期长尾"：图上部（前期）色带变化密集，下部（末期）大片颜色近乎不变，
即同样的时间跨度里含水率几乎不再下降。这是 t* 被末段主导的直接视觉证据。

图元：pcolormesh 色阶（矢量输出，非 imshow 栅格）+ C=0.15 判据等值线
+ t* 水平参考线与读数 + 色条（单位 kg/kg）。
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

fig, ax = plt.subplots(figsize=(6.0, 4.0), layout='constrained')

# pcolormesh 保持矢量单元格；shading='gouraud' 让连续场读起来平滑
pm = ax.pcolormesh(r, t, Z, cmap='YlGnBu', shading='gouraud',
                   vmin=float(Z.min()), vmax=float(Z.max()))

RR, TT = np.meshgrid(r, t)
cth = ax.contour(RR, TT, Z, levels=[C_th], colors=[COLORS['highlight']],
                 linewidths=2.0, zorder=6)
cs = ax.contour(RR, TT, Z, levels=[0.3, 0.6, 1.0, 1.5, 2.0],
                colors=[COLORS['text']], linewidths=0.5, alpha=0.5, zorder=5)
ax.clabel(cs, inline=True, fontsize=8, fmt='%.1f')

# Hovmöller 约定：时间自上而下递增
ax.invert_yaxis()

ax.axhline(t_star, color=COLORS['ref_line'], lw=1.0, ls=':', zorder=7)
ax.annotate(f'$t^*$={t_star:.2f} h', xy=(r[0], t_star), xytext=(6, -5),
            textcoords='offset points', fontsize=FS, ha='left', va='bottom',
            color=COLORS['text'])
ax.annotate(f'$C$={C_th}', xy=(r[-3], t_star * 0.82), xytext=(-6, -14),
            textcoords='offset points', fontsize=FS, ha='right', va='bottom',
            color=COLORS['highlight'])

ax.set_xlabel('半径 $r$ (cm)')
ax.set_ylabel('时间 $t$ (h)')
ax.set_xlim(r[0], r[-1])

cb = fig.colorbar(pm, ax=ax, pad=0.02, aspect=26)
cb.set_label('水分浓度 $C$ (kg/kg)')
cb.outline.set_linewidth(0.4)
cb.outline.set_edgecolor(COLORS['grid'])

set_paper_placement(fig, 0.86)
save_fig(fig, out('fig_q3_hovmoller.png'))
