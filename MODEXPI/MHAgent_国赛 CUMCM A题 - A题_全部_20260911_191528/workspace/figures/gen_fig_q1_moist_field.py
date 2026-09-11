"""问题 1 水分浓度时空场云图（custom matplotlib，物理场签名 + 渗透深度标注）。

本图讲什么：预热段水分场 C(r,t) 的全貌。与温度场相反，等值线全部挤在表面附近，
说明失水只在表层薄壳内发生；内部大片区域仍是初值色，即扩散尚未渗透进去。
渗透深度用 C 相对初值下降 1% 的位置定义（sqrt(D·t) 量级的直接可视化）。

图元：contourf 填充 + 等值线叠加 + 渗透深度前沿曲线（实测自场数据）
+ 前沿末端读数 + 色条（单位 kg/kg）。
数据来源：figures/problem_1_results.json 的 field_C（181 时刻 × 21 半径节点）。
渗透深度由该场按 1% 阈值逐时刻线性插值求得，非外部假设。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, PALETTE,
                      COLORS, out)

res = load('problem_1_results')
r = np.asarray(res['output_radii_cm'], dtype=float)
t = np.asarray(res['field_C']['times_s'], dtype=float)
Z = np.asarray(res['field_C']['values'], dtype=float)

C0 = float(Z[0].max())
RR, TT = np.meshgrid(r, t)

fig, ax = plt.subplots(figsize=(6.0, 3.7), layout='constrained')

levels = np.linspace(float(Z.min()), C0, 22)
cf = ax.contourf(RR, TT, Z, levels=levels, cmap='YlGnBu', extend='neither')
cs = ax.contour(RR, TT, Z, levels=[1.6, 1.8, 2.0, 2.2, 2.4, 2.5],
                colors=[COLORS['text']], linewidths=0.5, alpha=0.55)
ax.clabel(cs, inline=True, fontsize=8, fmt='%.1f')

# 渗透前沿：C 降到 0.99*C0 的半径，逐时刻线性插值（C 沿 r 单调非增）
thresh = 0.99 * C0
front = np.full(len(t), np.nan)
for i in range(len(t)):
    prof = Z[i]
    idx = np.where(prof <= thresh)[0]
    if idx.size == 0:
        continue
    j = idx[0]
    if j == 0:
        front[i] = r[0]
    else:
        x0, x1 = prof[j - 1], prof[j]
        w = 0.0 if x0 == x1 else (x0 - thresh) / (x0 - x1)
        front[i] = r[j - 1] + w * (r[j] - r[j - 1])

ok = ~np.isnan(front)
ax.plot(front[ok], t[ok], '-', color=COLORS['highlight'], lw=1.8, zorder=6)
ax.annotate(f'渗透前沿 {front[ok][-1]:.2f} cm',
            xy=(front[ok][-1], t[ok][-1]), xytext=(-8, -16),
            textcoords='offset points', fontsize=FS, ha='right', va='top',
            color=COLORS['highlight'],
            arrowprops=dict(arrowstyle='->', color=COLORS['highlight'], lw=0.8))

ax.set_xlabel('半径 $r$ (cm)')
ax.set_ylabel('时间 $t$ (s)')
ax.set_xlim(r[0], r[-1])
ax.set_ylim(t[0], t[-1])

cb = fig.colorbar(cf, ax=ax, pad=0.02, aspect=24)
cb.set_label('水分浓度 $C$ (kg/kg)')
cb.outline.set_linewidth(0.4)
cb.outline.set_edgecolor(COLORS['grid'])

set_paper_placement(fig, 0.86)
save_fig(fig, out('fig_q1_moist_field.png'))
