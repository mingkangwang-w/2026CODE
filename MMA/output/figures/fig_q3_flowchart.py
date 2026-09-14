# -*- coding: utf-8 -*-
"""问题三求解流程（横向，左→右），版式与 fig_q1/q2_flowchart.py 一致。

问题三与问题二同一物性组、同一内核，唯一差别是终止条件：把固定的 3 h 换成
阈值判据 max_r C < 0.15。所以这里菱形判的就是这条判据，而不是时间终点——
这与 Q1/Q2 的菱形语义不同，是照实画。

判据取全域最大值而不是中心值或平均值：中心是最难干的位置，只有中心也降到
0.15 以下才算整体达标；首达时刻再做一次线性插值细化，避免 t* 落在 60 s
输出网格的整数倍上（problem_3.py 的 B-20 通道专门否证这一点）。

输出：fig_q3_flowchart.svg / .png
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['SimSun', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'mathtext.fontset': 'cm',
    'svg.fonttype': 'none',
})

# ---------------------------------------------------------------- 版式
X0, X1 = 0.0, 123.0
Y0, Y1 = 3.5, 29.0
FIG_W = 10.5                 # 与问题一/二一致：画幅压窄 → 同样的字号在图中占比更大
CY, HH = 18.0, 15.0          # 节点行中心与高度
DHH = 17.0                   # 菱形高度
SLOPE = 0.62                 # 梯形斜边的收口比

NODE = [                     # (中心 x, 宽度, 形状)
    (11.5, 21.0, 'in'),
    (35.5, 21.0, 'proc'),
    (59.5, 21.0, 'proc'),
    (85.5, 25.0, 'dec'),     # 菱形内接矩形只有半宽，比其它节点宽
    (111.5, 21.0, 'out'),
]

INK, INK2, RULE = '#000000', '#1c1c1c', '#b0aea7'
BOX_F, BOX_E = '#f7f6f3', '#8a8880'        # 处理
IO_F, IO_E = '#edf1f4', '#6f7d8c'          # 输入 / 输出
DEC_F, DEC_E = '#dceaf9', '#2a78d6'        # 判断

PT = FIG_W * 72.0 / (X1 - X0)              # 每个数据单位对应的点数
LFS, TFS = 9.5, 14.0                       # 正文 / 标题字号（pt）


def shape(ax, cx, cy, w, h, kind):
    if kind == 'dec':
        pts = [(cx, cy + h / 2), (cx + w / 2, cy),
               (cx, cy - h / 2), (cx - w / 2, cy)]
        ax.add_patch(Polygon(pts, closed=True, facecolor=DEC_F,
                             edgecolor=DEC_E, lw=1.3, zorder=2))
    elif kind == 'in':                     # 左高右低：条件收口汇入
        pts = [(cx - w / 2, cy + h / 2), (cx + w / 2, cy + h * SLOPE / 2),
               (cx + w / 2, cy - h * SLOPE / 2), (cx - w / 2, cy - h / 2)]
        ax.add_patch(Polygon(pts, closed=True, facecolor=IO_F,
                             edgecolor=IO_E, lw=1.3, zorder=2))
    elif kind == 'out':                    # 左低右高：结果展开输出
        pts = [(cx - w / 2, cy + h * SLOPE / 2), (cx + w / 2, cy + h / 2),
               (cx + w / 2, cy - h / 2), (cx - w / 2, cy - h * SLOPE / 2)]
        ax.add_patch(Polygon(pts, closed=True, facecolor=IO_F,
                             edgecolor=IO_E, lw=1.3, zorder=2))
    else:                                  # 长方形（直角）
        ax.add_patch(FancyBboxPatch(
            (cx - w / 2, cy - h / 2), w, h,
            boxstyle='square,pad=0.10',
            facecolor=BOX_F, edgecolor=BOX_E, lw=1.3, zorder=2))


def block(ax, cx, cy, title, lines):
    """标题 + 正文，整块在节点内垂直居中。

    标题与正文的行高都按各自字号换算成数据单位，字号一改版面自动跟着变，
    不会因为标题放大而挤到正文。
    """
    title_h = TFS * 1.35 / PT
    lead = LFS * 1.55 / PT
    used = title_h + len(lines) * lead
    y = cy + used / 2
    ax.text(cx, y, title, ha='center', va='top', fontsize=TFS,
            fontweight='bold', color=INK, zorder=3)
    y -= title_h
    for ln in lines:
        ax.text(cx, y, ln, ha='center', va='top', fontsize=LFS,
                color=INK2, zorder=3)
        y -= lead


def arrow(ax, p, q, lw=1.5):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=13,
                                 linewidth=lw, color=RULE, zorder=1,
                                 shrinkA=0, shrinkB=0, capstyle='butt'))


def main():
    fig = plt.figure(figsize=(FIG_W, FIG_W * (Y1 - Y0) / (X1 - X0)))
    fig.patch.set_facecolor('white')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ax.axis('off')

    NODES = [
        ('输入条件', ['附录 3 变物性', '$D(C,T)$ 含 Arrhenius 项',
                 '附件 1 环境插值']),
        ('空间离散', ['守恒型控制体积法', '表面 Robin 直接进入通量',
                  '$N=80$，$\\Delta r=0.25$ mm']),
        ('时间推进', ['向后 Euler，$\\Delta t=5$ s', '每步 Picard 迭代',
                  '解 $T$ → 更新 $D$ → 解 $C$']),
        ('$C_{\\max}<0.15$？', ['逐时刻检查 $C_{\\max}$', '首达时线性插值细化']),
        ('输出结果', ['result3.xlsx、表 5', '$t^*=57.27$ h（2.39 天）']),
    ]

    for (cx, w, kind), (title, lines) in zip(NODE, NODES):
        shape(ax, cx, CY, w, DHH if kind == 'dec' else HH, kind)
        block(ax, cx, CY, title, lines)

    for k in range(len(NODE) - 1):
        (xa, wa, _), (xb, wb, _) = NODE[k], NODE[k + 1]
        arrow(ax, (xa + wa / 2, CY), (xb - wb / 2, CY))

    # 「是」「否」分支标注（「是」落在菱形→输出框那段的箭头上方）
    xd, xt = NODE[3][0], NODE[2][0]
    xo = NODE[4][0] - NODE[4][1] / 2
    ax.text((xd + NODE[3][1] / 2 + xo) / 2, CY + 1.1, '是', ha='center',
            va='bottom', fontsize=LFS, color=INK2, zorder=3)
    ax.text(xd + 1.6, 7.2, '否', ha='left', va='center', fontsize=LFS,
            color=INK2, zorder=3)

    # 回边：菱形下顶点 → 下 → 左 → 回到「时间推进」底边
    yb = 5.5
    ax.plot([xd, xd], [CY - DHH / 2, yb], color=RULE, lw=1.5, zorder=1,
            solid_capstyle='butt')
    ax.plot([xd, xt], [yb, yb], color=RULE, lw=1.5, zorder=1,
            solid_capstyle='butt')
    arrow(ax, (xt, yb), (xt, CY - HH / 2))

    fig.savefig('fig_q3_flowchart.svg', facecolor='white')
    fig.savefig('fig_q3_flowchart.png', dpi=300, facecolor='white')
    plt.close(fig)
    print('saved: fig_q3_flowchart.svg / .png')


if __name__ == '__main__':
    main()
