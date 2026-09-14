# -*- coding: utf-8 -*-
"""把 rf_tpe_surface_replica.png 的英文标注换成中文，其余像素逐位不变。

原图的生成脚本已不在仓库里（只剩 PNG），无法重新出图，故采用覆盖法：

    ① 在原图的像素数组上，把每处英文所在矩形直接填白（numpy 赋值，不经重采样）；
    ② 另起一张同尺寸、背景全透明的画布，只画中文标注；
    ③ 按 alpha 把中文图层合成到原图上。

这样文字区以外的像素与原图**逐位相同**——用 imshow + savefig 的写法会引入
半像素重采样，实测会改动 51 万个文字区外的像素。

各文字的矩形范围由连通域扫描原图得到。凡是与刻度数字共处一区的地方（x 轴标签与
刻度 "100"），把抹白区分成两块绕开数字，见下方注释。

输出：rf_tpe_surface_cn.png（原图 rf_tpe_surface_replica.png 不动）
"""
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

SRC = 'rf_tpe_surface_replica.png'
DST = 'rf_tpe_surface_cn.png'
DPI = 200                                  # 与源图同为 2460x2073 像素

# SimSun 与原图的衬线拉丁字形最接近；Latin 也用同一字体，保证同一条标注内一致
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['SimSun', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
})

# 需要抹白的矩形 (y0, y1, x0, x1)，坐标即像素
RECTS = [
    (16, 96, 300, 1742),        # 标题
    (206, 240, 228, 372),       # 图例第 1 行
    (252, 286, 228, 350),       # 图例第 2 行
    (1662, 1825, 412, 606),     # x 轴标签左段
    (1678, 1825, 606, 682),     # x 轴标签右段（上边界下移，绕开刻度 "100"）
    (1698, 1862, 1612, 1848),   # y 轴标签（上边界下移，绕开刻度 "15"）
    (1012, 1268, 2378, 2440),   # 色条标签
]

# 中文标注 (x, y, 文字, 字号, 水平对齐, 旋转)
LABELS = [
    (1020, 55, 'TPE 优化的随机森林代理模型：干燥时长 RMSE 三维曲面', 17.0, 'center', 0),
    (240, 222, 'TPE 试验点', 9.5, 'left', 0),
    (240, 269, 'TPE 最优点', 9.5, 'left', 0),
    (475, 1740, '决策树数量', 12.0, 'center', -25),
    (1725, 1762, '最大深度', 12.0, 'center', 20),
    (2412, 1140, '均方根误差（h）', 11.0, 'center', 90),
]


def main():
    src = plt.imread(SRC)
    H, W = src.shape[:2]
    rgb = src[..., :3].copy()

    # ---- ① 直接抹白（numpy 赋值，不经任何重采样）----
    for y0, y1, x0, x1 in RECTS:
        rgb[y0:y1, x0:x1] = 1.0

    # ---- ② 透明画布上只画中文 ----
    fig = plt.figure(figsize=(W / float(DPI), H / float(DPI)), dpi=DPI)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.patch.set_alpha(0.0)
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)                      # y 向下，与像素坐标一致
    ax.axis('off')
    for x, y, txt, fs, ha, rot in LABELS:
        ax.text(x, y, txt, fontsize=fs, ha=ha, va='center', rotation=rot,
                rotation_mode='anchor', color='black', zorder=5)
    fig.savefig('_overlay.png', transparent=True)
    plt.close(fig)

    # ---- ③ 按 alpha 合成 ----
    ov = plt.imread('_overlay.png')
    a = ov[..., 3:4] if ov.shape[2] == 4 else np.ones(ov.shape[:2] + (1,))
    out = rgb * (1.0 - a) + ov[..., :3] * a
    out = np.clip(out, 0.0, 1.0)
    if src.shape[2] == 4:
        out = np.dstack([out, np.ones((H, W, 1))])

    plt.imsave(DST, out)
    os.remove('_overlay.png')
    print('saved:', DST)


if __name__ == '__main__':
    main()
