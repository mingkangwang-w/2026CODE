# -*- coding: utf-8 -*-
"""
图F  干燥前沿推进：定半径模型（问题3）与收缩模型（问题4）的对比

定义干燥前沿 r*(t) 为满足 C(r*,t) = 0.15 的径向位置：r > r* 的外层已达到
干燥要求，r < r* 的内芯仍未干透。前沿由表面出发向中心推进，r*(t) 到达 0
的时刻即为整根药材的干燥结束时间。

该图把"干燥需要多久"分解为"前沿推进有多快"，并直接对比尺寸收缩带来的影响：
收缩缩短了扩散路径，但同时减小了蒸发面积，两种效应的净结果由本图给出。
"""
import numpy as np
import matplotlib.pyplot as plt

from _style import setup_style, save_fig, panel_label, npz, PALETTE

setup_style()
print('[图F] 干燥前沿推进')

THRESH = 0.15


def front_position(C, r_nodes, R_of_t=None, C_surf=None):
    """
    逐时刻求 C = THRESH 的径向位置（cm）。
    C 沿 r 单调递减，故对 (C, r) 反向后用线性插值。
    返回 nan 表示表面尚未达到阈值（前沿未形成）。
    """
    nt = C.shape[0]
    out = np.full(nt, np.nan)
    for i in range(nt):
        valid = np.isfinite(C[i])
        rr = r_nodes[valid].astype(float)
        cc = C[i, valid].astype(float)
        if R_of_t is not None and C_surf is not None:
            rr = np.r_[rr, R_of_t[i]]
            cc = np.r_[cc, C_surf[i]]
        if len(rr) < 2:
            continue
        if cc[-1] > THRESH:          # 连表面都还没干到阈值
            continue
        if cc[0] <= THRESH:          # 中心也已达标，前沿到达轴心
            out[i] = 0.0
            continue
        out[i] = np.interp(THRESH, cc[::-1], rr[::-1])
    return out


# ---------------- 问题3：定半径 ----------------
d3 = npz('_p3')
t3, C3, r3 = d3['t'], d3['C'], d3['r']
C3s = d3['C_surf']
T_end3 = float(d3['T_end'])
r3_cm = r3 * 100.0
front3 = front_position(C3, r3_cm)
R3_cm = np.full_like(t3, 2.0)

# ---------------- 问题4：收缩 ----------------
d4 = npz('_p4')
t4, C4, r4 = d4['t'], d4['C'], d4['r']
C4s, R4 = d4['C_surf'], d4['R']
T_end4 = float(d4['T_end'])
r4_cm = r4 * 100.0
R4_cm = R4 * 100.0
front4 = front_position(C4, r4_cm, R_of_t=R4_cm, C_surf=C4s)

th3, th4 = t3 / 3600.0, t4 / 3600.0


def first_valid(th, f):
    idx = np.where(np.isfinite(f))[0]
    return th[idx[0]] if len(idx) else np.nan


print(f'  问题3 干燥时间 {T_end3/3600:.2f} h , 前沿形成于 {first_valid(th3, front3):.2f} h')
print(f'  问题4 干燥时间 {T_end4/3600:.2f} h , 前沿形成于 {first_valid(th4, front4):.2f} h')
print(f'  收缩使干燥时间缩短 {(T_end3-T_end4)/3600:.2f} h '
      f'({(T_end3-T_end4)/T_end3*100:.1f}%)')

# ---------------- 绘图 ----------------
fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.2))

# (a) 前沿位置
ax = axes[0]
ax.plot(th3, R3_cm, color=PALETTE['blue_light'], lw=1.3, ls='-')
ax.plot(th3, front3, color=PALETTE['blue_main'], lw=2.0, label='问题3：定半径')
ax.plot(th4, R4_cm, color=PALETTE['red_light'], lw=1.3, ls='-')
ax.plot(th4, front4, color=PALETTE['red_main'], lw=2.0, label='问题4：尺寸收缩')
ax.fill_between(th3, 0, np.nan_to_num(front3, nan=0.0),
                color=PALETTE['blue_main'], alpha=0.10)
ax.text(T_end3 / 3600 * 0.42, 0.42, '未干透内芯', fontsize=8,
        color=PALETTE['neutral_dark'])
ax.text(T_end3 / 3600 * 0.62, 1.72, '已干外层', fontsize=8,
        color=PALETTE['neutral_mid'])
ax.set_xlabel('时间 / h')
ax.set_ylabel(r'干燥前沿位置 $r^*$ / cm')
ax.set_xlim(0, max(T_end3, T_end4) / 3600 * 1.02)
ax.set_ylim(0, 2.1)
ax.legend(fontsize=7.5, loc='lower left')
ax.text(0.98, 0.96, '细线为药材半径', transform=ax.transAxes, fontsize=7.5,
        ha='right', va='top', color=PALETTE['neutral_mid'])
panel_label(ax, 'a')

# (b) 未干透芯部占截面的比例
ax = axes[1]
frac3 = np.nan_to_num(front3, nan=2.0) ** 2 / R3_cm ** 2 * 100
frac4 = np.nan_to_num(front4, nan=np.nan) ** 2 / R4_cm ** 2 * 100
frac4 = np.where(np.isfinite(front4), frac4, 100.0)
ax.plot(th3, frac3, color=PALETTE['blue_main'], lw=1.9, label='问题3')
ax.plot(th4, frac4, color=PALETTE['red_main'], lw=1.9, label='问题4')
ax.set_xlabel('时间 / h')
ax.set_ylabel('未达标芯部占截面积比例 / %')
ax.set_xlim(0, max(T_end3, T_end4) / 3600 * 1.02)
ax.set_ylim(0, 105)
ax.legend(fontsize=8)
panel_label(ax, 'b')

# (c) 中心含水率与干燥时间对比
ax = axes[2]
ax.plot(th3, C3[:, 0], color=PALETTE['blue_main'], lw=1.9, label='问题3：定半径')
ax.plot(th4, C4[:, 0], color=PALETTE['red_main'], lw=1.9, label='问题4：尺寸收缩')
ax.axhline(THRESH, color=PALETTE['neutral_dark'], ls='--', lw=1.1)
ax.axvline(T_end3 / 3600, color=PALETTE['blue_main'], ls=':', lw=1.3)
ax.axvline(T_end4 / 3600, color=PALETTE['red_main'], ls=':', lw=1.3)
ax.annotate('', xy=(T_end4 / 3600, 0.62), xytext=(T_end3 / 3600, 0.62),
            arrowprops=dict(arrowstyle='<->', lw=1.1,
                            color=PALETTE['neutral_dark']))
ax.text((T_end3 + T_end4) / 7200, 0.68,
        f'缩短 {(T_end3-T_end4)/3600:.1f} h', fontsize=8, ha='center',
        color=PALETTE['neutral_dark'])
ax.text(T_end3 / 3600 * 0.45, 0.20, '$C=0.15$', fontsize=8,
        color=PALETTE['neutral_dark'])
ax.set_xlabel('时间 / h')
ax.set_ylabel(r'中心水分浓度 / (kg$\cdot$kg$^{-1}$)')
ax.set_xlim(0, max(T_end3, T_end4) / 3600 * 1.02)
ax.set_ylim(0, 2.0)
ax.legend(fontsize=7.5)
panel_label(ax, 'c')

fig.suptitle('图F  干燥前沿推进与尺寸收缩的影响', y=1.03)
fig.tight_layout()
save_fig(fig, 'figF_drying_front')
