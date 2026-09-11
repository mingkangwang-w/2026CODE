# -*- coding: utf-8 -*-
"""问题 1：预热平衡阶段（0–1800 s），附录 2 常物性 + D(C)。

验证：温度场 vs Bessel 半解析（Duhamel 叠加时变边界）；
      水分场 vs 常 D 半解析（注意 Q1 中 D(C) 在表面变化约 21%，
      常 D 近似与数值解的 ~0.04 kg/kg 偏差正是非线性效应量级，仍构成有效互验）；
      格式守恒一致性校验（模型自身守恒量 ∫C dV 与表面通量的平衡，HC-13）；
      显式/隐式互验。
交付：output/result1.xlsx、表 1/表 2（CSV）、图 fig_q1_*.png。
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from properties import Props, T0, C0, R0, H_CONV, HM_CONV
from solver import solve, cfl_limit
from analytic import CylinderSemiAnalytic
from io_utils import load_attachment1, make_boundary, save_result

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = 'output'
os.makedirs(f'{OUT}/figures', exist_ok=True)
os.makedirs(f'{OUT}/tables', exist_ok=True)

# ------------------------------------------------------------------ 数据与边界
t_a, T_a, C_a = load_attachment1()
bc = make_boundary(t_a, T_a, C_a)
props = Props('app2')

# ------------------------------------------------------------------ 数值求解
N = 161                      # dr = 0.125 mm，可分辨 Q1 水分边界层（~0.1 mm）
DT = 1.0
T_END = 1800.0
r_out = np.arange(0.0, R0 + 1e-12, 0.001)          # 0–2 cm，步长 0.1 cm
t_out = np.arange(1.0, T_END + 1e-9, 1.0)          # 1–1800 s
print(f'求解中：N={N}, dt={DT}s, 隐式+Picard ...')
res = solve(props, N, DT, T_END, bc, method='implicit', picard=2,
            r_out=r_out, t_out=t_out)
print('完成。表面 C(1800s)=%.4f，中心 C=%.4f，表面 T=%.4f，中心 T=%.4f'
      % (res['surf_C'][-1], res['center_C'][-1], res['surf_T'][-1], res['center_T'][-1]))

# 显式交叉验证（小步长）
dt_ex = cfl_limit(props, 81)
print(f'显式交叉验证：N=81, dt={dt_ex:.3f}s ...')
res_ex = solve(props, 81, dt_ex, T_END, bc, method='explicit',
               r_out=r_out, t_out=np.array([1800.0]))
diff_ex = np.nanmax(np.abs(res_ex['T_hist'][-1] - res['T_hist'][-1]))
print('显式 vs 隐式 末态温度最大偏差: %.5f °C' % diff_ex)

# ------------------------------------------------------------------ 半解析对照
alpha = 0.36 / (820.0 * 2600.0)
Bi = H_CONV * R0 / 0.36
sa_T = CylinderSemiAnalytic(alpha, Bi, R0, n_modes=300)
D0 = float(props.D(np.array([C0]), np.array([T0]))[0])
Bi_m = HM_CONV * R0 / D0
sa_C = CylinderSemiAnalytic(D0, Bi_m, R0, n_modes=300)
print(f'alpha={alpha:.4e}, Bi={Bi:.3f}; D0={D0:.4e}, Bi_m={Bi_m:.3f}')

x_norm = r_out / R0
t_tab = np.array([100, 300, 600, 900, 1200, 1500, 1800], float)
i_tab = [int(tt) - 1 for tt in t_tab]
T_num = res['T_hist'][i_tab]                    # (7, 21)
C_num = res['C_hist'][i_tab]
T_ana = np.array([sa_T.response(x_norm, tt, t_a, T_a, T0) for tt in t_tab])
C_ana = np.array([sa_C.response(x_norm, tt, t_a, C_a, C0) for tt in t_tab])
err_T = np.abs(T_num - T_ana)
err_C = np.abs(C_num - C_ana)
print('温度场 vs 半解析：max|err| = %.5f °C，RMS = %.5f °C'
      % (err_T.max(), np.sqrt((err_T**2).mean())))
print('水分场 vs 半解析（常D近似）：max|err| = %.5f kg/kg' % err_C.max())

# ------------------------------------------------------------------ 守恒校验
M = res['mass_series']                          # ∫C r dr（单位长）
flux = np.array([HM_CONV * (cs - bc(tt)[1]) for tt, cs in zip(res['times'], res['surf_C'])])
cum_out = np.cumsum(0.5 * (flux[1:] + flux[:-1]) * np.diff(res['times']))
cum_out = np.concatenate([[0.0], cum_out])
M0 = C0 * R0**2 / 2.0
resid = (M - M[0]) + R0 * cum_out
rel = np.abs(resid) / M0
print('格式守恒一致性（模型自身守恒量 ∫C dV 与表面通量平衡）：末端相对残差 = %.3e（判据 <1%%）' % rel[-1])

# ------------------------------------------------------------------ 交付文件
save_result(f'{OUT}/result1.xlsx', [
    ('温度', t_out, r_out * 100, res['T_hist'], False),
    ('水分浓度', t_out, r_out * 100, res['C_hist'], False),
])

r_tab = np.array([0, 0.005, 0.01, 0.015, 0.02])
j_tab = [int(round(rr / 0.001)) for rr in r_tab]
import csv
for name, mat in [('表1_温度', T_num), ('表2_水分浓度', C_num)]:
    with open(f'{OUT}/tables/{name}.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['时间/s'] + [f'{rr*100:g}' for rr in r_tab])
        for tt, row in zip(t_tab, mat[:, j_tab]):
            w.writerow([int(tt)] + [f'{v:.4f}' for v in row])
print('表 1/表 2 已存 output/tables/')

# ------------------------------------------------------------------ 图
colors = plt.cm.viridis(np.linspace(0, 0.9, len(t_tab)))
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for k, tt in enumerate(t_tab):
    axes[0].plot(r_out * 100, T_num[k], color=colors[k], label=f'{int(tt)} s')
    axes[0].plot(r_out * 100, T_ana[k], 'o', ms=3, color=colors[k], mfc='none')
axes[0].set_xlabel('到药材中心的距离 r / cm')
axes[0].set_ylabel('温度 T / °C')
axes[0].set_title('问题1 温度径向剖面（实线=数值，圆点=半解析）')
axes[0].legend(fontsize=8)
for k, tt in enumerate(t_tab):
    axes[1].plot(r_out * 100, C_num[k], color=colors[k], label=f'{int(tt)} s')
    axes[1].plot(r_out * 100, C_ana[k], 'o', ms=3, color=colors[k], mfc='none')
axes[1].set_xlabel('到药材中心的距离 r / cm')
axes[1].set_ylabel('水分浓度 C / (kg/kg)')
axes[1].set_title('问题1 水分浓度径向剖面（实线=数值，圆点=半解析）')
axes[1].legend(fontsize=8)
fig.tight_layout()
fig.savefig(f'{OUT}/figures/fig_q1_profiles.png', dpi=160)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
TT, RR = np.meshgrid(t_out, r_out * 100)
cf0 = axes[0].contourf(TT, RR, res['T_hist'].T, levels=24, cmap='hot')
axes[0].set_xlabel('时间 t / s'); axes[0].set_ylabel('r / cm')
axes[0].set_title('问题1 温度时空场 T(r,t)')
fig.colorbar(cf0, ax=axes[0])
cf1 = axes[1].contourf(TT, RR, res['C_hist'].T, levels=24, cmap='Blues_r')
axes[1].set_xlabel('时间 t / s'); axes[1].set_ylabel('r / cm')
axes[1].set_title('问题1 水分浓度时空场 C(r,t)')
fig.colorbar(cf1, ax=axes[1])
fig.tight_layout()
fig.savefig(f'{OUT}/figures/fig_q1_fields.png', dpi=160)
print('图已存 output/figures/')

# 汇总（供报告引用）
summary = {
    'T_max_err_vs_analytic': float(err_T.max()),
    'T_rms_err_vs_analytic': float(np.sqrt((err_T**2).mean())),
    'C_max_err_vs_analytic_constD': float(err_C.max()),
    'conservation_rel_resid': float(rel[-1]),   # 格式守恒一致性残差（∫C dV 平衡）
    'explicit_implicit_maxdiff_T': float(diff_ex),
    'surf_C_1800': float(res['surf_C'][-1]),
    'center_T_1800': float(res['center_T'][-1]),
    'surf_T_1800': float(res['surf_T'][-1]),
}
import json
with open(f'{OUT}/q1_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
