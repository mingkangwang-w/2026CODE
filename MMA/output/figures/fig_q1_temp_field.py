# -*- coding: utf-8 -*-
"""问题一 温度时空场云图（格式照搬 MODEXPI 的 gen_fig_q1_temp_field.py）。

本图讲什么：预热段温度场 T(r,t) 在 r-t 平面上的全貌。等值线近似平行于 t 轴说明
径向温差很小，热扩散时间尺度与预热时长同量级，故温度场基本随环境同步抬升。

图元：contourf 填充 + 深灰等值线叠加（标注温度值）+ 末时刻中心/表面读数
      + 色条（单位 °C）。
数据来源：../../data/result1.xlsx（由 solve_p1.py 写出，1800 个时刻 × 21 个半径节点）。

输出：fig_q1_temp_field.png（350 dpi）/ .svg
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
    r, t, Z = load_result1('温度')
    RR, TT = np.meshgrid(r, t)

    fig, ax = plt.subplots(figsize=(6.0, 3.7), layout='constrained')

    levels = np.linspace(float(Z.min()), float(Z.max()), 22)
    cf = ax.contourf(RR, TT, Z, levels=levels, cmap='YlOrRd', extend='neither')
    # 等值线叠加：给读者可读的定量骨架
    cl_levels = np.arange(np.ceil(Z.min()), np.floor(Z.max()) + 0.1, 1.0)
    cs = ax.contour(RR, TT, Z, levels=cl_levels, colors=[C_TEXT],
                    linewidths=0.5, alpha=0.55)
    ax.clabel(cs, cs.levels[::2], inline=True, fontsize=8, fmt='%.0f')

    ax.set_xlabel('半径 $r$ (cm)')
    ax.set_ylabel('时间 $t$ (s)')
    ax.set_xlim(r[0], r[-1])
    ax.set_ylim(t[0], t[-1])

    cb = fig.colorbar(cf, ax=ax, pad=0.02, aspect=24)
    cb.set_label('温度 $T$ (°C)')
    cb.outline.set_linewidth(0.4)
    cb.outline.set_edgecolor(C_GRID)

    # 末时刻中心/表面读数：给两端点名 + 数值，机理留正文
    ax.annotate(f'{Z[-1, -1]:.2f}', xy=(r[-1], t[-1]), xytext=(-4, -13),
                textcoords='offset points', fontsize=FS, ha='right', va='top',
                color=C_TEXT)
    ax.annotate(f'{Z[-1, 0]:.2f}', xy=(r[0], t[-1]), xytext=(4, -13),
                textcoords='offset points', fontsize=FS, ha='left', va='top',
                color=C_TEXT)

    base = os.path.join(HERE, 'fig_q1_temp_field')
    fig.savefig(base + '.png')
    fig.savefig(base + '.svg')
    plt.close(fig)
    print('saved: fig_q1_temp_field.png / .svg')
    print(f'  T 范围 [{Z.min():.4f}, {Z.max():.4f}] °C,  '
          f'{Z.shape[0]} 时刻 x {Z.shape[1]} 半径节点')
    print(f'  1800 s 中心 {Z[-1, 0]:.4f} °C, 表面 {Z[-1, -1]:.4f} °C')


if __name__ == '__main__':
    main()
