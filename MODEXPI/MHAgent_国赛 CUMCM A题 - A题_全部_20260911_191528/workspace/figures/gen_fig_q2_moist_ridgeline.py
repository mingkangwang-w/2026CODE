"""问题 2 水分径向分布的山脊图（advanced#23：堆叠径向分布 + 中位刻痕）。

本图讲什么：把前 3 h 内多个时刻的 C(r) 剖面沿时间轴上下错开堆叠，一眼看出
"表层持续陡降、中心缓慢跟随"的演化形态。相比多线叠加，山脊图能把 9 个时刻的
剖面形状变化分离开，避免线条互相遮挡。

图元：9 个时刻的剖面脊线（自下而上时间递增）+ 每条脊线下的渐变填充
+ 每个时刻的域内中位半径刻痕（C 的体积加权中位位置）+ 时刻标签（左侧轴）。
数据来源：figures/problem_2_results.json 的 field_C（181 时刻 × 21 半径节点），
按等时间间隔抽 9 个时刻。中位刻痕由该剖面按累积质量 50% 实算。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, PALETTE,
                      COLORS, _lighten, out)

res = load('problem_2_results')
r = np.asarray(res['output_radii_cm'], dtype=float)
t_all = np.asarray(res['field_C']['times_s'], dtype=float)
Z_all = np.asarray(res['field_C']['values'], dtype=float)

n_show = 9
pick = np.linspace(0, len(t_all) - 1, n_show).round().astype(int)
times = t_all[pick] / 3600.0
profs = Z_all[pick]

# 脊线垂直间距：按剖面动态范围定，保证相邻脊线不糊在一起
span = float(profs.max() - profs.min())
step = span / (n_show * 0.62)

fig, ax = plt.subplots(figsize=(6.0, 4.2), layout='constrained')

base = PALETTE[0]
for i in range(n_show):
    prof = profs[i]
    off = i * step
    y = prof - prof.min() + off
    frac = i / (n_show - 1)
    col = _lighten(base, 0.60 * (1.0 - frac))
    ax.fill_between(r, off, y, color=col, alpha=0.55, lw=0, zorder=2 + i)
    ax.plot(r, y, '-', color=col, lw=1.5, zorder=2 + i + 1)

    # 中位刻痕：累积质量（含 r 权重的圆柱体积元）达 50% 的半径
    w = prof * r
    cum = np.cumsum(w)
    if cum[-1] > 0:
        half = 0.5 * cum[-1]
        j = int(np.searchsorted(cum, half))
        j = min(max(j, 1), len(r) - 1)
        c0, c1 = cum[j - 1], cum[j]
        frac_j = 0.0 if c1 == c0 else (half - c0) / (c1 - c0)
        r_med = r[j - 1] + frac_j * (r[j] - r[j - 1])
        y_med = np.interp(r_med, r, y)
        ax.vlines(r_med, off, y_med, color=COLORS['highlight'], lw=1.1,
                  zorder=40)

ax.set_yticks([i * step for i in range(n_show)])
ax.set_yticklabels([f'{v:.2f}' for v in times])
ax.set_xlabel('半径 $r$ (cm)')
ax.set_ylabel('时间 $t$ (h)')
ax.set_xlim(r[0], r[-1])
ax.set_ylim(-0.06 * step, (n_show - 1) * step + span * 0.62)

# 图例：说明刻痕语义，图内不再重复塞字
ax.vlines([], [], [], color=COLORS['highlight'], lw=1.1,
          label='质量中位半径')
ax.plot([], [], '-', color=base, lw=1.5, label='$C(r)$ 剖面')
ax.legend(loc='upper right', fontsize=FS, frameon=False, labelspacing=0.3,
          handlelength=1.6)

for s in ('top', 'right'):
    ax.spines[s].set_visible(False)

set_paper_placement(fig, 0.86)
save_fig(fig, out('fig_q2_moist_ridgeline.png'))
