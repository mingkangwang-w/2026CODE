"""问题 4 收缩律一致性校验（advanced#8：Bland-Altman 一致性图）。

本图讲什么：附件 2 的 R(t) 是问题 4 的输入，而绝干质量守恒给出一条独立的
正向预测律 R_pred = R0*sqrt(V/V0)，V/V0 由体均含水率算出（不反演）。把两者
逐时刻配对做 Bland-Altman：若两者一致，说明"仅径向收缩 + 附录 4 密度"这组
假设与实测收缩自洽。终点处预测 1.237 cm vs 实测 1.198 cm，相对偏差 3.29%
（shrinkage_prediction 中三种假设组合里最小的一个）。

图元：差值-均值散点（按时间着色）+ 平均偏差线 + ±1.96 SD 一致界
+ 比例偏差回归线 + 零偏差参照线 + 终点配对标注。
数据来源：figures/problem_4_results.json 的 field_C（206 时刻 × 21 eta 节点）
与 radius_series（实测 R(t)，插值到场时刻）；预测律复用 code/properties.py 的
predict_radius_radial_only + APPENDIX4（与 problem_4.py 同一函数，不另写公式）。
体均含水率按圆柱体积元权重 2*eta 在 eta 网格上积分。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'code'))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, declutter_axes,
                      auto_legend, PALETTE, COLORS, _lighten, out)

import params as P
import properties as PR

res = load('problem_4_results')
n_eta = len(res['field_C']['values'][0])
eta = np.linspace(0.0, 1.0, n_eta)
t = np.asarray(res['field_C']['times_s'], dtype=float) / 3600.0
Z = np.asarray(res['field_C']['values'], dtype=float)

rs_t = np.asarray(res['radius_series']['times_s'], dtype=float) / 3600.0
rs_R = np.asarray(res['radius_series']['R_cm'], dtype=float)
R_meas = np.interp(t, rs_t, rs_R)

# 体均含水率：圆柱体积元权重 2*eta（无量纲域上 ∫2*eta*C d_eta）
w = 2.0 * eta
C_bar = np.trapezoid(Z * w[None, :], eta, axis=1) / np.trapezoid(w, eta)

# 正向预测：复用生产代码的收缩律，不在图脚本里重写公式
R_pred = np.asarray([float(PR.predict_radius_radial_only(c, PR.APPENDIX4))
                     for c in C_bar]) * P.CM_PER_M

mean_v = 0.5 * (R_pred + R_meas)
diff_v = R_pred - R_meas
bias = float(np.mean(diff_v))
sd = float(np.std(diff_v, ddof=1))
upper, lower = bias + 1.96 * sd, bias - 1.96 * sd

fig, ax = plt.subplots(figsize=(6.2, 3.7), layout='constrained')

xs = np.linspace(mean_v.min(), mean_v.max(), 200)
ax.fill_between(xs, lower, upper, color=_lighten(PALETTE[0], 0.55), alpha=0.20,
                lw=0, zorder=1, label='±1.96 SD')
ax.axhline(0.0, color=COLORS['ref_line'], lw=0.9, ls=':', zorder=2,
           label='零偏差')
ax.axhline(bias, color=PALETTE[0], lw=1.7, zorder=4,
           label=f'平均偏差 {bias:+.4f} cm')
ax.axhline(upper, color=PALETTE[3], lw=1.1, ls='--', zorder=3)
ax.axhline(lower, color=PALETTE[3], lw=1.1, ls='--', zorder=3)

sc = ax.scatter(mean_v, diff_v, c=t, cmap='YlOrRd', s=24, edgecolors='white',
                linewidths=0.5, zorder=6)

# 比例偏差回归线：判断偏差是否随半径系统漂移
sl, ic = np.polyfit(mean_v, diff_v, 1)
ax.plot(xs, sl * xs + ic, '-.', color=COLORS['highlight'], lw=1.3, zorder=7,
        label=f'比例偏差斜率 {sl:+.4f}')

ax.annotate(f'{upper:+.4f}', xy=(mean_v.max(), upper), xytext=(-2, 4),
            textcoords='offset points', fontsize=FS, ha='right', va='bottom',
            color=PALETTE[3])
ax.annotate(f'{lower:+.4f}', xy=(mean_v.max(), lower), xytext=(-2, -4),
            textcoords='offset points', fontsize=FS, ha='right', va='top',
            color=PALETTE[3])

ax.set_xlabel('预测与实测半径均值 (cm)')
ax.set_ylabel('预测 $-$ 实测 (cm)')   # SimHei 缺 U+2212，减号走 mathtext
declutter_axes(ax, grid='auto', grid_axis='y')
auto_legend(ax)

cb = fig.colorbar(sc, ax=ax, pad=0.02, aspect=26)
cb.set_label('时间 $t$ (h)')
cb.outline.set_linewidth(0.4)
cb.outline.set_edgecolor(COLORS['grid'])

set_paper_placement(fig, 0.90)
save_fig(fig, out('fig_q4_shrink_validation.png'))
