# -*- coding: utf-8 -*-
"""绘图共享样式（nature-figure 风格 + SimSun 中文字体）。"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors

FIGDIR = '/home/user/workspace/latex-template/texfile/figures'

PALETTE = {
    "blue_main": "#0F4D92", "blue_secondary": "#3775BA", "blue_light": "#A9C4E8",
    "red_main": "#B64342", "red_light": "#E9A6A1",
    "green": "#3B8E5E", "teal": "#42949E", "violet": "#9A4D8E",
    "orange": "#E28E2C", "gold": "#C9A227",
    "neutral_dark": "#4D4D4D", "neutral_mid": "#767676", "neutral_light": "#CFCECE",
}
DEFAULT_COLORS = [PALETTE["blue_main"], PALETTE["red_main"], PALETTE["green"],
                  PALETTE["teal"], PALETTE["violet"], PALETTE["orange"],
                  PALETTE["gold"], PALETTE["blue_secondary"]]


def setup_style(font_size=9.5, use_tex=False):
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['SimSun', 'Noto Sans CJK SC', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['svg.fonttype'] = 'none'
    plt.rcParams['pdf.fonttype'] = 42
    plt.rcParams['mathtext.fontset'] = 'cm'   # 数学符号用 Computer Modern，避免缺字形
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
    if use_tex:
        plt.rcParams['text.usetex'] = True


def save_fig(fig, name):
    os.makedirs(FIGDIR, exist_ok=True)
    base = os.path.join(FIGDIR, name)
    fig.savefig(base + '.pdf', bbox_inches='tight')
    fig.savefig(base + '.png', dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('saved', name)


def panel_label(ax, label, x=-0.14, y=1.04, fontsize=11, fontweight='bold'):
    ax.text(x, y, label, transform=ax.transAxes, fontsize=fontsize,
            fontweight=fontweight, ha='left', va='bottom', color='black')


def time_colors(n, cmap_name='viridis', vmin=0.0, vmax=1.0):
    cmap = plt.get_cmap(cmap_name)
    return [cmap(vmin + (vmax - vmin) * i / max(n - 1, 1)) for i in range(n)]
