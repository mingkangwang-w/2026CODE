"""问题 2 两阶段演化（empirical#7：双 Y 轴时间序列 + 阶段分隔）。

本图讲什么：变物性双向耦合下，前 3 h 内中心与表面的 T、C 演化。附件 1 的环境
温度在 10800 s 前已到 50 °C 平台，故全过程分为"预热段"（环境驱动升温，径向温差
可见）与"恒温段"（温度锁定在 50 °C，径向温差压到 0.117 K，失水成为唯一慢过程）。
分界点取环境温度首次进入平台 0.5 K 以内的时刻，由 env_series 实算而非人为指定。

图元：左轴两条温度曲线（中心/表面）+ 环境温度参考线；右轴两条含水率曲线（虚线）；
阶段分隔竖线 + 3 h 终点读数。
数据来源：figures/problem_2_results.json 的 center_series / surface_series /
env_series（各 10801 点，0-10800 s）与 summary 的 3 h 终值。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, declutter_axes,
                      auto_legend, PALETTE, COLORS, out)

res = load('problem_2_results')
t = np.asarray(res['center_series']['times_s'], dtype=float) / 3600.0
Tc = np.asarray(res['center_series']['T'], dtype=float)
Ts = np.asarray(res['surface_series']['T'], dtype=float)
Cc = np.asarray(res['center_series']['C'], dtype=float)
Cs = np.asarray(res['surface_series']['C'], dtype=float)
Tinf = np.asarray(res['env_series']['T_inf'], dtype=float)

# 阶段分界：环境温度首次进入平台 0.5 K 以内（实算，非人为设定）
T_plateau = float(Tinf.max())
hit = np.where(Tinf >= T_plateau - 0.5)[0]
t_split = float(t[hit[0]]) if hit.size else float(t[-1])

fig, ax = plt.subplots(figsize=(6.2, 3.6), layout='constrained')
ax2 = ax.twinx()

# 阶段底色：只做分区提示，不承载数值
ax.axvspan(t[0], t_split, color=PALETTE[0], alpha=0.06, lw=0, zorder=0)

ax.plot(t, Tinf, '-', color=COLORS['ref_line'], lw=1.0, zorder=2,
        label='环境 $T_\\infty$')
ax.plot(t, Ts, '-', color=PALETTE[1], lw=1.8, zorder=4, label='表面 $T$')
ax.plot(t, Tc, '-', color=PALETTE[0], lw=1.8, zorder=4, label='中心 $T$')
ax2.plot(t, Cs, '--', color=PALETTE[3], lw=1.7, zorder=3, label='表面 $C$')
ax2.plot(t, Cc, '--', color=PALETTE[2], lw=1.7, zorder=3, label='中心 $C$')

ax.axvline(t_split, color=COLORS['highlight'], lw=1.1, ls='-.', zorder=5)
ax.annotate(f'恒温段起点 {t_split:.2f} h', xy=(t_split, Tc.min()),
            xytext=(6, 2), textcoords='offset points', fontsize=FS,
            color=COLORS['highlight'], ha='left', va='bottom')

ax.set_xlabel('时间 $t$ (h)')
ax.set_ylabel('温度 $T$ (°C)')
ax2.set_ylabel('水分浓度 $C$ (kg/kg)')
ax.set_xlim(t[0], t[-1])
ax.set_ylim(Tc.min() - 1.2, T_plateau + 3.4)
ax2.set_ylim(Cs.min() - 0.10, Cc.max() + 0.42)

# 3 h 终点读数：曲线自左上降来，故读数放到终点下方的空白区
ax2.annotate(f'{Cc[-1]:.3f}', xy=(t[-1], Cc[-1]), xytext=(-3, -7),
             textcoords='offset points', fontsize=FS, ha='right',
             va='top', color=PALETTE[2])
ax2.annotate(f'{Cs[-1]:.3f}', xy=(t[-1], Cs[-1]), xytext=(-3, 6),
             textcoords='offset points', fontsize=FS, ha='right',
             va='bottom', color=PALETTE[3])

declutter_axes(ax, grid='auto', grid_axis='y')
ax2.spines['top'].set_visible(False)

h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, ncol=1, fontsize=FS, frameon=False,
          labelspacing=0.3, handlelength=1.7)
# 双轴 + 5 条线，按实际净空定位；放不下时由 helper 迁到外侧专用带
auto_legend(ax)

set_paper_placement(fig, 0.90)
save_fig(fig, out('fig_q2_stage_transition.png'))
