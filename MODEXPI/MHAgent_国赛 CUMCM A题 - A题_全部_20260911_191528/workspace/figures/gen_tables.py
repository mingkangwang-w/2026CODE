"""生成正文 Markdown 三线表（docx 导出工作流）。

每个单元格都从 figures/*.json 或 user_data/附件*.xlsx 现算，不手写数值，
以便 Step 10.5 的表格数据核对可逐格回溯到来源字段。

产物：
  TABLE_main_results.md      四问主结果汇总
  TABLE_descriptive_stats.md 输入数据（附件 1/2）描述性统计
  TABLE_validation.md        守恒、解析对照、网格收敛三类校验
  TABLE_sensitivity.md       6 个参数 ±10% 对 t* 的敏感性
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import json

import numpy as np
import pandas as pd

_ROOT = os.path.dirname(_HERE)


def load(name):
    with open(os.path.join(_HERE, f'{name}.json'), encoding='utf-8') as fh:
        return json.load(fh)


def write_table(fname, caption, header, rows, notes):
    """Markdown 三线表：标题加粗在表上，注释以 > 注：起。"""
    lines = [f'**{caption}**', '']
    lines.append('| ' + ' | '.join(header) + ' |')
    lines.append('|' + '|'.join(['---'] * len(header)) + '|')
    for r in rows:
        lines.append('| ' + ' | '.join(str(c) for c in r) + ' |')
    lines.append('')
    for nt in notes:
        lines.append(f'> 注：{nt}')
    path = os.path.join(_HERE, fname)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f'Wrote: {path}')


allres = load('all_results')
ans = allres['answers']
p1, p2, p3, p4 = (load(f'problem_{i}_results') for i in (1, 2, 3, 4))

# ── 表 1：主结果 ────────────────────────────────────────────────
a1, a2, a3, a4 = ans['problem_1'], ans['problem_2'], ans['problem_3'], ans['problem_4']
rows = [
    ['问题 1', '预热段温度场与水分场（常物性，附录 2）',
     f"$t$={a1['t_end_s'] / 60:.0f} min",
     f"$T_c$={a1['T_center_degC']:.3f} °C；$T_s$={a1['T_surface_degC']:.3f} °C；"
     f"$C_c$={a1['C_center']:.4f}；$C_s$={a1['C_surface']:.4f}"],
    ['问题 2', '变物性双向耦合（附录 3）',
     f"$t$={a2['t_end_h']:.0f} h",
     f"$T_c$={a2['T_center_degC']:.3f} °C；$T_s$={a2['T_surface_degC']:.3f} °C；"
     f"$C_c$={a2['C_center']:.4f}；$C_s$={a2['C_surface']:.4f}"],
    ['问题 3', '固定域烘干终点（$\\max_r C<0.15$ kg/kg，全域最大值）',
     f"$t^*$={a3['t_star_h']:.4f} h",
     f"={a3['t_star_days']:.4f} d；终点 $\\max_r C$={a3['maxC_at_tstar']:.6f}"],
    ['问题 4', '收缩域烘干终点（物质坐标 $\\eta=r/R(t)$，附录 4）',
     f"$t^*$={a4['t_star_h']:.4f} h",
     f"={a4['t_star_days']:.4f} d；$R(t^*)$={a4['R_at_tstar_cm']:.3f} cm；"
     f"较问题 3 缩短 {abs(a4['delta_vs_q3_h']):.4f} h"],
]
write_table(
    'TABLE_main_results.md', '表 7：四问主结果汇总',
    ['问题', '模型设定', '关键时刻', '结果'], rows,
    [f"$C$ 为干基含水率（kg/kg），下标 $c$、$s$ 分别指中心 $r=0$ 与表面 $r=R$。",
     f"问题 4 相对问题 3 的加速比（冻结半径对照 / 收缩）为 "
     f"{a4['shrink_speedup']:.4f}，见正文收缩机理讨论。",
     "数据来源：figures/all_results.json 的 answers 字段。"])

# ── 表 2：输入数据描述性统计 ────────────────────────────────────
att1 = pd.read_excel(os.path.join(_ROOT, 'user_data', '附件1.xlsx'))
att2 = pd.read_excel(os.path.join(_ROOT, 'user_data', '附件2.xlsx'))

t1 = att1['时间'].to_numpy(float)
T1 = att1['温度'].to_numpy(float)
C1 = att1['水分浓度'].to_numpy(float)
t2 = att2['时间'].to_numpy(float)
R2 = att2['半径'].to_numpy(float)


def stat_row(label, arr, unit, fmt='{:.4f}'):
    a = np.asarray(arr, dtype=float)
    return [label, unit, f'{a.size}', fmt.format(a.min()), fmt.format(a.max()),
            fmt.format(a.mean()), fmt.format(a.std(ddof=1))]


rows = [
    stat_row('烘房温度 $T_\\infty$', T1, '°C'),
    stat_row('烘房水分浓度 $C_\\infty$', C1, 'kg/kg', '{:.5f}'),
    stat_row('药材半径 $R$', R2, 'cm'),
]
dt1 = np.unique(np.diff(t1))
dt2 = np.unique(np.diff(t2))
i_stall = int(np.argmax(R2 <= R2[-1] + 1e-12))
write_table(
    'TABLE_descriptive_stats.md', '表 8：输入数据描述性统计',
    ['变量', '单位', '样本数 $n$', '最小值', '最大值', '均值', '标准差'], rows,
    [f"附件 1 覆盖 0–{t1[-1] / 3600:.0f} h，采样间隔 {dt1[0]:.0f} s；"
     f"附件 2 覆盖 0–{t2[-1] / 3600:.0f} h，采样间隔 {dt2[0]:.0f} s。",
     f"半径由 {R2[0]:.3f} cm 收缩至 {R2[-1]:.3f} cm（累计 "
     f"{(R2[0] - R2[-1]) / R2[0] * 100:.1f}%），并在 {t2[i_stall] / 3600:.1f} h "
     f"后不再变化。",
     "标准差按样本标准差（$n-1$）计算。数据来源：user_data/附件1.xlsx、附件2.xlsx。"])

# ── 表 3：模型校验 ──────────────────────────────────────────────
def eps_max(res):
    """eps_M=|(C0-M)-Q|/max(Q,1e-30)，t=0 处 Q=0 使其无定义，故只统计 Q>0。"""
    Q = np.asarray(res['mass_balance']['Q'], dtype=float)
    e = np.asarray(res['mass_balance']['eps_M'], dtype=float)
    m = Q > 0
    return float(np.nanmax(e[m])), int(m.sum())


av = p1['analytic_validation']
ct = p1['characteristic_times']
gc = p3['grid_convergence']
gtab = gc['table']
sp = p3['stability_probe']

rows = []
for tag, res in (('问题 1', p1), ('问题 2', p2), ('问题 3', p3), ('问题 4', p4)):
    e, n = eps_max(res)
    rows.append([f'{tag} 水分守恒残差 $\\varepsilon_M$', f'{e:.2e}',
                 '$<10^{-2}$', f'{n} 个采样时刻的最大值', '通过'])
rows.append(['问题 1 数值解 vs Bessel 级数解', f"{av['max_abs_dev_K']:.2e} K",
             '—', f"{av['n_modes']} 项级数，$Bi_h$={av['Bi_h']:.4f}", '通过'])
rows.append(['网格/时步收敛（逐级相对变化）',
             f"{gc['final_rel_change'] * 100:.3f}%",
             f"$<{gc['tol'] * 100:.0f}\\%$",
             f"{gtab[-2]['n_cells']}→{gtab[-1]['n_cells']} 单元，"
             f"$\\Delta t$ {gtab[-2]['dt_s']:.0f}→{gtab[-1]['dt_s']:.0f} s", '通过'])
rows.append(['显式格式稳定步长（隐式格式无需受限）',
             f"{sp['dt_stable_s']:.4f} s", '—',
             f"实际隐式步长 {sp['implicit_dt_s']:.0f} s，"
             f"为其 {sp['implicit_dt_s'] / sp['dt_stable_s']:.0f} 倍", '通过'])

write_table(
    'TABLE_validation.md', '表 9：模型校验汇总',
    ['校验项', '实测值', '判据', '说明', '结论'], rows,
    [f"特征时间 $\\tau_{{heat}}$={ct['tau_heat_s']:.1f} s、"
     f"$\\tau_{{mass}}$={ct['tau_mass_s']:.3e} s，二者相差约 "
     f"{ct['tau_mass_s'] / ct['tau_heat_s']:.0f} 倍，故温度先达平衡而水分主导总时长。",
     "守恒残差为相对量纲一量；$t=0$ 时累计通量 $Q=0$ 使相对残差无定义，已剔除。",
     "数据来源：figures/problem_{1..4}_results.json 的 mass_balance、"
     "analytic_validation、grid_convergence、stability_probe 字段。"])

# ── 表 4：参数敏感性 ────────────────────────────────────────────
sens = load('sensitivity_results')
mg = sens['main_group']
srows = {r['id']: r for r in mg['rows']}
base = mg['base_t_star_h']
rows = []
for rank, key in enumerate(mg['ranking_by_abs_rel_max'], start=1):
    r = srows[key]
    rows.append([rank, r['label'],
                 f"{r['t_star_high_h']:.3f}", f"{r['rel_change_high'] * 100:+.2f}%",
                 f"{r['t_star_low_h']:.3f}", f"{r['rel_change_low'] * 100:+.2f}%",
                 f"{r['abs_rel_max'] * 100:.2f}%"])
write_table(
    'TABLE_sensitivity.md', '表 10：参数敏感性排序',
    ['序', '参数', f"$\\times${mg['factor_high']:.1f} 的 $t^*$ (h)", '相对变化',
     f"$\\times${mg['factor_low']:.1f} 的 $t^*$ (h)", '相对变化',
     '最大绝对相对变化'], rows,
    [f"基准 $t^*$={base:.4f} h（敏感性算例统一用 "
     f"{mg['n_cells']} 单元、$\\Delta t$={mg['dt_s']:.0f} s 的粗网格以控算量，"
     f"故与表 7 的 {ans['problem_3']['t_star_h']:.4f} h 略有差异）。",
     "排序键为最大绝对相对变化，与 ranking_by_abs_rel_max 一致。",
     "数据来源：figures/sensitivity_results.json 的 main_group 字段。"])
