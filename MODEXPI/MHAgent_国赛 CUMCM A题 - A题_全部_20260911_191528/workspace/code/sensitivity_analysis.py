# -*- coding: utf-8 -*-
"""单因素 ±10% 灵敏度扫描（MODELING_REPORT §9.1，方法声明 MC-08）。

响应量统一取 t*（烘干终点时长）。三组扫描共用同一求解器：
  1. 主组：附录3 固定域，基准 N=20、Δt=20 s（§9.1 表的基准 t*=56.4950 h）；
     逐参数 ×1.1 与 ×0.9，**两个方向都报**（MC-08 禁止只报一个方向）。
  2. 环境组：C_inf 整体乘 0.5 / 2.0，基准 N=40、Δt=10 s（t*=57.0168 h）。
  3. 问题4 组：c_p 整体 ±20%，用于确认温度场细节对 t* 的影响是百分之几量级。

每个通道额外跑一次 factor=1.0 的空扰动：若某通道没接进求解器，空扰动仍会给
基准值（看不出问题），但**有效扰动也会给基准值**——两项合起来才能证明通道确实接上。
"""
from __future__ import annotations

import dataclasses

import data_io
import params as P
import problem_3 as p3
import problem_4 as p4
import resultio as RIO
import solver as SV

BASE_CELLS, BASE_DT_S = 20, 20.0        # §9.1 主组基准配置
ENV_CELLS, ENV_DT_S = 40, 10.0          # §9.1 环境组基准配置
Q4_CELLS, Q4_DT_S = p4.FROZEN_CELLS, p4.FROZEN_DT_S   # 40 / 10 s，与 §9.1 末段同配置
CP_FACTOR_HIGH, CP_FACTOR_LOW = 1.2, 0.8              # 问题4 热惯量 ±20%
ENV_C_FACTORS = (2.0, 0.5)
TOL_ABS_H = 1e-3                        # §9.1 表给到 4 位小数，容差取末位量级
TOL_REL_PCT = 5e-4                      # 变化率对账容差（绝对值，非百分点）
NEUTRAL_TOL = 1e-12                     # 空扰动应逐位复现基准
WIRED_MIN_REL = 1e-6                    # 有效扰动必须把 t* 推离基准

# §9.1 表的报告值（reference），逐项对账；h 的 −10% 方向报告未给，故为 None，
# 但本模块仍实算并落盘，以满足 MC-08「不得只报一个方向」。
SPECS = (
    {"id": "arrhenius_exp_T", "label": "Arrhenius 指数系数 3850", "kind": "exp_T",
     "ref_high": 171.9291, "ref_low": 23.1085,
     "ref_rel_high": 2.0433, "ref_rel_low": -0.5910},
    {"id": "moisture_exp_C", "label": "含水率指数系数 a=0.45", "kind": "exp_C",
     "ref_high": 71.6333, "ref_low": 45.1089,
     "ref_rel_high": 0.2680, "ref_rel_low": -0.2015},
    {"id": "radius_R0", "label": "初始半径 R0", "kind": "radius",
     "ref_high": 67.5694, "ref_low": 46.4273,
     "ref_rel_high": 0.1960, "ref_rel_low": -0.1782},
    {"id": "D_prefactor", "label": "D 前指数因子 2.4e-3", "kind": "pre",
     "ref_high": 52.0207, "ref_low": 61.9872,
     "ref_rel_high": -0.0792, "ref_rel_low": 0.0972},
    {"id": "hm_conv", "label": "对流传质系数 h_m", "kind": "hm",
     "ref_high": 55.8726, "ref_low": 57.2827,
     "ref_rel_high": -0.0110, "ref_rel_low": 0.0139},
    {"id": "h_conv", "label": "对流换热系数 h", "kind": "h",
     "ref_high": 56.4879, "ref_low": None,
     "ref_rel_high": -0.0001, "ref_rel_low": None},
)

# §9.1「读法」的核心结论：不确定性由 D 的两个指数系数与几何尺寸主导，
# 对两个对流系数最不敏感。该排序本身就是可证伪断言。
REF_RANK = ("arrhenius_exp_T", "moisture_exp_C", "radius_R0",
            "D_prefactor", "hm_conv", "h_conv")


class ScaledEnv:
    """环境水分驱动整体缩放的包装（只改 C_inf，温度驱动保持原样）。

    不复制插值逻辑，直接委托给 data_io 的实例，保证两组扫描的环境口径一致。
    """

    def __init__(self, env, c_factor: float) -> None:
        self.env = env
        self.c_factor = float(c_factor)

    def T_inf_scalar(self, t: float) -> float:
        return self.env.T_inf_scalar(t)

    def C_inf_scalar(self, t: float) -> float:
        return self.c_factor * self.env.C_inf_scalar(t)


def perturbed_tstar_h(kind: str, factor: float) -> float:
    """把单个参数乘 factor 后重解 t*（h）。其余参数一律保持基准值。

    exp_T / exp_C / pre 走 properties.D 的三个缩放入口（指数系数为负，
    ×1.1 即 3850→4235，使 D 减小、t* 变长）；radius 改求解域跨度；
    hm / h 改两个 Robin 系数。
    """
    if kind in ("exp_T", "exp_C", "pre"):
        key = {"exp_T": "exp_T_scale", "exp_C": "exp_C_scale", "pre": "pre_scale"}[kind]
        return p3.solve_tstar_h(BASE_CELLS, BASE_DT_S, D_kwargs={key: factor})
    if kind == "radius":
        return p3.solve_tstar_h(BASE_CELLS, BASE_DT_S, radius_m=factor * P.R0_M)
    if kind == "hm":
        return p3.solve_tstar_h(BASE_CELLS, BASE_DT_S, hm=factor * P.HM_CONV)
    if kind == "h":
        return p3.solve_tstar_h(BASE_CELLS, BASE_DT_S, h=factor * P.H_CONV)
    raise ValueError(f"未知扰动通道 {kind}")


def main_sweep(base_h: float) -> dict:
    """主组：六个参数 ×1.1 / ×0.9，附 factor=1.0 的通道接通性检验。"""
    hi, lo = P.SENS_FACTOR_HIGH, P.SENS_FACTOR_LOW      # 1.1 / 0.9
    rows = []
    for spec in SPECS:
        t_hi = perturbed_tstar_h(spec["kind"], hi)
        t_lo = perturbed_tstar_h(spec["kind"], lo)
        t_neutral = perturbed_tstar_h(spec["kind"], 1.0)
        rel_hi = t_hi / base_h - 1.0
        rel_lo = t_lo / base_h - 1.0
        rows.append({
            "id": spec["id"], "label": spec["label"], "kind": spec["kind"],
            "t_star_high_h": t_hi, "t_star_low_h": t_lo,
            "rel_change_high": rel_hi, "rel_change_low": rel_lo,
            "abs_rel_max": max(abs(rel_hi), abs(rel_lo)),
            "t_star_neutral_h": t_neutral,
            "neutral_dev_h": abs(t_neutral - base_h),
            "ref_t_star_high_h": spec["ref_high"], "ref_t_star_low_h": spec["ref_low"],
            "ref_rel_change_high": spec["ref_rel_high"],
            "ref_rel_change_low": spec["ref_rel_low"],
            "both_directions": True,
        })
    ranked = [r["id"] for r in sorted(rows, key=lambda r: -r["abs_rel_max"])]
    return {"base_t_star_h": base_h, "n_cells": BASE_CELLS, "dt_s": BASE_DT_S,
            "factor_high": hi, "factor_low": lo, "rows": rows,
            "ranking_by_abs_rel_max": ranked, "ranking_reference": list(REF_RANK)}


def env_sweep() -> dict:
    """环境组：C_inf 整体乘 2.0 / 0.5（§9.1 末段，基准 N=40、Δt=10 s）。"""
    env = data_io.get_env()
    base = p3.solve_tstar_h(ENV_CELLS, ENV_DT_S)
    rows = []
    for factor in ENV_C_FACTORS:
        hist = SV.simulate_fixed(p3.PROPS, ENV_DT_S, ScaledEnv(env, factor),
                                 n_cells=ENV_CELLS, out_dt_s=P.Q3_FILE_DT_S,
                                 stop_at_threshold=True)
        t_h = hist.t_star_s / P.SECONDS_PER_HOUR
        rows.append({"c_inf_factor": factor, "t_star_h": t_h,
                     "rel_change": t_h / base - 1.0})
    return {"base_t_star_h": base, "n_cells": ENV_CELLS, "dt_s": ENV_DT_S,
            "rows": rows, "ref_base_t_star_h": 57.0168,
            "ref_t_star_factor2_h": 61.2834, "ref_t_star_factor05_h": 56.1087}


def q4_cp_sweep() -> dict:
    """问题4 组：c_p 整体 ±20%，检验温度场细节对 t* 的影响量级（§9.1 末段）。"""
    rad = p4.radius_interpolator()
    base = p4.solve_tstar_h(Q4_CELLS, Q4_DT_S)
    rows = []
    for factor in (CP_FACTOR_HIGH, CP_FACTOR_LOW):
        group = dataclasses.replace(
            p4.PROPS, cp_const=factor * p4.PROPS.cp_const,
            cp_coef_frac=factor * p4.PROPS.cp_coef_frac)
        hist = SV.simulate_material(group, Q4_DT_S, data_io.get_env(), rad.R_scalar,
                                    n_cells=Q4_CELLS, out_dt_s=P.Q4_FILE_DT_S,
                                    stop_at_threshold=True)
        t_h = hist.t_star_s / P.SECONDS_PER_HOUR
        rows.append({"cp_factor": factor, "t_star_h": t_h,
                     "rel_change": t_h / base - 1.0})
    return {"base_t_star_h": base, "n_cells": Q4_CELLS, "dt_s": Q4_DT_S,
            "rows": rows, "ref_base_t_star_h": 50.9690,
            "ref_t_star_set_h": [50.9514, 50.9871]}


def validate(main: dict, env: dict, q4: dict) -> dict:
    """全部硬断言：逐项对账 §9.1、通道接通性、排序、方向性。"""
    if abs(main["base_t_star_h"] - 56.4950) > TOL_ABS_H:
        raise AssertionError(f"主组基准 t*={main['base_t_star_h']:.4f} != §9.1 的 56.4950 h")
    for row in main["rows"]:
        for side, key_t, key_ref, key_rel, key_ref_rel in (
                ("+10%", "t_star_high_h", "ref_t_star_high_h",
                 "rel_change_high", "ref_rel_change_high"),
                ("-10%", "t_star_low_h", "ref_t_star_low_h",
                 "rel_change_low", "ref_rel_change_low")):
            ref = row[key_ref]
            if ref is None:               # §9.1 未报该方向，本模块仍实算并落盘
                continue
            if abs(row[key_t] - ref) > TOL_ABS_H:
                raise AssertionError(
                    f"{row['id']} {side}：实算 {row[key_t]:.4f} h vs §9.1 {ref:.4f} h")
            if abs(row[key_rel] - row[key_ref_rel]) > TOL_REL_PCT:
                raise AssertionError(
                    f"{row['id']} {side} 变化率：实算 {row[key_rel]:.4f} vs §9.1 {row[key_ref_rel]:.4f}")
        if row["neutral_dev_h"] > NEUTRAL_TOL:
            raise AssertionError(
                f"{row['id']} 空扰动(factor=1.0) 偏离基准 {row['neutral_dev_h']:.3e} h，扰动通道有副作用")
        if not row["abs_rel_max"] > WIRED_MIN_REL:
            raise AssertionError(
                f"{row['id']} 有效扰动未推动 t*（abs_rel_max={row['abs_rel_max']:.3e}），该参数未接进求解器")
        if row["t_star_low_h"] is None or row["t_star_high_h"] is None:
            raise AssertionError(f"{row['id']} 缺一个扰动方向，违反 MC-08")
    if main["ranking_by_abs_rel_max"] != list(REF_RANK):
        raise AssertionError(
            f"灵敏度排序 {main['ranking_by_abs_rel_max']} != §9.1 排序 {list(REF_RANK)}")
    d_rank = [r["abs_rel_max"] for r in main["rows"] if r["id"] in ("arrhenius_exp_T", "moisture_exp_C")]
    conv_rank = [r["abs_rel_max"] for r in main["rows"] if r["id"] in ("hm_conv", "h_conv")]
    if not min(d_rank) > 10.0 * max(conv_rank):
        raise AssertionError(
            f"D 指数系数敏感度 {min(d_rank):.4f} 未比对流系数 {max(conv_rank):.4f} 高一个量级以上")
    exp_T = next(r for r in main["rows"] if r["id"] == "arrhenius_exp_T")
    if not (exp_T["rel_change_high"] > 0.0 > exp_T["rel_change_low"]):
        raise AssertionError("指数系数增大应使 D 减小、t* 变长；实测方向不符")
    pre = next(r for r in main["rows"] if r["id"] == "D_prefactor")
    if not (pre["rel_change_high"] < 0.0 < pre["rel_change_low"]):
        raise AssertionError("D 前指数因子增大应使 t* 变短；实测方向不符")

    if abs(env["base_t_star_h"] - env["ref_base_t_star_h"]) > TOL_ABS_H:
        raise AssertionError(f"环境组基准 t*={env['base_t_star_h']:.4f} != {env['ref_base_t_star_h']}")
    env_map = {row["c_inf_factor"]: row["t_star_h"] for row in env["rows"]}
    for factor, ref in ((2.0, env["ref_t_star_factor2_h"]), (0.5, env["ref_t_star_factor05_h"])):
        if abs(env_map[factor] - ref) > TOL_ABS_H:
            raise AssertionError(f"C_inf ×{factor}：实算 {env_map[factor]:.4f} h vs §9.1 {ref:.4f} h")
    if not env_map[2.0] > env["base_t_star_h"] > env_map[0.5]:
        raise AssertionError("环境水分升高应使干燥变慢；实测方向不符")

    if abs(q4["base_t_star_h"] - q4["ref_base_t_star_h"]) > TOL_ABS_H:
        raise AssertionError(f"问题4 组基准 t*={q4['base_t_star_h']:.4f} != {q4['ref_base_t_star_h']}")
    got = sorted(row["t_star_h"] for row in q4["rows"])
    ref_set = sorted(q4["ref_t_star_set_h"])
    if max(abs(a - b) for a, b in zip(got, ref_set)) > TOL_ABS_H:
        raise AssertionError(f"问题4 c_p ±20% 实算 {got} vs §9.1 {ref_set}")
    cp_max_rel = max(abs(row["rel_change"]) for row in q4["rows"])
    if not cp_max_rel < 1e-3:
        raise AssertionError(f"c_p ±20% 使 t* 变动 {cp_max_rel:.3e}，与「温度场细节几乎不影响 t*」矛盾")
    return {"main_rows": len(main["rows"]),
            "ranking_matches_reference": True,
            "cp_max_abs_rel": cp_max_rel,
            "d_exponent_over_convection_ratio": min(d_rank) / max(conv_rank),
            "n_assertions_passed": 4 * len(main["rows"]) + 10}


def main():
    print("[sensitivity] 主组基准求解（N=20, dt=20 s）…", flush=True)
    base_h = p3.solve_tstar_h(BASE_CELLS, BASE_DT_S)
    print(f"[sensitivity] 基准 t* = {base_h:.4f} h", flush=True)

    print(f"[sensitivity] 单因素 ±10% 扫描（{len(SPECS)} 个参数 × 3 次求解）…", flush=True)
    main_res = main_sweep(base_h)
    for row in main_res["rows"]:
        lo = f"{row['t_star_low_h']:.4f}"
        print(f"  {row['label']}: +10% → {row['t_star_high_h']:.4f} h "
              f"({row['rel_change_high']:+.2%})，-10% → {lo} h "
              f"({row['rel_change_low']:+.2%})", flush=True)

    print("[sensitivity] 环境组 C_inf ×2.0 / ×0.5（N=40, dt=10 s）…", flush=True)
    env_res = env_sweep()
    for row in env_res["rows"]:
        print(f"  C_inf ×{row['c_inf_factor']}: {row['t_star_h']:.4f} h "
              f"({row['rel_change']:+.2%})", flush=True)

    print("[sensitivity] 问题4 组 c_p ±20%（N=40, dt=10 s）…", flush=True)
    q4_res = q4_cp_sweep()
    for row in q4_res["rows"]:
        print(f"  c_p ×{row['cp_factor']}: {row['t_star_h']:.4f} h "
              f"({row['rel_change']:+.3%})", flush=True)

    checks = validate(main_res, env_res, q4_res)
    payload = {
        "analysis": "one_at_a_time_sensitivity",
        "method_claim": "MC-08",
        "response_quantity": "t_star_h",
        "title": "单因素 ±10% 灵敏度扫描（响应量 t*）",
        "source_section": "MODELING_REPORT §9.1",
        "note": "两个方向均实算并落盘；空扰动 factor=1.0 用于证明扰动通道确实接进求解器",
        "main_group": main_res,
        "env_group": env_res,
        "q4_cp_group": q4_res,
        "ranking": main_res["ranking_by_abs_rel_max"],
        "checks": checks,
        "conclusion": ("t* 的不确定性由 D 的两个指数系数与几何尺寸主导"
                       f"（最敏感项相对变化 {main_res['rows'][0]['abs_rel_max']:.4f}），"
                       f"对两个对流系数最不敏感（{main_res['rows'][-1]['abs_rel_max']:.2e}）；"
                       f"问题4 的 c_p ±20% 只使 t* 变动 {checks['cp_max_abs_rel']:.3e}，"
                       "即温度场细节对烘干时长几乎无影响"),
    }
    path, nbytes = RIO.write_results("sensitivity_results", payload)
    print(f"[sensitivity] 写出 {path.name}（{nbytes} bytes）", flush=True)
    print(f"[sensitivity] 排序 = {' > '.join(main_res['ranking_by_abs_rel_max'])}", flush=True)
    print(f"[sensitivity] 指数系数/对流系数 敏感度比 = "
          f"{checks['d_exponent_over_convection_ratio']:.1f} 倍", flush=True)
    print("[sensitivity] 全部断言通过", flush=True)
    return payload


if __name__ == "__main__":
    main()
