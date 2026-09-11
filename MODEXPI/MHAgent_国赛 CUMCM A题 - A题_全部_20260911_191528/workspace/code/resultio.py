# -*- coding: utf-8 -*-
"""结果 JSON 写盘与摘要工具。

figures/problem_N_results.json 内含时空场数组，体量较大，
禁止整体回读；诊断请用 summarize_results.py 只打印标量结论。
"""
from __future__ import annotations

import json

import numpy as np

import params as P

FIELD_DECIMALS = 6
SMALL_MAGNITUDE = 1e-4
SIGNIF_DIGITS = 6


def round_value(val: float) -> float:
    """场量保留 6 位小数以控体量；小量级改保留有效位数。

    绝对定点舍入会把 eps_M(1e-14)、D(1e-12)、Robin 残差这类诊断量全部压成 0.0，
    使 B-12「eps_M < 0.01」在结果 JSON 上退化成对 0 的空洞校验——审计脚本从 JSON
    重算时看不到真实量级。温度/含水率场的量级在 1e-2~1e2，走定点分支不受影响。
    """
    val = float(val)
    if val == 0.0:
        return 0.0
    if abs(val) >= SMALL_MAGNITUDE:
        return round(val, FIELD_DECIMALS)
    return float(f"{val:.{SIGNIF_DIGITS - 1}e}")


def _clean(obj):
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return _clean(obj.tolist())
    if isinstance(obj, (np.floating, float)):
        val = float(obj)
        if not np.isfinite(val):
            raise ValueError(f"结果含非有限值 {val}")
        return round_value(val)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj


def write_results(name: str, payload: dict):
    """写 figures/<name>.json，返回 (路径, 字节数)。"""
    P.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = P.FIGURES_DIR / f"{name}.json"
    text = json.dumps(_clean(payload), ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, encoding="utf-8")
    return path, len(text.encode("utf-8"))


def field_grid(times_s, fields, every: int, stride=None):
    """把逐输出步的场按 every 抽稀成绘图网格（云图/Hovmöller 用）。"""
    stride = P.OUT_NODE_STRIDE if stride is None else stride
    idx = list(range(0, len(times_s), every))
    if idx[-1] != len(times_s) - 1:
        idx.append(len(times_s) - 1)
    return {
        "times_s": [float(times_s[i]) for i in idx],
        "values": [[round_value(v) for v in np.asarray(fields[i])[::stride]]
                   for i in idx],
    }
