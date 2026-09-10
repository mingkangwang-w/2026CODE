# -*- coding: utf-8 -*-
"""
图A  毕渥数演化：传质由外部对流控制向内部扩散控制的转变

物理含义
    热毕渥数  Bi_h = h  * R / k(C)      —— 外部对流换热 与 内部导热 之比
    质毕渥数  Bi_m = h_m * R / D(C,T)   —— 外部对流传质 与 内部扩散 之比
Bi << 1 时内部阻力可忽略（温度/水分近似均匀）；Bi >> 1 时内部阻力主导，
药材内部出现显著梯度。由于 D 随含水率下降而急剧减小，Bi_m 在干燥过程中
上升一个量级以上，这正是干燥速率进入"降速段"的物理根源。
"""
import numpy as np
import matplotlib.pyplot as plt

from _style import (setup_style, save_fig, panel_label, npz,
                    PALETTE, DEFAULT_COLORS)
import common

setup_style()
print('[图A] 毕渥数演化')

# ---------------- 数据 ----------------
d = npz('_p3')
t = d['t']                      # s
C = d['C']                      # (nt, 21)
T = d['T']                      # (nt, 21)
C_surf = d['C_surf']
T_end = float(d['T_end'])
r = d['r']
th = t / 3600.0

rho_f, cp_f, k_f, D_f = common.props(3)
R0 = common.R0
h = common.h_conv
hm = common.hm

# 表面与中心的物性
T_surf = T[:, -1]
k_surf = k_f(C_surf)
D_surf = D_f(C_surf, T_surf)
D_cent = D_f(C[:, 0], T[:, 0])

Bi_h = h * R0 / k_surf
Bi_m = hm * R0 / D_surf

# 关键时刻
i0 = 0
i_end = len(t) - 1
# Bi_m 越过 1 与越过 10 的时刻
def cross_time(y, level):
    idx = np.where(y >= level)[0]
    return th[idx[0]] if len(idx) else np.nan

t_bi1 = cross_time(Bi_m, 1.0)
t_bi10 = cross_time(Bi_m, 10.0)

print(f'  Bi_h: {Bi_h[0]:.3f} -> {Bi_h[-1]:.3f}')
print(f'  Bi_m: {Bi_m[0]:.3f} -> {Bi_m[-1]:.3f}  (增大 {Bi_m[-1]/Bi_m[0]:.1f} 倍)')
print(f'  Bi_m 越过 1 : {t_bi1:.2f} h ; 越过 10 : {t_bi10:.2f} h')

# ---------------- 绘图 ----------------
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.2))

# (a) 毕渥数
ax = axes[0]
ax.semilogy(th, Bi_m, color=PALETTE['red_main'], lw=1.9,
            label=r'质毕渥数 $Bi_m = h_m R/D$')
ax.semilogy(th, Bi_h, color=PALETTE['blue_main'], lw=1.9,
            label=r'热毕渥数 $Bi_h = hR/k$')
ax.axhline(1.0, color=PALETTE['neutral_dark'], ls='--', lw=1.1)
ax.text(th[-1] * 0.98, 1.12, r'$Bi=1$', fontsize=8, ha='right',
        color=PALETTE['neutral_dark'])

# 控制机制分区底色
ax.axhspan(ax.get_ylim()[0], 1.0, color=PALETTE['blue_light'], alpha=0.18, zorder=0)
ax.text(2, 0.45, '外部对流控制', fontsize=8, color=PALETTE['blue_main'])
ax.text(2, 12, '内部扩散控制', fontsize=8, color=PALETTE['red_main'])

if np.isfinite(t_bi1):
    ax.axvline(t_bi1, color=PALETTE['neutral_mid'], ls=':', lw=1.2)
    ax.annotate(f'机制转变\n{t_bi1:.1f} h', xy=(t_bi1, 1.0),
                xytext=(t_bi1 + 6, 0.25), fontsize=8,
                arrowprops=dict(arrowstyle='->', lw=0.9,
                                color=PALETTE['neutral_dark']))

ax.set_xlabel('时间 / h')
ax.set_ylabel('毕渥数')
ax.set_xlim(0, T_end / 3600.0)
ax.legend(fontsize=8, loc='lower right')
panel_label(ax, 'a')

# (b) 扩散系数与导热系数的量级变化
ax = axes[1]
ax.semilogy(th, D_surf * 1e9, color=PALETTE['red_main'], lw=1.8,
            label='表面 $D$')
ax.semilogy(th, D_cent * 1e9, color=PALETTE['orange'], lw=1.8, ls='--',
            label='中心 $D$')
ax.set_xlabel('时间 / h')
ax.set_ylabel(r'水分扩散系数 $D$ / ($10^{-9}$ m$^2\cdot$s$^{-1}$)')
ax.set_xlim(0, T_end / 3600.0)
ax.legend(fontsize=8, loc='upper right')

ax2 = ax.twinx()
ax2.plot(th, k_surf, color=PALETTE['blue_main'], lw=1.6, alpha=0.85)
ax2.set_ylabel(r'导热系数 $k$ / (W$\cdot$m$^{-1}\cdot$K$^{-1}$)',
               color=PALETTE['blue_main'])
ax2.tick_params(axis='y', colors=PALETTE['blue_main'])
ax2.spines['right'].set_visible(True)
ax2.spines['right'].set_color(PALETTE['blue_main'])
ax2.spines['top'].set_visible(False)
ax.text(0.50, 0.10, '$k$（右轴）', transform=ax.transAxes, fontsize=8,
        color=PALETTE['blue_main'])
panel_label(ax, 'b')

fig.suptitle('图A  干燥过程中毕渥数与输运物性的演化', y=1.03)
fig.tight_layout()
save_fig(fig, 'figA_biot')
