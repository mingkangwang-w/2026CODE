# 论文数据真实性核对清单（数据原料）

**模式**: DOCX
**JSON 源**: all_results.json, problem_1_results.json, problem_2_results.json, problem_3_results.json, problem_4_results.json, sensitivity_results.json
**JSON 数据条目**: 1694
**已生成的 TABLE 文件**: 4 个

---

## 自检步骤（请你按以下顺序执行）

**重要原则**：本工作区的实验/分析阶段已经把所有真实数据存到 `figures/*.json`，
并由 paper-figure 步骤渲染成 `figures/TABLE_*.tex|md`。
**论文数据应能追溯到这些文件或题设，并允许有明确计算依据的派生量、单位换算及舍入。未直接匹配不等于编造。**

### 第 1 步：识别论文中的「数据性数字」

打开你的论文文件，逐章扫描：

- ✅ **需要核对的**：表格里的所有单元格数字、正文里引用实验结果的数字（如 "RMSE 达到 0.023"、"准确率 94%"、"最优解 295.83"、"R² 为 0.94"）
- ⏭️ **不需要核对的**（叙述里自然出现的数字）：
    - 章节编号、列号、引用 [1][2,3]、图编号「图 3-1」
    - 年份「2024 年」、日期「3 月 5 日」
    - 公式中的常数（在 `$...$` 或 `$$...$$` 内）
    - 算法描述里的步骤数「分 5 步」
    - 文献综述里别人论文的数字

### 第 2 步：对每个「数据性数字」核对

对照下方的 JSON 数据清单和 TABLE 文件全文：

1. **能在数据清单/TABLE 文件里找到完全一致的数字** → ✅ 真实，跳过
2. **数据清单里有但论文写错了**（如 RMSE 真实是 0.023，论文写的 0.999） → 改正文，**禁止反向操作**（禁止改 JSON）
3. **数据清单里没有这个数字** → 两种可能：
   - **AI 编造**（最常见）→ 删除该说法或从清单中找正确数据补充
   - **从其他来源算出来的合理派生量**（如百分比 = 子集/总数 ×100）→ 检查派生公式是否合理

### 第 3 步：表格优先用预生成的 TABLE 文件

如果论文里手抄了表格内容，**优先改成** `cat figures/TABLE_*.md >> paper/main.md` 直接嵌入（已经从 JSON 渲染好，不会出错）。

### 第 4 步：自检完成后登记独立回执

后置自检使用本轮任务指定的 `.mh/quality/data-review-ack-*.txt` 和确认值；不要将确认值写入论文。
如果本轮写作上下文仍明确要求兼容旧注释，必须在最终编译之前完成；编译之后不得为登记状态再次改源码。
没有本轮确认值时不要复制旧回执或自行编造；系统只接受与当前内容绑定的有效核对。

**判断原则**：
- 以 JSON 为准修论文，禁止反向修 JSON
- 不必把 JSON 中的每个数字都搬到论文里——只关心论文里出现的数字是否真实
- 不确定某个数字是不是数据 → 当成数据核对一遍，确认能找到来源就行

---

## 图表来源与论断对应（并入本次核对，不启动额外模型轮次）

数字出现过不等于支持当前论断。逐图核对数据所属问题、场景、参数、样本量和统计量；
跨问题引用允许，但必须解释可迁移的结论。一个概率水平的收敛曲线不能直接证明另一个临界点可靠。
下面仅列静态识别的真实文件引用，不代表已经验证数学结论；动态路径请按生成脚本补查。

| 图 | 生成脚本 | 可观察的数据来源 |
|---|---|---|
| fig_D_landscape | figures/gen_fig_D_landscape.py | 动态来源，需按脚本定位 |
| fig_grid_convergence | figures/gen_fig_grid_convergence.py | 动态来源，需按脚本定位 |
| fig_oven_input | figures/gen_fig_oven_input.py | 动态来源，需按脚本定位 |
| fig_property_laws | figures/gen_fig_property_laws.py | 动态来源，需按脚本定位 |
| fig_q1_analytic_validation | figures/gen_fig_q1_analytic_validation.py | 动态来源，需按脚本定位 |
| fig_q1_moist_field | figures/gen_fig_q1_moist_field.py | 动态来源，需按脚本定位 |
| fig_q1_moist_profiles | figures/gen_fig_q1_moist_profiles.py | 动态来源，需按脚本定位 |
| fig_q1_temp_field | figures/gen_fig_q1_temp_field.py | 动态来源，需按脚本定位 |
| fig_q1_temp_profiles | figures/gen_fig_q1_temp_profiles.py | 动态来源，需按脚本定位 |
| fig_q2_flux_balance | figures/gen_fig_q2_flux_balance.py | 动态来源，需按脚本定位 |
| fig_q2_moist_ridgeline | figures/gen_fig_q2_moist_ridgeline.py | 动态来源，需按脚本定位 |
| fig_q2_stage_transition | figures/gen_fig_q2_stage_transition.py | 动态来源，需按脚本定位 |
| fig_q34_compare_dumbbell | figures/gen_fig_q34_compare_dumbbell.py | 动态来源，需按脚本定位 |
| fig_q3_center_decay | figures/gen_fig_q3_center_decay.py | 动态来源，需按脚本定位 |
| fig_q3_hovmoller | figures/gen_fig_q3_hovmoller.py | 动态来源，需按脚本定位 |
| fig_q3_threshold_contour | figures/gen_fig_q3_threshold_contour.py | 动态来源，需按脚本定位 |
| fig_q4_moving_domain_heatmap | figures/gen_fig_q4_moving_domain_heatmap.py | 动态来源，需按脚本定位 |
| fig_q4_shrink_validation | figures/gen_fig_q4_shrink_validation.py | 动态来源，需按脚本定位 |
| fig_sensitivity_tornado | figures/gen_fig_sensitivity_tornado.py | 动态来源，需按脚本定位 |
| fig_shrink_radius | figures/gen_fig_shrink_radius.py | 动态来源，需按脚本定位 |
| tables | figures/gen_tables.py | 动态来源，需按脚本定位 |

## JSON 真实数据清单

### `all_results.json`（268 条）

| 数据路径 | 数值 |
|---|---|
| `study` | `CUMCM 2026A 药材的烘干问题` |
| `n_subproblems` | 4 |
| `entry_point` | `code/main.py` |
| `note` | `场量数组留在 figures/problem_N_results.json；本文件登记标量结论、§10⑦ 探针...` |
| `answers.problem_1.t_end_s` | 1800 |
| `answers.problem_1.T_center_degC` | 33.5756 |
| `answers.problem_1.T_surface_degC` | 36.7857 |
| `answers.problem_1.C_center` | 2.54999 |
| `answers.problem_1.C_surface` | 1.51036 |
| `answers.problem_2.t_end_h` | 3 |
| `answers.problem_2.T_center_degC` | 49.8495 |
| `answers.problem_2.T_surface_degC` | 49.9664 |
| `answers.problem_2.C_center` | 1.76619 |
| `answers.problem_2.C_surface` | 1.00811 |
| `answers.problem_3.t_star_h` | 57.2745 |
| `answers.problem_3.t_star_days` | 2.38644 |
| `answers.problem_3.criterion` | `max_r C < 0.15` |
| `answers.problem_3.maxC_at_tstar` | 0.149999 |
| `answers.problem_4.t_star_h` | 51.0444 |
| `answers.problem_4.t_star_days` | 2.12685 |
| `answers.problem_4.R_at_tstar_cm` | 1.2 |
| `answers.problem_4.delta_vs_q3_h` | -6.2301 |
| `answers.problem_4.shrink_speedup` | 2.53789 |
| `problems[0].problem` | 1 |
| `problems[0].title` | `预热平衡阶段的温度场与水分场` |
| `problems[0].method` | `守恒型有限体积 + 向后 Euler/Picard；附录 2 常物性` |
| `problems[0].property_group` | `附录2 常物性 rho=820, cp=2600, k=0.36; D = 7e-9*exp(-0.89/C)` |
| `problems[0].grid.n_cells` | 80 |
| `problems[0].grid.dt_s` | 0.25 |
| `problems[0].grid.dr_cm` | 0.025 |
| `problems[0].grid.out_dt_s` | 1 |
| `problems[0].grid.out_dr_cm` | 0.1 |
| `problems[0].grid.n_steps` | 7200 |
| `problems[0].summary.T_center_1800s` | 33.5756 |
| `problems[0].summary.T_surface_1800s` | 36.7857 |
| `problems[0].summary.C_center_1800s` | 2.54999 |
| `problems[0].summary.C_surface_1800s` | 1.51036 |
| `problems[0].summary.analytic_gap_K` | 0.002062 |
| `problems[0].eps_M` | 4.285e-14 |
| `problems[1].problem` | 2 |
| `problems[1].title` | `全过程变物性双向强耦合模型（输出截取前 3 h）` |
| `problems[1].method` | `守恒型有限体积 + 向后 Euler/Picard；附录 3 变物性双向耦合` |
| `problems[1].property_group` | `附录3 变物性 rho=650+128*C; cp=1450+2736*C/(C+1); k=0.21+0.3...` |
| `problems[1].grid.n_cells` | 80 |
| `problems[1].grid.dt_s` | 0.5 |
| `problems[1].grid.dr_cm` | 0.025 |
| `problems[1].grid.out_dt_s` | 1 |
| `problems[1].grid.out_dr_cm` | 0.1 |
| `problems[1].grid.n_steps` | 21600 |
| `problems[1].summary.T_center_3h` | 49.8495 |
| `problems[1].summary.T_surface_3h` | 49.9664 |
| `problems[1].summary.C_center_3h` | 1.76619 |
| `problems[1].summary.C_surface_3h` | 1.00811 |
| `problems[1].summary.conservation_degradation_factor` | 1.75e+12 |
| `problems[1].eps_M` | 2.339e-14 |
| `problems[2].problem` | 3 |
| `problems[2].title` | `烘干终点判定与总烘干时长` |
| `problems[2].method` | `守恒型有限体积 + 向后 Euler/Picard；阈值首达 + 线性插值细化` |
| `problems[2].property_group` | `附录3 变物性 rho=650+128*C; cp=1450+2736*C/(C+1); k=0.21+0.3...` |
| `problems[2].grid.n_cells` | 80 |
| `problems[2].grid.dt_s` | 5 |
| `problems[2].grid.dr_cm` | 0.025 |
| `problems[2].grid.out_dt_s` | 60 |
| `problems[2].grid.out_dr_cm` | 0.1 |
| `problems[2].grid.n_steps` | 41238 |
| `problems[2].summary.t_star_h` | 57.2745 |
| `problems[2].summary.grid_final_rel_change` | 0.004519 |
| `problems[2].summary.maxC_at_tstar` | 0.149999 |
| `problems[2].summary.C_center_6h` | 1.01711 |
| `problems[2].summary.t_star_mean_criterion_h` | 35.6427 |
| `problems[2].summary.t_star_product_exponent_h` | 16.4735 |
| `problems[2].eps_M` | 1.556e-14 |
| `problems[3].problem` | 4 |
| `problems[3].title` | `收缩动边界下的烘干时长（附件 2 的 R(t) + 附录 4 物性，物质坐标）` |
| `problems[3].method` | `物质坐标 eta=r/R(t) + 守恒型有限体积 + 向后 Euler + Picard 强耦合；扩散项乘 ...` |
| `problems[3].property_group` | `附录4 变物性 rho=760+90*C; cp=1850+2150*C/(C+1); k=0.12+0.20...` |
| `problems[3].grid.n_cells` | 80 |
| `problems[3].grid.dt_s` | 5 |
| `problems[3].grid.eta_span` | 1 |
| `problems[3].grid.out_dt_s` | 60 |
| `problems[3].grid.picard_rounds_max` | 3 |
| `problems[3].summary.t_star_h` | 51.0444 |
| `problems[3].summary.R_at_tstar_cm` | 1.2 |
| `problems[3].summary.shrink_speedup` | 2.53789 |
| `problems[3].summary.t_star_q3_h` | 57.2745 |
| `problems[3].summary.D_ratio_app4_over_app3` | 0.185603 |
| `problems[3].eps_M` | 9.149e-14 |
| `logic_probes.bounds[0].id` | `bd_tstar_q3_range` |
| `logic_probes.bounds[0].quantity` | `t_star_Q3` |
| `logic_probes.bounds[0].lo` | 20 |
| `logic_probes.bounds[0].hi` | 200 |
| `logic_probes.bounds[0].unit` | `h` |
| `logic_probes.bounds[0].expected` | 57.2745 |
| `logic_probes.bounds[0].tol` | 0.6 |
| `logic_probes.bounds[0].value` | 57.2745 |
| `logic_probes.bounds[1].id` | `bd_tstar_q4_range` |
| `logic_probes.bounds[1].quantity` | `t_star_Q4` |
| `logic_probes.bounds[1].lo` | 20 |
| `logic_probes.bounds[1].hi` | 200 |
| `logic_probes.bounds[1].unit` | `h` |
| `logic_probes.bounds[1].expected` | 51.0444 |
| `logic_probes.bounds[1].tol` | 0.3 |
| `logic_probes.bounds[1].value` | 51.0444 |
| `logic_probes.bounds[1].delta_vs_q3` | -6.2301 |
| `logic_probes.bounds[2].id` | `bd_mass_residual` |
| `logic_probes.bounds[2].quantity` | `eps_M` |
| `logic_probes.bounds[2].lo` | 0 |
| `logic_probes.bounds[2].hi` | 0.01 |
| `logic_probes.bounds[2].unit` | `1` |
| `logic_probes.bounds[2].expected` | 1e-14 |
| `logic_probes.bounds[2].tol` | 1e-06 |
| `logic_probes.bounds[2].values[0]` | 4.285e-14 |
| `logic_probes.bounds[2].values[1]` | 2.339e-14 |
| `logic_probes.bounds[2].values[2]` | 1.556e-14 |
| `logic_probes.bounds[2].values[3]` | 9.149e-14 |
| `logic_probes.bounds[2].value` | 9.149e-14 |
| `logic_probes.bounds[6].id` | `bd_shrink_pred_error` |
| `logic_probes.bounds[6].quantity` | `relative error of forward-predicted R_end` |
| `logic_probes.bounds[6].lo` | 0 |
| `logic_probes.bounds[6].hi` | 0.08 |
| `logic_probes.bounds[6].unit` | `1` |
| `logic_probes.bounds[6].expected` | 0.0329 |
| `logic_probes.bounds[6].tol` | 0.005 |
| `logic_probes.bounds[6].values[0]` | 0.03293 |
| `logic_probes.bounds[6].values[1]` | 0.107342 |
| `logic_probes.bounds[6].values[2]` | 0.212193 |
| `logic_probes.bounds[6].value` | 0.03293 |
| `logic_probes.bounds[6].combos[0]` | `附录4+仅径向` |
| `logic_probes.bounds[6].combos[1]` | `附录3+仅径向` |
| `logic_probes.bounds[6].combos[2]` | `附录4+各向同性` |
| `logic_probes.bounds[...]` | `<3 项省略>` |
| `logic_probes.monotonic[0].id` | `mono_tstar_in_D` |
| `logic_probes.monotonic[0].more` | `D_prefactor` |
| `logic_probes.monotonic[0].then` | `t_star` |
| `logic_probes.monotonic[0].observed_sign` | -1 |
| `logic_probes.monotonic[0].expect_sign` | -1 |
| `logic_probes.monotonic[0].t_star_high_h` | 52.0207 |
| `logic_probes.monotonic[0].t_star_low_h` | 61.9872 |
| `logic_probes.monotonic[0].base_t_star_h` | 56.495 |
| `logic_probes.monotonic[1].id` | `mono_tstar_in_R0` |
| `logic_probes.monotonic[1].more` | `R0` |
| `logic_probes.monotonic[1].then` | `t_star` |
| `logic_probes.monotonic[1].observed_sign` | 1 |
| `logic_probes.monotonic[1].expect_sign` | 1 |
| `logic_probes.monotonic[1].t_star_high_h` | 67.5694 |
| `logic_probes.monotonic[1].t_star_low_h` | 46.4273 |
| `logic_probes.monotonic[1].base_t_star_h` | 56.495 |
| `logic_probes.report.rows[0].id` | `bd_tstar_q3_range` |
| `logic_probes.report.rows[0].value` | 57.2745 |
| `logic_probes.report.rows[0].dev_vs_expected` | 0 |
| `logic_probes.report.rows[0].tol` | 0.6 |
| `logic_probes.report.rows[0].range_scope` | `all` |
| `logic_probes.report.rows[0].in_range` | 1 |
| `logic_probes.report.rows[1].id` | `bd_tstar_q4_range` |
| `logic_probes.report.rows[1].value` | 51.0444 |
| `logic_probes.report.rows[1].dev_vs_expected` | 0 |
| `logic_probes.report.rows[1].tol` | 0.3 |
| `logic_probes.report.rows[1].range_scope` | `all` |
| `logic_probes.report.rows[1].in_range` | 1 |
| `logic_probes.report.rows[2].id` | `bd_mass_residual` |
| `logic_probes.report.rows[2].value` | 9.149e-14 |
| `logic_probes.report.rows[2].dev_vs_expected` | 8.149e-14 |
| `logic_probes.report.rows[2].tol` | 1e-06 |
| `logic_probes.report.rows[2].range_scope` | `all` |
| `logic_probes.report.rows[2].in_range` | 1 |
| `logic_probes.report.rows[6].id` | `bd_shrink_pred_error` |
| `logic_probes.report.rows[6].value` | 0.03293 |
| `logic_probes.report.rows[6].dev_vs_expected` | 3.024e-05 |
| `logic_probes.report.rows[6].tol` | 0.005 |
| `logic_probes.report.rows[6].range_scope` | `primary_plus_counterexamples` |
| `logic_probes.report.rows[6].in_range` | 1 |
| `logic_probes.report.rows[...]` | `<3 项省略>` |
| `logic_probes.report.n_bounds` | 7 |
| `sensitivity.ranking[0]` | `arrhenius_exp_T` |
| `sensitivity.ranking[1]` | `moisture_exp_C` |
| `sensitivity.ranking[2]` | `radius_R0` |
| `sensitivity.ranking[5]` | `h_conv` |
| `sensitivity.ranking[...]` | `<2 项省略>` |
| `sensitivity.base_t_star_h` | 56.495 |
| `sensitivity.rows[0].id` | `arrhenius_exp_T` |
| `sensitivity.rows[0].label` | `Arrhenius 指数系数 3850` |
| `sensitivity.rows[0].t_star_high_h` | 171.929 |
| `sensitivity.rows[0].t_star_low_h` | 23.1085 |
| `sensitivity.rows[0].rel_change_high` | 2.04326 |
| `sensitivity.rows[0].rel_change_low` | -0.590963 |
| `sensitivity.rows[0].abs_rel_max` | 2.04326 |
| `sensitivity.rows[1].id` | `moisture_exp_C` |
| `sensitivity.rows[1].label` | `含水率指数系数 a=0.45` |
| `sensitivity.rows[1].t_star_high_h` | 71.6333 |
| `sensitivity.rows[1].t_star_low_h` | 45.1089 |
| `sensitivity.rows[1].rel_change_high` | 0.267958 |
| `sensitivity.rows[1].rel_change_low` | -0.201542 |
| `sensitivity.rows[1].abs_rel_max` | 0.267958 |
| `sensitivity.rows[2].id` | `radius_R0` |
| `sensitivity.rows[2].label` | `初始半径 R0` |
| `sensitivity.rows[2].t_star_high_h` | 67.5694 |
| `sensitivity.rows[2].t_star_low_h` | 46.4273 |
| `sensitivity.rows[2].rel_change_high` | 0.196023 |
| `sensitivity.rows[2].rel_change_low` | -0.178205 |
| `sensitivity.rows[2].abs_rel_max` | 0.196023 |
| `sensitivity.rows[5].id` | `h_conv` |
| `sensitivity.rows[5].label` | `对流换热系数 h` |
| `sensitivity.rows[5].t_star_high_h` | 56.4879 |
| `sensitivity.rows[5].t_star_low_h` | 56.5037 |
| `sensitivity.rows[5].rel_change_high` | -0.000126 |
| `sensitivity.rows[5].rel_change_low` | 0.000154 |
| `sensitivity.rows[5].abs_rel_max` | 0.000154 |
| `sensitivity.rows[...]` | `<2 项省略>` |
| `sensitivity.conclusion` | `t* 的不确定性由 D 的两个指数系数与几何尺寸主导（最敏感项相对变化 2.0433），对两个对流系数最不敏感...` |
| `cross_problem_ledger.n_overwritten` | 21 |
| `cross_problem_ledger.n_added` | 5 |
| `cross_problem_ledger.observed_provenance` | `computed` |
| `cross_problem_ledger.measured.Q1.初始含水率_kgkg` | 2.55 |
| `cross_problem_ledger.measured.Q1.水分质量守恒残差` | 4.285e-14 |
| `cross_problem_ledger.measured.Q1.中心含水率_1800s` | 2.54999 |
| `cross_problem_ledger.measured.Q2.初始含水率_kgkg` | 2.55 |
| `cross_problem_ledger.measured.Q2.水分质量守恒残差` | 2.339e-14 |
| `cross_problem_ledger.measured.Q2.中心含水率_1800s` | 2.54993 |
| `cross_problem_ledger.measured.Q2.三小时末全场温差_degC` | 0.116929 |
| `cross_problem_ledger.measured.Q2.三小时末中心含水率` | 1.76619 |
| `cross_problem_ledger.measured.Q2.三小时末表面含水率` | 1.00811 |
| `cross_problem_ledger.measured.Q2.环境温度平台值_degC` | 49.9989 |
| `cross_problem_ledger.measured.Q3.初始含水率_kgkg` | 2.55 |
| `cross_problem_ledger.measured.Q3.水分质量守恒残差` | 1.556e-14 |
| `cross_problem_ledger.measured.Q3.三小时末全场温差_degC` | 0.117116 |
| `cross_problem_ledger.measured.Q3.三小时末中心含水率` | 1.76628 |
| `cross_problem_ledger.measured.Q3.三小时末表面含水率` | 1.00816 |
| `cross_problem_ledger.measured.Q3.环境温度平台值_degC` | 49.9989 |
| `cross_problem_ledger.measured.Q3.烘干结束时间_h` | 57.2745 |
| `cross_problem_ledger.measured.Q3.终点最大含水率` | 0.149999 |
| `cross_problem_ledger.measured.Q3.终点药材半径_cm` | 2 |
| `cross_problem_ledger.measured.Q4.初始含水率_kgkg` | 2.55 |
| `cross_problem_ledger.measured.Q4.水分质量守恒残差` | 9.149e-14 |
| `cross_problem_ledger.measured.Q4.物质坐标守恒残差` | 9.149e-14 |
| `cross_problem_ledger.measured.Q4.环境温度平台值_degC` | 49.9989 |
| `cross_problem_ledger.measured.Q4.烘干结束时间_h` | 51.0444 |
| `cross_problem_ledger.measured.Q4.终点最大含水率` | 0.15 |
| `cross_problem_ledger.measured.Q4.终点药材半径_cm` | 1.2 |
| `cross_problem_ledger.imposes_check.n_conditions` | 29 |
| `cross_problem_ledger.imposes_check.n_pairs` | 18 |
| `cross_problem_ledger.imposes_check.rows[0].from` | `Q1` |
| `cross_problem_ledger.imposes_check.rows[0].to` | `Q1` |
| `cross_problem_ledger.imposes_check.rows[0].quantity` | `初始含水率_kgkg` |
| `cross_problem_ledger.imposes_check.rows[0].side` | `must_le` |
| `cross_problem_ledger.imposes_check.rows[0].bound` | 2.55 |
| `cross_problem_ledger.imposes_check.rows[0].observed` | 2.55 |
| `cross_problem_ledger.imposes_check.rows[1].from` | `Q1` |
| `cross_problem_ledger.imposes_check.rows[1].to` | `Q1` |
| `cross_problem_ledger.imposes_check.rows[1].quantity` | `初始含水率_kgkg` |
| `cross_problem_ledger.imposes_check.rows[1].side` | `must_ge` |
| `cross_problem_ledger.imposes_check.rows[1].bound` | 2.55 |
| `cross_problem_ledger.imposes_check.rows[1].observed` | 2.55 |
| `cross_problem_ledger.imposes_check.rows[2].from` | `Q1` |
| `cross_problem_ledger.imposes_check.rows[2].to` | `Q2` |
| `cross_problem_ledger.imposes_check.rows[2].quantity` | `初始含水率_kgkg` |
| `cross_problem_ledger.imposes_check.rows[2].side` | `must_le` |
| `cross_problem_ledger.imposes_check.rows[2].bound` | 2.55 |
| `cross_problem_ledger.imposes_check.rows[2].observed` | 2.55 |
| `cross_problem_ledger.imposes_check.rows[28].from` | `Q4` |
| `cross_problem_ledger.imposes_check.rows[28].to` | `Q4` |
| `cross_problem_ledger.imposes_check.rows[28].quantity` | `物质坐标守恒残差` |
| `cross_problem_ledger.imposes_check.rows[28].side` | `must_le` |
| `cross_problem_ledger.imposes_check.rows[28].bound` | 1e-06 |
| `cross_problem_ledger.imposes_check.rows[28].observed` | 9.149e-14 |
| `cross_problem_ledger.imposes_check.rows[...]` | `<25 项省略>` |
| `cross_problem_ledger.imposes_check.all_satisfied` | 1 |
| `cross_problem_ledger.imposes_check.checker_note` | `_utils/cross_problem_check.py 不在本工作区的 _utils/ 下，本函数按台账 ...` |
| `runtime_s` | 200.11 |

### `problem_1_results.json`（316 条）

| 数据路径 | 数值 |
|---|---|
| `problem` | 1 |
| `title` | `预热平衡阶段的温度场与水分场` |
| `method` | `守恒型有限体积 + 向后 Euler/Picard；附录 2 常物性` |
| `property_group` | `附录2 常物性 rho=820, cp=2600, k=0.36; D = 7e-9*exp(-0.89/C)` |
| `grid.n_cells` | 80 |
| `grid.dt_s` | 0.25 |
| `grid.dr_cm` | 0.025 |
| `grid.out_dt_s` | 1 |
| `grid.out_dr_cm` | 0.1 |
| `grid.n_steps` | 7200 |
| `output_radii_cm[0]` | 0 |
| `output_radii_cm[1]` | 0.1 |
| `output_radii_cm[2]` | 0.2 |
| `output_radii_cm[20]` | 2 |
| `output_radii_cm[...]` | `<17 项省略>` |
| `paper_tables.table1_temperature[0].t_s` | 100 |
| `paper_tables.table1_temperature[0].values[0]` | 28.0001 |
| `paper_tables.table1_temperature[0].values[1]` | 28.0004 |
| `paper_tables.table1_temperature[0].values[2]` | 28.0041 |
| `paper_tables.table1_temperature[0].values[3]` | 28.0328 |
| `paper_tables.table1_temperature[0].values[4]` | 28.1801 |
| `paper_tables.table1_temperature[1].t_s` | 300 |
| `paper_tables.table1_temperature[1].values[0]` | 28.041 |
| `paper_tables.table1_temperature[1].values[1]` | 28.0637 |
| `paper_tables.table1_temperature[1].values[2]` | 28.1516 |
| `paper_tables.table1_temperature[1].values[3]` | 28.3683 |
| `paper_tables.table1_temperature[1].values[4]` | 28.849 |
| `paper_tables.table1_temperature[2].t_s` | 600 |
| `paper_tables.table1_temperature[2].values[0]` | 28.4538 |
| `paper_tables.table1_temperature[2].values[1]` | 28.5364 |
| `paper_tables.table1_temperature[2].values[2]` | 28.8043 |
| `paper_tables.table1_temperature[2].values[3]` | 29.3162 |
| `paper_tables.table1_temperature[2].values[4]` | 30.1654 |
| `paper_tables.table1_temperature[6].t_s` | 1800 |
| `paper_tables.table1_temperature[6].values[0]` | 33.5756 |
| `paper_tables.table1_temperature[6].values[1]` | 33.7723 |
| `paper_tables.table1_temperature[6].values[2]` | 34.3644 |
| `paper_tables.table1_temperature[6].values[3]` | 35.3624 |
| `paper_tables.table1_temperature[6].values[4]` | 36.7857 |
| `paper_tables.table1_temperature[...]` | `<3 项省略>` |
| `paper_tables.table2_moisture[0].t_s` | 100 |
| `paper_tables.table2_moisture[0].values[0]` | 2.55 |
| `paper_tables.table2_moisture[0].values[1]` | 2.55 |
| `paper_tables.table2_moisture[0].values[2]` | 2.55 |
| `paper_tables.table2_moisture[0].values[3]` | 2.55 |
| `paper_tables.table2_moisture[0].values[4]` | 2.249 |
| `paper_tables.table2_moisture[1].t_s` | 300 |
| `paper_tables.table2_moisture[1].values[0]` | 2.55 |
| `paper_tables.table2_moisture[1].values[1]` | 2.55 |
| `paper_tables.table2_moisture[1].values[2]` | 2.55 |
| `paper_tables.table2_moisture[1].values[3]` | 2.5492 |
| `paper_tables.table2_moisture[1].values[4]` | 2.0517 |
| `paper_tables.table2_moisture[2].t_s` | 600 |
| `paper_tables.table2_moisture[2].values[0]` | 2.55 |
| `paper_tables.table2_moisture[2].values[1]` | 2.55 |
| `paper_tables.table2_moisture[2].values[2]` | 2.55 |
| `paper_tables.table2_moisture[2].values[3]` | 2.5352 |
| `paper_tables.table2_moisture[2].values[4]` | 1.8775 |
| `paper_tables.table2_moisture[6].t_s` | 1800 |
| `paper_tables.table2_moisture[6].values[0]` | 2.55 |
| `paper_tables.table2_moisture[6].values[1]` | 2.5497 |
| `paper_tables.table2_moisture[6].values[2]` | 2.5382 |
| `paper_tables.table2_moisture[6].values[3]` | 2.3755 |
| `paper_tables.table2_moisture[6].values[4]` | 1.5104 |
| `paper_tables.table2_moisture[...]` | `<3 项省略>` |
| `table_radii_cm[0]` | 0 |
| `table_radii_cm[1]` | 0.5 |
| `table_radii_cm[2]` | 1 |
| `table_radii_cm[3]` | 1.5 |
| `table_radii_cm[4]` | 2 |
| `center_series.times_s[0]` | 0 |
| `center_series.times_s[1]` | 1 |
| `center_series.times_s[2]` | 2 |
| `center_series.times_s[1800]` | 1800 |
| `center_series.times_s[...]` | `<1797 项省略>` |
| `center_series.T[0]` | 28 |
| `center_series.T[1]` | 28 |
| `center_series.T[2]` | 28 |
| `center_series.T[1800]` | 33.5756 |
| `center_series.T[...]` | `<1797 项省略>` |
| `center_series.C[0]` | 2.55 |
| `center_series.C[1]` | 2.55 |
| `center_series.C[2]` | 2.55 |
| `center_series.C[1800]` | 2.54999 |
| `center_series.C[...]` | `<1797 项省略>` |
| `surface_series.times_s[0]` | 0 |
| `surface_series.times_s[1]` | 1 |
| `surface_series.times_s[2]` | 2 |
| `surface_series.times_s[1800]` | 1800 |
| `surface_series.times_s[...]` | `<1797 项省略>` |
| `surface_series.T[0]` | 28 |
| `surface_series.T[1]` | 28.0002 |
| `surface_series.T[2]` | 28.0005 |
| `surface_series.T[1800]` | 36.7857 |
| `surface_series.T[...]` | `<1797 项省略>` |
| `surface_series.C[0]` | 2.55 |
| `surface_series.C[1]` | 2.53524 |
| `surface_series.C[2]` | 2.52248 |
| `surface_series.C[1800]` | 1.51036 |
| `surface_series.C[...]` | `<1797 项省略>` |
| `env_series.times_s[0]` | 0 |
| `env_series.times_s[1]` | 1 |
| `env_series.times_s[2]` | 2 |
| `env_series.times_s[1800]` | 1800 |
| `env_series.times_s[...]` | `<1797 项省略>` |
| `env_series.T_inf[0]` | 28 |
| `env_series.T_inf[1]` | 28.0088 |
| `env_series.T_inf[2]` | 28.0176 |
| `env_series.T_inf[1800]` | 41.513 |
| `env_series.T_inf[...]` | `<1797 项省略>` |
| `env_series.C_inf[0]` | 0.01963 |
| `env_series.C_inf[1]` | 0.019637 |
| `env_series.C_inf[2]` | 0.019643 |
| `env_series.C_inf[1800]` | 0.03307 |
| `env_series.C_inf[...]` | `<1797 项省略>` |
| `field_T.times_s[0]` | 0 |
| `field_T.times_s[1]` | 10 |
| `field_T.times_s[2]` | 20 |
| `field_T.times_s[180]` | 1800 |
| `field_T.times_s[...]` | `<177 项省略>` |
| `field_T.values[0][0]` | 28 |
| `field_T.values[0][1]` | 28 |
| `field_T.values[0][2]` | 28 |
| `field_T.values[0][20]` | 28 |
| `field_T.values[0][...]` | `<17 项省略>` |
| `field_T.values[1][0]` | 28 |
| `field_T.values[1][1]` | 28 |
| `field_T.values[1][2]` | 28 |
| `field_T.values[1][20]` | 28.0058 |
| `field_T.values[1][...]` | `<17 项省略>` |
| `field_T.values[2][0]` | 28 |
| `field_T.values[2][1]` | 28 |
| `field_T.values[2][2]` | 28 |
| `field_T.values[2][20]` | 28.0161 |
| `field_T.values[2][...]` | `<17 项省略>` |
| `field_T.values[180][0]` | 33.5756 |
| `field_T.values[180][1]` | 33.5835 |
| `field_T.values[180][2]` | 33.6071 |
| `field_T.values[180][20]` | 36.7857 |
| `field_T.values[180][...]` | `<17 项省略>` |
| `field_T.values[...]` | `<177 项省略>` |
| `field_C.times_s[0]` | 0 |
| `field_C.times_s[1]` | 10 |
| `field_C.times_s[2]` | 20 |
| `field_C.times_s[180]` | 1800 |
| `field_C.times_s[...]` | `<177 项省略>` |
| `field_C.values[0][0]` | 2.55 |
| `field_C.values[0][1]` | 2.55 |
| `field_C.values[0][2]` | 2.55 |
| `field_C.values[0][20]` | 2.55 |
| `field_C.values[0][...]` | `<17 项省略>` |
| `field_C.values[1][0]` | 2.55 |
| `field_C.values[1][1]` | 2.55 |
| `field_C.values[1][2]` | 2.55 |
| `field_C.values[1][20]` | 2.45886 |
| `field_C.values[1][...]` | `<17 项省略>` |
| `field_C.values[2][0]` | 2.55 |
| `field_C.values[2][1]` | 2.55 |
| `field_C.values[2][2]` | 2.55 |
| `field_C.values[2][20]` | 2.4149 |
| `field_C.values[2][...]` | `<17 项省略>` |
| `field_C.values[180][0]` | 2.54999 |
| `field_C.values[180][1]` | 2.54999 |
| `field_C.values[180][2]` | 2.54998 |
| `field_C.values[180][20]` | 1.51036 |
| `field_C.values[180][...]` | `<17 项省略>` |
| `field_C.values[...]` | `<177 项省略>` |
| `mass_balance.times_s[0]` | 0 |
| `mass_balance.times_s[1]` | 1 |
| `mass_balance.times_s[2]` | 2 |
| `mass_balance.times_s[1800]` | 1800 |
| `mass_balance.times_s[...]` | `<1797 项省略>` |
| `mass_balance.M[0]` | 2.55 |
| `mass_balance.M[1]` | 2.5498 |
| `mass_balance.M[2]` | 2.5496 |
| `mass_balance.M[1800]` | 2.29347 |
| `mass_balance.M[...]` | `<1797 项省略>` |
| `mass_balance.Q[0]` | 0 |
| `mass_balance.Q[1]` | 0.000202 |
| `mass_balance.Q[2]` | 0.000402 |
| `mass_balance.Q[1800]` | 0.25653 |
| `mass_balance.Q[...]` | `<1797 项省略>` |
| `mass_balance.eps_M[0]` | 8.882e+14 |
| `mass_balance.eps_M[1]` | 4.489e-13 |
| `mass_balance.eps_M[2]` | 3.959e-13 |
| `mass_balance.eps_M[1800]` | 4.285e-14 |
| `mass_balance.eps_M[...]` | `<1797 项省略>` |
| `analytic_validation.n_modes` | 2000 |
| `analytic_validation.Bi_h` | 1.38889 |
| `analytic_validation.max_abs_dev_K` | 0.002062 |
| `analytic_validation.detail.100s.numeric[0]` | 28.0001 |
| `analytic_validation.detail.100s.numeric[1]` | 28.0004 |
| `analytic_validation.detail.100s.numeric[2]` | 28.0041 |
| `analytic_validation.detail.100s.numeric[3]` | 28.0328 |
| `analytic_validation.detail.100s.numeric[4]` | 28.1801 |
| `analytic_validation.detail.100s.analytic[0]` | 28.0001 |
| `analytic_validation.detail.100s.analytic[1]` | 28.0003 |
| `analytic_validation.detail.100s.analytic[2]` | 28.004 |
| `analytic_validation.detail.100s.analytic[3]` | 28.0327 |
| `analytic_validation.detail.100s.analytic[4]` | 28.1799 |
| `analytic_validation.detail.100s.max_abs_dev` | 0.000198 |
| `analytic_validation.detail.300s.numeric[0]` | 28.041 |
| `analytic_validation.detail.300s.numeric[1]` | 28.0637 |
| `analytic_validation.detail.300s.numeric[2]` | 28.1516 |
| `analytic_validation.detail.300s.numeric[3]` | 28.3683 |
| `analytic_validation.detail.300s.numeric[4]` | 28.849 |
| `analytic_validation.detail.300s.analytic[0]` | 28.0408 |
| `analytic_validation.detail.300s.analytic[1]` | 28.0635 |
| `analytic_validation.detail.300s.analytic[2]` | 28.1514 |
| `analytic_validation.detail.300s.analytic[3]` | 28.3681 |
| `analytic_validation.detail.300s.analytic[4]` | 28.8485 |
| `analytic_validation.detail.300s.max_abs_dev` | 0.000516 |
| `analytic_validation.detail.600s.numeric[0]` | 28.4538 |
| `analytic_validation.detail.600s.numeric[1]` | 28.5364 |
| `analytic_validation.detail.600s.numeric[2]` | 28.8043 |
| `analytic_validation.detail.600s.numeric[3]` | 29.3162 |
| `analytic_validation.detail.600s.numeric[4]` | 30.1654 |
| `analytic_validation.detail.600s.analytic[0]` | 28.4533 |
| `analytic_validation.detail.600s.analytic[1]` | 28.536 |
| `analytic_validation.detail.600s.analytic[2]` | 28.8039 |
| `analytic_validation.detail.600s.analytic[3]` | 29.3159 |
| `analytic_validation.detail.600s.analytic[4]` | 30.1645 |
| `analytic_validation.detail.600s.max_abs_dev` | 0.000889 |
| `analytic_validation.detail.900s.numeric[0]` | 29.3248 |
| `analytic_validation.detail.900s.numeric[1]` | 29.4587 |
| `analytic_validation.detail.900s.numeric[2]` | 29.8758 |
| `analytic_validation.detail.900s.numeric[3]` | 30.6164 |
| `analytic_validation.detail.900s.numeric[4]` | 31.7306 |
| `analytic_validation.detail.900s.analytic[0]` | 29.3243 |
| `analytic_validation.detail.900s.analytic[1]` | 29.4582 |
| `analytic_validation.detail.900s.analytic[2]` | 29.8755 |
| `analytic_validation.detail.900s.analytic[3]` | 30.6161 |
| `analytic_validation.detail.900s.analytic[4]` | 31.7293 |
| `analytic_validation.detail.900s.max_abs_dev` | 0.001246 |
| `analytic_validation.detail.1200s.numeric[0]` | 30.5432 |
| `analytic_validation.detail.1200s.numeric[1]` | 30.7102 |
| `analytic_validation.detail.1200s.numeric[2]` | 31.2227 |
| `analytic_validation.detail.1200s.numeric[3]` | 32.1129 |
| `analytic_validation.detail.1200s.numeric[4]` | 33.4278 |
| `analytic_validation.detail.1200s.analytic[0]` | 30.5427 |
| `analytic_validation.detail.1200s.analytic[1]` | 30.7098 |
| `analytic_validation.detail.1200s.analytic[2]` | 31.2223 |
| `analytic_validation.detail.1200s.analytic[3]` | 32.1126 |
| `analytic_validation.detail.1200s.analytic[4]` | 33.4262 |
| `analytic_validation.detail.1200s.max_abs_dev` | 0.001597 |
| `analytic_validation.detail.1500s.numeric[0]` | 31.9961 |
| `analytic_validation.detail.1500s.numeric[1]` | 32.1871 |
| `analytic_validation.detail.1500s.numeric[2]` | 32.7664 |
| `analytic_validation.detail.1500s.numeric[3]` | 33.7465 |
| `analytic_validation.detail.1500s.numeric[4]` | 35.1204 |
| `analytic_validation.detail.1500s.analytic[0]` | 31.9957 |
| `analytic_validation.detail.1500s.analytic[1]` | 32.1867 |
| `analytic_validation.detail.1500s.analytic[2]` | 32.766 |
| `analytic_validation.detail.1500s.analytic[3]` | 33.7463 |
| `analytic_validation.detail.1500s.analytic[4]` | 35.1186 |
| `analytic_validation.detail.1500s.max_abs_dev` | 0.001801 |
| `analytic_validation.detail.1800s.numeric[0]` | 33.5756 |
| `analytic_validation.detail.1800s.numeric[1]` | 33.7723 |
| `analytic_validation.detail.1800s.numeric[2]` | 34.3644 |
| `analytic_validation.detail.1800s.numeric[3]` | 35.3624 |
| `analytic_validation.detail.1800s.numeric[4]` | 36.7857 |
| `analytic_validation.detail.1800s.analytic[0]` | 33.5753 |
| `analytic_validation.detail.1800s.analytic[1]` | 33.772 |
| `analytic_validation.detail.1800s.analytic[2]` | 34.3642 |
| `analytic_validation.detail.1800s.analytic[3]` | 35.3621 |
| `analytic_validation.detail.1800s.analytic[4]` | 36.7837 |
| `analytic_validation.detail.1800s.max_abs_dev` | 0.002062 |
| `explicit_cross_check.dt_used_s` | 0.083279 |
| `explicit_cross_check.dt_stable_s` | 0.166563 |
| `explicit_cross_check.dt_row_bound_s` | 0.083281 |
| `explicit_cross_check.n_steps` | 21614 |
| `explicit_cross_check.max_abs_dev_T_K` | 0.0004 |
| `explicit_cross_check.max_abs_dev_C` | 2.99e-05 |
| `characteristic_times.tau_heat_s` | 2369 |
| `characteristic_times.tau_mass_s` | 8.101e+04 |
| `characteristic_times.alpha_m2_s` | 1.689e-07 |
| `characteristic_times.Bi_h` | 1.38889 |
| `characteristic_times.Bi_m` | 3.2404 |
| `diagnostics.eps_M` | 4.285e-14 |
| `diagnostics.robin_res_T` | 1.053e-06 |
| `diagnostics.robin_res_C` | 0.001351 |
| `diagnostics.center_sym_T.grad_center` | -1.571e-05 |
| `diagnostics.center_sym_T.grad_surface` | 328.284 |
| `diagnostics.center_sym_T.ratio` | 4.785e-08 |
| `diagnostics.center_sym_C.grad_center` | 1.581e-05 |
| `diagnostics.center_sym_C.grad_surface` | -303.938 |
| `diagnostics.center_sym_C.ratio` | 5.201e-08 |
| `diagnostics.T_range[0]` | 28 |
| `diagnostics.T_range[1]` | 36.7857 |
| `diagnostics.C_range[0]` | 1.51036 |
| `diagnostics.C_range[1]` | 2.55 |
| `diagnostics.max_diff_C` | 7.994e-15 |
| `diagnostics.argmax_max` | 0 |
| `diagnostics.max_center_deficit` | 7.55e-15 |
| `diagnostics.n_center_violations` | 0 |
| `xlsx_report.path` | `C:\Users\17038\AppData\Roaming\ModexData\library-cxscTJ...` |
| `xlsx_report.sheets[0]` | `温度` |
| `xlsx_report.sheets[1]` | `水分浓度` |
| `xlsx_report.温度.n_rows` | 1801 |
| `xlsx_report.温度.t_first` | 0 |
| `xlsx_report.温度.t_last` | 1800 |
| `xlsx_report.温度.dt_s` | 1 |
| `xlsx_report.温度.n_cols` | 21 |
| `xlsx_report.温度.sampled_cells` | 200 |
| `xlsx_report.水分浓度.n_rows` | 1801 |
| `xlsx_report.水分浓度.t_first` | 0 |
| `xlsx_report.水分浓度.t_last` | 1800 |
| `xlsx_report.水分浓度.dt_s` | 1 |
| `xlsx_report.水分浓度.n_cols` | 21 |
| `xlsx_report.水分浓度.sampled_cells` | 200 |
| `summary.T_center_1800s` | 33.5756 |
| `summary.T_surface_1800s` | 36.7857 |
| `summary.C_center_1800s` | 2.54999 |
| `summary.C_surface_1800s` | 1.51036 |
| `summary.eps_M` | 4.285e-14 |
| `summary.analytic_gap_K` | 0.002062 |

### `problem_2_results.json`（291 条）

| 数据路径 | 数值 |
|---|---|
| `problem` | 2 |
| `title` | `全过程变物性双向强耦合模型（输出截取前 3 h）` |
| `method` | `守恒型有限体积 + 向后 Euler/Picard；附录 3 变物性双向耦合` |
| `property_group` | `附录3 变物性 rho=650+128*C; cp=1450+2736*C/(C+1); k=0.21+0.3...` |
| `grid.n_cells` | 80 |
| `grid.dt_s` | 0.5 |
| `grid.dr_cm` | 0.025 |
| `grid.out_dt_s` | 1 |
| `grid.out_dr_cm` | 0.1 |
| `grid.n_steps` | 21600 |
| `output_radii_cm[0]` | 0 |
| `output_radii_cm[1]` | 0.1 |
| `output_radii_cm[2]` | 0.2 |
| `output_radii_cm[20]` | 2 |
| `output_radii_cm[...]` | `<17 项省略>` |
| `paper_tables.table3_temperature[0].t_h` | 0.5 |
| `paper_tables.table3_temperature[0].t_s` | 1800 |
| `paper_tables.table3_temperature[0].values[0]` | 32.19 |
| `paper_tables.table3_temperature[0].values[1]` | 32.3828 |
| `paper_tables.table3_temperature[0].values[2]` | 32.9666 |
| `paper_tables.table3_temperature[0].values[3]` | 33.9614 |
| `paper_tables.table3_temperature[0].values[4]` | 35.4135 |
| `paper_tables.table3_temperature[1].t_h` | 1 |
| `paper_tables.table3_temperature[1].t_s` | 3600 |
| `paper_tables.table3_temperature[1].values[0]` | 40.3816 |
| `paper_tables.table3_temperature[1].values[1]` | 40.5536 |
| `paper_tables.table3_temperature[1].values[2]` | 41.0605 |
| `paper_tables.table3_temperature[1].values[3]` | 41.8783 |
| `paper_tables.table3_temperature[1].values[4]` | 42.9977 |
| `paper_tables.table3_temperature[2].t_h` | 1.5 |
| `paper_tables.table3_temperature[2].t_s` | 5400 |
| `paper_tables.table3_temperature[2].values[0]` | 45.8465 |
| `paper_tables.table3_temperature[2].values[1]` | 45.9345 |
| `paper_tables.table3_temperature[2].values[2]` | 46.1927 |
| `paper_tables.table3_temperature[2].values[3]` | 46.6048 |
| `paper_tables.table3_temperature[2].values[4]` | 47.1399 |
| `paper_tables.table3_temperature[5].t_h` | 3 |
| `paper_tables.table3_temperature[5].t_s` | 1.08e+04 |
| `paper_tables.table3_temperature[5].values[0]` | 49.8495 |
| `paper_tables.table3_temperature[5].values[1]` | 49.8553 |
| `paper_tables.table3_temperature[5].values[2]` | 49.8746 |
| `paper_tables.table3_temperature[5].values[3]` | 49.9101 |
| `paper_tables.table3_temperature[5].values[4]` | 49.9664 |
| `paper_tables.table3_temperature[...]` | `<2 项省略>` |
| `paper_tables.table4_moisture[0].t_h` | 0.5 |
| `paper_tables.table4_moisture[0].t_s` | 1800 |
| `paper_tables.table4_moisture[0].values[0]` | 2.5499 |
| `paper_tables.table4_moisture[0].values[1]` | 2.5489 |
| `paper_tables.table4_moisture[0].values[2]` | 2.5255 |
| `paper_tables.table4_moisture[0].values[3]` | 2.3258 |
| `paper_tables.table4_moisture[0].values[4]` | 1.6486 |
| `paper_tables.table4_moisture[1].t_h` | 1 |
| `paper_tables.table4_moisture[1].t_s` | 3600 |
| `paper_tables.table4_moisture[1].values[0]` | 2.5257 |
| `paper_tables.table4_moisture[1].values[1]` | 2.4947 |
| `paper_tables.table4_moisture[1].values[2]` | 2.3578 |
| `paper_tables.table4_moisture[1].values[3]` | 2.023 |
| `paper_tables.table4_moisture[1].values[4]` | 1.4711 |
| `paper_tables.table4_moisture[2].t_h` | 1.5 |
| `paper_tables.table4_moisture[2].t_s` | 5400 |
| `paper_tables.table4_moisture[2].values[0]` | 2.386 |
| `paper_tables.table4_moisture[2].values[1]` | 2.3256 |
| `paper_tables.table4_moisture[2].values[2]` | 2.1344 |
| `paper_tables.table4_moisture[2].values[3]` | 1.802 |
| `paper_tables.table4_moisture[2].values[4]` | 1.3475 |
| `paper_tables.table4_moisture[5].t_h` | 3 |
| `paper_tables.table4_moisture[5].t_s` | 1.08e+04 |
| `paper_tables.table4_moisture[5].values[0]` | 1.7662 |
| `paper_tables.table4_moisture[5].values[1]` | 1.7165 |
| `paper_tables.table4_moisture[5].values[2]` | 1.5702 |
| `paper_tables.table4_moisture[5].values[3]` | 1.3333 |
| `paper_tables.table4_moisture[5].values[4]` | 1.0081 |
| `paper_tables.table4_moisture[...]` | `<2 项省略>` |
| `table_radii_cm[0]` | 0 |
| `table_radii_cm[1]` | 0.5 |
| `table_radii_cm[2]` | 1 |
| `table_radii_cm[3]` | 1.5 |
| `table_radii_cm[4]` | 2 |
| `table_times_h[0]` | 0.5 |
| `table_times_h[1]` | 1 |
| `table_times_h[2]` | 1.5 |
| `table_times_h[5]` | 3 |
| `table_times_h[...]` | `<2 项省略>` |
| `center_series.times_s[0]` | 0 |
| `center_series.times_s[1]` | 1 |
| `center_series.times_s[2]` | 2 |
| `center_series.times_s[10800]` | 1.08e+04 |
| `center_series.times_s[...]` | `<10797 项省略>` |
| `center_series.T[0]` | 28 |
| `center_series.T[1]` | 28 |
| `center_series.T[2]` | 28 |
| `center_series.T[10800]` | 49.8495 |
| `center_series.T[...]` | `<10797 项省略>` |
| `center_series.C[0]` | 2.55 |
| `center_series.C[1]` | 2.55 |
| `center_series.C[2]` | 2.55 |
| `center_series.C[10800]` | 1.76619 |
| `center_series.C[...]` | `<10797 项省略>` |
| `surface_series.times_s[0]` | 0 |
| `surface_series.times_s[1]` | 1 |
| `surface_series.times_s[2]` | 2 |
| `surface_series.times_s[10800]` | 1.08e+04 |
| `surface_series.times_s[...]` | `<10797 项省略>` |
| `surface_series.T[0]` | 28 |
| `surface_series.T[1]` | 28.0001 |
| `surface_series.T[2]` | 28.0004 |
| `surface_series.T[10800]` | 49.9664 |
| `surface_series.T[...]` | `<10797 项省略>` |
| `surface_series.C[0]` | 2.55 |
| `surface_series.C[1]` | 2.53568 |
| `surface_series.C[2]` | 2.52344 |
| `surface_series.C[10800]` | 1.00811 |
| `surface_series.C[...]` | `<10797 项省略>` |
| `env_series.times_s[0]` | 0 |
| `env_series.times_s[1]` | 1 |
| `env_series.times_s[2]` | 2 |
| `env_series.times_s[10800]` | 1.08e+04 |
| `env_series.times_s[...]` | `<10797 项省略>` |
| `env_series.T_inf[0]` | 28 |
| `env_series.T_inf[1]` | 28.0088 |
| `env_series.T_inf[2]` | 28.0176 |
| `env_series.T_inf[10800]` | 50.195 |
| `env_series.T_inf[...]` | `<10797 项省略>` |
| `env_series.C_inf[0]` | 0.01963 |
| `env_series.C_inf[1]` | 0.019637 |
| `env_series.C_inf[2]` | 0.019643 |
| `env_series.C_inf[10800]` | 0.04977 |
| `env_series.C_inf[...]` | `<10797 项省略>` |
| `field_T.times_s[0]` | 0 |
| `field_T.times_s[1]` | 60 |
| `field_T.times_s[2]` | 120 |
| `field_T.times_s[180]` | 1.08e+04 |
| `field_T.times_s[...]` | `<177 项省略>` |
| `field_T.values[0][0]` | 28 |
| `field_T.values[0][1]` | 28 |
| `field_T.values[0][2]` | 28 |
| `field_T.values[0][20]` | 28 |
| `field_T.values[0][...]` | `<17 项省略>` |
| `field_T.values[1][0]` | 28 |
| `field_T.values[1][1]` | 28 |
| `field_T.values[1][2]` | 28 |
| `field_T.values[1][20]` | 28.0582 |
| `field_T.values[1][...]` | `<17 项省略>` |
| `field_T.values[2][0]` | 28.0001 |
| `field_T.values[2][1]` | 28.0001 |
| `field_T.values[2][2]` | 28.0001 |
| `field_T.values[2][20]` | 28.1768 |
| `field_T.values[2][...]` | `<17 项省略>` |
| `field_T.values[180][0]` | 49.8495 |
| `field_T.values[180][1]` | 49.8497 |
| `field_T.values[180][2]` | 49.8504 |
| `field_T.values[180][20]` | 49.9664 |
| `field_T.values[180][...]` | `<17 项省略>` |
| `field_T.values[...]` | `<177 项省略>` |
| `field_C.times_s[0]` | 0 |
| `field_C.times_s[1]` | 60 |
| `field_C.times_s[2]` | 120 |
| `field_C.times_s[180]` | 1.08e+04 |
| `field_C.times_s[...]` | `<177 项省略>` |
| `field_C.values[0][0]` | 2.55 |
| `field_C.values[0][1]` | 2.55 |
| `field_C.values[0][2]` | 2.55 |
| `field_C.values[0][20]` | 2.55 |
| `field_C.values[0][...]` | `<17 项省略>` |
| `field_C.values[1][0]` | 2.55 |
| `field_C.values[1][1]` | 2.55 |
| `field_C.values[1][2]` | 2.55 |
| `field_C.values[1][20]` | 2.32946 |
| `field_C.values[1][...]` | `<17 项省略>` |
| `field_C.values[2][0]` | 2.55 |
| `field_C.values[2][1]` | 2.55 |
| `field_C.values[2][2]` | 2.55 |
| `field_C.values[2][20]` | 2.24357 |
| `field_C.values[2][...]` | `<17 项省略>` |
| `field_C.values[180][0]` | 1.76619 |
| `field_C.values[180][1]` | 1.76419 |
| `field_C.values[180][2]` | 1.75822 |
| `field_C.values[180][20]` | 1.00811 |
| `field_C.values[180][...]` | `<17 项省略>` |
| `field_C.values[...]` | `<177 项省略>` |
| `mass_balance.times_s[0]` | 0 |
| `mass_balance.times_s[1]` | 1 |
| `mass_balance.times_s[2]` | 2 |
| `mass_balance.times_s[10800]` | 1.08e+04 |
| `mass_balance.times_s[...]` | `<10797 项省略>` |
| `mass_balance.M[0]` | 2.55 |
| `mass_balance.M[1]` | 2.5498 |
| `mass_balance.M[2]` | 2.5496 |
| `mass_balance.M[10800]` | 1.3825 |
| `mass_balance.M[...]` | `<10797 项省略>` |
| `mass_balance.Q[0]` | 0 |
| `mass_balance.Q[1]` | 0.000202 |
| `mass_balance.Q[2]` | 0.000402 |
| `mass_balance.Q[10800]` | 1.1675 |
| `mass_balance.Q[...]` | `<10797 项省略>` |
| `mass_balance.eps_M[0]` | 8.882e+14 |
| `mass_balance.eps_M[1]` | 1.163e-12 |
| `mass_balance.eps_M[2]` | 6.305e-13 |
| `mass_balance.eps_M[10800]` | 2.339e-14 |
| `mass_balance.eps_M[...]` | `<10797 项省略>` |
| `long_run_probe.t_end_s` | 1.1e+05 |
| `long_run_probe.t_last_recorded_s` | 1.1e+05 |
| `long_run_probe.n_steps` | 22000 |
| `long_run_probe.dt_s` | 5 |
| `long_run_probe.maxC_end` | 0.20347 |
| `long_run_probe.C_center_end` | 0.20347 |
| `long_run_probe.T_center_end` | 49.9989 |
| `long_run_probe.eps_M_end` | 1.134e-14 |
| `long_run_probe.env_T_inf_end` | 49.9989 |
| `long_run_probe.env_C_inf_end` | 0.049988 |
| `long_run_probe.finite` | 1 |
| `conservation_form_probe.eps_M_conservative` | 9.243e-15 |
| `conservation_form_probe.eps_M_node_sided` | 0.016179 |
| `conservation_form_probe.degradation_factor` | 1.75e+12 |
| `conservation_form_probe.t_end_s` | 600 |
| `celsius_misuse_probe.T_degC` | 50 |
| `celsius_misuse_probe.T_K` | 323.15 |
| `celsius_misuse_probe.D_kelvin` | 1.347e-08 |
| `celsius_misuse_probe.D_celsius_misuse` | 7.293e-37 |
| `celsius_misuse_probe.ratio_misuse_over_correct` | 5.414e-29 |
| `property_profiles.C_nodes[0]` | 1.76619 |
| `property_profiles.C_nodes[1]` | 1.76419 |
| `property_profiles.C_nodes[2]` | 1.75822 |
| `property_profiles.C_nodes[20]` | 1.00811 |
| `property_profiles.C_nodes[...]` | `<17 项省略>` |
| `property_profiles.rho[0]` | 876.072 |
| `property_profiles.rho[1]` | 875.817 |
| `property_profiles.rho[2]` | 875.052 |
| `property_profiles.rho[20]` | 779.038 |
| `property_profiles.rho[...]` | `<17 项省略>` |
| `property_profiles.cp[0]` | 3197 |
| `property_profiles.cp[1]` | 3196 |
| `property_profiles.cp[2]` | 3194 |
| `property_profiles.cp[20]` | 2824 |
| `property_profiles.cp[...]` | `<17 项省略>` |
| `property_profiles.k[0]` | 0.452627 |
| `property_profiles.k[1]` | 0.452528 |
| `property_profiles.k[2]` | 0.45223 |
| `property_profiles.k[20]` | 0.400767 |
| `property_profiles.k[...]` | `<17 项省略>` |
| `property_profiles.D[0]` | 1.239e-08 |
| `property_profiles.D[1]` | 1.238e-08 |
| `property_profiles.D[2]` | 1.237e-08 |
| `property_profiles.D[20]` | 1.027e-08 |
| `property_profiles.D[...]` | `<17 项省略>` |
| `diagnostics.eps_M` | 2.339e-14 |
| `diagnostics.robin_res_T` | 0.000543 |
| `diagnostics.robin_res_C` | 6.538e-05 |
| `diagnostics.center_sym_T.grad_center` | -2.562e-05 |
| `diagnostics.center_sym_T.grad_surface` | 14.2525 |
| `diagnostics.center_sym_T.ratio` | 1.797e-06 |
| `diagnostics.center_sym_C.grad_center` | -2.867e-05 |
| `diagnostics.center_sym_C.grad_surface` | -74.6346 |
| `diagnostics.center_sym_C.ratio` | 3.841e-07 |
| `diagnostics.T_range[0]` | 28 |
| `diagnostics.T_range[1]` | 49.9664 |
| `diagnostics.C_range[0]` | 1.00811 |
| `diagnostics.C_range[1]` | 2.55 |
| `diagnostics.max_diff_C` | 7.105e-15 |
| `diagnostics.argmax_max` | 0 |
| `diagnostics.max_center_deficit` | 1.021e-14 |
| `diagnostics.n_center_violations` | 0 |
| `diagnostics.prop_ptp_min.rho` | 0.954352 |
| `diagnostics.prop_ptp_min.cp` | 1.62208 |
| `diagnostics.prop_ptp_min.k` | 0.000225 |
| `diagnostics.prop_ptp_min.D` | 2.906e-12 |
| `diagnostics.T_K_range[0]` | 301.15 |
| `diagnostics.T_K_range[1]` | 323.116 |
| `diagnostics.picard_rounds_max` | 3 |
| `xlsx_report.path` | `C:\Users\17038\AppData\Roaming\ModexData\library-cxscTJ...` |
| `xlsx_report.sheets[0]` | `温度` |
| `xlsx_report.sheets[1]` | `水分浓度` |
| `xlsx_report.温度.n_rows` | 10801 |
| `xlsx_report.温度.t_first` | 0 |
| `xlsx_report.温度.t_last` | 10800 |
| `xlsx_report.温度.dt_s` | 1 |
| `xlsx_report.温度.n_cols` | 21 |
| `xlsx_report.温度.sampled_cells` | 200 |
| `xlsx_report.水分浓度.n_rows` | 10801 |
| `xlsx_report.水分浓度.t_first` | 0 |
| `xlsx_report.水分浓度.t_last` | 10800 |
| `xlsx_report.水分浓度.dt_s` | 1 |
| `xlsx_report.水分浓度.n_cols` | 21 |
| `xlsx_report.水分浓度.sampled_cells` | 200 |
| `summary.T_center_3h` | 49.8495 |
| `summary.T_surface_3h` | 49.9664 |
| `summary.C_center_3h` | 1.76619 |
| `summary.C_surface_3h` | 1.00811 |
| `summary.eps_M` | 2.339e-14 |
| `summary.long_run_t_end_s` | 1.1e+05 |
| `summary.conservation_degradation_factor` | 1.75e+12 |

### `problem_3_results.json`（308 条）

| 数据路径 | 数值 |
|---|---|
| `problem` | 3 |
| `title` | `烘干终点判定与总烘干时长` |
| `method` | `守恒型有限体积 + 向后 Euler/Picard；阈值首达 + 线性插值细化` |
| `property_group` | `附录3 变物性 rho=650+128*C; cp=1450+2736*C/(C+1); k=0.21+0.3...` |
| `grid.n_cells` | 80 |
| `grid.dt_s` | 5 |
| `grid.dr_cm` | 0.025 |
| `grid.out_dt_s` | 60 |
| `grid.out_dr_cm` | 0.1 |
| `grid.n_steps` | 41238 |
| `answer.t_star_h` | 57.2745 |
| `answer.t_star_s` | 2.062e+05 |
| `answer.criterion` | `max_r C(r,t) < 0.15 kg/kg（干基，全域最大值）` |
| `answer.t_star_days` | 2.3864 |
| `output_radii_cm[0]` | 0 |
| `output_radii_cm[1]` | 0.1 |
| `output_radii_cm[2]` | 0.2 |
| `output_radii_cm[20]` | 2 |
| `output_radii_cm[...]` | `<17 项省略>` |
| `paper_tables.table5_moisture[0].label` | `6` |
| `paper_tables.table5_moisture[0].t_h` | 6 |
| `paper_tables.table5_moisture[0].t_s` | 2.16e+04 |
| `paper_tables.table5_moisture[0].is_end` | 0 |
| `paper_tables.table5_moisture[0].values[0]` | 1.0171 |
| `paper_tables.table5_moisture[0].values[1]` | 0.9883 |
| `paper_tables.table5_moisture[0].values[2]` | 0.9016 |
| `paper_tables.table5_moisture[0].values[3]` | 0.7551 |
| `paper_tables.table5_moisture[0].values[4]` | 0.5329 |
| `paper_tables.table5_moisture[1].label` | `12` |
| `paper_tables.table5_moisture[1].t_h` | 12 |
| `paper_tables.table5_moisture[1].t_s` | 4.32e+04 |
| `paper_tables.table5_moisture[1].is_end` | 0 |
| `paper_tables.table5_moisture[1].values[0]` | 0.4562 |
| `paper_tables.table5_moisture[1].values[1]` | 0.4432 |
| `paper_tables.table5_moisture[1].values[2]` | 0.4032 |
| `paper_tables.table5_moisture[1].values[3]` | 0.3298 |
| `paper_tables.table5_moisture[1].values[4]` | 0.1643 |
| `paper_tables.table5_moisture[2].label` | `18` |
| `paper_tables.table5_moisture[2].t_h` | 18 |
| `paper_tables.table5_moisture[2].t_s` | 6.48e+04 |
| `paper_tables.table5_moisture[2].is_end` | 0 |
| `paper_tables.table5_moisture[2].values[0]` | 0.2989 |
| `paper_tables.table5_moisture[2].values[1]` | 0.2916 |
| `paper_tables.table5_moisture[2].values[2]` | 0.2687 |
| `paper_tables.table5_moisture[2].values[3]` | 0.2252 |
| `paper_tables.table5_moisture[2].values[4]` | 0.0847 |
| `paper_tables.table5_moisture[9].label` | `烘干结束时间` |
| `paper_tables.table5_moisture[9].t_h` | 57.2745 |
| `paper_tables.table5_moisture[9].t_s` | 2.062e+05 |
| `paper_tables.table5_moisture[9].is_end` | 1 |
| `paper_tables.table5_moisture[9].values[0]` | 0.15 |
| `paper_tables.table5_moisture[9].values[1]` | 0.1477 |
| `paper_tables.table5_moisture[9].values[2]` | 0.1401 |
| `paper_tables.table5_moisture[9].values[3]` | 0.1247 |
| `paper_tables.table5_moisture[9].values[4]` | 0.0526 |
| `paper_tables.table5_moisture[...]` | `<6 项省略>` |
| `paper_tables.n_full_rows` | 9 |
| `paper_tables.radii_cm[0]` | 0 |
| `paper_tables.radii_cm[1]` | 0.5 |
| `paper_tables.radii_cm[2]` | 1 |
| `paper_tables.radii_cm[3]` | 1.5 |
| `paper_tables.radii_cm[4]` | 2 |
| `profile_at_tstar.radii_cm[0]` | 0 |
| `profile_at_tstar.radii_cm[1]` | 0.5 |
| `profile_at_tstar.radii_cm[2]` | 1 |
| `profile_at_tstar.radii_cm[3]` | 1.5 |
| `profile_at_tstar.radii_cm[4]` | 2 |
| `profile_at_tstar.C[0]` | 0.15 |
| `profile_at_tstar.C[1]` | 0.1477 |
| `profile_at_tstar.C[2]` | 0.1401 |
| `profile_at_tstar.C[3]` | 0.1247 |
| `profile_at_tstar.C[4]` | 0.0526 |
| `profile_at_tstar.T[0]` | 49.9989 |
| `profile_at_tstar.T[1]` | 49.9989 |
| `profile_at_tstar.T[2]` | 49.9989 |
| `profile_at_tstar.T[3]` | 49.9989 |
| `profile_at_tstar.T[4]` | 49.9989 |
| `profile_at_tstar.C_full_nodes[0]` | 0.149999 |
| `profile_at_tstar.C_full_nodes[1]` | 0.149908 |
| `profile_at_tstar.C_full_nodes[2]` | 0.149632 |
| `profile_at_tstar.C_full_nodes[20]` | 0.052646 |
| `profile_at_tstar.C_full_nodes[...]` | `<17 项省略>` |
| `center_series.times_s[0]` | 0 |
| `center_series.times_s[1]` | 60 |
| `center_series.times_s[2]` | 120 |
| `center_series.times_s[3437]` | 2.062e+05 |
| `center_series.times_s[...]` | `<3434 项省略>` |
| `center_series.T[0]` | 28 |
| `center_series.T[1]` | 28 |
| `center_series.T[2]` | 28.0001 |
| `center_series.T[3437]` | 49.9989 |
| `center_series.T[...]` | `<3434 项省略>` |
| `center_series.C[0]` | 2.55 |
| `center_series.C[1]` | 2.55 |
| `center_series.C[2]` | 2.55 |
| `center_series.C[3437]` | 0.149999 |
| `center_series.C[...]` | `<3434 项省略>` |
| `surface_series.times_s[0]` | 0 |
| `surface_series.times_s[1]` | 60 |
| `surface_series.times_s[2]` | 120 |
| `surface_series.times_s[3437]` | 2.062e+05 |
| `surface_series.times_s[...]` | `<3434 项省略>` |
| `surface_series.T[0]` | 28 |
| `surface_series.T[1]` | 28.0597 |
| `surface_series.T[2]` | 28.1792 |
| `surface_series.T[3437]` | 49.9989 |
| `surface_series.T[...]` | `<3434 项省略>` |
| `surface_series.C[0]` | 2.55 |
| `surface_series.C[1]` | 2.33175 |
| `surface_series.C[2]` | 2.24517 |
| `surface_series.C[3437]` | 0.052646 |
| `surface_series.C[...]` | `<3434 项省略>` |
| `env_series.times_s[0]` | 0 |
| `env_series.times_s[1]` | 60 |
| `env_series.times_s[2]` | 120 |
| `env_series.times_s[3437]` | 2.062e+05 |
| `env_series.times_s[...]` | `<3434 项省略>` |
| `env_series.T_inf[0]` | 28 |
| `env_series.T_inf[1]` | 28.528 |
| `env_series.T_inf[2]` | 29.192 |
| `env_series.T_inf[3437]` | 49.9989 |
| `env_series.T_inf[...]` | `<3434 项省略>` |
| `env_series.C_inf[0]` | 0.01963 |
| `env_series.C_inf[1]` | 0.02002 |
| `env_series.C_inf[2]` | 0.02053 |
| `env_series.C_inf[3437]` | 0.049988 |
| `env_series.C_inf[...]` | `<3434 项省略>` |
| `field_C.times_s[0]` | 0 |
| `field_C.times_s[1]` | 3600 |
| `field_C.times_s[2]` | 7200 |
| `field_C.times_s[58]` | 2.062e+05 |
| `field_C.times_s[...]` | `<55 项省略>` |
| `field_C.values[0][0]` | 2.55 |
| `field_C.values[0][1]` | 2.55 |
| `field_C.values[0][2]` | 2.55 |
| `field_C.values[0][20]` | 2.55 |
| `field_C.values[0][...]` | `<17 项省略>` |
| `field_C.values[1][0]` | 2.52543 |
| `field_C.values[1][1]` | 2.52435 |
| `field_C.values[1][2]` | 2.52102 |
| `field_C.values[1][20]` | 1.47128 |
| `field_C.values[1][...]` | `<17 项省略>` |
| `field_C.values[2][0]` | 2.17077 |
| `field_C.values[2][1]` | 2.16827 |
| `field_C.values[2][2]` | 2.16077 |
| `field_C.values[2][20]` | 1.23113 |
| `field_C.values[2][...]` | `<17 项省略>` |
| `field_C.values[58][0]` | 0.149999 |
| `field_C.values[58][1]` | 0.149908 |
| `field_C.values[58][2]` | 0.149632 |
| `field_C.values[58][20]` | 0.052646 |
| `field_C.values[58][...]` | `<17 项省略>` |
| `field_C.values[...]` | `<55 项省略>` |
| `field_T.times_s[0]` | 0 |
| `field_T.times_s[1]` | 3600 |
| `field_T.times_s[2]` | 7200 |
| `field_T.times_s[58]` | 2.062e+05 |
| `field_T.times_s[...]` | `<55 项省略>` |
| `field_T.values[0][0]` | 28 |
| `field_T.values[0][1]` | 28 |
| `field_T.values[0][2]` | 28 |
| `field_T.values[0][20]` | 28 |
| `field_T.values[0][...]` | `<17 项省略>` |
| `field_T.values[1][0]` | 40.3817 |
| `field_T.values[1][1]` | 40.3886 |
| `field_T.values[1][2]` | 40.4093 |
| `field_T.values[1][20]` | 42.9983 |
| `field_T.values[1][...]` | `<17 项省略>` |
| `field_T.values[2][0]` | 48.4476 |
| `field_T.values[2][1]` | 48.4492 |
| `field_T.values[2][2]` | 48.4537 |
| `field_T.values[2][20]` | 49.0017 |
| `field_T.values[2][...]` | `<17 项省略>` |
| `field_T.values[58][0]` | 49.9989 |
| `field_T.values[58][1]` | 49.9989 |
| `field_T.values[58][2]` | 49.9989 |
| `field_T.values[58][20]` | 49.9989 |
| `field_T.values[58][...]` | `<17 项省略>` |
| `field_T.values[...]` | `<55 项省略>` |
| `mass_balance.times_s[0]` | 0 |
| `mass_balance.times_s[1]` | 60 |
| `mass_balance.times_s[2]` | 120 |
| `mass_balance.times_s[3437]` | 2.062e+05 |
| `mass_balance.times_s[...]` | `<3434 项省略>` |
| `mass_balance.M[0]` | 2.55 |
| `mass_balance.M[1]` | 2.53858 |
| `mass_balance.M[2]` | 2.52772 |
| `mass_balance.M[3437]` | 0.123808 |
| `mass_balance.M[...]` | `<3434 项省略>` |
| `mass_balance.Q[0]` | 0 |
| `mass_balance.Q[1]` | 0.011423 |
| `mass_balance.Q[2]` | 0.022279 |
| `mass_balance.Q[3437]` | 2.42619 |
| `mass_balance.Q[...]` | `<3434 项省略>` |
| `mass_balance.eps_M[0]` | 8.882e+14 |
| `mass_balance.eps_M[1]` | 4.085e-14 |
| `mass_balance.eps_M[2]` | 1.339e-14 |
| `mass_balance.eps_M[3437]` | 1.556e-14 |
| `mass_balance.eps_M[...]` | `<3434 项省略>` |
| `grid_convergence.table[0].n_cells` | 20 |
| `grid_convergence.table[0].dt_s` | 20 |
| `grid_convergence.table[0].dr_cm` | 0.1 |
| `grid_convergence.table[0].t_star_h` | 56.495 |
| `grid_convergence.table[1].n_cells` | 40 |
| `grid_convergence.table[1].dt_s` | 10 |
| `grid_convergence.table[1].dr_cm` | 0.05 |
| `grid_convergence.table[1].t_star_h` | 57.0168 |
| `grid_convergence.table[1].rel_change_vs_coarser` | 0.009236 |
| `grid_convergence.table[2].n_cells` | 80 |
| `grid_convergence.table[2].dt_s` | 5 |
| `grid_convergence.table[2].dr_cm` | 0.025 |
| `grid_convergence.table[2].t_star_h` | 57.2745 |
| `grid_convergence.table[2].rel_change_vs_coarser` | 0.004519 |
| `grid_convergence.final_rel_change` | 0.004519 |
| `grid_convergence.tol` | 0.01 |
| `stability_probe.dt_used_s` | 0.097087 |
| `stability_probe.dt_stable_s` | 0.194196 |
| `stability_probe.dt_row_bound_s` | 0.097098 |
| `stability_probe.n_steps` | 6180 |
| `stability_probe.t_end_s` | 600 |
| `stability_probe.implicit_dt_s` | 5 |
| `stability_probe.finite` | 1 |
| `stability_probe.T_final_center` | 28.2677 |
| `stability_probe.C_final_center` | 2.55 |
| `criterion_variants.t_star_h_by_criterion.max` | 57.2745 |
| `criterion_variants.t_star_h_by_criterion.mean` | 35.6427 |
| `criterion_variants.t_star_h_by_criterion.surface` | 12.5562 |
| `criterion_variants.mean_minus_max_h` | -21.6317 |
| `criterion_variants.surface_minus_max_h` | -44.7182 |
| `product_exponent_probe.n_cells` | 20 |
| `product_exponent_probe.dt_s` | 20 |
| `product_exponent_probe.t_star_fraction_h` | 56.495 |
| `product_exponent_probe.t_star_product_h` | 16.4735 |
| `product_exponent_probe.ratio` | 0.291592 |
| `product_exponent_probe.problem_text_range_h[0]` | 48 |
| `product_exponent_probe.problem_text_range_h[1]` | 72 |
| `product_exponent_probe.product_inside_problem_text` | 0 |
| `q2_anchor_3h.t_s` | 1.08e+04 |
| `q2_anchor_3h.T_spread_degC` | 0.117116 |
| `q2_anchor_3h.C_center` | 1.76628 |
| `q2_anchor_3h.C_surface` | 1.00816 |
| `q2_anchor_3h.T_center` | 49.8492 |
| `q2_anchor_3h.T_surface` | 49.9663 |
| `diagnostics.eps_M` | 1.556e-14 |
| `diagnostics.t_star_h` | 57.2745 |
| `diagnostics.t_star_s` | 2.062e+05 |
| `diagnostics.robin_res_T` | 0.000545 |
| `diagnostics.robin_res_C` | 6.558e-05 |
| `diagnostics.robin_detail.anchor_3h.t_h` | 3 |
| `diagnostics.robin_detail.anchor_3h.drive_T_degC` | 0.22872 |
| `diagnostics.robin_detail.anchor_3h.drive_C` | 0.958393 |
| `diagnostics.robin_detail.anchor_3h.abs_res_T_W_m2` | 0.003118 |
| `diagnostics.robin_detail.anchor_3h.abs_res_C_kg_m2s` | 5.028e-11 |
| `diagnostics.robin_detail.anchor_3h.rel_res_T` | 0.000545 |
| `diagnostics.robin_detail.anchor_3h.rel_res_C` | 6.558e-05 |
| `diagnostics.robin_detail.anchor_3h.D_surface_m2_s` | 1.027e-08 |
| `diagnostics.robin_detail.anchor_3h.Bi_m` | 1.55766 |
| `diagnostics.robin_detail.anchor_3h.layer_over_cell` | 51.3593 |
| `diagnostics.robin_detail.tstar.t_h` | 57.275 |
| `diagnostics.robin_detail.tstar.drive_T_degC` | 1.705e-13 |
| `diagnostics.robin_detail.tstar.drive_C` | 0.002659 |
| `diagnostics.robin_detail.tstar.abs_res_T_W_m2` | 1.201e-11 |
| `diagnostics.robin_detail.tstar.abs_res_C_kg_m2s` | 1.746e-09 |
| `diagnostics.robin_detail.tstar.rel_res_T` | 2.28158 |
| `diagnostics.robin_detail.tstar.rel_res_C` | 0.82074 |
| `diagnostics.robin_detail.tstar.D_surface_m2_s` | 3.118e-12 |
| `diagnostics.robin_detail.tstar.Bi_m` | 5132 |
| `diagnostics.robin_detail.tstar.layer_over_cell` | 0.015588 |
| `diagnostics.robin_detail.scale_T_W_m2` | 549.972 |
| `diagnostics.robin_detail.scale_C_kg_m2s` | 2e-06 |
| `diagnostics.center_sym_T.grad_center` | -2.43e-05 |
| `diagnostics.center_sym_T.grad_surface` | 14.2597 |
| `diagnostics.center_sym_T.ratio` | 1.704e-06 |
| `diagnostics.center_sym_C.grad_center` | 5.833e-06 |
| `diagnostics.center_sym_C.grad_surface` | -122.028 |
| `diagnostics.center_sym_C.ratio` | 4.78e-08 |
| `diagnostics.T_range[0]` | 28 |
| `diagnostics.T_range[1]` | 50.0398 |
| `diagnostics.C_range[0]` | 0.052646 |
| `diagnostics.C_range[1]` | 2.55 |
| `diagnostics.maxC_at_tstar` | 0.149999 |
| `diagnostics.argmax_at_tstar` | 0 |
| `diagnostics.max_diff_C` | 1.332e-15 |
| `diagnostics.argmax_max` | 0 |
| `diagnostics.max_center_deficit` | 2.22e-15 |
| `diagnostics.n_center_violations` | 0 |
| `diagnostics.prop_ptp_min.rho` | 6.10701 |
| `diagnostics.prop_ptp_min.cp` | 10.4992 |
| `diagnostics.prop_ptp_min.k` | 0.001458 |
| `diagnostics.prop_ptp_min.D` | 1.859e-11 |
| `diagnostics.T_K_range[0]` | 301.15 |
| `diagnostics.T_K_range[1]` | 323.19 |
| `diagnostics.picard_rounds_max` | 3 |
| `xlsx_report.path` | `C:\Users\17038\AppData\Roaming\ModexData\library-cxscTJ...` |
| `xlsx_report.sheets[0]` | `Sheet1` |
| `xlsx_report.Sheet1.n_rows` | 3437 |
| `xlsx_report.Sheet1.t_first` | 0 |
| `xlsx_report.Sheet1.t_last` | 206160 |
| `xlsx_report.Sheet1.dt_s` | 60 |
| `xlsx_report.Sheet1.n_cols` | 21 |
| `xlsx_report.Sheet1.sampled_cells` | 200 |
| `summary.t_star_h` | 57.2745 |
| `summary.eps_M` | 1.556e-14 |
| `summary.grid_final_rel_change` | 0.004519 |
| `summary.maxC_at_tstar` | 0.149999 |
| `summary.C_center_6h` | 1.01711 |
| `summary.t_star_mean_criterion_h` | 35.6427 |
| `summary.t_star_product_exponent_h` | 16.4735 |

### `problem_4_results.json`（396 条）

| 数据路径 | 数值 |
|---|---|
| `problem` | 4 |
| `title` | `收缩动边界下的烘干时长（附件 2 的 R(t) + 附录 4 物性，物质坐标）` |
| `method` | `物质坐标 eta=r/R(t) + 守恒型有限体积 + 向后 Euler + Picard 强耦合；扩散项乘 ...` |
| `property_group` | `附录4 变物性 rho=760+90*C; cp=1850+2150*C/(C+1); k=0.12+0.20...` |
| `grid.n_cells` | 80 |
| `grid.dt_s` | 5 |
| `grid.eta_span` | 1 |
| `grid.out_dt_s` | 60 |
| `grid.picard_rounds_max` | 3 |
| `answer.t_star_h` | 51.0444 |
| `answer.t_star_s` | 1.838e+05 |
| `answer.t_star_days` | 2.1268 |
| `answer.R_at_tstar_cm` | 1.2 |
| `answer.criterion` | `max_eta C(eta,t) < 0.15 kg/kg（干基，全域最大值）` |
| `output_radii_cm[0]` | 0 |
| `output_radii_cm[1]` | 0.1 |
| `output_radii_cm[2]` | 0.2 |
| `output_radii_cm[20]` | 2 |
| `output_radii_cm[...]` | `<17 项省略>` |
| `paper_tables.table6_moisture[0].label` | `6` |
| `paper_tables.table6_moisture[0].t_h` | 6 |
| `paper_tables.table6_moisture[0].values[0]` | 1.71958 |
| `paper_tables.table6_moisture[0].values[1]` | 1.53774 |
| `paper_tables.table6_moisture[0].values[2]` | 1.02263 |
| `paper_tables.table6_moisture[0].surface_value` | 0.420655 |
| `paper_tables.table6_moisture[0].surface_radius_cm` | 1.374 |
| `paper_tables.table6_moisture[0].center_value` | 1.71958 |
| `paper_tables.table6_moisture[1].label` | `12` |
| `paper_tables.table6_moisture[1].t_h` | 12 |
| `paper_tables.table6_moisture[1].values[0]` | 0.737812 |
| `paper_tables.table6_moisture[1].values[1]` | 0.654752 |
| `paper_tables.table6_moisture[1].values[2]` | 0.408404 |
| `paper_tables.table6_moisture[1].surface_value` | 0.166972 |
| `paper_tables.table6_moisture[1].surface_radius_cm` | 1.248 |
| `paper_tables.table6_moisture[1].center_value` | 0.737812 |
| `paper_tables.table6_moisture[2].label` | `18` |
| `paper_tables.table6_moisture[2].t_h` | 18 |
| `paper_tables.table6_moisture[2].values[0]` | 0.408844 |
| `paper_tables.table6_moisture[2].values[1]` | 0.368727 |
| `paper_tables.table6_moisture[2].values[2]` | 0.239733 |
| `paper_tables.table6_moisture[2].surface_value` | 0.089245 |
| `paper_tables.table6_moisture[2].surface_radius_cm` | 1.214 |
| `paper_tables.table6_moisture[2].center_value` | 0.408844 |
| `paper_tables.table6_moisture[8].label` | `烘干结束时间` |
| `paper_tables.table6_moisture[8].t_h` | 51.0444 |
| `paper_tables.table6_moisture[8].values[0]` | 0.15 |
| `paper_tables.table6_moisture[8].values[1]` | 0.141238 |
| `paper_tables.table6_moisture[8].values[2]` | 0.107932 |
| `paper_tables.table6_moisture[8].surface_value` | 0.052604 |
| `paper_tables.table6_moisture[8].surface_radius_cm` | 1.2 |
| `paper_tables.table6_moisture[8].center_value` | 0.15 |
| `paper_tables.table6_moisture[...]` | `<5 项省略>` |
| `paper_tables.fixed_radii_cm[0]` | 0 |
| `paper_tables.fixed_radii_cm[1]` | 0.5 |
| `paper_tables.fixed_radii_cm[2]` | 1 |
| `paper_tables.fixed_radii_cm[3]` | 1.5 |
| `paper_tables.fixed_radii_cm[4]` | 2 |
| `paper_tables.last_col_label` | `药材表面` |
| `paper_tables.n_full_rows` | 8 |
| `profile_at_tstar.eta[0]` | 0 |
| `profile_at_tstar.eta[1]` | 0.0125 |
| `profile_at_tstar.eta[2]` | 0.025 |
| `profile_at_tstar.eta[80]` | 1 |
| `profile_at_tstar.eta[...]` | `<77 项省略>` |
| `profile_at_tstar.C[0]` | 0.15 |
| `profile_at_tstar.C[1]` | 0.149992 |
| `profile_at_tstar.C[2]` | 0.149969 |
| `profile_at_tstar.C[80]` | 0.052604 |
| `profile_at_tstar.C[...]` | `<77 项省略>` |
| `profile_at_tstar.T[0]` | 49.9989 |
| `profile_at_tstar.T[1]` | 49.9989 |
| `profile_at_tstar.T[2]` | 49.9989 |
| `profile_at_tstar.T[80]` | 49.9989 |
| `profile_at_tstar.T[...]` | `<77 项省略>` |
| `profile_at_tstar.R_cm` | 1.2 |
| `center_series.times_s[0]` | 0 |
| `center_series.times_s[1]` | 60 |
| `center_series.times_s[2]` | 120 |
| `center_series.times_s[3062]` | 1.837e+05 |
| `center_series.times_s[...]` | `<3059 项省略>` |
| `center_series.C[0]` | 2.55 |
| `center_series.C[1]` | 2.55 |
| `center_series.C[2]` | 2.55 |
| `center_series.C[3062]` | 0.15002 |
| `center_series.C[...]` | `<3059 项省略>` |
| `center_series.T[0]` | 28 |
| `center_series.T[1]` | 28 |
| `center_series.T[2]` | 28 |
| `center_series.T[3062]` | 49.9989 |
| `center_series.T[...]` | `<3059 项省略>` |
| `surface_series.times_s[0]` | 0 |
| `surface_series.times_s[1]` | 60 |
| `surface_series.times_s[2]` | 120 |
| `surface_series.times_s[3062]` | 1.837e+05 |
| `surface_series.times_s[...]` | `<3059 项省略>` |
| `surface_series.C[0]` | 2.55 |
| `surface_series.C[1]` | 2.10887 |
| `surface_series.C[2]` | 1.93724 |
| `surface_series.C[3062]` | 0.052605 |
| `surface_series.C[...]` | `<3059 项省略>` |
| `surface_series.T[0]` | 28 |
| `surface_series.T[1]` | 28.0767 |
| `surface_series.T[2]` | 28.2267 |
| `surface_series.T[3062]` | 49.9989 |
| `surface_series.T[...]` | `<3059 项省略>` |
| `radius_series.times_s[0]` | 0 |
| `radius_series.times_s[1]` | 60 |
| `radius_series.times_s[2]` | 120 |
| `radius_series.times_s[3062]` | 1.837e+05 |
| `radius_series.times_s[...]` | `<3059 项省略>` |
| `radius_series.R_cm[0]` | 2 |
| `radius_series.R_cm[1]` | 1.99577 |
| `radius_series.R_cm[2]` | 1.99153 |
| `radius_series.R_cm[3062]` | 1.2 |
| `radius_series.R_cm[...]` | `<3059 项省略>` |
| `env_series.times_s[0]` | 0 |
| `env_series.times_s[1]` | 60 |
| `env_series.times_s[2]` | 120 |
| `env_series.times_s[3062]` | 1.837e+05 |
| `env_series.times_s[...]` | `<3059 项省略>` |
| `env_series.T_inf[0]` | 28 |
| `env_series.T_inf[1]` | 28.528 |
| `env_series.T_inf[2]` | 29.192 |
| `env_series.T_inf[3062]` | 49.9989 |
| `env_series.T_inf[...]` | `<3059 项省略>` |
| `env_series.C_inf[0]` | 0.01963 |
| `env_series.C_inf[1]` | 0.02002 |
| `env_series.C_inf[2]` | 0.02053 |
| `env_series.C_inf[3062]` | 0.049988 |
| `env_series.C_inf[...]` | `<3059 项省略>` |
| `field_C.times_s[0]` | 0 |
| `field_C.times_s[1]` | 900 |
| `field_C.times_s[2]` | 1800 |
| `field_C.times_s[205]` | 1.837e+05 |
| `field_C.times_s[...]` | `<202 项省略>` |
| `field_C.values[0][0]` | 2.55 |
| `field_C.values[0][1]` | 2.55 |
| `field_C.values[0][2]` | 2.55 |
| `field_C.values[0][20]` | 2.55 |
| `field_C.values[0][...]` | `<17 项省略>` |
| `field_C.values[1][0]` | 2.55 |
| `field_C.values[1][1]` | 2.55 |
| `field_C.values[1][2]` | 2.55 |
| `field_C.values[1][20]` | 1.32163 |
| `field_C.values[1][...]` | `<17 项省略>` |
| `field_C.values[2][0]` | 2.55 |
| `field_C.values[2][1]` | 2.55 |
| `field_C.values[2][2]` | 2.55 |
| `field_C.values[2][20]` | 1.13118 |
| `field_C.values[2][...]` | `<17 项省略>` |
| `field_C.values[205][0]` | 0.15002 |
| `field_C.values[205][1]` | 0.149899 |
| `field_C.values[205][2]` | 0.149533 |
| `field_C.values[205][20]` | 0.052605 |
| `field_C.values[205][...]` | `<17 项省略>` |
| `field_C.values[...]` | `<202 项省略>` |
| `field_T.times_s[0]` | 0 |
| `field_T.times_s[1]` | 900 |
| `field_T.times_s[2]` | 1800 |
| `field_T.times_s[205]` | 1.837e+05 |
| `field_T.times_s[...]` | `<202 项省略>` |
| `field_T.values[0][0]` | 28 |
| `field_T.values[0][1]` | 28 |
| `field_T.values[0][2]` | 28 |
| `field_T.values[0][20]` | 28 |
| `field_T.values[0][...]` | `<17 项省略>` |
| `field_T.values[1][0]` | 28.4239 |
| `field_T.values[1][1]` | 28.4286 |
| `field_T.values[1][2]` | 28.4429 |
| `field_T.values[1][20]` | 31.4075 |
| `field_T.values[1][...]` | `<17 项省略>` |
| `field_T.values[2][0]` | 31.0469 |
| `field_T.values[2][1]` | 31.058 |
| `field_T.values[2][2]` | 31.0913 |
| `field_T.values[2][20]` | 35.9141 |
| `field_T.values[2][...]` | `<17 项省略>` |
| `field_T.values[205][0]` | 49.9989 |
| `field_T.values[205][1]` | 49.9989 |
| `field_T.values[205][2]` | 49.9989 |
| `field_T.values[205][20]` | 49.9989 |
| `field_T.values[205][...]` | `<17 项省略>` |
| `field_T.values[...]` | `<202 项省略>` |
| `mass_balance.times_s[0]` | 0 |
| `mass_balance.times_s[1]` | 60 |
| `mass_balance.times_s[2]` | 120 |
| `mass_balance.times_s[3062]` | 1.837e+05 |
| `mass_balance.times_s[...]` | `<3059 项省略>` |
| `mass_balance.M[0]` | 2.55 |
| `mass_balance.M[1]` | 2.53923 |
| `mass_balance.M[2]` | 2.52965 |
| `mass_balance.M[3062]` | 0.118246 |
| `mass_balance.M[...]` | `<3059 项省略>` |
| `mass_balance.Q[0]` | 0 |
| `mass_balance.Q[1]` | 0.010773 |
| `mass_balance.Q[2]` | 0.020346 |
| `mass_balance.Q[3062]` | 2.43175 |
| `mass_balance.Q[...]` | `<3059 项省略>` |
| `mass_balance.eps_M[0]` | 4.441e+14 |
| `mass_balance.eps_M[1]` | 3.204e-14 |
| `mass_balance.eps_M[2]` | 2.183e-14 |
| `mass_balance.eps_M[3062]` | 9.168e-14 |
| `mass_balance.eps_M[...]` | `<3059 项省略>` |
| `frozen_radius_probe.n_cells` | 40 |
| `frozen_radius_probe.dt_s` | 10 |
| `frozen_radius_probe.t_star_shrinking_h` | 50.969 |
| `frozen_radius_probe.t_star_frozen_h` | 129.354 |
| `frozen_radius_probe.speedup` | 2.53789 |
| `frozen_radius_probe.compression` | 0.394028 |
| `construct_conservation.M_ini` | 2.24004 |
| `construct_conservation.M_end` | 2.24004 |
| `construct_conservation.drift` | 0 |
| `construct_conservation.eps_M_not_applicable` | `h_m=0 → Q≡0，eps_M 的分母无定义；本通道用 drift 判守恒` |
| `construct_conservation.pseudo_convection` | 0 |
| `construct_conservation.t_end_s` | 2e+05 |
| `construct_conservation.amplitude` | 0.3 |
| `construct_conservation_pseudo.M_ini` | 2.24004 |
| `construct_conservation_pseudo.M_end` | 1.94786 |
| `construct_conservation_pseudo.drift` | 0.130433 |
| `construct_conservation_pseudo.eps_M_not_applicable` | `h_m=0 → Q≡0，eps_M 的分母无定义；本通道用 drift 判守恒` |
| `construct_conservation_pseudo.pseudo_convection` | 1 |
| `construct_conservation_pseudo.t_end_s` | 2e+05 |
| `construct_conservation_pseudo.amplitude` | 0.3 |
| `pseudo_convection_probe.n_cells` | 40 |
| `pseudo_convection_probe.dt_s` | 10 |
| `pseudo_convection_probe.material_t_star_h` | 50.969 |
| `pseudo_convection_probe.material_eps_M` | 4.2e-14 |
| `pseudo_convection_probe.pseudo_t_star_h` | 48.783 |
| `pseudo_convection_probe.pseudo_eps_M` | 0.568829 |
| `pseudo_convection_probe.eps_M_ratio` | 1.354e+13 |
| `pseudo_convection_probe.construct_drift_material` | 0 |
| `pseudo_convection_probe.construct_drift_pseudo` | 0.130433 |
| `pseudo_convection_probe.construct_drift_ratio` | 1.304e+29 |
| `deviation_P4_C1c.capability` | `P4-C1(c)` |
| `deviation_P4_C1c.checklist_demands` | `eta 坐标方程保留伪对流项 (eta*dR/dt/R)*dC/deta；关闭该项后守恒残差至少变差一个量级` |
| `deviation_P4_C1c.this_code_does` | `不保留该项（物质坐标形式），并把附加该项作为反例通道` |
| `deviation_P4_C1c.why` | `坐标运动项与固相对流项精确相消（§5.4）。附加该项等于把同一物理输运计两次，故它不是被省略而是本就不存在。` |
| `deviation_P4_C1c.measured_constructive_test.setup` | `D=0、h_m=0、非均匀初值 C0(1+0.3cos(pi*eta))、积到 2e5 s；此时没有任何物理机...` |
| `deviation_P4_C1c.measured_constructive_test.material_coords_drift_reported` | 0 |
| `deviation_P4_C1c.measured_constructive_test.pseudo_convection_drift_reported` | 0.231256 |
| `deviation_P4_C1c.measured_real_case.setup` | `N=40、dt=10 s 真实工况` |
| `deviation_P4_C1c.measured_real_case.material_t_star_h_reported` | 50.969 |
| `deviation_P4_C1c.measured_real_case.material_eps_M_reported` | 4.38e-15 |
| `deviation_P4_C1c.measured_real_case.pseudo_t_star_h_reported` | 52.5333 |
| `deviation_P4_C1c.measured_real_case.pseudo_eps_M_reported` | 0.2542 |
| `deviation_P4_C1c.counterexample_reproducibility` | `反例通道的绝对漂移量随离散方式变化（本通道 0.1304 vs §9.3 的 0.2313，同量级同方向）；可...` |
| `deviation_P4_C1c.conclusion` | `实测方向与该子条要求相反：保留该项使守恒残差恶化 13 个量级以上（本次 eps_M 比 1.35e13 倍）...` |
| `deviation_P4_C1c.counterexample_channel` | `solver.simulate_material(pseudo_convection=True)` |
| `deviation_P4_C1c.other_subitems` | `P4-C1 的 (a)(b)(d) 三条照单全部满足，未偏离。` |
| `deviation_P4_C1c.documented_in` | `MODELING_REPORT.md §0.2 / §5.4 / §9.3 / §14` |
| `deviation_P4_C1c.measured_this_run.construct_drift_material` | 0 |
| `deviation_P4_C1c.measured_this_run.construct_drift_pseudo` | 0.130433 |
| `deviation_P4_C1c.measured_this_run.construct_drift_ratio` | 1.304e+29 |
| `deviation_P4_C1c.measured_this_run.material_t_star_h` | 50.969 |
| `deviation_P4_C1c.measured_this_run.material_eps_M` | 4.2e-14 |
| `deviation_P4_C1c.measured_this_run.pseudo_t_star_h` | 48.783 |
| `deviation_P4_C1c.measured_this_run.pseudo_eps_M` | 0.568829 |
| `deviation_P4_C1c.measured_this_run.eps_M_ratio` | 1.354e+13 |
| `deviation_P4_C1c.reconciliation[0].item` | `构造性守恒·物质坐标漂移` |
| `deviation_P4_C1c.reconciliation[0].measured` | 0 |
| `deviation_P4_C1c.reconciliation[0].reference` | 0 |
| `deviation_P4_C1c.reconciliation[0].tol` | 1e-06 |
| `deviation_P4_C1c.reconciliation[0].kind` | `max` |
| `deviation_P4_C1c.reconciliation[0].gap` | 0 |
| `deviation_P4_C1c.reconciliation[0].ok` | 1 |
| `deviation_P4_C1c.reconciliation[0].note` | `物质坐标下总量恒等，漂移应为机器精度` |
| `deviation_P4_C1c.reconciliation[1].item` | `真实工况·物质坐标 t*` |
| `deviation_P4_C1c.reconciliation[1].measured` | 50.969 |
| `deviation_P4_C1c.reconciliation[1].reference` | 50.969 |
| `deviation_P4_C1c.reconciliation[1].tol` | 0.3 |
| `deviation_P4_C1c.reconciliation[1].kind` | `abs` |
| `deviation_P4_C1c.reconciliation[1].gap` | 2.14e-05 |
| `deviation_P4_C1c.reconciliation[1].ok` | 1 |
| `deviation_P4_C1c.reconciliation[1].note` | `生产路径，须复现 §9.3 锚点` |
| `deviation_P4_C1c.reconciliation[2].item` | `真实工况·物质坐标 eps_M` |
| `deviation_P4_C1c.reconciliation[2].measured` | 4.2e-14 |
| `deviation_P4_C1c.reconciliation[2].reference` | 4.38e-15 |
| `deviation_P4_C1c.reconciliation[2].tol` | 1e-12 |
| `deviation_P4_C1c.reconciliation[2].kind` | `max` |
| `deviation_P4_C1c.reconciliation[2].gap` | 4.2e-14 |
| `deviation_P4_C1c.reconciliation[2].ok` | 1 |
| `deviation_P4_C1c.reconciliation[2].note` | `只核对量级类别：机器精度量不可能逐位复现` |
| `deviation_P4_C1c.reconciliation[5].item` | `伪对流/物质坐标 eps_M 倍数` |
| `deviation_P4_C1c.reconciliation[5].measured` | 1.354e+13 |
| `deviation_P4_C1c.reconciliation[5].reference` | 1e+10 |
| `deviation_P4_C1c.reconciliation[5].tol` | 1e+10 |
| `deviation_P4_C1c.reconciliation[5].kind` | `min` |
| `deviation_P4_C1c.reconciliation[5].gap` | 1.354e+13 |
| `deviation_P4_C1c.reconciliation[5].ok` | 1 |
| `deviation_P4_C1c.reconciliation[5].note` | `这是偏离说明真正依赖的断言：保留该项使守恒恶化 10 个量级以上` |
| `deviation_P4_C1c.reconciliation[...]` | `<2 项省略>` |
| `deviation_P4_C1c.reconciled` | 1 |
| `robin_order_probe.table[0].n_cells` | 20 |
| `robin_order_probe.table[0].rel_res_T` | 0.014609 |
| `robin_order_probe.table[0].rel_res_C` | 0.007958 |
| `robin_order_probe.table[0].layer_over_cell` | 2.91714 |
| `robin_order_probe.table[1].n_cells` | 40 |
| `robin_order_probe.table[1].rel_res_T` | 0.004349 |
| `robin_order_probe.table[1].rel_res_C` | 0.003707 |
| `robin_order_probe.table[1].order_T` | 1.74827 |
| `robin_order_probe.table[1].layer_over_cell` | 5.83869 |
| `robin_order_probe.table[2].n_cells` | 80 |
| `robin_order_probe.table[2].rel_res_T` | 0.001212 |
| `robin_order_probe.table[2].rel_res_C` | 0.001271 |
| `robin_order_probe.table[2].order_T` | 1.84341 |
| `robin_order_probe.table[2].layer_over_cell` | 11.6795 |
| `robin_order_probe.orders[0]` | 1.74827 |
| `robin_order_probe.orders[1]` | 1.84341 |
| `robin_order_probe.min_order` | 1.74827 |
| `robin_order_probe.dt_s` | 2.5 |
| `robin_order_probe.why` | `为 ROBIN_TOL_T_Q4=2e-3 提供收敛证据；阶数趋于 2 即纯截断误差` |
| `shrinkage_prediction.combos.附录4+仅径向.R_pred_at_Cinf_cm` | 1.23745 |
| `shrinkage_prediction.combos.附录4+仅径向.R_measured_min_cm` | 1.198 |
| `shrinkage_prediction.combos.附录4+仅径向.rel_dev` | 0.03293 |
| `shrinkage_prediction.combos.附录4+仅径向.monotone_in_C` | 1 |
| `shrinkage_prediction.combos.附录3+仅径向.R_pred_at_Cinf_cm` | 1.32659 |
| `shrinkage_prediction.combos.附录3+仅径向.R_measured_min_cm` | 1.198 |
| `shrinkage_prediction.combos.附录3+仅径向.rel_dev` | 0.107342 |
| `shrinkage_prediction.combos.附录3+仅径向.monotone_in_C` | 1 |
| `shrinkage_prediction.combos.附录4+各向同性.R_pred_at_Cinf_cm` | 1.45221 |
| `shrinkage_prediction.combos.附录4+各向同性.R_measured_min_cm` | 1.198 |
| `shrinkage_prediction.combos.附录4+各向同性.rel_dev` | 0.212193 |
| `shrinkage_prediction.combos.附录4+各向同性.monotone_in_C` | 1 |
| `shrinkage_prediction.best` | `附录4+仅径向` |
| `shrinkage_prediction.direction` | `forward: C -> R（不反演）` |
| `capability.t_star_q4_h` | 51.0444 |
| `capability.t_star_q3_h` | 57.2745 |
| `capability.D_app4_at_C0_50C` | 2.5e-09 |
| `capability.D_app3_at_C0_50C` | 1.347e-08 |
| `capability.D_ratio_app4_over_app3` | 0.185603 |
| `capability.shrink_deviations.附录4+仅径向` | 0.03293 |
| `capability.shrink_deviations.附录3+仅径向` | 0.107342 |
| `capability.shrink_deviations.附录4+各向同性` | 0.212193 |
| `diagnostics.eps_M` | 9.149e-14 |
| `diagnostics.t_star_h` | 51.0444 |
| `diagnostics.t_star_s` | 1.838e+05 |
| `diagnostics.R_at_tstar_cm` | 1.2 |
| `diagnostics.robin_detail.anchor_3h.t_h` | 3 |
| `diagnostics.robin_detail.anchor_3h.R_m` | 0.01552 |
| `diagnostics.robin_detail.anchor_3h.drive_T_degC` | 0.217651 |
| `diagnostics.robin_detail.anchor_3h.drive_C` | 0.634542 |
| `diagnostics.robin_detail.anchor_3h.abs_res_T_W_m2` | 0.0066 |
| `diagnostics.robin_detail.anchor_3h.abs_res_C_kg_m2s` | 6.452e-10 |
| `diagnostics.robin_detail.anchor_3h.rel_res_T` | 0.001213 |
| `diagnostics.robin_detail.anchor_3h.rel_res_C` | 0.001271 |
| `diagnostics.robin_detail.anchor_3h.D_surface_m2_s` | 1.813e-09 |
| `diagnostics.robin_detail.anchor_3h.Bi_m` | 6.84953 |
| `diagnostics.robin_detail.anchor_3h.layer_over_cell` | 11.6796 |
| `diagnostics.robin_detail.tstar.t_h` | 51.0444 |
| `diagnostics.robin_detail.tstar.R_m` | 0.012 |
| `diagnostics.robin_detail.tstar.drive_T_degC` | 3.197e-13 |
| `diagnostics.robin_detail.tstar.drive_C` | 0.002616 |
| `diagnostics.robin_detail.tstar.abs_res_T_W_m2` | 1.243e-12 |
| `diagnostics.robin_detail.tstar.abs_res_C_kg_m2s` | 9.308e-10 |
| `diagnostics.robin_detail.tstar.rel_res_T` | 0.13822 |
| `diagnostics.robin_detail.tstar.rel_res_C` | 0.444535 |
| `diagnostics.robin_detail.tstar.D_surface_m2_s` | 9.381e-12 |
| `diagnostics.robin_detail.tstar.Bi_m` | 1023 |
| `diagnostics.robin_detail.tstar.layer_over_cell` | 0.078179 |
| `diagnostics.robin_detail.scale_T_W_m2` | 549.972 |
| `diagnostics.robin_detail.scale_C_kg_m2s` | 2e-06 |
| `diagnostics.center_sym_C.grad_center` | 1.156e-07 |
| `diagnostics.center_sym_C.grad_surface` | -1.48648 |
| `diagnostics.center_sym_C.ratio` | 7.779e-08 |
| `diagnostics.T_range[0]` | 28 |
| `diagnostics.T_range[1]` | 50.0498 |
| `diagnostics.C_range[0]` | 0.052604 |
| `diagnostics.C_range[1]` | 2.55 |
| `diagnostics.R_range_cm[0]` | 1.2 |
| `diagnostics.R_range_cm[1]` | 2 |
| `diagnostics.maxC_at_tstar` | 0.15 |
| `diagnostics.argmax_at_tstar` | 0 |
| `diagnostics.max_diff_C` | 4.441e-15 |
| `diagnostics.argmax_max` | 0 |
| `diagnostics.max_center_deficit` | 1.288e-14 |
| `diagnostics.n_center_violations` | 0 |
| `diagnostics.prop_ptp_min.rho` | 6.16063 |
| `diagnostics.prop_ptp_min.cp` | 11.9075 |
| `diagnostics.prop_ptp_min.k` | 0.001108 |
| `diagnostics.prop_ptp_min.D` | 3.316e-12 |
| `diagnostics.T_K_range[0]` | 301.15 |
| `diagnostics.T_K_range[1]` | 323.2 |
| `diagnostics.picard_rounds_max` | 3 |
| `xlsx_report.path` | `C:\Users\17038\AppData\Roaming\ModexData\library-cxscTJ...` |
| `xlsx_report.sheets[0]` | `Sheet1` |
| `xlsx_report.Sheet1.n_rows` | 3063 |
| `xlsx_report.Sheet1.t_first` | 0 |
| `xlsx_report.Sheet1.t_last` | 183720 |
| `xlsx_report.Sheet1.dt_s` | 60 |
| `xlsx_report.Sheet1.n_cols` | 21 |
| `xlsx_report.Sheet1.sampled_cells` | 200 |
| `summary.t_star_h` | 51.0444 |
| `summary.R_at_tstar_cm` | 1.2 |
| `summary.eps_M` | 9.149e-14 |
| `summary.shrink_speedup` | 2.53789 |
| `summary.t_star_q3_h` | 57.2745 |
| `summary.D_ratio_app4_over_app3` | 0.185603 |

### `sensitivity_results.json`（115 条）

| 数据路径 | 数值 |
|---|---|
| `analysis` | `one_at_a_time_sensitivity` |
| `method_claim` | `MC-08` |
| `response_quantity` | `t_star_h` |
| `title` | `单因素 ±10% 灵敏度扫描（响应量 t*）` |
| `source_section` | `MODELING_REPORT §9.1` |
| `note` | `两个方向均实算并落盘；空扰动 factor=1.0 用于证明扰动通道确实接进求解器` |
| `main_group.base_t_star_h` | 56.495 |
| `main_group.n_cells` | 20 |
| `main_group.dt_s` | 20 |
| `main_group.factor_high` | 1.1 |
| `main_group.factor_low` | 0.9 |
| `main_group.rows[0].id` | `arrhenius_exp_T` |
| `main_group.rows[0].label` | `Arrhenius 指数系数 3850` |
| `main_group.rows[0].kind` | `exp_T` |
| `main_group.rows[0].t_star_high_h` | 171.929 |
| `main_group.rows[0].t_star_low_h` | 23.1085 |
| `main_group.rows[0].rel_change_high` | 2.04326 |
| `main_group.rows[0].rel_change_low` | -0.590963 |
| `main_group.rows[0].abs_rel_max` | 2.04326 |
| `main_group.rows[0].t_star_neutral_h` | 56.495 |
| `main_group.rows[0].neutral_dev_h` | 0 |
| `main_group.rows[0].ref_t_star_high_h` | 171.929 |
| `main_group.rows[0].ref_t_star_low_h` | 23.1085 |
| `main_group.rows[0].ref_rel_change_high` | 2.0433 |
| `main_group.rows[0].ref_rel_change_low` | -0.591 |
| `main_group.rows[0].both_directions` | 1 |
| `main_group.rows[1].id` | `moisture_exp_C` |
| `main_group.rows[1].label` | `含水率指数系数 a=0.45` |
| `main_group.rows[1].kind` | `exp_C` |
| `main_group.rows[1].t_star_high_h` | 71.6333 |
| `main_group.rows[1].t_star_low_h` | 45.1089 |
| `main_group.rows[1].rel_change_high` | 0.267958 |
| `main_group.rows[1].rel_change_low` | -0.201542 |
| `main_group.rows[1].abs_rel_max` | 0.267958 |
| `main_group.rows[1].t_star_neutral_h` | 56.495 |
| `main_group.rows[1].neutral_dev_h` | 0 |
| `main_group.rows[1].ref_t_star_high_h` | 71.6333 |
| `main_group.rows[1].ref_t_star_low_h` | 45.1089 |
| `main_group.rows[1].ref_rel_change_high` | 0.268 |
| `main_group.rows[1].ref_rel_change_low` | -0.2015 |
| `main_group.rows[1].both_directions` | 1 |
| `main_group.rows[2].id` | `radius_R0` |
| `main_group.rows[2].label` | `初始半径 R0` |
| `main_group.rows[2].kind` | `radius` |
| `main_group.rows[2].t_star_high_h` | 67.5694 |
| `main_group.rows[2].t_star_low_h` | 46.4273 |
| `main_group.rows[2].rel_change_high` | 0.196023 |
| `main_group.rows[2].rel_change_low` | -0.178205 |
| `main_group.rows[2].abs_rel_max` | 0.196023 |
| `main_group.rows[2].t_star_neutral_h` | 56.495 |
| `main_group.rows[2].neutral_dev_h` | 0 |
| `main_group.rows[2].ref_t_star_high_h` | 67.5694 |
| `main_group.rows[2].ref_t_star_low_h` | 46.4273 |
| `main_group.rows[2].ref_rel_change_high` | 0.196 |
| `main_group.rows[2].ref_rel_change_low` | -0.1782 |
| `main_group.rows[2].both_directions` | 1 |
| `main_group.rows[5].id` | `h_conv` |
| `main_group.rows[5].label` | `对流换热系数 h` |
| `main_group.rows[5].kind` | `h` |
| `main_group.rows[5].t_star_high_h` | 56.4879 |
| `main_group.rows[5].t_star_low_h` | 56.5037 |
| `main_group.rows[5].rel_change_high` | -0.000126 |
| `main_group.rows[5].rel_change_low` | 0.000154 |
| `main_group.rows[5].abs_rel_max` | 0.000154 |
| `main_group.rows[5].t_star_neutral_h` | 56.495 |
| `main_group.rows[5].neutral_dev_h` | 0 |
| `main_group.rows[5].ref_t_star_high_h` | 56.4879 |
| `main_group.rows[5].ref_rel_change_high` | -0.0001 |
| `main_group.rows[5].both_directions` | 1 |
| `main_group.rows[...]` | `<2 项省略>` |
| `main_group.ranking_by_abs_rel_max[0]` | `arrhenius_exp_T` |
| `main_group.ranking_by_abs_rel_max[1]` | `moisture_exp_C` |
| `main_group.ranking_by_abs_rel_max[2]` | `radius_R0` |
| `main_group.ranking_by_abs_rel_max[5]` | `h_conv` |
| `main_group.ranking_by_abs_rel_max[...]` | `<2 项省略>` |
| `main_group.ranking_reference[0]` | `arrhenius_exp_T` |
| `main_group.ranking_reference[1]` | `moisture_exp_C` |
| `main_group.ranking_reference[2]` | `radius_R0` |
| `main_group.ranking_reference[5]` | `h_conv` |
| `main_group.ranking_reference[...]` | `<2 项省略>` |
| `env_group.base_t_star_h` | 57.0168 |
| `env_group.n_cells` | 40 |
| `env_group.dt_s` | 10 |
| `env_group.rows[0].c_inf_factor` | 2 |
| `env_group.rows[0].t_star_h` | 61.2834 |
| `env_group.rows[0].rel_change` | 0.07483 |
| `env_group.rows[1].c_inf_factor` | 0.5 |
| `env_group.rows[1].t_star_h` | 56.1087 |
| `env_group.rows[1].rel_change` | -0.015927 |
| `env_group.ref_base_t_star_h` | 57.0168 |
| `env_group.ref_t_star_factor2_h` | 61.2834 |
| `env_group.ref_t_star_factor05_h` | 56.1087 |
| `q4_cp_group.base_t_star_h` | 50.969 |
| `q4_cp_group.n_cells` | 40 |
| `q4_cp_group.dt_s` | 10 |
| `q4_cp_group.rows[0].cp_factor` | 1.2 |
| `q4_cp_group.rows[0].t_star_h` | 50.9871 |
| `q4_cp_group.rows[0].rel_change` | 0.000356 |
| `q4_cp_group.rows[1].cp_factor` | 0.8 |
| `q4_cp_group.rows[1].t_star_h` | 50.9514 |
| `q4_cp_group.rows[1].rel_change` | -0.000344 |
| `q4_cp_group.ref_base_t_star_h` | 50.969 |
| `q4_cp_group.ref_t_star_set_h[0]` | 50.9514 |
| `q4_cp_group.ref_t_star_set_h[1]` | 50.9871 |
| `ranking[0]` | `arrhenius_exp_T` |
| `ranking[1]` | `moisture_exp_C` |
| `ranking[2]` | `radius_R0` |
| `ranking[5]` | `h_conv` |
| `ranking[...]` | `<2 项省略>` |
| `checks.main_rows` | 6 |
| `checks.ranking_matches_reference` | 1 |
| `checks.cp_max_abs_rel` | 0.000356 |
| `checks.d_exponent_over_convection_ratio` | 19.2179 |
| `checks.n_assertions_passed` | 34 |
| `conclusion` | `t* 的不确定性由 D 的两个指数系数与几何尺寸主导（最敏感项相对变化 2.0433），对两个对流系数最不敏感...` |

---

## 已生成的 TABLE 文件（论文应直接嵌入这些表，不要自己手抄）

### `figures/TABLE_descriptive_stats.md` (713 字节)

```markdown
**表 8：输入数据描述性统计**

| 变量 | 单位 | 样本数 $n$ | 最小值 | 最大值 | 均值 | 标准差 |
|---|---|---|---|---|---|---|
| 烘房温度 $T_\infty$ | °C | 241 | 28.0000 | 50.2460 | 47.2453 | 5.1148 |
| 烘房水分浓度 $C_\infty$ | kg/kg | 241 | 0.01963 | 0.05025 | 0.04476 | 0.00814 |
| 药材半径 $R$ | cm | 145 | 1.1980 | 2.0000 | 1.2460 | 0.1270 |

> 注：附件 1 覆盖 0–4 h，采样间隔 60 s；附件 2 覆盖 0–72 h，采样间隔 1800 s。
> 注：半径由 2.000 cm 收缩至 1.198 cm（累计 40.1%），并在 67.0 h 后不再变化。
> 注：标准差按样本标准差（$n-1$）计算。数据来源：user_data/附件1.xlsx、附件2.xlsx。
```

### `figures/TABLE_main_results.md` (992 字节)

```markdown
**表 7：四问主结果汇总**

| 问题 | 模型设定 | 关键时刻 | 结果 |
|---|---|---|---|
| 问题 1 | 预热段温度场与水分场（常物性，附录 2） | $t$=30 min | $T_c$=33.576 °C；$T_s$=36.786 °C；$C_c$=2.5500；$C_s$=1.5104 |
| 问题 2 | 变物性双向耦合（附录 3） | $t$=3 h | $T_c$=49.849 °C；$T_s$=49.966 °C；$C_c$=1.7662；$C_s$=1.0081 |
| 问题 3 | 固定域烘干终点（$\max_r C<0.15$ kg/kg，全域最大值） | $t^*$=57.2745 h | =2.3864 d；终点 $\max_r C$=0.149999 |
| 问题 4 | 收缩域烘干终点（物质坐标 $\eta=r/R(t)$，附录 4） | $t^*$=51.0444 h | =2.1269 d；$R(t^*)$=1.200 cm；较问题 3 缩短 6.2301 h |

> 注：$C$ 为干基含水率（kg/kg），下标 $c$、$s$ 分别指中心 $r=0$ 与表面 $r=R$。
> 注：问题 4 相对问题 3 的加速比（冻结半径对照 / 收缩）为 2.5379，见正文收缩机理讨论。
> 注：数据来源：figures/all_results.json 的 answers 字段。
```

### `figures/TABLE_sensitivity.md` (1000 字节)

```markdown
**表 10：参数敏感性排序**

| 序 | 参数 | $\times$1.1 的 $t^*$ (h) | 相对变化 | $\times$0.9 的 $t^*$ (h) | 相对变化 | 最大绝对相对变化 |
|---|---|---|---|---|---|---|
| 1 | Arrhenius 指数系数 3850 | 171.929 | +204.33% | 23.109 | -59.10% | 204.33% |
| 2 | 含水率指数系数 a=0.45 | 71.633 | +26.80% | 45.109 | -20.15% | 26.80% |
| 3 | 初始半径 R0 | 67.569 | +19.60% | 46.427 | -17.82% | 19.60% |
| 4 | D 前指数因子 2.4e-3 | 52.021 | -7.92% | 61.987 | +9.72% | 9.72% |
| 5 | 对流传质系数 h_m | 55.873 | -1.10% | 57.283 | +1.39% | 1.39% |
| 6 | 对流换热系数 h | 56.488 | -0.01% | 56.504 | +0.02% | 0.02% |

> 注：基准 $t^*$=56.4950 h（敏感性算例统一用 20 单元、$\Delta t$=20 s 的粗网格以控算量，故与表 7 的 57.2745 h 略有差异）。
> 注：排序键为最大绝对相对变化，与 ranking_by_abs_rel_max 一致。
> 注：数据来源：figures/sensitivity_results.json 的 main_group 字段。
```

### `figures/TABLE_validation.md` (1337 字节)

```markdown
**表 9：模型校验汇总**

| 校验项 | 实测值 | 判据 | 说明 | 结论 |
|---|---|---|---|---|
| 问题 1 水分守恒残差 $\varepsilon_M$ | 4.49e-13 | $<10^{-2}$ | 1800 个采样时刻的最大值 | 通过 |
| 问题 2 水分守恒残差 $\varepsilon_M$ | 1.16e-12 | $<10^{-2}$ | 10800 个采样时刻的最大值 | 通过 |
| 问题 3 水分守恒残差 $\varepsilon_M$ | 4.09e-14 | $<10^{-2}$ | 3437 个采样时刻的最大值 | 通过 |
| 问题 4 水分守恒残差 $\varepsilon_M$ | 9.30e-14 | $<10^{-2}$ | 3062 个采样时刻的最大值 | 通过 |
| 问题 1 数值解 vs Bessel 级数解 | 2.06e-03 K | — | 2000 项级数，$Bi_h$=1.3889 | 通过 |
| 网格/时步收敛（逐级相对变化） | 0.452% | $<1\%$ | 40→80 单元，$\Delta t$ 10→5 s | 通过 |
| 显式格式稳定步长（隐式格式无需受限） | 0.1942 s | — | 实际隐式步长 5 s，为其 26 倍 | 通过 |

> 注：特征时间 $\tau_{heat}$=2368.9 s、$\tau_{mass}$=8.101e+04 s，二者相差约 34 倍，故温度先达平衡而水分主导总时长。
> 注：守恒残差为相对量纲一量；$t=0$ 时累计通量 $Q=0$ 使相对残差无定义，已剔除。
> 注：数据来源：figures/problem_{1..4}_results.json 的 mass_balance、analytic_validation、grid_convergence、stability_probe 字段。
```
