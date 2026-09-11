# -*- coding: utf-8 -*-
"""问题 2：整个烘干过程的变物性耦合模型（附录 3），输出前 3 h。

模型覆盖全过程（问题 3 复用同配置跑到终点），此处交付 0–3 h：
result2.xlsx（1 s × 0.1 cm，两个工作表）、表 3/表 4（0.5 h × 0.5 cm）。
验证：水分守恒（HC-13）；与问题 1 的物性切换自洽性。
"""
import os
import sys
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from properties import Props, T0, C0, R0, H_CONV, HM_CONV
from solver import solve
from io_utils import load_attachment1, make_boundary, save_result

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = 'output'
os.makedirs(f'{OUT}/figures', exist_ok=True)
os.makedirs(f'{OUT}/tables', exist_ok=True)

t_a, T_a, C_a = load_attachment1()
bc = make_boundary(t_a, T_a, C_a)
props = Props('app3')

N = 81
DT = 1.0
T_END = 10800.0                      # 3 h
r_out = np.arange(0.0, R0 + 1e-12, 0.001)
t_out = np.arange(1.0, T_END + 1e-9, 1.0)
print(f'问题2 求解中：N={N}, dt={DT}s, 附录3 变物性 + Picard ...')
res = solve(props, N, DT, T_END, bc, method='implicit', picard=2,
            r_out=r_out, t_out=t_out)
print('3h 末态：中心 T=%.4f，表面 T=%.4f，中心 C=%.4f，表面 C=%.4f'
      % (res['center_T'][-1], res['surf_T'][-1], res['center_C'][-1], res['surf_C'][-1]))

# ------------------------------------------------------------------ 守恒校验
M = res['mass_series']
flux = np.array([HM_CONV * (cs - bc(tt)[1]) for tt, cs in zip(res['times'], res['surf_C'])])
cum_out = np.concatenate([[0.0], np.cumsum(0.5 * (flux[1:] + flux[:-1]) * np.diff(res['times']))])
M0 = C0 * R0**2 / 2.0
rel = np.abs((M - M[0]) + R0 * cum_out) / M0
print('格式守恒一致性（模型自身守恒量 ∫C dV 与表面通量平衡）：末端相对残差 = %.3e' % rel[-1])

# ------------------------------------------------------------------ 交付
save_result(f'{OUT}/result2.xlsx', [
    ('温度', t_out, r_out * 100, res['T_hist'], False),
    ('水分浓度', t_out, r_out * 100, res['C_hist'], False),
])

t_tab = np.array([1800, 3600, 5400, 7200, 9000, 10800])       # 0.5–3.0 h
r_tab = np.array([0, 0.005, 0.01, 0.015, 0.02])
j_tab = [int(round(rr / 0.001)) for rr in r_tab]
i_tab = [int(tt) - 1 for tt in t_tab]
for name, mat in [('表3_温度', res['T_hist']), ('表4_水分浓度', res['C_hist'])]:
    with open(f'{OUT}/tables/{name}.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['时间/h'] + [f'{rr*100:g}' for rr in r_tab])
        for tt, row in zip(t_tab, mat[i_tab][:, j_tab]):
            w.writerow([f'{tt/3600:g}'] + [f'{v:.4f}' for v in row])
print('表 3/表 4 已存 output/tables/')

# ------------------------------------------------------------------ 图
th = res['times'] / 3600.0
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
tinf = np.array([bc(tt)[0] for tt in res['times']])
cinf = np.array([bc(tt)[1] for tt in res['times']])
axes[0].plot(th, tinf, 'k--', lw=1, label='烘房 $T_\\infty$')
axes[0].plot(th, res['surf_T'], label='药材表面')
axes[0].plot(th, res['center_T'], label='药材中心')
axes[0].axvline(3.0, color='gray', ls=':', lw=0.8)
axes[0].set_xlabel('时间 t / h'); axes[0].set_ylabel('温度 T / °C')
axes[0].set_title('问题2 温度演化（附录3变物性）'); axes[0].legend(fontsize=8)
axes[1].plot(th, res['surf_C'], label='药材表面')
axes[1].plot(th, res['center_C'], label='药材中心')
ax2 = axes[1].twinx()
ax2.plot(th, cinf, 'k--', lw=1, label='烘房 $C_\\infty$')
ax2.set_ylabel('烘房水分浓度 / (kg/kg)', fontsize=8)
axes[1].set_xlabel('时间 t / h'); axes[1].set_ylabel('药材水分浓度 C / (kg/kg)')
axes[1].set_title('问题2 水分浓度演化'); axes[1].legend(fontsize=8, loc='upper right')
fig.tight_layout()
fig.savefig(f'{OUT}/figures/fig_q2_evolution.png', dpi=160)

fig, ax = plt.subplots(figsize=(6.5, 4.2))
sel = [600, 1800, 3600, 7200, 10800]
cols = plt.cm.viridis(np.linspace(0, 0.9, len(sel)))
for k, tt in enumerate(sel):
    ax.plot(r_out * 100, res['C_hist'][int(tt) - 1], color=cols[k], label=f'{tt/3600:g} h')
ax.set_xlabel('到药材中心的距离 r / cm'); ax.set_ylabel('水分浓度 C / (kg/kg)')
ax.set_title('问题2 水分浓度径向剖面推进')
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(f'{OUT}/figures/fig_q2_profiles.png', dpi=160)

summary = {
    'conservation_rel_resid': float(rel[-1]),
    'center_T_3h': float(res['center_T'][-1]), 'surf_T_3h': float(res['surf_T'][-1]),
    'center_C_3h': float(res['center_C'][-1]), 'surf_C_3h': float(res['surf_C'][-1]),
}
with open(f'{OUT}/q2_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
