# -*- coding: utf-8 -*-
"""问题一 水分浓度时空场云图（格式照搬 MODEXPI 的 gen_fig_q1_moist_field.py）。

本图讲什么：预热段水分场 C(r,t) 的全貌。等值线全部挤在表面附近，说明失水只在
表层薄壳内发生；内部大片区域仍是初值色，即扩散尚未渗透进去。渗透深度用 C 相对
初值下降 1% 的位置定义（sqrt(D·t) 量级的直接可视化）。

图元：contourf 填充 + 等值线叠加 + 渗透深度前沿曲线（实测自场数据）
      + 前沿末端读数 + 色条（单位 kg/kg）。
数据来源：../../data/result1.xlsx（由 solve_p1.py 写出，1800 个时刻 × 21 个半径节点）。

输出：fig_q1_moist_field.png（350 dpi）/ .svg
"""
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
MMA = os.path.dirname(os.path.dirname(HERE))
XLSX = os.path.join(MMA, 'data', 'result1.xlsx')

# ---------------------------------------------------------------- 样式
# 与参考图一致：字号 11/12/10、sans-serif 中文、350 dpi、白底、无网格。
# 颜色取自参考 PNG 的像素采样（其调色板是按工作区名做种子随机生成的，
# 重新 import 会得到不同结果，所以这里直接固化实测值）。
FS = 10.0
C_TEXT = '#333333'          # 等值线与读数文字
C_FRONT = '#4BA15C'         # 渗透前沿曲线与标注
C_GRID = '#E0E0E0'          # 色条描边

plt.rcParams.update({
    'font.size': 11.0,
    'font.family': 'sans-serif',
    'font.sans-serif': ['SimSun', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'axes.labelsize': 12.0,
    'axes.titlesize': 13.0,
    'xtick.labelsize': 10.0,
    'ytick.labelsize': 10.0,
    'axes.linewidth': 0.8,
    'axes.unicode_minus': False,
    'savefig.dpi': 350.0,
    'svg.fonttype': 'none',
})


def load_result1(sheet):
    """读 result1.xlsx 的一个工作表 → (r_cm, t_s, Z)，Z 形状 (n_t, n_r)。"""
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    rows = list(wb[sheet].iter_rows(values_only=True))
    r = np.asarray(rows[0][1:], dtype=float)                 # cm
    body = np.asarray([row[1:] for row in rows[1:]], dtype=float)
    t = np.asarray([row[0] for row in rows[1:]], dtype=float)  # s
    return r, t, body


def main():
    r, t, Z = load_result1('水分浓度')
    C0 = float(Z[0].max())
    RR, TT = np.meshgrid(r, t)

    fig, ax = plt.subplots(figsize=(6.0, 3.7), layout='constrained')

    levels = np.linspace(float(Z.min()), C0, 22)
    cf = ax.contourf(RR, TT, Z, levels=levels, cmap='YlGnBu', extend='neither')
    cs = ax.contour(RR, TT, Z, levels=[1.6, 1.8, 2.0, 2.2, 2.4, 2.5],
                    colors=[C_TEXT], linewidths=0.5, alpha=0.55)
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
    ax.plot(front[ok], t[ok], '-', color=C_FRONT, lw=1.8, zorder=6)
    ax.annotate(f'渗透前沿 {front[ok][-1]:.2f} cm',
                xy=(front[ok][-1], t[ok][-1]), xytext=(-8, -16),
                textcoords='offset points', fontsize=FS, ha='right', va='top',
                color=C_FRONT,
                arrowprops=dict(arrowstyle='->', color=C_FRONT, lw=0.8))

    ax.set_xlabel('半径 $r$ (cm)')
    ax.set_ylabel('时间 $t$ (s)')
    ax.set_xlim(r[0], r[-1])
    ax.set_ylim(t[0], t[-1])

    cb = fig.colorbar(cf, ax=ax, pad=0.02, aspect=24)
    cb.set_label('水分浓度 $C$ (kg/kg)')
    cb.outline.set_linewidth(0.4)
    cb.outline.set_edgecolor(C_GRID)

    base = os.path.join(HERE, 'fig_q1_moist_field')
    fig.savefig(base + '.png')
    fig.savefig(base + '.svg')
    plt.close(fig)
    print(f'saved: fig_q1_moist_field.png / .svg')
    print(f'  C 范围 [{Z.min():.4f}, {Z.max():.4f}] kg/kg,  '
          f'{Z.shape[0]} 时刻 x {Z.shape[1]} 半径节点')
    print(f'  1800 s 渗透前沿 = {front[ok][-1]:.4f} cm')


if __name__ == '__main__':
    main()
