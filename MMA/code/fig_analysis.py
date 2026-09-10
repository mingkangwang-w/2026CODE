# -*- coding: utf-8 -*-
"""分析与验证图：收敛性、灵敏度(tornado)、SHAP 贡献度。"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import qmc
import common
from common import simulate
from figstyle import setup_style, save_fig, panel_label, PALETTE, DEFAULT_COLORS

setup_style()


def dry_time(problem=3, **over):
    """粗网格快速计算干燥时间（小时），over 覆盖 common 模块常量。"""
    saved = {k: getattr(common, k) for k in over}
    for k, v in over.items():
        setattr(common, k, v)
    try:
        res = simulate(problem, 400000.0, 60.0, N=100,
                       out_times=np.array([1e12]), out_r=np.array([0.0]),
                       drying_thresh=0.15)
        return res['T_end'] / 3600.0
    finally:
        for k, v in saved.items():
            setattr(common, k, v)


# ================= 图10：收敛性 =================
Nv = [50, 100, 200, 400]
Ts, Cs = [], []
for N in Nv:
    r = simulate(1, 1800.0, 0.25, N=N, out_times=np.array([1800.0]),
                 out_r=np.array([0.0, 0.02]))
    Ts.append(r['T_out'][0, 1]); Cs.append(r['C_out'][0, 1])
Ts = np.array(Ts); Cs = np.array(Cs)
dr = 0.02 / np.array(Nv)
# Richardson 二阶外推参考值
T_ref = (4 * Ts[-1] - Ts[-2]) / 3.0
C_ref = (4 * Cs[-1] - Cs[-2]) / 3.0
eT = np.abs(Ts - T_ref); eC = np.abs(Cs - C_ref)

fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
ax = axes[0]
ax.loglog(dr, eT, 'o-', color=PALETTE['blue_main'], label='温度（表面）')
ax.loglog(dr, eC, 's--', color=PALETTE['red_main'], label='水分（表面）')
ax.loglog(dr, 3e-3 * dr ** 2, 'k:', lw=1.2, label='二阶参考 $O(\\Delta r^2)$')
ax.set_xlabel('空间步长 $\\Delta r$ / m'); ax.set_ylabel('绝对误差')
ax.legend(fontsize=8)
panel_label(ax, 'a')

# 问题3 干燥时间随网格/时间步收敛
ax = axes[1]
N3 = [200, 300, 400]; tend3 = [57.4139, 57.4389, 57.4514]
ax.plot(N3, tend3, 'o-', color=PALETTE['blue_main'], label='干燥时间')
ax.set_xlabel('网格区间数 $N$'); ax.set_ylabel('干燥时间 / h')
ax.legend(fontsize=8)
panel_label(ax, 'b')
fig.suptitle('图10  数值解收敛性检验', y=1.02)
save_fig(fig, 'fig10_convergence')

# ================= 图11：灵敏度 tornado =================
base = {'h_conv': 25.0, 'hm': 8e-7, 'T_AIR_CONST': 50.0,
        'C_AIR_CONST': 0.05, 'C0_INIT': 2.55, 'R0': 0.02}
names = ['$h$', '$h_m$', '$T_{air}$', '$C_{air}$', '$C_0$', '$R_0$']
keys = ['h_conv', 'hm', 'T_AIR_CONST', 'C_AIR_CONST', 'C0_INIT', 'R0']
t0 = dry_time()
rows = []
for k in keys:
    hi = dry_time(**{k: base[k] * 1.2})
    lo = dry_time(**{k: base[k] * 0.8})
    rows.append((lo, hi))
rows = np.array(rows)
order = np.argsort(np.abs(rows - t0).max(axis=1))  # 按影响从小到大

fig, ax = plt.subplots(figsize=(4.6, 3.4))
y = np.arange(len(keys))
for j, i in enumerate(order):
    lo, hi = rows[i]
    ax.barh(j, hi - lo, left=lo, height=0.55, color=PALETTE['blue_secondary'],
            alpha=0.9, edgecolor='none')
    ax.plot([lo, hi], [j, j], color='none')
    ax.plot(t0, j, 'k|', ms=8, markeredgewidth=1.4)
ax.axvline(t0, color=PALETTE['neutral_dark'], ls='--', lw=1.1)
ax.set_yticks(y); ax.set_yticklabels([names[i] for i in order])
ax.set_xlabel('干燥时间 / h')
ax.text(t0, -0.6, f'基准 {t0:.2f} h', ha='center', fontsize=8, color=PALETTE['neutral_dark'])
fig.suptitle('图11  参数 ±20% 对干燥时间的灵敏度', y=1.02)
save_fig(fig, 'fig11_sensitivity')

# ================= 图12：SHAP 贡献度 =================
np.random.seed(42)
sampler = qmc.LatinHypercube(d=6)
Xunit = sampler.random(n=60)
lo_b = np.array([20.0, 6.4e-7, 40.0, 0.04, 2.04, 0.016])
hi_b = np.array([30.0, 9.6e-7, 60.0, 0.06, 3.06, 0.024])
X = qmc.scale(Xunit, lo_b, hi_b)
y = np.array([dry_time(h_conv=X[i, 0], hm=X[i, 1], T_AIR_CONST=X[i, 2],
                       C_AIR_CONST=X[i, 3], C0_INIT=X[i, 4], R0=X[i, 5])
              for i in range(len(X))])

from sklearn.ensemble import RandomForestRegressor
import shap
model = RandomForestRegressor(n_estimators=300, random_state=0).fit(X, y)
explainer = shap.TreeExplainer(model)
sv = explainer.shap_values(X)

feat_names = ['$h$', '$h_m$', '$T_{air}$', '$C_{air}$', '$C_0$', '$R_0$']
mean_abs = np.abs(sv).mean(axis=0)
order2 = np.argsort(mean_abs)

fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.1))
ax = axes[0]
ax.barh(np.arange(6), mean_abs[order2], color=PALETTE['blue_main'], alpha=0.9)
ax.set_yticks(np.arange(6)); ax.set_yticklabels([feat_names[i] for i in order2])
ax.set_xlabel('平均 |SHAP| 值（干燥时间 / h）')
ax.set_title('参数贡献度', fontsize=9)
panel_label(ax, 'a')

# 蜂群图（手工绘制）
ax = axes[1]
cmap = plt.get_cmap('RdYlBu_r')
for j in range(6):
    fj = order2[j]
    vals = X[:, fj]
    vn = (vals - lo_b[fj]) / (hi_b[fj] - lo_b[fj])
    jit = 0.35 * (np.random.default_rng(fj).random(len(sv)) - 0.5)
    ax.scatter(sv[:, fj], j + jit, c=vn, cmap=cmap, vmin=0, vmax=1,
               s=12, linewidths=0, alpha=0.85)
ax.axvline(0, color=PALETTE['neutral_dark'], ls='-', lw=0.9)
ax.set_yticks(np.arange(6)); ax.set_yticklabels([feat_names[i] for i in order2])
ax.set_xlabel('SHAP 值（对干燥时间的影响 / h）')
ax.set_title('SHAP 蜂群图', fontsize=9)
panel_label(ax, 'b')
fig.suptitle('图12  参数对干燥时间的 SHAP 贡献度分析', y=1.02)
save_fig(fig, 'fig12_shap')
print('fig_analysis done, baseline dry time =', round(t0, 3), 'h')
