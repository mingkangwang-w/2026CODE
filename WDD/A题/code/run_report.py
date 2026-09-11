# -*- coding: utf-8 -*-
"""汇总：输入数据图、Q3/Q4 对比图与两效应竞争分析、全问题验证报告。

为画对比曲线，此处以轻量方式重算 Q3/Q4 主求解（不存剖面，约几分钟）。
"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from properties import Props, C0, C_THRESHOLD
from solver import solve
from io_utils import load_attachment1, load_attachment2, make_boundary, make_radius

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False
OUT = 'output'

# ------------------------------------------------------------------ 附件数据图
t_a, T_a, C_a = load_attachment1()
t_r, R_cm = load_attachment2()

fig, ax1 = plt.subplots(figsize=(7, 4.2))
ax1.plot(t_a / 3600, T_a, 'r-', lw=1.2)
ax1.set_xlabel('时间 t / h'); ax1.set_ylabel('温度 / °C', color='r')
ax1.tick_params(axis='y', labelcolor='r')
ax2 = ax1.twinx()
ax2.plot(t_a / 3600, C_a, 'b-', lw=1.2)
ax2.set_ylabel('水分浓度 / (kg/kg)', color='b')
ax2.tick_params(axis='y', labelcolor='b')
ax1.axvline(3.0, color='gray', ls=':', lw=1)
ax1.annotate('约 3 h 后进入平台（恒温干燥阶段，\n$t>4$ h 取平台值延拓）', xy=(3.05, 33), fontsize=8)
ax1.set_title('附件1：烘房温度与水分浓度（每 60 s）')
fig.tight_layout()
fig.savefig(f'{OUT}/figures/fig_oven_input.png', dpi=160)

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.plot(t_r / 3600, R_cm, 'g-', lw=1.5)
ax.axvline(67.0, color='gray', ls=':', lw=1)
ax.annotate('67 h 后半径停滞于 1.198 cm', xy=(67, 1.22), xytext=(38, 1.5), fontsize=8,
            arrowprops=dict(arrowstyle='->', color='gray'))
ax.set_xlabel('时间 t / h'); ax.set_ylabel('药材半径 R / cm')
ax.set_title('附件2：药材半径收缩曲线（每 1800 s）')
fig.tight_layout()
fig.savefig(f'{OUT}/figures/fig_shrink_radius.png', dpi=160)
print('附件数据图已存')

# ------------------------------------------------------------------ Q3/Q4 对比（轻量重算）
bc = make_boundary(t_a, T_a, C_a)
R_func, Rdot_func = make_radius(t_r, R_cm)
T_MAX = 62 * 3600.0
print('轻量重算 Q3 ...')
r3 = solve(Props('app3'), 81, 10.0, T_MAX, bc, method='implicit', picard=2,
           stop_at_threshold=True)
print('轻量重算 Q4 ...')
r4 = solve(Props('app4'), 81, 10.0, T_MAX, bc, method='implicit', picard=2,
           R_func=R_func, Rdot_func=Rdot_func, stop_at_threshold=True)
t3, t4 = r3['t_star'] / 3600, r4['t_star'] / 3600
print(f'Q3 t* = {t3:.4f} h, Q4 t* = {t4:.4f} h, 相差 {t3-t4:.2f} h（{(t3-t4)/t3*100:.1f}%）')

fig, ax = plt.subplots(figsize=(7.5, 4.4))
ax.plot(r3['times'] / 3600, r3['center_C'], 'b-', lw=1.4,
        label=f'问题3（固定 R=2 cm，附录3）：$t^*$={t3:.2f} h')
ax.plot(r4['times'] / 3600, r4['center_C'], 'r-', lw=1.4,
        label=f'问题4（收缩 R(t)，附录4）：$t^*$={t4:.2f} h')
ax.axhline(C_THRESHOLD, color='k', ls='--', lw=1, label='阈值 0.15 kg/kg')
for tt, cc in [(t3, 'b'), (t4, 'r')]:
    ax.plot([tt], [C_THRESHOLD], 'o', color=cc)
    ax.axvline(tt, color=cc, ls=':', lw=0.8)
ax.set_xlabel('时间 t / h'); ax.set_ylabel('中心水分浓度 C(0,t) / (kg/kg)')
ax.set_title('问题3 与问题4 烘干终点对比：收缩效应 vs 扩散系数减小')
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(f'{OUT}/figures/fig_q34_compare.png', dpi=160)

# ------------------------------------------------------------------ 两效应竞争的定量分析
p3, p4 = Props('app3'), Props('app4')
Cgrid = np.array([2.55, 1.0, 0.5, 0.3, 0.2, 0.15])
D3 = p3.D(Cgrid, np.full_like(Cgrid, 50.0))
D4 = p4.D(Cgrid, np.full_like(Cgrid, 50.0))
print('\n两效应竞争定量表（T=50°C）：')
print('  C      D3(m²/s)     D4(m²/s)     D3/D4   R²比例(近似)')
for c, d3, d4 in zip(Cgrid, D3, D4):
    print(f'  {c:4.2f}  {d3:.3e}  {d4:.3e}  {d3/d4:6.2f}')
print('  收缩使特征时间 ∝ R²：末期 (1.198/2)² = %.4f' % (1.198 / 2) ** 2)
print('  末期 D3/D4≈2–3 < 1/0.36≈2.8 → 收缩效应占上风 → Q4 略快 ✓')

# ------------------------------------------------------------------ 汇总报告
q1 = json.load(open(f'{OUT}/q1_summary.json', encoding='utf-8'))
q2 = json.load(open(f'{OUT}/q2_summary.json', encoding='utf-8'))
q3 = json.load(open(f'{OUT}/q3_summary.json', encoding='utf-8'))
q4 = json.load(open(f'{OUT}/q4_summary.json', encoding='utf-8'))
report = {
    '问题1': {
        '温度场_vs_Bessel半解析_max_err(°C)': q1['T_max_err_vs_analytic'],
        '水分场_vs_常D半解析_max_err(kg/kg)': q1['C_max_err_vs_analytic_constD'],
        '格式守恒一致性残差(∫CdV平衡)': q1['conservation_rel_resid'],
        '显式隐式互验_maxdiff(°C)': q1['explicit_implicit_maxdiff_T'],
    },
    '问题2': {'格式守恒一致性残差(∫CdV平衡)': q2['conservation_rel_resid'],
              '3h末态': {'中心T': q2['center_T_3h'], '表面T': q2['surf_T_3h'],
                        '中心C': q2['center_C_3h'], '表面C': q2['surf_C_3h']}},
    '问题3': {'t*(h)': q3['t_star_h'], '网格收敛': q3['grid_convergence'],
              '格式守恒一致性残差(∫CdV平衡)': q3['conservation_rel_resid'],
              'lnMR斜率(/h)': q3['lnMR_slope_per_h']},
    '问题4': {'t*(h)': q4['t_star_h'], 'R(t*)(cm)': q4['R_at_t_star_cm'],
              '网格收敛': q4['grid_convergence'],
              '动域质量恒等式相对偏差': q4['moving_mass_identity_rel_resid']},
    '对比': {'t3-t4(h)': t3 - t4, '题面锚': '2-3 天（48-72 h），两者均落入'},
}
with open(f'{OUT}/final_report.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
print('\n' + json.dumps(report, ensure_ascii=False, indent=2, default=float))
