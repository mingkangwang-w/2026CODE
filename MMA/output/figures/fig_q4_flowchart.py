# -*- coding: utf-8 -*-
"""问题四求解流程（横向，左→右 + 上下分支），版式与 fig_q1/q2/q3_flowchart.py 一致。

问题四比前三问多一层结构，故在主链上下各挂一个分支节点：

    · 上分支「半径输入」——附件 2 的 R(t) 是问题四独有的第三个输入源，
      单独提出来，其输出向下汇入「物质坐标变换」；
    · 下分支「坐标变换依据」——说明物质坐标形式是由守恒律直接导出的，
      坐标运动项与固相对流项精确相消，故方程不含 dR/dt 项。
      这是问题四最容易写错的地方（对固定介质方程做 Landau 变换会多出一项
      伪对流），单独标出以免被当成普通近似。

形状约定
    梯形  = 输入 / 输出（两侧开口，梯形朝向流程方向）
    长方形 = 算法处理步骤
    菱形  = 判断（含回边）

输出：fig_q4_flowchart.svg / .png
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
Y0, Y1 = 0.0, 48.0
FIG_W = 10.5                 # 与前三张一致：画幅压窄 → 同样的字号在图中占比更大
CY, HH = 25.0, 14.0          # 主链行中心与高度
DHH = 16.0                   # 菱形高度
UY, UH = 41.0, 12.0          # 上分支节点
LY, LH = 9.0, 12.0           # 下分支节点
SLOPE = 0.62                 # 梯形斜边的收口比

MAIN = [                     # (中心 x, 宽度, 形状)
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


def arrow(ax, p, q, lw=1.5, ms=13):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=ms,
                                 linewidth=lw, color=RULE, zorder=1,
                                 shrinkA=0, shrinkB=0, capstyle='butt'))


def main():
    fig = plt.figure(figsize=(FIG_W, FIG_W * (Y1 - Y0) / (X1 - X0)))
    fig.patch.set_facecolor('white')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ax.axis('off')

    # ------------------------------------------------ 主链
    MAIN_NODES = [
        ('输入条件', ['附录 4 变物性', '$D(C,T)$ 含 Arrhenius 项',
                  '附件 1 环境插值']),
        ('物质坐标变换', ['令 $\\eta=r/R(t)$', '扩散 $\\times1/R^2$、表面 $\\times1/R$',
                    '动域 $\\to$ 定域 $\\eta\\in[0,1]$']),
        ('时间推进', ['向后 Euler + Picard', '每步取 $R(t^{n+1})$',
                  '解 $T$ → 更新 $D$ → 解 $C$']),
        ('$C_{\\max}<0.15$？', ['逐时刻检查 $C_{\\max}$', '首达时线性插值细化']),
        ('输出结果', ['result4.xlsx、表 6', '$t^*=51.04$ h（2.13 天）']),
    ]
    for (cx, w, kind), (title, lines) in zip(MAIN, MAIN_NODES):
        shape(ax, cx, CY, w, DHH if kind == 'dec' else HH, kind)
        block(ax, cx, CY, title, lines)
    for k in range(len(MAIN) - 1):
        (xa, wa, _), (xb, wb, _) = MAIN[k], MAIN[k + 1]
        arrow(ax, (xa + wa / 2, CY), (xb - wb / 2, CY))

    # ------------------------------------------------ 上分支：半径输入
    ux = MAIN[1][0]
    shape(ax, ux, UY, 23.0, UH, 'proc')
    block(ax, ux, UY, '半径输入',
          ['附件 2 实测 $R(t)$', '段内线性、段外保持端点',
           '$R_0=2$ cm → $R(t^*)=1.2$ cm'])
    arrow(ax, (ux, UY - UH / 2), (ux, CY + HH / 2))

    # ------------------------------------------------ 下分支：坐标变换依据
    dx = MAIN[1][0]
    shape(ax, dx, LY, 23.0, LH, 'proc')
    block(ax, dx, LY, '坐标变换依据',
          ['由守恒律直接导出', '运动项与对流项精确相消', '故方程不含 $\\dot R$ 项'])
    # 注解性连接：细线、不带箭头，区别于流程箭头
    ax.plot([dx, dx], [CY - HH / 2, LY + LH / 2], color=RULE, lw=0.9,
            zorder=1, solid_capstyle='butt')

    # ------------------------------------------------ 回边（外层时间循环）
    xd, xt = MAIN[3][0], MAIN[2][0]
    yb = 7.0
    ax.plot([xd, xd], [CY - DHH / 2, yb], color=RULE, lw=1.5, zorder=1,
            solid_capstyle='butt')
    ax.plot([xd, xt], [yb, yb], color=RULE, lw=1.5, zorder=1,
            solid_capstyle='butt')
    arrow(ax, (xt, yb), (xt, CY - HH / 2))

    # 「是」「否」分支标注
    xo = MAIN[4][0] - MAIN[4][1] / 2
    ax.text((xd + MAIN[3][1] / 2 + xo) / 2, CY + 1.1, '是', ha='center',
            va='bottom', fontsize=LFS, color=INK2, zorder=3)
    ax.text(xd + 1.6, yb + 1.7, '否', ha='left', va='center', fontsize=LFS,
            color=INK2, zorder=3)

    fig.savefig('fig_q4_flowchart.svg', facecolor='white')
    fig.savefig('fig_q4_flowchart.png', dpi=300, facecolor='white')
    plt.close(fig)
    print('saved: fig_q4_flowchart.svg / .png')


if __name__ == '__main__':
    main()
