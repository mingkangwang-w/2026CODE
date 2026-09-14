# -*- coding: utf-8 -*-
"""
示意图：斜置圆柱形药材的透视框架图（纯线条，无填充/明暗）。

表达内容
    · 圆柱轮廓：远端的后半椭圆弧、上下两条母线、近端截面椭圆的整圈
    · 不可见轮廓：远端圆周朝向柱身的一半被柱体挡住，按制图习惯画成虚线
    · 半径 2 cm：在柱身上沿 e_v 方向标注（该方向无透视压缩，长度即真实 R）
    · 长度 25 cm：在柱身下方平行于轴线标注（示意，不按比例）
    · 表面对流：橙色箭头 = 温度对流（空气向药材供热，箭头指向柱面）
                蓝色箭头 = 水分对流（表面向空气蒸发，箭头背离柱面）
    · 内部传质：截面椭圆内自轴心向外的径向箭头 = 水分扩散

关于投影
    取正交投影：柱轴单位向量 e_u = (cos b, sin b)，截面内与之垂直的
    单位向量 e_v = (-sin b, cos b)。视线绕竖直轴偏转 psi（sin psi = CAP_K）后
        · 截面正圆 → 椭圆：沿 e_u 半轴 R·CAP_K，沿 e_v 半轴 R（不压缩）
        · 柱身轮廓 = 轴线沿 e_v 偏移 ±R 的两条平行线
        · 截面内径向方向 → (R·CAP_K·sin t)·e_u + (R·cos t)·e_v
        · 截面圆周参数 t 中，sin t > 0 的一半朝向柱身，sin t < 0 的一半背离柱身
    故半径尺寸必须画在 e_v 方向；长度尺寸沿 e_u，是投影长度（本就示意）。

输出：fig_herb_cylinder.svg / .png
"""
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

CJK_FONT = 'SimSun'
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': [CJK_FONT, 'Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'mathtext.fontset': 'cm',
    'svg.fonttype': 'none',      # 文字保留为 <text> 节点，可在 AI/Inkscape 里编辑
    'font.size': 10,
})

# ---------------------------------------------------------------- 画布与几何
X0, X1 = 0.0, 100.0
Y0, Y1 = 4.5, 46.0

BETA = np.radians(13.541)            # 柱轴倾角
E_U = np.array([np.cos(BETA), np.sin(BETA)])        # 沿轴方向
E_V = np.array([-np.sin(BETA), np.cos(BETA)])       # 垂直轴方向（无透视压缩）

RAD = 5.8                            # 半径（绘图单位，代表 2 cm）
CAP_K = 0.42                         # 横向压缩比
CAP_A = RAD * CAP_K                  # 截面椭圆沿 e_u 的半轴
AX_LEN = 40.0                        # 柱长（示意，不代表 25 cm 的真实比例）
P_FAR = np.array([24.0, 18.5])       # 远端轴心
P_NEAR = P_FAR + AX_LEN * E_U        # 近端轴心（截面中心）
AX_V = P_NEAR - P_FAR

# 表面对流箭头：沿轴的位置比例
HEAT_T = (0.14, 0.28, 0.42)          # 温度对流（左半段）
WATR_T = (0.54, 0.68, 0.82)          # 水分对流（右半段）
LAB_HEAT_T, LAB_WATR_T = 0.28, 0.68  # 文字标注所对的轴向位置

# ---------------------------------------------------------------- 配色
LINE = '#1f1f1f'            # 圆柱轮廓线
INK, INK2, INK3 = '#1a1a1a', '#4d4d4d', '#7d766c'
ORANGE = '#d9531e'          # 温度
BLUE = '#1c63c4'            # 水分
AXIS_C = '#9a8b78'


def pt_surf(t, off=0.0):
    """柱面（上母线）上轴向位置比例为 t 的点，再沿 e_v 外移 off。"""
    return P_FAR + t * AX_V + (RAD + off) * E_V


def arrow(ax, p, q, color, lw=1.6, ms=12, z=7, style='-|>'):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms,
                                 linewidth=lw, color=color, zorder=z,
                                 shrinkA=0, shrinkB=0, capstyle='butt'))


def main():
    fig = plt.figure(figsize=(10.4, 10.4 * (Y1 - Y0) / (X1 - X0)))
    fig.patch.set_facecolor('white')
    ax = fig.add_axes([0, 0, 1, 1])          # 坐标铺满画布 → 两方向等比例
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y0, Y1)
    ax.axis('off')

    # ================================================== 1. 柱体轮廓
    # 椭圆参数式 cen + CAP_A·sin(t)·e_u + RAD·cos(t)·e_v：
    #   t=0 为上母线切点，t=180 为下母线切点，t=90 为朝近端一侧的极值点。
    def cap_arc(cen, t0, t1):
        tt = np.radians(np.linspace(t0, t1, 72))
        return (cen[None, :] + (CAP_A * np.sin(tt))[:, None] * E_U[None, :]
                + (RAD * np.cos(tt))[:, None] * E_V[None, :])

    # 远端圆周被柱体挡住的一半（sin t>0，朝向柱身）——不可见轮廓，虚线
    hid = cap_arc(P_FAR, 0, 180)
    ax.plot(hid[:, 0], hid[:, 1], color=LINE, lw=1.05,
            linestyle=(0, (4.5, 3.0)), zorder=2, dash_capstyle='butt')

    # 可见轮廓：远端背离柱身的一半 → 上母线 → 近端前半弧 → 下母线。
    # 末尾补回远端弧起点以画出下母线，整体不闭合，免得近端前半弧被描两遍。
    vis = np.vstack([cap_arc(P_FAR, 180, 360), cap_arc(P_NEAR, 0, 180),
                     cap_arc(P_FAR, 180, 181)])
    ax.plot(vis[:, 0], vis[:, 1], color=LINE, lw=1.4, zorder=3,
            solid_capstyle='round')

    # 近端截面的后半弧：截面是朝向视线的平面圆盘，整圈轮廓都可见
    back = cap_arc(P_NEAR, 180, 360)
    ax.plot(back[:, 0], back[:, 1], color=LINE, lw=1.4, zorder=4.5,
            solid_capstyle='round')

    # 轴线（点划线）
    ax.plot(*np.array([P_FAR - 0.13 * AX_V, P_NEAR + 0.08 * AX_V]).T,
            color=AXIS_C, lw=0.75, zorder=2, linestyle=(0, (7, 3, 1.5, 3)))

    # ================================================== 2. 内部水分扩散箭头
    for t in np.arange(0.0, 360.0, 45.0):
        th = np.radians(t)
        tip = (P_NEAR + 0.88 * CAP_A * np.sin(th) * E_U
               + 0.88 * RAD * np.cos(th) * E_V)
        ax.add_patch(FancyArrowPatch(
            tuple(P_NEAR), tuple(tip), arrowstyle='-|>', mutation_scale=9,
            linewidth=1.45, color=BLUE, zorder=5, shrinkA=3.5, shrinkB=0,
            capstyle='butt'))
    ax.plot([P_NEAR[0]], [P_NEAR[1]], marker='o', ms=3.6, mfc=LINE,
            mec=LINE, zorder=6)

    # ================================================== 3. 半径尺寸（沿 e_v，无压缩）
    r_mid = P_FAR + 0.50 * AX_V
    r_top = r_mid + RAD * E_V
    for p in (r_top, r_mid):
        ax.plot(*np.array([p + 2.6 * E_U, p - 2.2 * E_U]).T,
                color=INK3, lw=0.7, zorder=3)
    arrow(ax, tuple(r_mid + 0.5 * E_V), tuple(r_top - 0.5 * E_V), INK2,
          lw=1.0, ms=9, z=6, style='<|-|>')
    # 文字随柱轴倾斜：水平排版的文字放在斜柱里，末端必然横穿轴线
    ax.text(*(r_mid + 0.5 * RAD * E_V + 1.7 * E_U), '半径 $R$ = 2 cm',
            ha='left', va='center', fontsize=10.5, color=INK, zorder=7,
            rotation=np.degrees(BETA), rotation_mode='anchor')

    # ================================================== 4. 长度尺寸（沿 e_u，示意）
    d = 11.4
    dpa, dpb = P_FAR - d * E_V, P_NEAR - d * E_V
    for p in (P_FAR, P_NEAR):
        ax.plot(*np.array([p - (RAD + 0.7) * E_V, p - (d + 1.4) * E_V]).T,
                color=INK3, lw=0.7, zorder=3)
    arrow(ax, tuple(dpa + 1.3 * E_U), tuple(dpb - 1.3 * E_U), INK2,
          lw=1.0, ms=9, z=6, style='<|-|>')
    ax.text(*(0.5 * (dpa + dpb) - 3.0 * E_V), '长度 $L$ = 25 cm',
            ha='center', va='center', fontsize=10.5, color=INK, zorder=7,
            rotation=np.degrees(BETA), rotation_mode='anchor')

    # ================================================== 5. 表面对流
    # 温度：空气比药材热 → 箭头指向柱面；水分：表面比空气湿 → 箭头背离柱面
    for t in HEAT_T:
        arrow(ax, tuple(pt_surf(t, 5.3)), tuple(pt_surf(t, 0.55)), ORANGE)
    for t in WATR_T:
        arrow(ax, tuple(pt_surf(t, 0.55)), tuple(pt_surf(t, 5.3)), BLUE)

    ax.text(*pt_surf(LAB_HEAT_T, 8.9),
            r'$-k\left.\partial_r T\right|_{r=R}=h\,(T_\infty-T)$',
            ha='center', va='center', fontsize=10, color=INK2, zorder=7)
    ax.text(*pt_surf(LAB_HEAT_T, 13.4), '温度对流', ha='center', va='center',
            fontsize=10.5, fontweight='bold', color=ORANGE, zorder=7)

    ax.text(*pt_surf(LAB_WATR_T, 8.9),
            r'$-D\left.\partial_r C\right|_{r=R}=h_m\,(C-C_\infty)$',
            ha='center', va='center', fontsize=10, color=INK2, zorder=7)
    ax.text(*pt_surf(LAB_WATR_T, 13.4), '水分对流', ha='center', va='center',
            fontsize=10.5, fontweight='bold', color=BLUE, zorder=7)

    # ================================================== 6. 内部传质说明
    blk = np.array([72.5, 27.0])
    for k, (txt, fs, fw, col) in enumerate([
            ('横截面（内部）', 10.5, 'bold', INK),
            ('水分自轴心向表面扩散', 9.5, 'normal', INK2),
            (r'$\partial_t C=\frac{1}{r}\,\partial_r\!\left(r\,D(C,T)\,\partial_r C\right)$',
             9.5, 'normal', INK2),
            (r'轴心对称：$\partial_r C=0$', 9.5, 'normal', INK2)]):
        ax.text(blk[0], blk[1] + 6.45 - k * 4.3, txt, ha='left', va='center',
                fontsize=fs, fontweight=fw, color=col, zorder=7)

    # 引线：终点落在椭圆上（沿方向求交，避免手调偏移量）
    lead0 = blk + np.array([-1.9, -1.4])
    w = lead0 - P_NEAR
    w = w / np.hypot(*w)
    rr = 1.0 / np.hypot((w @ E_U) / CAP_A, (w @ E_V) / RAD)
    arrow(ax, tuple(lead0), tuple(P_NEAR + rr * w), INK3, lw=0.8, ms=8, z=2.8)

    # ================================================== 输出
    fig.savefig('fig_herb_cylinder.svg', facecolor='white')
    fig.savefig('fig_herb_cylinder.png', dpi=300, facecolor='white')
    plt.close(fig)
    print('saved: fig_herb_cylinder.svg / .png')


if __name__ == '__main__':
    main()
