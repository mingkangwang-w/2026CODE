# facts_audit 报告

stage: code

fatal: 0, warn: 22

## 拒绝项

## 警告项
- ⚠ MODELING_REPORT.md 有 238 个数值需说明来源或推导: [-59.1, -47.43, -43.73, -20.15, -17.82, -7.92, -1.59, -1.1, -0.034, -0.0175, -0.012, -0.01, -0.0087, -0.0044, 0.001]；派生计算值不要求与题设原值相等，不得仅因此删除或替换结果
- ⚠ code\data_io.py:5 值=14400.0 环境量在 t<=14400 s 用分段线性插值，t>14400 s 取平台常值（MODELING_REPORT §2.1，禁止线性外推）。
- ⚠ code\data_io.py:5 值=14400.0 环境量在 t<=14400 s 用分段线性插值，t>14400 s 取平台常值（MODELING_REPORT §2.1，禁止线性外推）。
- ⚠ code\data_io.py:5 值=2.1 环境量在 t<=14400 s 用分段线性插值，t>14400 s 取平台常值（MODELING_REPORT §2.1，禁止线性外推）。
- ⚠ code\data_io.py:47 值=16.0 raise AssertionError(f"{fname} sha256 {digest[:16]} != 基线 {prof['sha256'][:16]}"
- ⚠ code\data_io.py:47 值=16.0 raise AssertionError(f"{fname} sha256 {digest[:16]} != 基线 {prof['sha256'][:16]}"
- ⚠ code\data_io.py:74 值=14400.0 """环境温度（摄氏度）；t>14400 s 返回平台均值，不做趋势外推。"""
- ⚠ code\data_io.py:79 值=14400.0 """环境水分浓度（kg/kg 干基）；t>14400 s 返回平台均值。"""
- ⚠ code\data_io.py:140 值=22.0 """B-22 / mf_plateau_extrap / mf_moving_domain / tr_* 的运行时复核。"""
- ⚠ code\data_io.py:142 值=200000.0 far = 2e5
- ⚠ code\data_io.py:143 值=0.001 if abs(env.T_inf_scalar(far) - P.T_INF_PLATEAU_REF) >= 1e-3:
- ⚠ code\data_io.py:144 值=200000.0 raise AssertionError(f"T_inf(2e5)={env.T_inf_scalar(far)} 未落在平台参考值 1e-3 内")
- ⚠ code\data_io.py:144 值=0.001 raise AssertionError(f"T_inf(2e5)={env.T_inf_scalar(far)} 未落在平台参考值 1e-3 内")
- ⚠ code\data_io.py:146 值=200000.0 raise AssertionError(f"C_inf(2e5)={env.C_inf_scalar(far)} 未落在平台参考值 1e-5 内")
- ⚠ code\data_io.py:153 值=10000000.0 if abs(rad.R_scalar(-1.0) - P.R0_M) > 1e-12 or abs(rad.R_scalar(1e7) - rad.R_min
- ⚠ code\fvkernel.py:8 值=9.3 不含伪对流项（§0.2 / §9.3：坐标运动项与固相对流项精确相消）。
- ⚠ code\fvkernel.py:48 值=14.0 同一个通量表达式，离散守恒因此是恒等式。="node" 是 B-14/P2-C1(d) 的反例通道：
- ⚠ code\fvkernel.py:118 值=6.4 """eps_M = |(C0 - M) - Q| / max(Q, 1e-30)（§6.4）。"""
- ⚠ code\fvkernel.py:132 值=0.9 """显式格式稳定步长 0.9*min(dr²/(2 D_max), dr²/(2 alpha_max))（B-18）。"""
- ⚠ code\fvkernel.py:132 值=18.0 """显式格式稳定步长 0.9*min(dr²/(2 D_max), dr²/(2 alpha_max))（B-18）。"""
- ⚠ code\fvkernel.py:133 值=0.9 return 0.9 * min(delta ** 2 / (2.0 * D_max), delta ** 2 / (2.0 * alpha_max))
- ⚠ 10 个公式符号未匹配代码命名，需核对变量映射或运行证据，不能仅凭别名判定未实现: ['Bi_hJ_0', 'DATA_FACTS', 'FIGURE_MANIFEST', 'Gamma_j', 'METHOD_CLAIMS', 'METHOD_CLAIMS_MACHINE', 'PDF_VISION_STATE', 'R_0L', 'R_of_row', 'STYLE_FAMILY']