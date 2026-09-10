# -*- coding: utf-8 -*-
"""
新增插图的共享样式与路径解析模块。

与 code/figstyle.py 的区别：
  1. 路径基于 __file__ 自动解析，不再硬编码 Linux 绝对路径；
  2. 图片保存到本目录（MMA/output/figures）；
  3. 中文字体按 Windows 环境优先选择 SimSun。
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ---------------- 路径解析 ----------------
HERE = os.path.dirname(os.path.abspath(__file__))          # MMA/output/figures
MMA = os.path.dirname(os.path.dirname(HERE))               # MMA
CODE_DIR = os.path.join(MMA, 'code')
DATA_DIR = os.path.join(MMA, 'data')

if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

import common                                              # noqa: E402
common.DATA = DATA_DIR                                     # 覆盖原硬编码路径


def npz(name):
    """加载 code/ 目录下缓存的求解结果（_p2 / _p3 / _p4）。"""
    return np.load(os.path.join(CODE_DIR, name + '.npz'))


# ---------------- 配色 ----------------
PALETTE = {
    'blue_main': '#0F4D92', 'blue_secondary': '#3775BA', 'blue_light': '#A9C4E8',
    'red_main': '#B64342', 'red_light': '#E9A6A1',
    'green': '#3B8E5E', 'teal': '#42949E', 'violet': '#9A4D8E',
    'orange': '#E28E2C', 'gold': '#C9A227',
    'neutral_dark': '#4D4D4D', 'neutral_mid': '#767676', 'neutral_light': '#CFCECE',
}
DEFAULT_COLORS = [PALETTE['blue_main'], PALETTE['red_main'], PALETTE['green'],
                  PALETTE['teal'], PALETTE['violet'], PALETTE['orange'],
                  PALETTE['gold'], PALETTE['blue_secondary']]


def setup_style(font_size=9.5):
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['SimSun', 'Microsoft YaHei', 'SimHei',
                                       'Noto Sans CJK SC', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['pdf.fonttype'] = 42
    plt.rcParams['svg.fonttype'] = 'none'
    plt.rcParams['mathtext.fontset'] = 'cm'
    plt.rcParams['font.size'] = font_size
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.linewidth'] = 0.9
    plt.rcParams['legend.frameon'] = False
    plt.rcParams['axes.titlesize'] = font_size + 0.5
    plt.rcParams['axes.labelsize'] = font_size
    plt.rcParams['xtick.labelsize'] = font_size - 1
    plt.rcParams['ytick.labelsize'] = font_size - 1
    plt.rcParams['lines.linewidth'] = 1.6
    plt.rcParams['lines.markersize'] = 3.5


def save_fig(fig, name):
    base = os.path.join(HERE, name)
    fig.savefig(base + '.pdf', bbox_inches='tight')
    fig.savefig(base + '.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('  已保存:', name + '.png / .pdf')


def panel_label(ax, label, x=-0.14, y=1.04, fontsize=11):
    ax.text(x, y, label, transform=ax.transAxes, fontsize=fontsize,
            fontweight='bold', ha='left', va='bottom', color='black')


def trapz(y, x, axis=-1):
    """兼容 NumPy 1.x / 2.x（np.trapz 在 NumPy 2.0 已移除）。"""
    fn = getattr(np, 'trapezoid', None) or np.trapz
    return fn(y, x=x, axis=axis)


def mean_moisture(C, r):
    """圆柱截面积加权平均含水率  Cbar = 2/R^2 * ∫ C r dr。"""
    num = trapz(C * r[None, :], r, axis=1)
    den = trapz(r, r)
    return num / den
