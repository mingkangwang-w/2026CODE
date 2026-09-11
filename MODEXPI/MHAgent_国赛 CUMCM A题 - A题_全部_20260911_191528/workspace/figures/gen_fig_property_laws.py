"""附录 2/3/4 物性本构对照四面板图（basic#12）。

本图讲什么：三组物性（附录 2 常物性、附录 3、附录 4）的 rho、c_p、k、D 随含水率 C 的变化，
说明问题 1 用常物性、问题 2/3 用附录 3、问题 4 用附录 4，且 D 在判据 C=0.15 附近骤降。

面板：(a) rho(C)；(b) c_p(C)；(c) k(C)；(d) D(C) 对数纵轴（附录 3/4 在平台温度下取值）。
四个面板共用 C 轴与判据竖线 C=0.15，(d) 另标 C0=2.55。

数据来源：code/properties.py 的 APPENDIX2/3/4（其系数全部来自 PROBLEM_FACTS.json），
温度取 code/params.py 的 T_INF_PLATEAU_REF（附件 1 平台均温）。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'code'))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import (FS, save_fig, set_paper_placement, declutter_axes,
                      consolidate_shared_legends, log_pow_ticks,
                      PALETTE, COLORS, out)

import params as P
import properties as PR

GROUPS = [('附录 2', PR.APPENDIX2), ('附录 3', PR.APPENDIX3), ('附录 4', PR.APPENDIX4)]
T_REF = P.T_INF_PLATEAU_REF
C = np.linspace(P.C_TH * 0.5, P.C0, 400)

fig, axes = plt.subplots(2, 2, figsize=(5.6, 4.7), layout='constrained')

specs = [
    (axes[0, 0], 'rho', r'$\rho$ (kg/m$^3$)', False),
    (axes[0, 1], 'cp', r'$c_p$ (J/(kg·K))', False),
    (axes[1, 0], 'k', r'$k$ (W/(m·K))', False),
    (axes[1, 1], 'D', r'$D$ (m$^2$/s)', True),
]

for ax, key, ylab, logy in specs:
    for i, (name, grp) in enumerate(GROUPS):
        if key == 'D':
            y = grp.D(C, np.full_like(C, T_REF))
        else:
            y = getattr(grp, key)(C)
        y = np.broadcast_to(np.asarray(y, dtype=float), C.shape)
        ls = '--' if grp.is_constant() else '-'
        ax.plot(C, y, ls, color=PALETTE[i], lw=1.7, label=name)
    ax.axvline(P.C_TH, color=COLORS['ref_line'], lw=0.8, ls=':', zorder=1)
    ax.set_ylabel(ylab)
    if logy:
        ax.set_yscale('log')
        log_pow_ticks(ax, 'y')
    declutter_axes(ax, grid='auto', grid_axis='y')

for ax in (axes[1, 0], axes[1, 1]):
    ax.set_xlabel('含水率 $C$ (kg/kg)')
for ax in (axes[0, 0], axes[0, 1]):
    ax.tick_params(labelbottom=False)

axD = axes[1, 1]
D_th = float(PR.APPENDIX3.D(P.C_TH, T_REF))
D_c0 = float(PR.APPENDIX3.D(P.C0, T_REF))
axD.text(0.05, 0.93, f'{D_c0 / D_th:.0f}×', transform=axD.transAxes,
         fontsize=FS, ha='left', va='top', color=PALETTE[1])
axes[0, 1].annotate(f'$C$={P.C_TH}', xy=(P.C_TH, 0.96),
                    xycoords=('data', 'axes fraction'),
                    xytext=(8, 0), textcoords='offset points',
                    fontsize=FS, color=COLORS['text'], va='top')

for i, ax in enumerate(axes.flat):
    ax.set_title(f'({chr(97 + i)})', fontsize=FS, fontweight='bold', loc='left', pad=3)
    ax.set_xlim(C[0] - 0.05, C[-1] + 0.05)

consolidate_shared_legends(fig, list(axes.flat), where='top', ncol=3)
set_paper_placement(fig, 0.80)
save_fig(fig, out('fig_property_laws.png'))
