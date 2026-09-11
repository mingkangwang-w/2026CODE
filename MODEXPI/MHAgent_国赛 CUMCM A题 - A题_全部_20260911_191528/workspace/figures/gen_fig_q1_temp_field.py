"""问题 1 温度时空场云图（custom matplotlib，物理场签名）。

本图讲什么：预热段温度场 T(r,t) 在 r-t 平面上的全貌。等值线近似平行于 t 轴
说明径向温差很小（1800 s 时中心 33.58 / 表面 36.79，差 3.21 K），热扩散
时间尺度 tau_heat=2368.9 s 与预热时长同量级，故温度场基本随环境同步抬升。

图元：contourf 填充 + 黑色等值线叠加（标注温度值）+ 表面/中心两条参考线
+ 色条（单位 °C）。
数据来源：figures/problem_1_results.json 的 field_T（181 时刻 × 21 半径节点）
与 output_radii_cm。
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
t = np.asarray(res['field_T']['times_s'], dtype=float)
Z = np.asarray(res['field_T']['values'], dtype=float)   # (n_t, n_r)

RR, TT = np.meshgrid(r, t)

fig, ax = plt.subplots(figsize=(6.0, 3.7), layout='constrained')

levels = np.linspace(float(Z.min()), float(Z.max()), 22)
cf = ax.contourf(RR, TT, Z, levels=levels, cmap='YlOrRd', extend='neither')
# 等值线叠加：给读者可读的定量骨架
cl_levels = np.arange(np.ceil(Z.min()), np.floor(Z.max()) + 0.1, 1.0)
cs = ax.contour(RR, TT, Z, levels=cl_levels, colors=[COLORS['text']],
                linewidths=0.5, alpha=0.55)
ax.clabel(cs, cs.levels[::2], inline=True, fontsize=8, fmt='%.0f')

ax.set_xlabel('半径 $r$ (cm)')
ax.set_ylabel('时间 $t$ (s)')
ax.set_xlim(r[0], r[-1])
ax.set_ylim(t[0], t[-1])

cb = fig.colorbar(cf, ax=ax, pad=0.02, aspect=24)
cb.set_label('温度 $T$ (°C)')
cb.outline.set_linewidth(0.4)
cb.outline.set_edgecolor(COLORS['grid'])

# 末时刻中心/表面读数：给两端点名 + 数值，机理留正文
ax.annotate(f'{Z[-1, -1]:.2f}', xy=(r[-1], t[-1]), xytext=(-4, -13),
            textcoords='offset points', fontsize=FS, ha='right', va='top',
            color=COLORS['text'])
ax.annotate(f'{Z[-1, 0]:.2f}', xy=(r[0], t[-1]), xytext=(4, -13),
            textcoords='offset points', fontsize=FS, ha='left', va='top',
            color=COLORS['text'])

set_paper_placement(fig, 0.86)
save_fig(fig, out('fig_q1_temp_field.png'))
