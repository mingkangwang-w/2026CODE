"""扩散系数 D(C,T) 三维地形（competition#6）。

本图讲什么：附录 3 的 D = 2.4e-3·exp(-0.45/C)·exp(-3850/T_K) 在 (C, T) 平面上的地形。
含水率一侧的分式指数使 D 在判据 C=0.15 附近坍塌数个量级，这是末期刚性（t* 达 57 h）的来源；
温度一侧的 Arrhenius 因子影响温和，故提温不能线性缩短工期。

图元：lg D 的三维曲面 + 底面等高线投影 + 判据 C=0.15 处的脊线 + 判据点/初值点标注。
数据来源：code/properties.py APPENDIX3（系数源自 PROBLEM_FACTS.json），
C 取 [C_TH/2, C0]，T 取 [T0_DEGC, 平台均温 + 5 K]。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), 'code'))

import numpy as np
import matplotlib.pyplot as plt

from _figbase import FS, save_fig, set_paper_placement, PALETTE, COLORS, out

import params as P
import properties as PR

GRP = PR.APPENDIX3
C = np.linspace(P.C_TH * 0.5, P.C0, 90)
T = np.linspace(P.T0_DEGC, P.T_INF_PLATEAU_REF + 5.0, 90)
CC, TT = np.meshgrid(C, T)
D = GRP.D(CC, TT)
Z = np.log10(D)

fig = plt.figure(figsize=(5.7, 4.3))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(CC, TT, Z, cmap='coolwarm', alpha=0.9, linewidth=0,
                       edgecolor='none', antialiased=True, rstride=2, cstride=2)
z_off = float(Z.min()) - 0.9
ax.contour(CC, TT, Z, zdir='z', offset=z_off, cmap='coolwarm', alpha=0.45,
           levels=12, linewidths=0.7)

# 判据 C=0.15 处的脊线：末期刚性发生在这条线上
Z_th = np.log10(GRP.D(np.full_like(T, P.C_TH), T))
ax.plot(np.full_like(T, P.C_TH), T, Z_th, color=COLORS['highlight'], lw=1.8,
        zorder=8)

T_ref = P.T_INF_PLATEAU_REF
z_lo = float(np.log10(GRP.D(P.C_TH, T_ref)))
z_hi = float(np.log10(GRP.D(P.C0, T_ref)))
ax.scatter([P.C_TH], [T_ref], [z_lo], s=34, color=COLORS['highlight'],
           edgecolor='white', linewidth=1.0, depthshade=False, zorder=10)
ax.scatter([P.C0], [T_ref], [z_hi], s=34, color=PALETTE[2],
           edgecolor='white', linewidth=1.0, depthshade=False, zorder=10)
ax.text(P.C_TH, T_ref, z_lo - 0.75, f'$C$={P.C_TH}', fontsize=FS,
        color=COLORS['highlight'], ha='center')
ax.text(P.C0, T_ref, z_hi + 0.55, f'$C_0$={P.C0}', fontsize=FS,
        color=PALETTE[2], ha='center')

ax.set_xlabel('含水率 $C$ (kg/kg)', labelpad=2)
ax.set_ylabel('温度 $T$ (°C)', labelpad=2)
ax.set_zlabel('$\\lg D$ (m$^2$/s)', labelpad=2)
ax.set_zlim(z_off, float(Z.max()) + 0.35)
ax.view_init(elev=24, azim=-131)
ax.tick_params(pad=1)

cb = fig.colorbar(surf, ax=ax, shrink=0.55, aspect=16, pad=0.02)
cb.set_label('$\\lg D$')
cb.outline.set_linewidth(0.4)

set_paper_placement(fig, 0.80)
save_fig(fig, out('fig_D_landscape.png'))
