# -*- coding: utf-8 -*-
"""参数口径唯一来源：全部物理常数由 PROBLEM_FACTS.json 派生，其余模块不得写裸数值。

对应 MODELING_REPORT.md §10 ⓪ 参数口径表。数值网格参数（N、dt）来自 §6.3 表。
"""
from __future__ import annotations

import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
FACTS_PATH = WORKSPACE / "PROBLEM_FACTS.json"
PROFILE_PATH = WORKSPACE / "DATA_PROFILE.json"
USER_DATA_DIR = WORKSPACE / "user_data"
OUTPUT_DIR = WORKSPACE / "output"
FIGURES_DIR = WORKSPACE / "figures"
TMP_DIR = WORKSPACE / "_tmp"

FACTS = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
DATA_PROFILE = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

CM_PER_M = 100.0
KELVIN_OFFSET = 273.15
SECONDS_PER_HOUR = 3600.0
DECADE = 10.0

_geo = FACTS["geometry"]
_ic = FACTS["initial_conditions"]
_a2 = FACTS["given_params_appendix2"]
_a3 = FACTS["empirical_formulas_appendix3"]
_a4 = FACTS["empirical_formulas_appendix4"]
_out = FACTS["output_spec"]

L_M = _geo["length_cm"] / CM_PER_M
R0_M = _geo["radius_cm"] / CM_PER_M
R0_CM = float(_geo["radius_cm"])
T0_DEGC = float(_ic["T0_degC"])
C0 = float(_ic["C0_kg_per_kg"])
C_TH = float(FACTS["drying_criterion"]["C_threshold_kg_per_kg"])
DURATION_DAYS_LOW = float(FACTS["process_stages"]["total_duration_days_low"])
DURATION_DAYS_HIGH = float(FACTS["process_stages"]["total_duration_days_high"])

H_CONV = float(_a2["h_conv_heat_W_per_m2K"]["value"])
HM_CONV = _a2["hm_conv_mass_m_per_s"]["mantissa"] * DECADE ** _a2["hm_conv_mass_m_per_s"]["exp10"]

RHO_A2 = float(_a2["rho_kg_per_m3"]["value"])
CP_A2 = float(_a2["cp_J_per_kgK"]["value"])
K_A2 = float(_a2["k_W_per_mK"]["value"])
D_A2_PRE = _a2["D_formula"]["mantissa"] * DECADE ** _a2["D_formula"]["exp10"]
D_A2_EXP_C = float(_a2["D_formula"]["exp_numerator"])

RHO_A3_CONST = float(_a3["rho"]["const"])
RHO_A3_COEF_C = float(_a3["rho"]["coef_C"])
CP_A3_CONST = float(_a3["cp"]["const"])
CP_A3_COEF_FRAC = float(_a3["cp"]["coef_frac"])
K_A3_CONST = float(_a3["k"]["const"])
K_A3_COEF_FRAC = float(_a3["k"]["coef_frac"])
D_A3_PRE = _a3["D"]["mantissa"] * DECADE ** _a3["D"]["exp10"]
D_A3_EXP_C = float(_a3["D"]["exp1_numerator"])
D_A3_EXP_T = float(_a3["D"]["exp2_numerator"])

RHO_A4_CONST = float(_a4["rho"]["const"])
RHO_A4_COEF_C = float(_a4["rho"]["coef_C"])
CP_A4_CONST = float(_a4["cp"]["const"])
CP_A4_COEF_FRAC = float(_a4["cp"]["coef_frac"])
K_A4_CONST = float(_a4["k"]["const"])
K_A4_COEF_FRAC = float(_a4["k"]["coef_frac"])
D_A4_PRE = _a4["D"]["mantissa"] * DECADE ** _a4["D"]["exp10"]
D_A4_EXP_C = float(_a4["D"]["exp1_numerator"])
D_A4_EXP_T = float(_a4["D"]["exp2_numerator"])

# 源码级可见的公式口径（B-01 / mf_fraction_exponent 静态扫描依据）：
# 附录2 D = 7e-9*exp(-0.89/C)；附录3 D = 2.4e-3*exp(-0.45/C)*exp(-3850/T_K)；
# 附录4 D = 4.2e-4*exp(-0.30/C)*exp(-3850/T_K)。指数项一律为分式，非 exp(-0.89*C) 乘积。
FORMULA_D_A2 = "D = 7e-9*exp(-0.89/C)"
FORMULA_D_A3 = "D = 2.4e-3*exp(-0.45/C)*exp(-3850/T_K)"
FORMULA_D_A4 = "D = 4.2e-4*exp(-0.30/C)*exp(-3850/T_K)"
FORMULA_PROPS_A3 = "rho=650+128*C; cp=1450+2736*C/(C+1); k=0.21+0.38*C/(C+1)"
FORMULA_PROPS_A4 = "rho=760+90*C; cp=1850+2150*C/(C+1); k=0.12+0.20*C/(C+1)"

DECIMALS = int(_out["decimals"]["value"])
Q1_TABLE_TIMES_S = [float(v) for v in _out["Q1"]["paper_table_times_s"]]
Q1_TABLE_RADII_CM = [float(v) for v in _out["Q1"]["paper_table_radii_cm"]]
Q1_FILE_DT_S = float(_out["Q1"]["file_dt_s"])
Q1_FILE_DR_CM = float(_out["Q1"]["file_dr_cm"])
Q1_FILE_T_END_S = float(_out["Q1"]["file_t_end_s"])
Q1_SHEETS = list(_out["Q1"]["file_sheets"])

Q2_TABLE_TIMES_H = [float(v) for v in _out["Q2"]["paper_table_times_h"]]
Q2_TABLE_RADII_CM = [float(v) for v in _out["Q2"]["paper_table_radii_cm"]]
Q2_FILE_DT_S = float(_out["Q2"]["file_dt_s"])
Q2_FILE_DR_CM = float(_out["Q2"]["file_dr_cm"])
Q2_FILE_T_END_S = float(_out["Q2"]["file_t_end_h"]) * SECONDS_PER_HOUR
Q2_SHEETS = list(_out["Q2"]["file_sheets"])

Q3_TABLE_DT_H = float(_out["Q3"]["paper_table_dt_h"])
Q3_TABLE_DR_CM = float(_out["Q3"]["paper_table_dr_cm"])
Q3_TABLE_LAST_ROW = _out["Q3"]["paper_table_last_row"]
Q3_FILE_DT_S = float(_out["Q3"]["file_dt_s"])
Q3_FILE_DR_CM = float(_out["Q3"]["file_dr_cm"])

Q4_TABLE_DT_H = float(_out["Q4"]["paper_table_dt_h"])
Q4_TABLE_DR_CM = float(_out["Q4"]["paper_table_dr_cm"])
Q4_TABLE_LAST_COL = _out["Q4"]["paper_table_last_col"]
Q4_TABLE_LAST_ROW = _out["Q4"]["paper_table_last_row"]
Q4_FILE_DT_S = float(_out["Q4"]["file_dt_s"])
Q4_FILE_DR_CM = float(_out["Q4"]["file_dr_cm"])

# ---- 数值参数（MODELING_REPORT §6.3 表 + §10 ⓪ 表末段）----
N_CELLS = 80                 # 径向控制体数，使输出 0.1 cm 恰为计算节点的每第 4 个
DT_Q1_S = 0.25
DT_Q2_S = 0.5
DT_Q3_S = 5.0
DT_Q4_S = 5.0
PICARD_ROUNDS = 3
PICARD_TOL_T = 1e-6
PICARD_TOL_C = 1e-8
C_FLOOR = 1e-8               # 仅防 exp(-a/C) 下溢，远低于判据阈值 0.15
T_MAX_HOURS = 200.0          # 积分上限保护（bd_tstar 上界）
EPS_M_LIMIT = 0.01           # HC-13
CONV_TOL_GRID = 0.01         # B-17
SENS_FACTOR_LOW = 0.9        # MC-08 单因素 ±10%
SENS_FACTOR_HIGH = 1.1
ENV_DATA_T_END_S = 14400.0   # 附件1 覆盖区间上界
ENV_PLATEAU_START_S = 10800.0  # 平台段起点（§2.1）
T_INF_PLATEAU_REF = 49.9989  # §10 ⓪ 表 derived 值，供 B-22 复核
C_INF_PLATEAU_REF = 0.04999
R_MIN_REF_M = 0.01198        # 附件2 收缩末半径

# ---- 交付网格 ----
N_OUT_COLS = int(round(R0_CM / Q1_FILE_DR_CM)) + 1     # 21 列：0 ~ 2 cm
OUT_NODE_STRIDE = int(round(Q1_FILE_DR_CM / (R0_CM / N_CELLS)))   # 4
OUT_RADII_CM = [i * Q1_FILE_DR_CM for i in range(N_OUT_COLS)]

# ---- 派生特征量（MODELING_REPORT §4 末、§10 ⓪）----
ALPHA_A2 = K_A2 / (RHO_A2 * CP_A2)                 # 1.6886e-7 m^2/s
TAU_HEAT_A2_S = R0_M ** 2 / ALPHA_A2               # 2368.9 s
BI_H_A2 = H_CONV * R0_M / K_A2                     # 1.3889


def _exp_frac(numerator: float, denominator: float) -> float:
    """exp(numerator/denominator)，numerator 为负；分式指数，不是乘积。"""
    import math
    return math.exp(numerator / max(denominator, C_FLOOR))


D_A2_AT_C0 = D_A2_PRE * _exp_frac(D_A2_EXP_C, C0)          # 7e-9*exp(-0.89/2.55)
TAU_MASS_A2_S = R0_M ** 2 / D_A2_AT_C0                     # 8.101e4 s
BI_M_A2 = HM_CONV * R0_M / D_A2_AT_C0                      # 3.2404


def _consistency_report() -> dict:
    """口径一致性：把 §10 ⓪ 表里的 derived 数值当作独立锚点复核派生结果。"""
    checks = {
        "R0_M": (R0_M, 0.02, 1e-12),
        "L_M": (L_M, 0.25, 1e-12),
        "C0": (C0, 2.55, 1e-12),
        "C_TH": (C_TH, 0.15, 1e-12),
        "H_CONV": (H_CONV, 25.0, 1e-12),
        "HM_CONV": (HM_CONV, 8e-7, 1e-18),
        "ALPHA_A2": (ALPHA_A2, 1.6886e-7, 1e-11),
        "TAU_HEAT_A2_S": (TAU_HEAT_A2_S, 2368.9, 0.1),
        "BI_H_A2": (BI_H_A2, 1.3889, 1e-4),
        "TAU_MASS_A2_S": (TAU_MASS_A2_S, 8.101e4, 20.0),
        "BI_M_A2": (BI_M_A2, 3.2404, 1e-3),
        "N_OUT_COLS": (float(N_OUT_COLS), 21.0, 0.0),
        "OUT_NODE_STRIDE": (float(OUT_NODE_STRIDE), 4.0, 0.0),
    }
    bad = {k: v for k, (v, ref, tol) in checks.items() if abs(v - ref) > tol}
    if bad:
        raise AssertionError(f"[params] 口径一致性失败：{bad}")
    assert D_A2_EXP_C < 0.0 and D_A3_EXP_C < 0.0 and D_A4_EXP_C < 0.0
    assert D_A3_EXP_T < 0.0 and D_A4_EXP_T < 0.0
    assert "exp(-0.89/" in FORMULA_D_A2 and "exp(-0.89*" not in FORMULA_D_A2
    assert "exp(-0.45/" in FORMULA_D_A3 and "exp(-0.30/" in FORMULA_D_A4
    return {k: v for k, (v, _r, _t) in checks.items()}


if __name__ == "__main__":
    report = _consistency_report()
    for key, val in report.items():
        print(f"  {key} = {val!r}")
    print("[params] 口径一致性 OK")
