"""图脚本共用引导模块：路径注入、样式初始化、数据加载、面板标号。"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from _utils.plot_utils import (  # noqa: E402
    setup_style, save_fig, set_paper_placement, auto_legend,
    consolidate_shared_legends, dynamic_limits, declutter_axes,
    draw_vector_heatmap, uncertainty_band, smart_labels,
    PALETTE, PALETTE_LIGHT, COLORS, _lighten,
)

setup_style()

FIGDIR = _HERE
_SEARCH = [_HERE, os.path.join(_ROOT, 'output')]

# 全篇统一：标注/图例/面板标号都用刻度字号，避免同图多种手写字号（也不会低于印刷可读线）
FS = 10.0


def load(name):
    if not name.endswith('.json'):
        name += '.json'
    for d in _SEARCH:
        p = os.path.join(d, name)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
    raise FileNotFoundError(name)


def log_pow_ticks(ax, axis='y'):
    """对数轴指数刻度：绕开 matplotlib 的 \\mathdefault 包裹。

    SimHei 缺 U+2212，默认 LogFormatterSciNotation 生成的
    ``$\\mathdefault{10^{-9}}$`` 会把负号渲染成豆腐块；把 10 放到公式外、
    只让指数走 mathtext 即可正常显示。
    """
    import math
    from matplotlib.ticker import FuncFormatter

    def _fmt(v, _pos):
        if v <= 0:
            return ''
        e = math.log10(v)
        ei = int(round(e))
        if abs(e - ei) > 1e-6:
            return ''
        return '10$^{%d}$' % ei

    target = ax.yaxis if axis == 'y' else ax.xaxis
    target.set_major_formatter(FuncFormatter(_fmt))
    return ax


def panel(ax, tag, dx=-0.02, dy=1.045):
    ax.text(dx, dy, tag, transform=ax.transAxes, fontsize=9,
            fontweight='bold', va='bottom', ha='left')


def out(name):
    return os.path.join(FIGDIR, name)
