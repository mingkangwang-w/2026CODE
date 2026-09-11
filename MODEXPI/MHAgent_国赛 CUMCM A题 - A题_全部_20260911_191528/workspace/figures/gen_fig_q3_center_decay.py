"""问题 3 中心含水率长时程衰减（competition#17：多步衰减 + 阈值线 + t* 标注）。

本图讲什么：中心含水率从 C0=2.55 衰减到判据 0.15 的全过程（0 → 57.27 h）。
形态上是"前段快、后段极慢"的长尾：D 含 exp(-0.45/C) 的分式指数，C 越低 D 越小，
于是末段自身减速，这是 t* 达 57.27 h 而非线性外推所得短得多值的原因。
图中同时画出表面曲线作对照——表面早在 12.56 h 就已达标（criterion_variants），
说明判据必须取全域最大值而非表面值。

图元：中心/表面两条衰减曲线 + 0.15 判据线 + t* 竖线与读数
+ 判据口径对照刻痕（表面达标时刻）+ 半对数纵轴显示末段长尾。
数据来源：figures/problem_3_results.json 的 center_series / surface_series
（各 3438 点，0-2.06e5 s）、answer.t_star_h=57.2745、criterion_variants。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, declutter_axes,
                      auto_legend, log_pow_ticks, PALETTE, COLORS, _lighten,
                      out)

res = load('problem_3_results')
t = np.asarray(res['center_series']['times_s'], dtype=float) / 3600.0
Cc = np.asarray(res['center_series']['C'], dtype=float)
Cs = np.asarray(res['surface_series']['C'], dtype=float)
t_star = float(res['answer']['t_star_h'])
C_th = 0.15
t_surf = float(res['criterion_variants']['t_star_h_by_criterion']['surface'])

fig, ax = plt.subplots(figsize=(6.2, 3.7), layout='constrained')

ax.fill_between(t, C_th, Cc, where=(Cc >= C_th),
                color=_lighten(PALETTE[0], 0.60), alpha=0.35, lw=0, zorder=1)
ax.plot(t, Cc, '-', color=PALETTE[0], lw=2.0, zorder=4, label='中心 $C$')
ax.plot(t, Cs, '-', color=PALETTE[3], lw=1.5, zorder=3, label='表面 $C$')

ax.axhline(C_th, color=COLORS['highlight'], lw=1.2, ls='--', zorder=5,
           label=f'判据 $C$={C_th}')
ax.axvline(t_star, color=COLORS['ref_line'], lw=1.0, ls=':', zorder=5)

ax.set_yscale('log')
log_pow_ticks(ax, axis='y')

# t* 读数：给这条竖线命名 + 数值
ax.annotate(f'$t^*$={t_star:.2f} h', xy=(t_star, Cc.max()),
            xytext=(-6, -4), textcoords='offset points', fontsize=FS,
            ha='right', va='top', color=COLORS['text'])
# 表面达标时刻：判据口径对照的锚点
ax.annotate(f'表面达标 {t_surf:.2f} h', xy=(t_surf, C_th),
            xytext=(10, 16), textcoords='offset points', fontsize=FS,
            ha='left', va='bottom', color=PALETTE[3],
            arrowprops=dict(arrowstyle='->', color=PALETTE[3], lw=0.8))

ax.set_xlabel('时间 $t$ (h)')
ax.set_ylabel('水分浓度 $C$ (kg/kg)')
ax.set_xlim(t[0], t[-1] * 1.02)
ax.set_ylim(min(Cs.min(), C_th) * 0.72, Cc.max() * 1.45)
declutter_axes(ax, grid='auto', grid_axis='y')
auto_legend(ax)

set_paper_placement(fig, 0.90)
save_fig(fig, out('fig_q3_center_decay.png'))
