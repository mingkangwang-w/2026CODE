# -*- coding: utf-8 -*-
"""
Figure: moisture content in the shrinking cylinder as a space-time heatmap
(Problem 4, reference-coordinate / Lagrange solution).

Form choice
    The data is a regular (time x radius) grid of a single magnitude, so the
    recommended form is a heatmap with a SEQUENTIAL, single-hue, light->dark
    colour scale.  A scatter plot was rejected: the field is a smooth PDE
    solution, not a set of discrete samples, and a scatter would waste the
    positional channel that already carries radius and time.

Encodings
    x        time (h)
    y        distance from centre (cm), physical coordinates
    colour   moisture content C (kg/kg), one hue, light = dry -> dark = wet
    mask     r > R(t) is outside the sample and is left blank
    overlay  R(t)          solid  - the moving surface
             C = 0.15      dashed - the drying criterion

Output (SVG, with a PNG preview alongside):
    fig_p4_heatmap.svg
    fig_p4_heatmap.png

Data: ../../code/_p4.npz, produced by ../../code/solve_p4.py
"""
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
MMA = os.path.dirname(os.path.dirname(HERE))
NPZ = os.path.join(MMA, 'code', '_p4.npz')

# ---------------------------------------------------------------- palette
# Sequential ramp: ONE hue (blue), light -> dark, documented 100->700 steps.
# Light = low moisture (dry), dark = high moisture (wet).
SEQ_BLUE = ['#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec', '#5598e7',
            '#3987e5', '#2a78d6', '#256abf', '#1c5cab', '#184f95', '#104281',
            '#0d366b']
SURFACE = '#fcfcfb'      # chart surface
INK = '#0b0b0b'          # primary text
INK2 = '#52514e'         # secondary text
RULE = '#dcdbd6'         # recessive hairline
ACCENT = '#eb6834'       # threshold annotation (drying criterion)

CMAP = LinearSegmentedColormap.from_list('seq_blue', SEQ_BLUE, N=256)

C_FRONT = 0.15           # drying criterion, kg/kg
STRIDE = 4               # time-axis thinning for the vector export (4 min)

# Chinese font.  SimSun matches the body text of the paper; swap the first
# entry for 'SimHei' if a sans face is preferred for figure labels.
# Note: SimSun has no U+2212 (minus sign), which only matters on log axes -
# this figure has none, so axes.unicode_minus=False is enough.
CJK_FONT = 'SimSun'
TEXT_AS_PATHS = False    # True -> outline the text (renders anywhere, not editable)


def main():
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': [CJK_FONT, 'Microsoft YaHei', 'SimHei',
                            'DejaVu Sans'],
        'axes.unicode_minus': False,
        # 'none' keeps the text as real <text> nodes (editable, small file);
        # 'path' outlines it so the SVG renders on machines without the font.
        'svg.fonttype': 'path' if TEXT_AS_PATHS else 'none',
        'mathtext.fontset': 'cm',        # formulas stay in Computer Modern
        'font.size': 9.5,
        'axes.linewidth': 0.8,
        'xtick.labelsize': 8.5,
        'ytick.labelsize': 8.5,
    })

    d = np.load(NPZ)
    t = d['t'] / 3600.0                  # s -> h
    C = d['C']                           # (nt, nr) at fixed physical distances
    C_surf = d['C_surf']
    R = d['R'] * 100.0                   # m -> cm
    r = d['r'] * 100.0                   # m -> cm
    T_end = float(d['T_end']) / 3600.0

    # Mask cells outside the current sample radius
    Cm = np.where(r[None, :] <= R[:, None], C, np.nan)

    # ---- curvilinear mesh so the top edge follows the true surface R(t) ----
    # The field is sampled at fixed distances r[j], so a rectilinear grid would
    # leave a stepped gap of up to half a cell under R(t).  Instead the outermost
    # cell of each column is stretched to close on R(t) exactly.
    # The field is smooth in time, so thinning the time axis costs nothing
    # visually while keeping the SVG vector and a sane file size.
    nt_full, nr = C.shape
    idx = np.unique(np.r_[np.arange(0, nt_full, STRIDE), nt_full - 1])
    ts, Cs, Rs = t[idx], C[idx], R[idx]
    nt = len(idx)

    tc = np.concatenate([[ts[0]], 0.5 * (ts[:-1] + ts[1:]), [ts[-1]]])    # nt+1
    Csc = C_surf[idx]
    Rc = np.interp(tc, ts, Rs)

    edges0 = np.concatenate([[max(r[0] - 0.05, 0.0)], r + 0.05])          # nr+1
    Xc = np.tile(tc[:, None], (1, nr + 1))
    Yc = np.tile(edges0[None, :], (len(tc), 1))
    V = np.full((nt, nr), np.nan)

    for i in range(nt):
        Rm = max(Rc[i], Rc[i + 1])
        jm = int(np.searchsorted(r, Rm, side='right')) - 1
        if jm < 0:
            continue
        V[i, :jm] = Cs[i, :jm]
        # outermost strip spans [r[jm]-0.05, R(t)]; average of its two ends
        V[i, jm] = 0.5 * (Cs[i, jm] + Csc[i])
        for e in (i, i + 1):
            Yc[e, jm + 1:] = Rc[e]

    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    # ---------------- heatmap ----------------
    mesh = ax.pcolormesh(Xc, Yc, V, cmap=CMAP, vmin=0.0, vmax=2.55,
                         shading='flat')

    # ---------------- overlays ----------------
    # Moving surface R(t) - solid, the domain edge
    ax.plot(t, R, color=INK, lw=1.4, solid_capstyle='round', zorder=5)

    # Drying front C = 0.15 - dashed, it IS a threshold
    try:
        ax.contour(t, r, Cm.T, levels=[C_FRONT], colors=[ACCENT],
                   linewidths=1.5, linestyles='--', zorder=6)
    except Exception as exc:                                   # noqa: BLE001
        print('  (contour skipped:', exc, ')')

    # ---------------- axes ----------------
    ax.set_xlabel('时间 / h', color=INK)
    ax.set_ylabel('到药材中心的距离 / cm', color=INK)
    ax.set_xlim(0, T_end)
    ax.set_ylim(0, 2.0)

    ax.tick_params(colors=INK2, length=3)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(RULE)

    # ---------------- colourbar ----------------
    # Drawn by hand as vector strips: matplotlib's stock Colorbar emits an
    # embedded raster into the SVG, which would defeat the vector export.
    from matplotlib.patches import Rectangle
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    cax = make_axes_locatable(ax).append_axes('right', size='3.2%', pad=0.22)
    n_strip = 256
    ylev = np.linspace(0.0, 2.55, n_strip + 1)
    for k in range(n_strip):
        cax.add_patch(Rectangle((0.0, ylev[k]), 1.0, ylev[k + 1] - ylev[k],
                                facecolor=CMAP(k / (n_strip - 1.0)),
                                edgecolor='none', linewidth=0))
    cax.set_xlim(0.0, 1.0)
    cax.set_ylim(0.0, 2.55)
    cax.set_xticks([])
    cax.yaxis.tick_right()
    cax.yaxis.set_label_position('right')
    cax.set_yticks([0, 0.5, 1.0, 1.5, 2.0, 2.5])
    cax.tick_params(colors=INK2, length=2)
    cax.set_ylabel(r'水分浓度 $C$ / (kg$\cdot$kg$^{-1}$)',
                   color=INK, labelpad=4)
    for s in ('top', 'left', 'bottom', 'right'):
        cax.spines[s].set_visible(False)

    # ---------------- selective direct labels ----------------
    # Endpoint of the drying time - the one number that matters
    ax.plot([T_end], [0.0], marker='o', ms=4.5, mfc=SURFACE, mec=INK,
            mew=1.2, zorder=7, clip_on=False)
    ax.annotate(f'干燥时长 $t^*$ = {T_end:.1f} h',
                xy=(T_end, 0.0), xytext=(-14, 24), textcoords='offset points',
                ha='right', fontsize=9, color=INK, zorder=7)

    # One label per overlay, placed on the feature itself
    ax.text(t[0] + 1.5, R[0] - 0.14, r'药材表面 $R(t)$', fontsize=8.5,
            color=INK, va='top')

    # Drying front label anchored where the front crosses a chosen radius
    r_anchor = 1.0
    j = int(np.argmin(np.abs(r - r_anchor)))
    col = Cm[:, j]
    k = np.argmax(col < C_FRONT) if np.any(col < C_FRONT) else len(t) // 2
    t_a, r_a = t[k], r[j]
    ax.annotate(f'$C$ = {C_FRONT:g}（干燥前沿）',
                xy=(t_a, r_a), xytext=(-12, 30), textcoords='offset points',
                ha='right', fontsize=8.5, color=ACCENT, zorder=7,
                arrowprops=dict(arrowstyle='-', lw=0.9, color=ACCENT,
                                shrinkA=1, shrinkB=3))

    # t* is already annotated on the plot itself, so the subtitle carries only
    # the geometry and the sampling - keeping the two title lines from
    # overrunning the axes width.
    ax.set_title(
        f'收缩试样内的水分浓度演化\n'
        f'半径 {R[0]:.2f} → {R[-1]:.2f} cm   |   取样间隔 0.1 cm × 60 s',
        fontsize=9.5, color=INK, loc='left', pad=8, linespacing=1.15)

    fig.tight_layout()

    base = os.path.join(HERE, 'fig_p4_heatmap')
    fig.savefig(base + '.svg', facecolor=SURFACE, bbox_inches='tight')
    fig.savefig(base + '.png', dpi=300, facecolor=SURFACE, bbox_inches='tight')
    plt.close(fig)
    print('saved: fig_p4_heatmap.svg / .png')
    print(f'  grid {C.shape[0]} x {C.shape[1]},  '
          f't* = {T_end:.4f} h,  R {R[0]:.3f} -> {R[-1]:.3f} cm')


if __name__ == '__main__':
    main()
