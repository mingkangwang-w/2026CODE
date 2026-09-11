"""问题 2 质量守恒校验（basic#8：渐变填充面积图 + 端点标注）。

本图讲什么：把"累计表面失水通量 Q(t)"与"域内水分减少量 M(0)-M(t)"两条曲线画在
一起做守恒校验（HC-13）。守恒型有限体积离散下两者应逐点相等，实测相对残差
eps_M=2.34e-14，即达到双精度舍入量级——图上两条线完全重合，故用"差值"面板
把残差单独放大展示，否则读者只能看到一条线。

面板：(a) 累计失水通量与域内减少量（重合的两条线 + 渐变填充）；
      (b) 两者之差随时间的量级（对数轴，显示始终停在 1e-14 舍入量级）。
数据来源：figures/problem_2_results.json 的 mass_balance（times_s / M / Q，
各 10801 点）与 diagnostics.eps_M。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, load, save_fig, set_paper_placement, declutter_axes,
                      panel, auto_legend, log_pow_ticks, PALETTE, COLORS,
                      _lighten, out)

res = load('problem_2_results')
mb = res['mass_balance']
t = np.asarray(mb['times_s'], dtype=float) / 3600.0
M = np.asarray(mb['M'], dtype=float)
Q = np.asarray(mb['Q'], dtype=float)
drop = M[0] - M                      # 域内水分减少量
eps_M = float(res['diagnostics']['eps_M'])

fig, axes = plt.subplots(2, 1, figsize=(6.0, 4.2), layout='constrained',
                         sharex=True, gridspec_kw={'height_ratios': [1.5, 1.0]})

# ── (a) 两条守恒量 ──
ax = axes[0]
ax.fill_between(t, 0, drop, color=_lighten(PALETTE[0], 0.55), alpha=0.45,
                lw=0, zorder=2)
ax.plot(t, drop, '-', color=PALETTE[0], lw=2.2, zorder=3,
        label='域内减少量 $M(0)-M(t)$')
ax.plot(t, Q, '--', color=PALETTE[3], lw=1.4, zorder=4,
        label='累计表面通量 $Q(t)$')
ax.annotate(f'{Q[-1]:.4f}', xy=(t[-1], Q[-1]), xytext=(-4, -12),
            textcoords='offset points', fontsize=FS, ha='right', va='top',
            color=PALETTE[0])
ax.set_ylabel('累计失水量 (kg/kg)')
ax.set_ylim(0, max(drop.max(), Q.max()) * 1.18)
declutter_axes(ax, grid='auto', grid_axis='y')
panel(ax, '(a)')
auto_legend(ax, fontsize=FS)

# ── (b) 残差量级（对数轴） ──
ax = axes[1]
diff = np.abs(drop - Q)
scale = max(float(np.max(np.abs(drop))), 1e-30)
rel = diff / scale
pos = rel[rel > 0]
floor = 10 ** (np.floor(np.log10(pos.min())) - 0.5) if pos.size else 1e-18
plot_rel = np.where(rel > 0, rel, floor)
ax.plot(t, plot_rel, '-', color=PALETTE[1], lw=1.4, zorder=3)
ax.set_yscale('log')
log_pow_ticks(ax, axis='y')
ax.axhline(1e-12, color=COLORS['ref_line'], lw=0.8, ls=':', zorder=2,
           label='舍入量级 10$^{-12}$')
ax.set_xlabel('时间 $t$ (h)')
ax.set_ylabel('相对残差')
ax.set_xlim(t[0], t[-1])
declutter_axes(ax, grid='auto', grid_axis='y')
panel(ax, '(b)')
auto_legend(ax, fontsize=FS)

set_paper_placement(fig, 0.86)
save_fig(fig, out('fig_q2_flux_balance.png'))
