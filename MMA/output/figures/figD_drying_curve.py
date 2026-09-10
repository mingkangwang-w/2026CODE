# -*- coding: utf-8 -*-
"""
图D  干燥速率曲线与特性干燥曲线

(a) 干燥速率对时间作图：直观展示预热升速、短暂恒速、随后长时间降速的全过程。
(b) 干燥速率对平均含水率作图（干燥工程中的"特性干燥曲线"）：
    恒速段在该坐标下表现为一段近水平的平台，平台终止处即临界含水率 C_cr，
    它把干燥过程分成表面汽化控制的恒速段与内部扩散控制的降速段。
    该图比 rate–time 图更能揭示控制机制的切换，是干燥领域的标准表示方法。

平均含水率按圆柱截面积加权：Cbar(t) = 2/R^2 * ∫_0^R C(r,t) r dr
"""
import numpy as np
import matplotlib.pyplot as plt

from _style import (setup_style, save_fig, panel_label, npz, trapz,
                    mean_moisture, PALETTE)

setup_style()
print('[图D] 干燥速率与特性干燥曲线')

# ---------------- 数据 ----------------
d = npz('_p3')
t = d['t']
C = d['C']
r = d['r']
T_end = float(d['T_end'])
th = t / 3600.0

Cbar = mean_moisture(C, r)
rate = -np.gradient(Cbar, th)              # kg/(kg·h)

# 轻度平滑（去掉数值微分噪声），仅用于定位极值与绘图
def smooth(y, w=15):
    if len(y) < w:
        return y
    ker = np.ones(w) / w
    pad = np.r_[np.full(w // 2, y[0]), y, np.full(w // 2, y[-1])]
    return np.convolve(pad, ker, mode='valid')[:len(y)]

rate_s = smooth(rate)

i_peak = int(np.argmax(rate_s))
C_peak = Cbar[i_peak]
rate_peak = rate_s[i_peak]

# 临界含水率：速率降到峰值 95% 处（恒速平台结束）
after = np.where((np.arange(len(rate_s)) > i_peak) & (rate_s < 0.95 * rate_peak))[0]
i_cr = int(after[0]) if len(after) else i_peak
C_cr = Cbar[i_cr]

print(f'  初始平均含水率 {Cbar[0]:.4f} , 终点 {Cbar[-1]:.4f} kg/kg')
print(f'  最大干燥速率 {rate_peak:.4f} kg/(kg·h)  出现在 t={th[i_peak]:.2f} h, Cbar={C_peak:.3f}')
print(f'  临界含水率 C_cr = {C_cr:.4f} kg/kg  (t={th[i_cr]:.2f} h)')

# ---------------- 绘图 ----------------
fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2))

# (a) 速率-时间
ax = axes[0]
ax.plot(th, rate, color=PALETTE['blue_light'], lw=0.9, alpha=0.8)
ax.plot(th, rate_s, color=PALETTE['blue_main'], lw=1.9)
ax.axvline(th[i_cr], color=PALETTE['red_main'], ls=':', lw=1.3)
ax.annotate(f'临界点 {th[i_cr]:.1f} h', xy=(th[i_cr], rate_s[i_cr]),
            xytext=(th[i_cr] + 8, rate_peak * 0.72), fontsize=8,
            arrowprops=dict(arrowstyle='->', lw=0.9, color=PALETTE['red_main']))
ax.text(th[i_cr] * 0.35, rate_peak * 0.35, '升速与\n恒速段', fontsize=8,
        ha='center', color=PALETTE['neutral_dark'])
ax.text((th[i_cr] + th[-1]) / 2, rate_peak * 0.35, '降速段', fontsize=8,
        ha='center', color=PALETTE['neutral_dark'])
ax.set_xlabel('时间 / h')
ax.set_ylabel(r'干燥速率 $-\mathrm{d}\bar{C}/\mathrm{d}t$ / (kg$\cdot$kg$^{-1}\cdot$h$^{-1}$)')
ax.set_xlim(0, T_end / 3600.0)
ax.set_ylim(0, rate_peak * 1.15)
panel_label(ax, 'a')

# (b) 特性干燥曲线：速率-平均含水率（横轴反向，干燥沿箭头方向推进）
ax = axes[1]
ax.plot(Cbar, rate_s, color=PALETTE['green'], lw=1.9)
ax.plot(C_peak, rate_peak, 'o', ms=5, color=PALETTE['blue_main'])
ax.plot(C_cr, rate_s[i_cr], 's', ms=5.5, color=PALETTE['red_main'])
ax.annotate(f'临界含水率\n$C_{{cr}}={C_cr:.2f}$',
            xy=(C_cr, rate_s[i_cr]), xytext=(C_cr - 0.85, rate_peak * 0.55),
            fontsize=8, arrowprops=dict(arrowstyle='->', lw=0.9,
                                        color=PALETTE['red_main']))
ax.axvline(0.15, color=PALETTE['neutral_dark'], ls='--', lw=1.1)
ax.text(0.17, rate_peak * 0.9, '终点 $C=0.15$', fontsize=8,
        color=PALETTE['neutral_dark'])
ax.invert_xaxis()
ax.annotate('', xy=(0.05, rate_peak * 1.06), xytext=(Cbar[0] * 0.95, rate_peak * 1.06),
            arrowprops=dict(arrowstyle='->', lw=1.1, color=PALETTE['neutral_mid']))
ax.text(Cbar[0] * 0.55, rate_peak * 1.08, '干燥进行方向', fontsize=7.5,
        ha='center', color=PALETTE['neutral_mid'])
ax.set_xlabel(r'平均含水率 $\bar{C}$ / (kg$\cdot$kg$^{-1}$)')
ax.set_ylabel(r'干燥速率 / (kg$\cdot$kg$^{-1}\cdot$h$^{-1}$)')
ax.set_ylim(0, rate_peak * 1.15)
panel_label(ax, 'b')

fig.suptitle('图D  干燥速率曲线与特性干燥曲线', y=1.03)
fig.tight_layout()
save_fig(fig, 'figD_drying_curve')
