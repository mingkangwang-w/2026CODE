# -*- coding: utf-8 -*-
"""多样化图：小提琴图（径向水分分布）+ Sankey 水分流向图。"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.sankey import Sankey
from figstyle import setup_style, save_fig, panel_label, PALETTE, DEFAULT_COLORS

setup_style()
d3 = np.load('/home/user/workspace/code/_p3.npz')
t3 = d3['t']; C3 = d3['C']; r_cm = d3['r'] * 100.0; T_end3 = d3['T_end']

# ---------- 图13：小提琴图（各时刻径向水分分布） ----------
sel = [6, 12, 18, 24, 30, 36, 42, 48]
sel_i = [int(np.argmin(np.abs(t3 - x * 3600))) for x in sel]
data = [C3[i] for i in sel_i]
positions = np.arange(len(sel))

fig, ax = plt.subplots(figsize=(5.4, 3.4))
colors = plt.get_cmap('viridis')(np.linspace(0, 0.85, len(sel)))
vp = ax.violinplot(data, positions=positions, widths=0.75, showmeans=False,
                   showmedians=True, showextrema=True)
for k, body in enumerate(vp['bodies']):
    body.set_facecolor(colors[k]); body.set_alpha(0.75); body.set_edgecolor('none')
for part in ('cbars', 'cmins', 'cmaxes', 'cmedians'):
    vp[part].set_color(PALETTE['neutral_dark'])
    vp[part].set_linewidth(0.8)
ax.set_xticks(positions)
ax.set_xticklabels([f'{x} h' for x in sel], rotation=0)
ax.set_xlabel('干燥时间 / h')
ax.set_ylabel('径向水分浓度 / (kg·kg$^{-1}$)')
ax.axhline(0.15, color=PALETTE['red_main'], ls='--', lw=1.1)
ax.text(len(sel) - 0.2, 0.16, '$C=0.15$', color=PALETTE['red_main'], fontsize=8, ha='right')
fig.suptitle('图13  不同时刻药材内部水分浓度的径向分布', y=1.02)
save_fig(fig, 'fig13_violin')

# ---------- 图14：Sankey 水分流向 ----------
Cbar = np.trapz(C3 * r_cm[None, :], r_cm, axis=1) / np.trapz(r_cm, r_cm)
C0 = 2.55
i4 = int(np.argmin(np.abs(t3 - 14400.0)))          # 预热结束（4 h）
C_pre = Cbar[i4]; C_end = Cbar[-1]
rem_pre = C0 - C_pre                                # 预热段去除
rem_const = C_pre - C_end                           # 恒温段去除
residual = C_end                                    # 残留
total = C0
f1 = rem_pre / total; f2 = rem_const / total; f3 = residual / total

fig = plt.figure(figsize=(6.2, 3.2))
ax = fig.add_subplot(1, 1, 1, xticks=[], yticks=[], frame_on=False)
sankey = Sankey(ax=ax, scale=0.012, offset=0.1, head_angle=135,
                format='%.1f', unit='%', gap=0.35, shoulder=0.03)
sankey.add(flows=[-100, f1 * 100, f2 * 100, f3 * 100],
           labels=['初始水分\n(干基)', '预热段蒸发去除', '恒温段蒸发去除', '残留水分'],
           orientations=[0, 1, 1, 1],
           pathlengths=[0.6, 0.6, 0.6, 0.6],
           facecolor=PALETTE['blue_main'], alpha=0.9)
diagrams = sankey.finish()
for d in diagrams:
    d.patch.set_facecolor(PALETTE['blue_main'])
    d.patch.set_alpha(0.9)
    for t in d.texts:
        t.set_fontsize(8)
fig.suptitle('图14  干燥过程水分流向（干基含水率质量平衡）', y=1.0)
save_fig(fig, 'fig14_sankey')
print(f'fig_misc done: 预热去除 {f1*100:.1f}%, 恒温去除 {f2*100:.1f}%, 残留 {f3*100:.1f}%')
