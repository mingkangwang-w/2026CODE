# 图表证据溯源记录（数据图阶段）

生成日期：2026-09-11　题号：2026A 药材的烘干问题　输出格式：docx（图为 PNG）

本文件逐图记录：对应问题/情形、生成脚本、数据文件与字段、参数条件、样本量、
统计量与不确定度口径。**未知项一律写“未知”，不以推测填充。**

## 总览

| 项 | 值 |
|---|---|
| FIGURE_MANIFEST 中 DATA 图 | 20 |
| 已生成 PNG | 20（名称与清单逐一对应，无多余、无缺漏） |
| 生成脚本 | figures/gen_fig_*.py，20 个，一图一脚本 |
| 表格 | figures/TABLE_{main_results,descriptive_stats,validation,sensitivity}.md（表 7~表 10） |
| 插图清单 | figures/latex_includes.tex（20 个 figure 环境） |
| 本阶段不负责 | TIKZ 4 张、DRAWIO 6 张、GPTIMG 1 张（交下游 paper-figure-html / drawio 步骤） |

### 通用口径

- **数值来源**：全部读自 `figures/*.json`（由 `code/main.py` 实跑产出）或
  `user_data/附件{1,2}.xlsx` 原始数据；图脚本内不硬编码结果数值。
- **物性曲线**：`fig_property_laws`、`fig_D_landscape` 直接调用生产代码
  `code/properties.py` 的本构函数求值，不在图脚本里重写公式。
- **不确定度**：本题为确定性 PDE 数值求解，**无统计抽样、无观测噪声、无置信区间**。
  因此除 `fig_q4_shrink_validation` 的 ±1.96 SD 一致界外，其余图不含误差棒或
  置信带；这不是遗漏，而是问题性质决定。所谓“误差”均为**数值误差**
  （守恒残差、解析对照偏差、网格收敛相对变化），口径见表 9。
- **样本量含义**：以下“样本量”指输出采样点数（时刻数 × 径向节点数），
  由各 results JSON 的 `grid` 段决定，不是统计样本。
- **判据常数**：`C_th = 0.15` kg/kg（干基），来自题面终点判据，非拟合值。
## 一、输入数据与物性（4 张）

### fig_oven_input
- 问题/情形：全局输入——附件 1 烘房环境曲线
- 脚本：`figures/gen_fig_oven_input.py`
- 数据与字段：`user_data/附件1.xlsx` 列「时间」「温度」「水分浓度」
- 参数条件：0–4 h，采样间隔 60 s
- 样本量：241 行
- 统计量/不确定度：无统计量，原始序列直绘；平台起点由 `温度` 首次达最大值处取出
  （10800 s），非拟合

### fig_shrink_radius
- 问题/情形：问题 4 输入——附件 2 半径收缩曲线
- 脚本：`figures/gen_fig_shrink_radius.py`
- 数据与字段：`user_data/附件2.xlsx` 列「时间」「半径」
- 参数条件：0–72 h，采样间隔 1800 s
- 样本量：145 行
- 统计量/不确定度：无统计量；R 由 2.000 cm 降至 1.198 cm（累计 40.1%），
  停滞点取 `R <= R_end + 1e-12` 首次成立处（67.0 h）

### fig_property_laws
- 问题/情形：全局——附录 2/3/4 三组物性本构对照
- 脚本：`figures/gen_fig_property_laws.py`
- 数据与字段：`code/properties.py` 的 `APPENDIX2/3/4`（系数溯源至
  `PROBLEM_FACTS.json`）；温度取 `code/params.py` 的 `T_INF_PLATEAU_REF`
- 参数条件：C 扫过 [0, C0]，C0=2.55；(d) 面板 D 取平台温度下的值
- 样本量：解析曲线，非采样数据（网格点数仅为绘图分辨率）
- 统计量/不确定度：不适用（确定性本构公式）

### fig_D_landscape
- 问题/情形：全局——扩散系数 D(C,T) 地形，解释末期刚性
- 脚本：`figures/gen_fig_D_landscape.py`
- 数据与字段：`code/properties.py` 的 `APPENDIX3`，
  D = 2.4e-3·exp(-0.45/C)·exp(-3850/T_K)
- 参数条件：C ∈ [C_th/2, C0]，T ∈ [T0, 平台均温 + 5 K]
- 样本量：解析曲面，非采样数据
- 统计量/不确定度：不适用（确定性本构公式）

## 二、问题 1：预热平衡阶段（5 张）

四张场图与剖面图共用同一次求解：`code/problem_1.py`，常物性（附录 2），
网格 80 单元、dt=0.25 s、dr=0.025 cm，输出降采样为 dt=1 s、dr=0.1 cm。

### fig_q1_temp_profiles
- 问题/情形：问题 1 指定时刻温度径向剖面
- 脚本：`figures/gen_fig_q1_temp_profiles.py`
- 数据与字段：`figures/problem_1_results.json` → `paper_tables.table1_temperature`
  与 `output_radii_cm`
- 参数条件：7 个指定时刻（100–1800 s）× 5 个径向位置
- 样本量：7 × 5 = 35 个数值
- 统计量/不确定度：无统计量，直读求解结果

### fig_q1_moist_profiles
- 问题/情形：问题 1 水分径向剖面（表层陡降 + 中心平台）
- 脚本：`figures/gen_fig_q1_moist_profiles.py`
- 数据与字段：`problem_1_results.json` → `field_C.values`、`field_C.times_s`、
  `output_radii_cm`
- 参数条件：从 181 个输出时刻中取 7 个叠绘；C0=2.55
- 样本量：field_C 为 181 时刻 × 21 节点
- 统计量/不确定度：无统计量，直读求解结果

### fig_q1_temp_field
- 问题/情形：问题 1 温度时空场
- 脚本：`figures/gen_fig_q1_temp_field.py`
- 数据与字段：`problem_1_results.json` → `field_T`（`times_s`、`values`）、
  `output_radii_cm`
- 参数条件：0–1800 s，21 个径向节点
- 样本量：181 × 21 = 3801
- 统计量/不确定度：无统计量；等值线间隔 1 °C

### fig_q1_moist_field
- 问题/情形：问题 1 水分时空场与扩散渗透前沿
- 脚本：`figures/gen_fig_q1_moist_field.py`
- 数据与字段：`problem_1_results.json` → `field_C`、`output_radii_cm`
- 参数条件：0–1800 s，21 个径向节点
- 样本量：181 × 21 = 3801
- 统计量/不确定度：渗透前沿为**派生量**，按阈值 0.99·C0 逐时刻线性插值定位
  （定义写在脚本首注），非文献值也非拟合值

### fig_q1_analytic_validation
- 问题/情形：问题 1 数值解 vs Bessel 级数半解析解
- 脚本：`figures/gen_fig_q1_analytic_validation.py`
- 数据与字段：`problem_1_results.json` → `analytic_validation`
  （`detail` 的 7 个时刻 × `numeric`/`analytic` 各 5 位置、`max_abs_dev`）
- 参数条件：级数取 2000 项，Bi_h=1.3889；仅在常物性设定下可比
- 样本量：7 时刻 × 5 位置 = 35 对配对值
- 统计量/不确定度：偏差为**数值格式误差**，逐时刻最大绝对偏差，
  全局最大 2.06e-03 K；无统计置信区间（确定性对照）
## 三、问题 2：变物性双向耦合（3 张）

共用求解：`code/problem_2.py`，附录 3 变物性 + Picard 耦合，
网格 80 单元、dt=0.5 s，输出 3 h 内。

### fig_q2_stage_transition
- 问题/情形：问题 2 升温段与恒温段的分界
- 脚本：`figures/gen_fig_q2_stage_transition.py`
- 数据与字段：`problem_2_results.json` → `center_series`、`surface_series`、
  `env_series`（`T_inf`）
- 参数条件：0–3 h
- 样本量：10801 个时刻
- 统计量/不确定度：阶段分界为**派生量**，取 `T_inf` 首次进入
  (最大值 − 0.5 °C) 的时刻，判据写在脚本内，不预设 3 h 中某个整点

### fig_q2_moist_ridgeline
- 问题/情形：问题 2 水分径向分布的堆叠演化
- 脚本：`figures/gen_fig_q2_moist_ridgeline.py`
- 数据与字段：`problem_2_results.json` → `field_C`、`output_radii_cm`
- 参数条件：从 181 个输出时刻中取 9 个堆叠
- 样本量：field_C 为 181 时刻 × 21 节点
- 统计量/不确定度：每条剖面的刻痕为**质量中位半径**（按 `cumsum(C·r)` 达 50%
  处插值），是分布位置的稳健指标，非均值、非拟合参数

### fig_q2_flux_balance
- 问题/情形：问题 2 水分守恒校验（累计失水 vs 域内减少）
- 脚本：`figures/gen_fig_q2_flux_balance.py`
- 数据与字段：`problem_2_results.json` → `mass_balance`（`M`、`Q`、`times_s`）
- 参数条件：0–3 h
- 样本量：10801 个时刻
- 统计量/不确定度：残差为**相对数值残差** |(C0−M)−Q| / Q，非统计误差；
  对数轴下限由数据最小正值向下取整定出，不设固定地板值。
  **注意**：t=0 处 Q=0 使相对残差无定义，作图与统计均剔除该点

## 四、问题 3：固定域烘干终点（3 张）

共用求解：`code/problem_3.py`，附录 3 物性，80 单元、dt=5 s，
判据 max_r C < 0.15 kg/kg，t* = 57.2745 h。

### fig_q3_center_decay
- 问题/情形：问题 3 中心含水率长时程衰减与判据达成
- 脚本：`figures/gen_fig_q3_center_decay.py`
- 数据与字段：`problem_3_results.json` → `center_series`、`surface_series`、
  `answer.t_star_h`、`criterion_variants`
- 参数条件：0–57.27 h
- 样本量：3438 个时刻
- 统计量/不确定度：无统计量；表面达标时刻 12.56 h 取自 `criterion_variants`，
  用于说明判据口径差异（表面达标远早于全域达标）

### fig_q3_threshold_contour
- 问题/情形：问题 3 干燥前沿在 r–t 平面的推进
- 脚本：`figures/gen_fig_q3_threshold_contour.py`
- 数据与字段：`problem_3_results.json` → `field_C`、`output_radii_cm`、
  `answer.t_star_h`
- 参数条件：59 个输出时刻 × 21 个径向节点
- 样本量：59 × 21 = 1239
- 统计量/不确定度：等值线由 matplotlib 在上述网格上插值生成；
  细等值线取 [0.3, 0.5, 0.8, 1.2, 1.6, 2.0]（原含 2.0/2.4 两级在 t<3 h 内
  相距不足 1 h、标签互压，已舍去最上一级）

### fig_q3_hovmoller
- 问题/情形：问题 3 全时程水分场，凸显末期长尾
- 脚本：`figures/gen_fig_q3_hovmoller.py`
- 数据与字段：`problem_3_results.json` → `field_C`、`output_radii_cm`、
  `answer.t_star_h`
- 参数条件：同上，59 × 21
- 样本量：1239
- 统计量/不确定度：无统计量。**偏离规划一处**：配方 advanced#29 原用
  `RdBu_r` 色图，本项目禁用红绿/红蓝发散色图，改用 `YlGnBu`，
  图表语法（时间纵轴自上而下、等值线叠加、色条）保持不变

## 五、问题 4 与跨问对比（3 张）

共用求解：`code/problem_4.py`，物质坐标 η=r/R(t) + 附录 4 物性，
80 单元、dt=5 s、Picard 最多 3 轮，t* = 51.0444 h。

### fig_q4_moving_domain_heatmap
- 问题/情形：问题 4 收缩域上的水分时空分布
- 脚本：`figures/gen_fig_q4_moving_domain_heatmap.py`
- 数据与字段：`problem_4_results.json` → `field_C`（**落在等距 η 网格上**，
  非物理半径）、`radius_series.R_cm`、`answer.t_star_h`、`answer.R_at_tstar_cm`
- 参数条件：206 个输出时刻 × 21 个 η 节点；R(t) 由 3063 点插值到场时刻
- 样本量：206 × 21 = 4326
- 统计量/不确定度：无统计量。**坐标口径**：作图时按 r = η·R(t) 逐时刻映射回
  物理半径，域外区域遮罩。该字段的 η 属性经查 `code/resultio.py` 的
  `field_grid`（等距跨步、无坐标变换）确认，未按物理半径误读

### fig_q4_shrink_validation
- 问题/情形：问题 4 收缩律自洽性——绝干质量守恒预测半径 vs 附件 2 实测半径
- 脚本：`figures/gen_fig_q4_shrink_validation.py`
- 数据与字段：`problem_4_results.json` → `field_C`、`radius_series`；
  预测律调用 `code/properties.py` 的 `predict_radius_radial_only` + `APPENDIX4`
- 参数条件：体均含水率按圆柱体积元权重 2η 在 η 网格上积分；
  预测为**正向**计算，不由实测反演
- 样本量：206 个配对时刻
- 统计量/不确定度：Bland–Altman 口径——平均偏差、±1.96 SD 一致界
  （SD 为样本标准差 n−1）、比例偏差为差值对均值的一次回归斜率。
  这是全部图中**唯一**含区间的图，其区间是配对差值的分散度，
  不是抽样置信区间。终点相对偏差 3.29%

### fig_q34_compare_dumbbell
- 问题/情形：问题 3（固定域）与问题 4（收缩域）各位置达标时刻对比
- 脚本：`figures/gen_fig_q34_compare_dumbbell.py`
- 数据与字段：`problem_3_results.json` 与 `problem_4_results.json` 的
  `field_C` 及各自 `answer.t_star_h`（57.2745 / 51.0444）
- 参数条件：取 5 个无量纲位置 η ∈ {0, 0.25, 0.50, 0.75, 1}；
  **以 η 而非物理半径配对**，因问题 4 的物理半径随时间变化，只有物质坐标可比
- 样本量：5 个配对位置（各自由 59 / 206 个时刻的序列插值求得）
- 统计量/不确定度：达标时刻为**派生量**，取该位置 C 首次 ≤0.15 处沿时间线性插值；
  无统计不确定度
## 六、稳健性与数值可靠性（2 张）

### fig_sensitivity_tornado
- 问题/情形：6 个参数对 t* 的敏感性排序
- 脚本：`figures/gen_fig_sensitivity_tornado.py`
- 数据与字段：`figures/sensitivity_results.json` → `main_group`
  （`rows` 的 `rel_change_high`/`rel_change_low`、`ranking_by_abs_rel_max`、
  `base_t_star_h`）
- 参数条件：单因子 ±10%（factor 1.1 / 0.9）；**粗网格 20 单元、dt=20 s**，
  基准 t*=56.4950 h，与问题 3 正式结果 57.2745 h 不同源，不可混用
- 样本量：6 个因子 × 2 个方向 = 12 次独立求解
- 统计量/不确定度：相对变化 = (t*_扰动 − t*_基准)/t*_基准；单因子 OAT 设计，
  **不含交互项**，故不能据此推断参数组合效应

### fig_grid_convergence
- 问题/情形：网格与时间步收敛性（能力项 P3-C4）
- 脚本：`figures/gen_fig_grid_convergence.py`
- 数据与字段：`problem_3_results.json` → `grid_convergence.table`
  （3 级：20/40/80 单元，dt 20/10/5 s，dr 0.1/0.05/0.025 cm，
  t* 56.4950/57.0168/57.2745 h，逐级相对变化 —/0.9236%/0.4519%）与 `tol=0.01`
- 参数条件：空间与时间同步加密（每级 dr 与 dt 同时减半）
- 样本量：3 个网格级别
- 统计量/不确定度：逐级相对变化对比 1% 容差；相对变化逐级近似减半，
  与一阶隐式格式预期一致。**未做 Richardson 外推**，故未给收敛阶的点估计

## 七、质量闸结果

| 检查 | 命令 | 结果 |
|---|---|---|
| 保存钩子（遮挡/对比度/字号） | 各 `gen_fig_*.py` 保存时自动执行 | 20/20 通过 |
| 图字号与留白 | `_utils/figure_pdf_quality_check.py figures --paper paper` | 通过 |
| 图内文字预算 | `_utils/figure_text_budget.py figures` | 21 个脚本通过 |
| 规划图型 vs 实际代码 | `_utils/recipe_audit.py --plan PROBLEM_ANALYSIS.md --figdir figures` | 可判定 9 张全部一致 |
| 数据图视觉复核 | `_utils/data_fig_vision_check.pyc <png>` 逐图 | 20/20 PASS |
| 表格数据回溯 | 独立脚本重算 25 个单元格 | 0 失败，见 `figures/TABLE_DATA_CHECK_PASSED.txt` |

修复记录（均改图，未改校验器）：

1. `fig_q1_temp_profiles`：表面读数压在上升曲线上 → 移至曲线上方左侧空白；
   中心读数一度下移又压到淡色基线曲线，故复原至上方楔形空白。
2. `fig_q2_stage_transition`：中心含水率端点读数压在下降曲线上 → 改置于端点下方；
   图例由硬编码 `loc` 改为 `auto_legend` 实测定位。
3. `fig_q4_shrink_validation`：SimHei 缺 U+2212 字形 → 纵轴标签减号改走 mathtext
   （已核实 `plot_utils.py` 已设 `axes.unicode_minus: False`，刻度标签本无此问题）。
4. `fig_q34_compare_dumbbell`：连接线原用 `ax.plot`，未命中配方要求的
   `hlines+scatter` 图型签名 → 改为 `ax.hlines`。
5. `fig_q3_threshold_contour`：视觉复核指出底部 `2.4`/`2.0` 两个等值线标签互压
   → 舍去最上一级等值线。

## 八、口径更正与遗留事项

- **已更正**：`PROBLEM_ANALYSIS.md` 的 FIGURE_MANIFEST 中 `fig_q34_compare_dumbbell`
  一行原写“总时长 57.1 h vs 52.6 h”，与 results JSON 的 57.2745 / 51.0444 h 不符
  （规划期占位数）。已按数据改正，使规划与产物一致。
- **表编号**：表 1~表 6 为题目要求的答案表（`paper_tables` 的 table1..table6），
  本阶段新增表自表 7 起编，避免与答案表冲突。
- **本阶段未覆盖**：TIKZ 4 张（几何/控制体/边界条件/坐标映射）、
  DRAWIO 6 张（路线图与四问流程图、求解器架构）、GPTIMG 1 张（烘房场景），
  由下游 `paper-figure-html` / `paper-figure-drawio` 步骤产出。
- **未知项**：附件 1/2 的测量不确定度（仪器精度、重复测量次数）题面未给出，
  故全部图未标观测误差棒 —— 此为**未知**，不是判定为零。

## 九、复核轮次记录（2026-09-11）

本轮为**验收复核**，未新增、未重画任何图（既有 20 张 PNG 的字节未变动）。

| 检查项 | 工具 | 结果 |
|---|---|---|
| 图表代码静态检查 | `_utils/figure_check.sh` | RC=0，0 CRITICAL / 0 WARNING / 0 配方问题 |
| 规划图型 vs 实际 API | 同上 | 9 张可判定图全部命中规划图型 |
| 图内标注预算 | 同上（AST 扫描） | 22 个脚本通过，标注仅含数值/短锚点 |
| 数据图视觉质检 | `_utils/data_fig_vision_check.pyc` | 20/20 PASS，0 pending / 0 skipped |
| Markdown 三线表合规 | 本轮临时脚本 | 4 表列数一致、分隔行完整、无 LaTeX 残留 |
| caption 长度 | 本轮临时脚本 | 20 条全部 ≤15 字，无句读、无结论内嵌 |
| PNG 分辨率 | PIL | 全部 ≥300 DPI（docx 中文防糊） |

**视觉质检说明**：`MH_DATA_FIG_VISION=1` 已开启，本轮逐张调用 vision 复核，
判定与 PNG 内容哈希绑定记入 `_tmp/datafig_vision_passed.txt`。
其中 5 次调用遇 `WinError 10054`（远端连接重置）——该工具在 API 异常时会
**失败即放行**并打印 PASS，故这 5 次一律不采信、剔除后重试至拿到干净判定，
未用异常返回充当通过凭据。

**两处已知读数陷阱复核（沿用既有定案，未改数据）**：

1. `problem_4_results.json` 的 `field_C` 落在等距 $\eta=r/R(t)$ 网格上，**不是**物理半径。
   `gen_fig_q4_moving_domain_heatmap.py:41` 以 `RR = eta[None,:] * R_at[:,None]`
   逐时刻映射回 $r$，右边界随 $R(t)$ 由 2.000 cm 内移至 1.198 cm —— 处理正确。
2. `mass_balance.eps_M` 首点在 $t=0$ 处因 $Q=0$ 而无定义（呈 1e14 量级伪值）。
   `gen_tables.py:114-119` 以 `m = Q > 0` 掩码后再取 `nanmax` —— 处理正确；
   `gen_fig_q2_flux_balance.py:31` 取的是 `diagnostics.eps_M` 标量（上游已归约），
   不触碰该数组首点。

---

# 结构类矢量图阶段（paper-figure-html，2026-09-11）

承接上文数据图阶段。本阶段产出 **HTML/CSS 流程与架构图 6 张 + TikZ 几何/离散图 4 张**，
共 10 张结构类矢量图。配置：`flowchart_engine=html`、`diagram_style=modern`
（family B，靛蓝 H0=224）、`language=zh`、`output_format=docx`、`flow_per_problem=True`。

## 交付清单（10 张，全部过闸）

### HTML 矢量图（6 张，Electron printToPDF）
| 图名 | 内容 | 画布(px) | 高/宽 | 占页 | 有效字号 |
|---|---|---|---|---|---|
| fig_roadmap | 四问递进 + 共享求解内核总路线 | 556×433 | 0.78 | — | 8.2pt |
| fig_flow_q1 | 问题 1：常物性、T–C 解耦双场推进 | 558×516 | 0.93 | 52% | 8.1pt |
| fig_flow_q2 | 问题 2：变物性 + 步内 Picard 自洽迭代 | 548×570 | 1.04 | 59% | 8.7pt |
| fig_flow_q3 | 问题 3：长时程推进 + 阈值判定 + 插值定 t* | 560×480 | 0.86 | 52% | 9.0pt |
| fig_flow_q4 | 问题 4：物质坐标变换 + 动边界推进 | 560×544 | 0.97 | 58% | 9.0pt |
| fig_solver_architecture | 一套内核 + 四组配置的分层架构 | 584×408 | 0.70 | 40% | 8.1pt |

### TikZ 矢量图（4 张，xelatex 编译）
| 图名 | 内容 | 高/宽 |
|---|---|---|
| tikz_cylinder_geometry | 圆柱几何、径向坐标、长径比 6.25 论证一维径向 | 0.57 |
| tikz_control_volume | 守恒型有限体积控制体、界面通量、r=0 半控制体、界面调和平均 | 0.63 |
| tikz_boundary_conditions | 表面两个 Robin 条件（对流换热 h、对流传质 h_m）通量平衡 | 0.50 |
| tikz_moving_boundary_transform | η=r/R(t) 物质坐标映射；固相对流与坐标运动项精确相消，仅留 1/R² | 0.44 |

## 质量闸结果

每张图走同一流水线：写 HTML/TeX → 渲染 PDF → 结构检查 → 几何检查 → 规范检查。

| 检查 | 命令 | 结果 |
|---|---|---|
| 结构（单页/矢量/尺寸） | `screenshot_capture --file … html_pdf_check` | 6 张 HTML ✅ |
| 几何（溢出/越界/重叠/对齐） | `screenshot_capture --geom-check` | 6 张 HTML ✅ |
| 规范（字号/占页/对比度/密度/泄漏） | `screenshot_capture --norm-check` | 6 张 HTML ✅ |
| TikZ 结构（配色语义化/密度） | `_utils/tikz_check.sh` | 4 张 0 CRITICAL ✅ |
| 插入尺寸有效字号 ≥8pt | `_utils/fig_include_size.py --strict` | 10 张 ✅ |
| 图 PDF 终检 | `_utils/figure_pdf_quality_check.py` | 可确定项全部通过 ✅ |

## 过程中修正的实质问题

1. **q2/q3/q4 有效字号卡在 8.0pt**（docx 5.5in 栏宽下 12px 文字被压到下限）。
   根因是原生画布偏宽。做法：收窄画布（q2→500px、q3/q4→480px）提高插入缩放比，
   并对 q2 合并「进入时间步」独立节点进迭代框标题以压高度，最终三图升到 8.7–9.0pt
   且占页 <60%。**不是靠放大 include 宽度绕过。**
2. **q3 终点节点结果泄漏**（"57.27 h" 具体数值）→ 改「输出干燥终点时刻 t\* 作为总时长」。
3. **q2 采样节点省略号被判截断** → `{0.5…3.0}` 改写为「0.5 至 3 h」。
4. **tikz_control_volume 界面公式重叠** → 嵌套分数改线性写法 `2 D_W D_P/(D_W+D_P)`。
5. **tikz_boundary_conditions 表面标签与说明重叠** → 「表面 r=R」由底部移到顶部。

## 与建模定案的一致性

- 问题 4 η 方程遵循已定案结论：**无伪对流项**，固相对流项 `+ηṘ/R ∂_ηC` 与坐标运动项
  `−ηṘ/R ∂_ηC` 精确相消，收缩效应仅由 `1/R²(t)` 因子承担（MODELING_REPORT §5.4）。
  TikZ 变换图与流程图 q4 均照此表达。
- Robin 系数 h=25、h_m=8×10⁻⁷ 四问同值（规则 R7）；长径比 L/(2R₀)=6.25 论证一维径向。

## 未覆盖项（诚实记录）

- **视觉复核（vision）：未审成。** 本环境无可用视觉模型，`figure_pdf_quality_check.py`
  另报 46 项「需复核」——多为浅靛蓝底框内文字的对比度需人眼确认。这些**不是**通过项，
  静态判据无法拦截；建议作者在最终 docx 中肉眼核对靛蓝强调框文字清晰度与灰度可读性。
- LaTeX 插入清单已追加 10 个 figure 环境至 `figures/latex_includes.tex`
  （宽度经 --strict 规整），原有 20 张数据图条目保持不变。
