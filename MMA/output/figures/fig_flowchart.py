# -*- coding: utf-8 -*-
"""
A 题求解流程图（横向矩阵版）。

版式：最左为竖栏「模型与算法」；右侧为 4×5 矩阵——行是问题一至问题四，
      列是从左到右的解决步骤：① 输入设定 → ② 建模处理 → ③ 求解推进
      → ④ 终止判断 → ⑤ 结果交付。

形状约定（不同形状表示不同功能）：
    梯形 = 输入 / 输出（收口汇入、展开输出，短边为长边的 0.62）
    矩形 = 处理步骤
    菱形 = 判断（终止判据）

问题一沿用 MMA 的方案：节点型控制体积离散 + Crank–Nicolson 隐式时间推进。

输出：fig_flowchart.svg / .png
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

CJK = 'Microsoft YaHei'          # 想让图内文字与正文宋体一致就改成 'SimSun'
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': [CJK, 'SimSun', 'SimHei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'mathtext.fontset': 'cm',
    'svg.fonttype': 'none',
})

INK, INK2, RULE = '#0b0b0b', '#4d4d4d', '#8a8880'
NEUT_F, NEUT_E = '#f5f4f1', '#9c9a92'      # 处理：矩形
ACC_F, ACC_E = '#dceaf9', '#2a78d6'        # 输入/输出：梯形
DEC_F, DEC_E = '#ffffff', '#2a78d6'        # 判断：菱形（白底蓝框）
LEF_F, LEF_E = '#eef1f4', '#7c8b99'        # 左侧竖栏
ARROW_C = '#b9b7b0'

# ---------------------------------------------------------------- 版式几何
FIG_W, FIG_H = 14.0, 6.2
HEAD_Y, HEAD_H = 96.0, 5.0
ROW_H, RGAP = 17.0, 1.6
NSTEP = 5
LBOX_CX, LBOX_W = 10.0, 18.0
LBL_CX, LBL_W = 22.9, 7.2
SX0, SCELL_W, SGAP = 26.8, 13.0, 1.8
TAPER = 0.70                                # 梯形短边 / 长边
T_DX = 0.8                                  # 梯形内文字向高边（长边）偏移，避开斜角吃字

ROW0_TOP = HEAD_Y - HEAD_H / 2 - 2.0
row_top = [ROW0_TOP - i * (ROW_H + RGAP) for i in range(4)]
row_cy = [t - ROW_H / 2 for t in row_top]
step_cx = [SX0 + SCELL_W / 2 + i * (SCELL_W + SGAP) for i in range(NSTEP)]
LB_TOP = ROW0_TOP
LB_BOT = row_top[3] - ROW_H
Y_TOP, Y_BOT = HEAD_Y + HEAD_H / 2 + 2.0, LB_BOT - 2.0

# 行距按「磅」指定，再换算成数据单位——否则不同画幅下会挤在一起
PT_PER_UNIT = FIG_H * 72.0 / (Y_TOP - Y_BOT)
LFS = 7.0                      # 正文字号 pt
LEAD = LFS * 1.62 / PT_PER_UNIT    # 行距（数据单位）


def shape(ax, cx, cy, w, h, kind, face, edge, lw=1.25):
    """按功能画节点形状：in/out = 梯形，dec = 菱形，其它 = 直角矩形。"""
    if kind == 'dec':
        pts = [(cx, cy + h / 2), (cx + w / 2, cy),
               (cx, cy - h / 2), (cx - w / 2, cy)]
        ax.add_patch(Polygon(pts, closed=True, facecolor=face,
                             edgecolor=edge, lw=lw, zorder=2))
    elif kind == 'in':                     # 左高右低：输入收口汇入
        pts = [(cx - w / 2, cy + h / 2), (cx + w / 2, cy + h * TAPER / 2),
               (cx + w / 2, cy - h * TAPER / 2), (cx - w / 2, cy - h / 2)]
        ax.add_patch(Polygon(pts, closed=True, facecolor=face,
                             edgecolor=edge, lw=lw, zorder=2))
    elif kind == 'out':                    # 左低右高：结果展开输出
        pts = [(cx - w / 2, cy + h * TAPER / 2), (cx + w / 2, cy + h / 2),
               (cx + w / 2, cy - h / 2), (cx - w / 2, cy - h * TAPER / 2)]
        ax.add_patch(Polygon(pts, closed=True, facecolor=face,
                             edgecolor=edge, lw=lw, zorder=2))
    else:                                  # 矩形（直角）
        ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h,
                               facecolor=face, edgecolor=edge,
                               lw=lw, zorder=2))


def box(ax, cx, cy, w, h, title, lines=(), kind='proc', face=None, edge=None,
        tfs=9.4, lfs=LFS, vcenter=False, tcolor=None):
    """矩形框：标题加粗，正文逐行；空串产生一个半行间隙。vcenter 时整块垂直居中。"""
    if face is None or edge is None:
        face, edge = {'in': (ACC_F, ACC_E), 'out': (ACC_F, ACC_E),
                      'dec': (DEC_F, DEC_E)}.get(kind, (NEUT_F, NEUT_E))
    if tcolor is None:
        tcolor = ACC_E if kind in ('in', 'out') else INK
    shape(ax, cx, cy, w, h, kind, face, edge)
    if not lines:
        ax.text(cx, cy, title, ha='center', va='center', fontsize=tfs,
                fontweight='bold', color=tcolor, zorder=3, linespacing=1.4)
        return
    tx = cx - (T_DX if kind == 'in' else -T_DX if kind == 'out' else 0.0)
    used = 1.42 + sum(1.0 if ln else 0.45 for ln in lines)
    y = (cy + used * LEAD / 2) if vcenter else (cy + h / 2 - 2.3)
    ax.text(tx, y, title, ha='center', va='top', fontsize=tfs,
            fontweight='bold', color=tcolor, zorder=3)
    y -= 1.42 * LEAD
    for ln in lines:
        if ln:
            ax.text(tx, y, ln, ha='center', va='top', fontsize=lfs,
                    color=INK2, zorder=3)
        y -= LEAD * (0.45 if not ln else 1.0)


def arrow(ax, p, q, color=ARROW_C, lw=1.4):
    ax.add_patch(FancyArrowPatch(
        p, q, arrowstyle='-|>', mutation_scale=12, linewidth=lw,
        color=color, zorder=1, shrinkA=0, shrinkB=0))


fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 100)
ax.set_ylim(Y_BOT, Y_TOP)
ax.axis('off')
fig.patch.set_facecolor('white')

# ================================================================ 左侧竖栏（矩形）
box(ax, LBOX_CX, (LB_TOP + LB_BOT) / 2, LBOX_W, LB_TOP - LB_BOT,
    '模型与算法', [
        '控制方程',
        '$\\rho c_p\\,\\partial_t T=\\frac{1}{r}\\,\\partial_r(r\\,k\\,\\partial_r T)$',
        '$\\partial_t C=\\frac{1}{r}\\,\\partial_r(r\\,D\\,\\partial_r C)$',
        '',
        '边界条件',
        '中心对称：$\\partial_r T=\\partial_r C=0$',
        '表面 Robin：',
        '$-k\\,\\partial_r T=h\\,(T-T_\\infty)$',
        '$-D\\,\\partial_r C=h_m\\,(C-C_\\infty)$',
        '',
        '空间离散',
        '守恒型控制体积法',
        '中心节点用洛必达法则',
        '表面取半控制体，界面通量共享',
        '',
        '时间推进',
        '隐式格式，无条件稳定',
        '每步解一个三对角方程组',
        '双向耦合用不动点迭代',
    ], kind='proc', face=LEF_F, edge=LEF_E, tfs=9.8, vcenter=True)

# ================================================================ 列标题
HEADS = ['① 输入设定', '② 建模处理', '③ 求解推进', '④ 终止判断', '⑤ 结果交付']
for cx, text in zip(step_cx, HEADS):
    box(ax, cx, HEAD_Y, SCELL_W, HEAD_H, text, kind='proc',
        face=ACC_F, edge=ACC_E, tfs=7.6, tcolor=ACC_E)

# ================================================================ 四行
ROWS = [
    ('问题一', ['预热平衡阶段', '（0–1800 s）'], [
        ('in', '物性与网格参数', ['附录 2 常物性',
                            '$\\rho=820$、$c_p=2600$',
                            '$k=0.36$、$h=25$',
                            '$D=7\\times10^{-9}e^{-0.89/C}$']),
        ('proc', '空间离散：节点型控制体积', ['中心节点用洛必达',
                                   '$\\to$ 系数 $4\\Gamma/\\Delta r^2$',
                                   '表面半控制体，通量共享',
                                   '$N=400$、$\\Delta r=0.05$ mm']),
        ('proc', '时间推进格式', ['Crank–Nicolson 平均前后斜率',
                            '$\\to$ 二阶、无条件稳定',
                            '$D(C)$ 用不动点迭代（4 轮）']),
        ('dec', '到 1800 s？', ['每步解三对角方程组',
                              '$\\Delta t=0.5$ s 推进']),
        ('out', '求解 0–1800 s', ['得温度场与水分浓度场',
                             '输出 result1.xlsx',
                             '表 1 温度、表 2 水分浓度']),
    ]),
    ('问题二', ['整个烘干过程', '（0–3 h）'], [
        ('in', '物性升级为附录 3 变物性', ['$\\rho,c_p,k$ 随 $C$ 变化',
                                '$D$ 随 $C$ 与 $T$ 变化',
                                '（Arrhenius 指数项）']),
        ('proc', '环境边界分两段处理', ['预热段：附件 1 插值',
                              '恒温段：平台值延拓',
                              '$50.0$ °C，$0.050$ kg/kg']),
        ('proc', '双向强耦合求解', ['隐式推进 + Picard 迭代',
                            '每步先解 $T$',
                            '再用新 $T$ 更新 $D$ 解 $C$']),
        ('dec', '到 3 h？', ['逐步推进至 $t=10800$ s',
                          '覆盖整个烘干过程']),
        ('out', '求解 0–3 h', ['得全过程双场演化',
                           '输出 result2.xlsx',
                           '表 3 温度、表 4 水分浓度']),
    ]),
    ('问题三', ['确定烘干', '所需时间'], [
        ('in', '沿用问题二模型与物性', ['附录 3 变物性',
                              '方程与离散格式不变']),
        ('proc', '设定烘干合格判据', ['各处水分浓度 $C<0.15$',
                             '中心最难干，故判中心值',
                             '$\\Leftrightarrow\\max_r C<0.15$']),
        ('proc', '推进至判据首次满足', ['逐时刻检查全域最大值',
                              '首达时刻线性插值细化',
                              '不取网格点的整数倍']),
        ('dec', '$\\max_r C<0.15$？', ['首达即取为该步 $t^*$']),
        ('out', '$t^*=57.46$ h', ['约 2.39 天',
                             '输出 result3.xlsx、表 5',
                             '与题面“2–3 天”一致']),
    ]),
    ('问题四', ['尺寸收缩下的', '烘干时长'], [
        ('in', '物性切换为附录 4', ['$\\rho=760+90C$ 等',
                            '$D$ 整体更小',
                            '按附件 2 的 $R(t)$ 插值']),
        ('proc', '材料坐标变换', ['令 $\\eta=r/R(t)$',
                            '把动域映射为定域',
                            '扩散项 $\\times1/R^2$',
                            '不需伪对流项']),
        ('proc', '收缩域上隐式求解', ['同一套控制体积 + 隐式推进',
                            '坐标运动项与固相对流项相消']),
        ('dec', '$\\max_r C<0.15$？', ['全域首次低于阈值',
                                  '即取该步为 $t^*$']),
        ('out', '$t^*=51.09$ h', ['约 2.13 天',
                             '输出 result4.xlsx、表 6',
                             '收缩缩短扩散路径']),
    ]),
]

for i, (name, sub, steps) in enumerate(ROWS):
    cy = row_cy[i]
    box(ax, LBL_CX, cy, LBL_W, ROW_H, name, sub, kind='proc',
        face=NEUT_F, edge=NEUT_E, tfs=9.2, vcenter=True)
    arrow(ax, (LBOX_CX + LBOX_W / 2, cy), (LBL_CX - LBL_W / 2, cy))
    arrow(ax, (LBL_CX + LBL_W / 2, cy), (step_cx[0] - SCELL_W / 2, cy))
    for k, (kind, title, lines) in enumerate(steps):
        box(ax, step_cx[k], cy, SCELL_W, ROW_H, title, lines,
            kind=kind, tfs=8.0, vcenter=True)
        if k < NSTEP - 1:
            x0 = step_cx[k] + SCELL_W / 2
            arrow(ax, (x0, cy), (x0 + SGAP, cy))

fig.savefig('fig_flowchart.svg', bbox_inches='tight', facecolor='white')
fig.savefig('fig_flowchart.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close(fig)
print('saved: fig_flowchart.svg / .png')
