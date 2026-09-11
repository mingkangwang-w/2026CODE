# -*- coding: utf-8 -*-
"""问题 4：收缩动边界（附件 2 给定 R(t)），附录 4 变物性，eta=r/R(t) 归一化。

验证：动域质量积分恒等式 dM/dt = R*Rdot*C_s - R*h_m*(C_s-C_inf)（PDE 严格恒等式，
      用于校验含伪对流项的离散）；网格收敛；与问题 3 对比（两效应竞争论证）。
交付：result4.xlsx（60 s × 0.1 cm，末列"药材表面"）、表 6。
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
from properties import Props, T0, C0, R0, HM_CONV, C_THRESHOLD
from solver import solve
from io_utils import load_attachment1, load_attachment2, make_boundary, make_radius, save_result

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

OUT = 'output'
os.makedirs(f'{OUT}/figures', exist_ok=True)
os.makedirs(f'{OUT}/tables', exist_ok=True)

t_a, T_a, C_a = load_attachment1()
bc = make_boundary(t_a, T_a, C_a)
t_r, R_cm = load_attachment2()
R_func, Rdot_func = make_radius(t_r, R_cm)
props = Props('app4')
T_MAX = 72 * 3600.0

# ------------------------------------------------------------------ 网格收敛
print('问题4 网格收敛试验（仅求 t*）...')
conv = []
for Nx, dtx in [(41, 10.0), (81, 10.0), (161, 10.0)]:
    r0 = solve(props, Nx, dtx, T_MAX, bc, method='implicit', picard=2,
               R_func=R_func, Rdot_func=Rdot_func, stop_at_threshold=True)
    conv.append(dict(N=Nx, dt=dtx, t_star_h=r0['t_star'] / 3600.0))
    print(f'  N={Nx:4d} dt={dtx:5.1f}s -> t* = {r0["t_star"]/3600:.4f} h')

# ------------------------------------------------------------------ 主求解
N, DT = 81, 10.0
r_out = np.arange(0.0, R0 - 1e-12, 0.001)          # 物理距离 0–1.9 cm（末列"药材表面"替代 2.0）
print(f'问题4 主求解：N={N}, dt={DT}s（eta 坐标动域）...')
res = solve(props, N, DT, T_MAX, bc, method='implicit', picard=2,
            R_func=R_func, Rdot_func=Rdot_func,
            r_out=r_out, t_out=np.arange(60.0, T_MAX, 60.0),
            stop_at_threshold=True)
t_star = res['t_star']
print(f't* = {t_star/3600:.4f} h，此时 R = {R_func(t_star)*100:.4f} cm')

# ------------------------------------------------------------------ 动域质量恒等式校验
# M_eta=∫C η dη，PDE 严格恒等式 dM_eta/dt = (Rdot/R)(C_s-2M_eta) - (h_m/R)(C_s-C_inf)
ts = res['times']
M = res['mass_series']
rhs = np.array([(Rdot_func(tt) / R_func(tt)) * (cs - 2.0 * m)
                - HM_CONV * (cs - bc(tt)[1]) / R_func(tt)
                for tt, cs, m in zip(ts, res['surf_C'], M)])
lhs_cum = M - M[0]
rhs_cum = np.concatenate([[0.0], np.cumsum(0.5 * (rhs[1:] + rhs[:-1]) * np.diff(ts))])
scale = abs(lhs_cum[-1]) + 1e-30
ident_resid = abs(lhs_cum[-1] - rhs_cum[-1]) / scale
print(f'动域质量恒等式：累计两端相对偏差 = {ident_resid:.3e}（伪对流项为二阶中心差分，判据 <1%）')

# ------------------------------------------------------------------ 交付
n_full = int(t_star // 60.0)
t_out = np.arange(60.0, (n_full + 1) * 60.0, 60.0)
C_hist = res['C_hist'][:n_full]
# 末列"药材表面"：各时刻 eta=1 的值（surf_C 逐步序列重采样到输出网格）
surf_at_out = np.interp(t_out, ts, res['surf_C'])
C_end_eta = res['C_final']
C_end = np.interp(r_out / R_func(t_star), res['xg'], C_end_eta)
out_mask = r_out > R_func(t_star) + 1e-12
C_end[out_mask] = np.nan
t_out_ext = np.concatenate([t_out, [t_star]])
C_hist_ext = np.vstack([C_hist, C_end])
surf_ext = np.concatenate([surf_at_out, [res['surf_C'][-1]]])
# 拼接：21 个物理列（超出 R(t) 处为空）+ 末列"药材表面"
data = np.column_stack([C_hist_ext, surf_ext])
r_cols = np.concatenate([r_out * 100, [np.nan]])      # 末列占位，表头写"药材表面"

save_result(f'{OUT}/result4.xlsx', [
    ('Sheet1', t_out_ext, r_cols, data, True),
])

# 表 6：每 6 h 一行 + 烘干结束时间行；列 0,0.5,...,2.0 + 药材表面
r_tab = np.array([0, 0.005, 0.01, 0.015])
j_tab = [int(round(rr / 0.001)) for rr in r_tab]
t6 = [h * 3600 for h in range(6, int(t_star // 3600) + 1, 6)]
with open(f'{OUT}/tables/表6_水分浓度.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['时间/h'] + [f'{rr*100:g}' for rr in r_tab] + ['药材表面'])
    for tt in t6:
        row = res['C_hist'][int(tt // 60) - 1]
        sv = float(np.interp(tt, ts, res['surf_C']))
        w.writerow([f'{tt/3600:g}'] + ['' if np.isnan(v) else f'{v:.4f}' for v in row[j_tab]] + [f'{sv:.4f}'])
    w.writerow([f'烘干结束时间({t_star/3600:.2f}h)']
               + ['' if np.isnan(v) else f'{v:.4f}' for v in C_end[j_tab]]
               + [f'{res["surf_C"][-1]:.4f}'])
print('表 6 已存 output/tables/')

# ------------------------------------------------------------------ 图
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
th = ts / 3600.0
axes[0].plot(th, res['center_C'], label='中心 $C(0,t)$（问题4）')
axes[0].plot(th, res['surf_C'], label='表面 $C(R(t),t)$（问题4）')
axes[0].axhline(C_THRESHOLD, color='r', ls='--', lw=1)
axes[0].axvline(t_star / 3600, color='gray', ls=':', lw=1)
axes[0].annotate(f'$t^*$ = {t_star/3600:.2f} h', xy=(t_star / 3600, 0.15),
                 xytext=(t_star / 3600 - 20, 0.8),
                 arrowprops=dict(arrowstyle='->', color='gray'))
axes[0].set_xlabel('时间 t / h'); axes[0].set_ylabel('水分浓度 C / (kg/kg)')
axes[0].set_title('问题4 收缩域上的含水率衰减')
axes[0].legend(fontsize=8)
axR = axes[0].twinx()
axR.plot(th, [R_func(tt) * 100 for tt in ts], 'g:', lw=1)
axR.set_ylabel('半径 R(t) / cm', color='g', fontsize=8)
TT, RRg = np.meshgrid(t_out / 3600.0, r_out * 100)
Ch = C_hist.T
cf = axes[1].contourf(TT, RRg, Ch, levels=24, cmap='Blues_r')
Rline = np.array([R_func(tt) * 100 for tt in t_out])
axes[1].plot(t_out / 3600.0, Rline, 'r-', lw=1.5, label='药材表面 R(t)')
axes[1].set_xlabel('时间 t / h'); axes[1].set_ylabel('r / cm')
axes[1].set_title('问题4 收缩域水分时空场')
axes[1].legend(fontsize=8, loc='upper right')
fig.colorbar(cf, ax=axes[1])
fig.tight_layout()
fig.savefig(f'{OUT}/figures/fig_q4_moving.png', dpi=160)

summary = {
    't_star_h': t_star / 3600.0,
    'R_at_t_star_cm': R_func(t_star) * 100,
    'grid_convergence': conv,
    'moving_mass_identity_rel_resid': float(ident_resid),
}
with open(f'{OUT}/q4_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2, default=float))
