# -*- coding: utf-8 -*-
"""四问总入口：依次执行问题 1~4 与灵敏度扫描，汇总 figures/all_results.json。

本文件不重新实现任何模型：每问的 main() 自行求解、自校验并写出
figures/problem_N_results.json，本文件只接收它们返回的 payload，
从中取出 MODELING_REPORT §10⑦ LOGIC_CONTRACT_MACHINE 要求的探针实测值，
逐条与合同的 lo/hi 区间和 expected/tol 对账，再落盘汇总文件。

同时用实算值覆盖 CROSS_PROBLEM_LEDGER.json 的 observed 字段，
并把 meta.observed_provenance 由 modeling_expected 改为 computed。
"""
from __future__ import annotations

import json
import time

import numpy as np

import params as P
import problem_1 as p1
import problem_2 as p2
import problem_3 as p3
import problem_4 as p4
import resultio as RIO
import sensitivity_analysis as sens

# §10⑦ bounds 的合同区间与期望值（lo/hi/expected/tol 逐字取自 LOGIC_CONTRACT_MACHINE）
BOUNDS_SPEC = {
    "bd_tstar_q3_range": {"quantity": "t_star_Q3", "lo": 20.0, "hi": 200.0,
                          "unit": "h", "expected": 57.2745, "tol": 0.6},
    "bd_tstar_q4_range": {"quantity": "t_star_Q4", "lo": 20.0, "hi": 200.0,
                          "unit": "h", "expected": 51.0444, "tol": 0.3},
    "bd_mass_residual": {"quantity": "eps_M", "lo": 0.0, "hi": 0.01,
                         "unit": "1", "expected": 1e-14, "tol": 1e-6},
    "bd_center_is_wettest": {"quantity": "argmax_r C", "lo": 0.0, "hi": 0.0,
                             "unit": "index", "expected": 0, "tol": 0},
    "bd_shrink_speedup": {"quantity": "t_star_Q4_fixedR / t_star_Q4_shrink",
                          "lo": 1.5, "hi": 3.5, "unit": "1",
                          "expected": 2.5379, "tol": 0.3},
    "bd_q1_analytic_gap": {"quantity": "max|T_FV - T_bessel| at t=1800 s",
                           "lo": 0.0, "hi": 0.01, "unit": "K",
                           "expected": 0.0031, "tol": 0.007},
    "bd_shrink_pred_error": {"quantity": "relative error of forward-predicted R_end",
                             "lo": 0.0, "hi": 0.08, "unit": "1",
                             "expected": 0.0329, "tol": 0.005},
}

# lo/hi 的作用域：多数条目的每个元素都受同一区间约束（如四问 eps_M 全部 < 1%）；
# bd_shrink_pred_error 例外——它的 values 里只有第一项（附录4+仅径向）是**被采用**的
# 假设，另两项是 §9.5 的反例组合（换密度公式 / 换收缩方向）。合同的推导原文写的是
# 「上界 8%，实测最优组合为 3.29%，若超过 8% 说明选错了密度公式或收缩方向」——
# 即区间约束的是最优组合，反例组合**必须**超出 8% 才具备鉴别力。故对反例侧
# 施加反向断言（> hi），而不是把它们从区间检查里摘掉。
RANGE_SCOPE = {"bd_shrink_pred_error": "primary_plus_counterexamples"}

SHRINK_COMBOS = ("附录4+仅径向", "附录3+仅径向", "附录4+各向同性")
LEDGER_PATH = P.WORKSPACE / "CROSS_PROBLEM_LEDGER.json"


def _entry(bid: str, **extra) -> dict:
    """把合同字段与实测字段并列写入一条 bounds 记录。"""
    spec = BOUNDS_SPEC[bid]
    return {"id": bid, **spec, **extra}


def build_bounds(pay1, pay2, pay3, pay4) -> list[dict]:
    """从四问 payload 取出 §10⑦ 的 7 条探针实测值。"""
    eps = [pay1["summary"]["eps_M"], pay2["summary"]["eps_M"],
           pay3["summary"]["eps_M"], pay4["summary"]["eps_M"]]
    argmax_max = max(pay["diagnostics"]["argmax_max"] for pay in (pay1, pay2, pay3, pay4))
    diff_max = max(pay["diagnostics"]["max_diff_C"] for pay in (pay1, pay2, pay3, pay4))
    t3 = pay3["summary"]["t_star_h"]
    t4 = pay4["summary"]["t_star_h"]
    shrink = pay4["shrinkage_prediction"]["combos"]
    return [
        _entry("bd_tstar_q3_range", value=t3),
        _entry("bd_tstar_q4_range", value=t4, delta_vs_q3=t4 - t3),
        _entry("bd_mass_residual", values=eps, value=max(eps)),
        _entry("bd_center_is_wettest", value=argmax_max,
               max_diff_C=diff_max,
               n_center_violations=sum(pay["diagnostics"]["n_center_violations"]
                                      for pay in (pay1, pay2, pay3, pay4))),
        _entry("bd_shrink_speedup", value=pay4["summary"]["shrink_speedup"],
               t_star_frozen_h=pay4["frozen_radius_probe"]["t_star_frozen_h"],
               t_star_shrinking_h=pay4["frozen_radius_probe"]["t_star_shrinking_h"]),
        _entry("bd_q1_analytic_gap", value=pay1["summary"]["analytic_gap_K"]),
        _entry("bd_shrink_pred_error",
               values=[shrink[name]["rel_dev"] for name in SHRINK_COMBOS],
               value=shrink[SHRINK_COMBOS[0]]["rel_dev"],
               combos=list(SHRINK_COMBOS)),
    ]


def validate_bounds(bounds: list[dict]) -> dict:
    """每条探针都必须落在合同区间内，且与 expected 的偏差不超过 tol。"""
    report = []
    for row in bounds:
        vals = row.get("values", [row["value"]])
        lo, hi = row["lo"], row["hi"]
        scope = RANGE_SCOPE.get(row["id"], "all")
        checked = vals[:1] if scope != "all" else vals
        for val in checked:
            if not (lo - 1e-12 <= float(val) <= hi + 1e-12):
                raise AssertionError(
                    f"{row['id']}：实测 {val} 越出合同区间 [{lo}, {hi}]")
        if scope == "primary_plus_counterexamples":
            for val in vals[1:]:
                if not float(val) > hi:
                    raise AssertionError(
                        f"{row['id']}：反例组合偏差 {val} 未超出上界 {hi}，"
                        "该组对照失去鉴别力（换错密度公式/收缩方向本应显著更差）")
        dev = abs(float(row["value"]) - float(row["expected"]))
        if dev > float(row["tol"]) + 1e-12:
            raise AssertionError(
                f"{row['id']}：实测 {row['value']} 与 expected {row['expected']} "
                f"相差 {dev:.6g}，超容差 {row['tol']}")
        report.append({"id": row["id"], "value": row["value"],
                       "dev_vs_expected": dev, "tol": row["tol"],
                       "range_scope": scope, "in_range": True})
    if len(report) != len(BOUNDS_SPEC):
        raise AssertionError(f"bounds 条数 {len(report)} != 合同 {len(BOUNDS_SPEC)}")
    return {"rows": report, "n_bounds": len(report)}


def build_monotonic(sens_payload: dict) -> list[dict]:
    """§10⑦ monotonic 的两条可扰动项，用灵敏度扫描的实测符号填 observed_sign。

    另外三条（dC/dr<=0、C(0,t) 非增、R(t) 非增）不是扰动型，已在各问的
    validate_constraints 内逐步断言，此处只登记 mono_tstar_in_D / mono_tstar_in_R0。
    """
    rows = {r["id"]: r for r in sens_payload["main_group"]["rows"]}
    out = []
    for probe_id, key, more, expect_sign in (
            ("mono_tstar_in_D", "D_prefactor", "D_prefactor", -1),
            ("mono_tstar_in_R0", "radius_R0", "R0", +1)):
        row = rows[key]
        sign = int(np.sign(row["rel_change_high"]))
        out.append({"id": probe_id, "more": more, "then": "t_star",
                    "observed_sign": sign, "expect_sign": expect_sign,
                    "t_star_high_h": row["t_star_high_h"],
                    "t_star_low_h": row["t_star_low_h"],
                    "base_t_star_h": sens_payload["main_group"]["base_t_star_h"]})
        if sign != expect_sign:
            raise AssertionError(
                f"{probe_id}：实测符号 {sign} 与合同声明 {expect_sign} 相反")
    return out


def _series_at(series: dict, t_s: float, key: str) -> float:
    """从 center/surface 序列里取指定时刻的值，时刻必须落在输出网格上。"""
    times = np.asarray(series["times_s"], dtype=float)
    idx = int(np.argmin(np.abs(times - t_s)))
    if abs(times[idx] - t_s) > 1e-9:
        raise AssertionError(f"时刻 {t_s} s 不在输出网格上")
    return float(series[key][idx])


def measured_ledger_values(pay1, pay2, pay3, pay4, env) -> dict:
    """台账 observed 的实算口径：每个量指明来源 payload 字段，不复算模型。"""
    row2 = np.asarray(pay2["field_T"]["values"][-1], dtype=float)
    if not (row2.argmin() == 0 and row2.argmax() == row2.size - 1):
        raise AssertionError("Q2 3 h 温度沿 r 非单调，全场温差不能用表面−中心代替")
    spread_3h = pay2["summary"]["T_surface_3h"] - pay2["summary"]["T_center_3h"]
    plateau = env.temp_plateau
    return {
        "Q1": {
            "初始含水率_kgkg": P.C0,
            "水分质量守恒残差": pay1["summary"]["eps_M"],
            "中心含水率_1800s": pay1["summary"]["C_center_1800s"],
        },
        "Q2": {
            "初始含水率_kgkg": P.C0,
            "水分质量守恒残差": pay2["summary"]["eps_M"],
            "中心含水率_1800s": _series_at(pay2["center_series"], 1800.0, "C"),
            "三小时末全场温差_degC": spread_3h,
            "三小时末中心含水率": pay2["summary"]["C_center_3h"],
            "三小时末表面含水率": pay2["summary"]["C_surface_3h"],
            "环境温度平台值_degC": plateau,
        },
        "Q3": {
            "初始含水率_kgkg": P.C0,
            "水分质量守恒残差": pay3["summary"]["eps_M"],
            "三小时末全场温差_degC": pay3["q2_anchor_3h"]["T_spread_degC"],
            "三小时末中心含水率": pay3["q2_anchor_3h"]["C_center"],
            "三小时末表面含水率": pay3["q2_anchor_3h"]["C_surface"],
            "环境温度平台值_degC": plateau,
            "烘干结束时间_h": pay3["summary"]["t_star_h"],
            "终点最大含水率": pay3["summary"]["maxC_at_tstar"],
            "终点药材半径_cm": P.R0_CM,
        },
        "Q4": {
            "初始含水率_kgkg": P.C0,
            "水分质量守恒残差": pay4["summary"]["eps_M"],
            "物质坐标守恒残差": pay4["summary"]["eps_M"],
            "环境温度平台值_degC": plateau,
            "烘干结束时间_h": pay4["summary"]["t_star_h"],
            "终点最大含水率": pay4["diagnostics"]["maxC_at_tstar"],
            "终点药材半径_cm": pay4["summary"]["R_at_tstar_cm"],
        },
    }


def update_ledger(measured: dict) -> dict:
    """用实算值覆盖 observed，并把 observed_provenance 改为 computed。

    只覆盖 value，unit 保持台账原字符串（meta.unit_guard 要求与上游逐字相同）；
    台账已登记但本轮没有实算来源的键会 raise，避免留下 modeling_expected 的旧值。
    """
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    changed, added = 0, 0
    for prob in ledger["problems"]:
        vals = measured[prob["id"]]
        observed = prob.setdefault("observed", {})
        for name, computed in vals.items():
            if name in observed:
                observed[name]["value"] = RIO.round_value(float(computed))
                changed += 1
            else:
                unit = _unit_for(ledger, name)
                observed[name] = {"value": RIO.round_value(float(computed)), "unit": unit}
                added += 1
        stale = set(observed) - set(vals)
        if stale:
            raise AssertionError(f"{prob['id']} 台账 observed 有未覆盖键 {sorted(stale)}")
    ledger["meta"]["observed_provenance"] = "computed"
    ledger["meta"]["observed_computed_by"] = "code/main.py（figures/all_results.json 同批实算）"
    ledger["meta"]["observed_computed_on"] = time.strftime("%Y-%m-%d")
    LEDGER_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    return {"n_overwritten": changed, "n_added": added,
            "observed_provenance": ledger["meta"]["observed_provenance"]}


def _unit_for(ledger: dict, quantity: str) -> str:
    """新增 observed 项时，单位取自任一子问题 conclusions 里的同名量（逐字复制）。"""
    for prob in ledger["problems"]:
        for con in prob["conclusions"]:
            if con["quantity"] == quantity:
                return con["unit"]
    raise AssertionError(f"台账 conclusions 中找不到量「{quantity}」的单位")


def check_ledger_imposes() -> dict:
    """把台账每条 conclusion 的 imposes 逐个下游子问题对撞（§10⑧ 的 29 条数值条件）。

    _utils/cross_problem_check.py 在本工作区的 _utils/ 下不存在（已在交付说明中报告），
    故这里按台账自身的 must_le / must_ge 语义直接复核实算 observed：
    每个 (下游问题 × 边界侧) 记为一条条件。缺少 observed 记录即 raise，
    不允许"上游登记了约束、下游没有对应实算值"这种静默通过。
    """
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    if ledger["meta"]["observed_provenance"] != "computed":
        raise AssertionError("台账 observed_provenance 仍非 computed，覆盖步骤未生效")
    by_id = {prob["id"]: prob for prob in ledger["problems"]}
    rows, n_cond = [], 0
    for prob in ledger["problems"]:
        for con in prob["conclusions"]:
            imposes = con.get("imposes") or {}
            name = con["quantity"]
            for target in imposes.get("on", []):
                obs = by_id[target]["observed"].get(name)
                if obs is None:
                    raise AssertionError(
                        f"{prob['id']} 的「{name}」对 {target} 施加约束，但 {target} "
                        "没有该量的实算 observed 记录")
                if obs["unit"] != con["unit"]:
                    raise AssertionError(
                        f"{target}.{name} 单位 {obs['unit']} != 上游 {con['unit']}")
                val = float(obs["value"])
                for side, key, ok in (("must_le", "must_le", lambda v, b: v <= b + 1e-9),
                                      ("must_ge", "must_ge", lambda v, b: v >= b - 1e-9)):
                    bound = imposes.get(key)
                    if bound is None:
                        continue
                    n_cond += 1
                    if not ok(val, float(bound)):
                        raise AssertionError(
                            f"[台账对撞] {prob['id']}→{target}「{name}」实算 {val:.6g} "
                            f"违反 {side}={bound}")
                    rows.append({"from": prob["id"], "to": target, "quantity": name,
                                 "side": side, "bound": float(bound), "observed": val})
    return {"n_conditions": n_cond, "n_pairs": len(set((r["to"], r["quantity"]) for r in rows)),
            "rows": rows, "all_satisfied": True,
            "checker_note": ("_utils/cross_problem_check.py 不在本工作区的 _utils/ 下，"
                             "本函数按台账 imposes 语义就地复核，结论可复算")}


def _brief(pay: dict, keys: tuple) -> dict:
    """汇总文件只登记标量结论，场量数组留在各问自己的 results JSON 里。"""
    return {"problem": pay["problem"], "title": pay["title"], "method": pay["method"],
            "property_group": pay["property_group"], "grid": pay["grid"],
            "summary": {k: pay["summary"][k] for k in keys},
            "eps_M": pay["summary"]["eps_M"]}


def main():
    import data_io

    t0 = time.time()
    print("=" * 64, flush=True)
    print("[main] 问题 1：预热平衡阶段（附录 2 常物性）", flush=True)
    pay1 = p1.main()
    print(f"[main] 问题 1 完成，累计 {time.time() - t0:.1f} s", flush=True)

    print("=" * 64, flush=True)
    print("[main] 问题 2：双向强耦合全过程模型（附录 3 变物性）", flush=True)
    pay2 = p2.main()
    print(f"[main] 问题 2 完成，累计 {time.time() - t0:.1f} s", flush=True)

    print("=" * 64, flush=True)
    print("[main] 问题 3：烘干终点判定与总时长（附录 3）", flush=True)
    pay3 = p3.main()
    print(f"[main] 问题 3 完成，累计 {time.time() - t0:.1f} s", flush=True)

    print("=" * 64, flush=True)
    print("[main] 问题 4：收缩动边界（附录 4 + 附件 2，物质坐标）", flush=True)
    pay4 = p4.main()
    print(f"[main] 问题 4 完成，累计 {time.time() - t0:.1f} s", flush=True)

    print("=" * 64, flush=True)
    print("[main] 单因素 ±10% 灵敏度扫描（MC-08）", flush=True)
    pay_s = sens.main()
    print(f"[main] 灵敏度完成，累计 {time.time() - t0:.1f} s", flush=True)

    print("=" * 64, flush=True)
    bounds = build_bounds(pay1, pay2, pay3, pay4)
    bounds_report = validate_bounds(bounds)
    monotonic = build_monotonic(pay_s)
    env = data_io.get_env()
    measured = measured_ledger_values(pay1, pay2, pay3, pay4, env)
    ledger_report = update_ledger(measured)
    imposes_report = check_ledger_imposes()

    t3, t4 = pay3["summary"]["t_star_h"], pay4["summary"]["t_star_h"]
    payload = {
        "study": "CUMCM 2026A 药材的烘干问题",
        "n_subproblems": 4,
        "entry_point": "code/main.py",
        "note": ("场量数组留在 figures/problem_N_results.json；本文件登记标量结论、"
                 "§10⑦ 探针实测值与台账覆盖报告"),
        "answers": {
            "problem_1": {"t_end_s": P.Q1_FILE_T_END_S,
                          "T_center_degC": pay1["summary"]["T_center_1800s"],
                          "T_surface_degC": pay1["summary"]["T_surface_1800s"],
                          "C_center": pay1["summary"]["C_center_1800s"],
                          "C_surface": pay1["summary"]["C_surface_1800s"]},
            "problem_2": {"t_end_h": P.Q2_FILE_T_END_S / P.SECONDS_PER_HOUR,
                          "T_center_degC": pay2["summary"]["T_center_3h"],
                          "T_surface_degC": pay2["summary"]["T_surface_3h"],
                          "C_center": pay2["summary"]["C_center_3h"],
                          "C_surface": pay2["summary"]["C_surface_3h"]},
            "problem_3": {"t_star_h": t3, "t_star_days": t3 / 24.0,
                          "criterion": "max_r C < 0.15",
                          "maxC_at_tstar": pay3["summary"]["maxC_at_tstar"]},
            "problem_4": {"t_star_h": t4, "t_star_days": t4 / 24.0,
                          "R_at_tstar_cm": pay4["summary"]["R_at_tstar_cm"],
                          "delta_vs_q3_h": t4 - t3,
                          "shrink_speedup": pay4["summary"]["shrink_speedup"]},
        },
        "problems": [
            _brief(pay1, ("T_center_1800s", "T_surface_1800s", "C_center_1800s",
                          "C_surface_1800s", "analytic_gap_K")),
            _brief(pay2, ("T_center_3h", "T_surface_3h", "C_center_3h",
                          "C_surface_3h", "conservation_degradation_factor")),
            _brief(pay3, ("t_star_h", "grid_final_rel_change", "maxC_at_tstar",
                          "C_center_6h", "t_star_mean_criterion_h",
                          "t_star_product_exponent_h")),
            _brief(pay4, ("t_star_h", "R_at_tstar_cm", "shrink_speedup",
                          "t_star_q3_h", "D_ratio_app4_over_app3")),
        ],
        "logic_probes": {"bounds": bounds, "monotonic": monotonic,
                         "report": bounds_report},
        "sensitivity": {"ranking": pay_s["ranking"],
                        "base_t_star_h": pay_s["main_group"]["base_t_star_h"],
                        "rows": [{k: r[k] for k in
                                  ("id", "label", "t_star_high_h", "t_star_low_h",
                                   "rel_change_high", "rel_change_low", "abs_rel_max")}
                                 for r in pay_s["main_group"]["rows"]],
                        "conclusion": pay_s["conclusion"]},
        "cross_problem_ledger": {**ledger_report, "measured": measured,
                                 "imposes_check": imposes_report},
        "runtime_s": time.time() - t0,
    }
    out_path, nbytes = RIO.write_results("all_results", payload)
    print(f"[main] 写出 {out_path.name}（{nbytes} bytes）", flush=True)
    print(f"[main] logic_probes.bounds 实测 {bounds_report['n_bounds']} 条全部落在合同区间内",
          flush=True)
    for row in bounds:
        shown = row.get("values", row["value"])
        print(f"    {row['id']} = {shown}", flush=True)
    print(f"[main] 台账 observed 覆盖 {ledger_report['n_overwritten']} 项、"
          f"新增 {ledger_report['n_added']} 项，provenance = "
          f"{ledger_report['observed_provenance']}", flush=True)
    print(f"[main] 台账 imposes 对撞 {imposes_report['n_conditions']} 条数值条件"
          f"（{imposes_report['n_pairs']} 个下游量）全部满足", flush=True)
    print(f"[main] 四问答案：Q3 t* = {t3:.4f} h、Q4 t* = {t4:.4f} h"
          f"（差 {t4 - t3:+.4f} h）", flush=True)
    print(f"[main] 总耗时 {time.time() - t0:.1f} s", flush=True)
    return payload


if __name__ == "__main__":
    main()
