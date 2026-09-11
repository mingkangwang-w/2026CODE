"""问题 4 收缩域上的水分时空分布（basic#5：手动布局热力图 + 域外遮罩）。

本图讲什么：问题 4 在物质坐标 eta=r/R(t) 上求解，本图把解映射回物理半径
r=eta*R(t) 画在 r-t 平面上，于是右边界随 R(t) 从 2.000 cm 内移到 1.198 cm，
域外区域用遮罩表示"物料已不在那里"。这是问题 3（固定域）与问题 4 的本质差别：
收缩使扩散路径变短，t* 由 57.27 h 降到 51.04 h。

图元：pcolormesh 色阶（在 r-t 平面，逐时刻按 R(t) 拉伸）+ 域外遮罩
+ 收缩边界 R(t) 曲线 + C=0.15 判据等值线 + t* 与末端半径读数 + 色条。
数据来源：figures/problem_4_results.json 的 field_C（206 时刻 × 21 个 eta 节点，
eta 等距 0..1）、radius_series（R_cm，3063 点，插值到 field 时刻）、
answer.t_star_h=51.0444 与 R_at_tstar_cm=1.2。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, PALETTE,
                      COLORS, out)

res = load('problem_4_results')
n_eta = len(res['field_C']['values'][0])
eta = np.linspace(0.0, 1.0, n_eta)          # field_C 落在等距 eta 网格上
t = np.asarray(res['field_C']['times_s'], dtype=float) / 3600.0
Z = np.asarray(res['field_C']['values'], dtype=float)

rs_t = np.asarray(res['radius_series']['times_s'], dtype=float) / 3600.0
rs_R = np.asarray(res['radius_series']['R_cm'], dtype=float)
R_at = np.interp(t, rs_t, rs_R)             # 场时刻上的收缩半径

t_star = float(res['answer']['t_star_h'])
R_star = float(res['answer']['R_at_tstar_cm'])
C_th = 0.15
R0 = float(rs_R[0])

# eta → 物理半径：逐时刻把 [0,1] 拉伸到 [0,R(t)]
RR = eta[None, :] * R_at[:, None]
TT = np.repeat(t[:, None], n_eta, axis=1)

fig, ax = plt.subplots(figsize=(6.0, 3.9), layout='constrained')

pm = ax.pcolormesh(RR, TT, Z, cmap='YlGnBu', shading='gouraud',
                   vmin=float(Z.min()), vmax=float(Z.max()))

# 域外遮罩：R(t) 右侧不再有物料
ax.fill_betweenx(t, R_at, R0 * 1.02, color='white', alpha=0.90, lw=0, zorder=4)
ax.fill_betweenx(t, R_at, R0 * 1.02, color=COLORS['grid'], alpha=0.28, lw=0,
                 hatch='///', edgecolor=COLORS['grid'], zorder=5)

ax.plot(R_at, t, '-', color=COLORS['highlight'], lw=2.0, zorder=7,
        label='收缩边界 $R(t)$')

cth = ax.contour(RR, TT, Z, levels=[C_th], colors=[PALETTE[3]],
                 linewidths=1.8, zorder=8)

ax.axhline(t_star, color=COLORS['ref_line'], lw=1.0, ls=':', zorder=7)
ax.annotate(f'$t^*$={t_star:.2f} h', xy=(0.0, t_star), xytext=(5, 6),
            textcoords='offset points', fontsize=FS, ha='left', va='bottom',
            color=COLORS['text'])
ax.annotate(f'$R$={R_star:.3f} cm', xy=(R_star, t_star), xytext=(9, -6),
            textcoords='offset points', fontsize=FS, ha='left', va='top',
            color=COLORS['highlight'])
ax.plot([], [], '-', color=PALETTE[3], lw=1.8, label=f'判据 $C$={C_th}')

ax.set_xlabel('半径 $r$ (cm)')
ax.set_ylabel('时间 $t$ (h)')
ax.set_xlim(0.0, R0 * 1.02)
ax.set_ylim(t[0], t[-1])
ax.legend(loc='upper left', fontsize=FS, frameon=False, labelspacing=0.3,
          handlelength=1.6)

cb = fig.colorbar(pm, ax=ax, pad=0.02, aspect=26)
cb.set_label('水分浓度 $C$ (kg/kg)')
cb.outline.set_linewidth(0.4)
cb.outline.set_edgecolor(COLORS['grid'])

set_paper_placement(fig, 0.86)
save_fig(fig, out('fig_q4_moving_domain_heatmap.png'))
