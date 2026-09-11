# -*- coding: utf-8 -*-
"""附件读取与环境/半径驱动函数构造。

读附件1（烘房温度、水分浓度）与附件2（药材半径），行数与 sha256 对 DATA_PROFILE.json 复核。
环境量在 t<=14400 s 用分段线性插值，t>14400 s 取平台常值（MODELING_REPORT §2.1，禁止线性外推）。
"""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

import params as P

ENV_FILE = "附件1.xlsx"
RADIUS_FILE = "附件2.xlsx"
SHEET = "Sheet1"
COL_TIME = "时间"
COL_TEMP = "温度"
COL_CONC = "水分浓度"
COL_RADIUS = "半径"


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_sheet(fname: str, expect_cols: list[str]) -> pd.DataFrame:
    """按 DATA_PROFILE.json 的行数/列名/哈希基线读单表，不接受裸 read_excel 缺 sheet_name。"""
    path = P.USER_DATA_DIR / fname
    prof = P.DATA_PROFILE["files"][fname]
    book = pd.read_excel(path, sheet_name=None)
    if len(book) != prof["n_sheets"]:
        raise AssertionError(f"{fname} 工作表数 {len(book)} != 基线 {prof['n_sheets']}")
    df = book[SHEET]
    rows_ref = prof["sheets"][SHEET]["rows"]
    if len(df) != rows_ref:
        raise AssertionError(f"{fname} 行数 {len(df)} != DATA_PROFILE 基线 {rows_ref}（禁止截断/抽样）")
    if list(df.columns) != prof["sheets"][SHEET]["cols"]:
        raise AssertionError(f"{fname} 列名 {list(df.columns)} != 基线")
    if list(df.columns) != expect_cols:
        raise AssertionError(f"{fname} 列名与本模块约定不符：{list(df.columns)}")
    digest = _sha256(path)
    if digest != prof["sha256"]:
        raise AssertionError(f"{fname} sha256 {digest[:16]} != 基线 {prof['sha256'][:16]}")
    if df.isna().to_numpy().any():
        raise AssertionError(f"{fname} 存在缺失值，需先确认口径再计算")
    return df


class EnvDriving:
    """烘房环境驱动：区间内分段线性插值，区间外平台常值延拓。"""

    def __init__(self) -> None:
        df = _load_sheet(ENV_FILE, [COL_TIME, COL_TEMP, COL_CONC])
        self.t = df[COL_TIME].to_numpy(dtype=float)
        self.temp = df[COL_TEMP].to_numpy(dtype=float)
        self.conc = df[COL_CONC].to_numpy(dtype=float)
        if not np.all(np.diff(self.t) > 0):
            raise AssertionError("附件1 时间列非严格递增")
        self.t_end = float(self.t[-1])
        if abs(self.t_end - P.ENV_DATA_T_END_S) > 1e-9:
            raise AssertionError(f"附件1 覆盖上界 {self.t_end} != {P.ENV_DATA_T_END_S}")
        mask = self.t >= P.ENV_PLATEAU_START_S
        self.n_plateau = int(mask.sum())
        self.temp_plateau = float(self.temp[mask].mean())
        self.conc_plateau = float(self.conc[mask].mean())
        self.temp_plateau_std = float(self.temp[mask].std(ddof=1))
        self.conc_plateau_std = float(self.conc[mask].std(ddof=1))

    def T_inf(self, t):
        """环境温度（摄氏度）；t>14400 s 返回平台均值，不做趋势外推。"""
        inside = np.interp(t, self.t, self.temp)
        return np.where(np.asarray(t) > self.t_end, self.temp_plateau, inside)

    def C_inf(self, t):
        """环境水分浓度（kg/kg 干基）；t>14400 s 返回平台均值。"""
        inside = np.interp(t, self.t, self.conc)
        return np.where(np.asarray(t) > self.t_end, self.conc_plateau, inside)

    def T_inf_scalar(self, t: float) -> float:
        return float(self.T_inf(t))

    def C_inf_scalar(self, t: float) -> float:
        return float(self.C_inf(t))


class RadiusHistory:
    """附件2 给定的 R(t)：区间内线性插值，区间外端点保持（tr_radius_data）。"""

    def __init__(self) -> None:
        df = _load_sheet(RADIUS_FILE, [COL_TIME, COL_RADIUS])
        self.t = df[COL_TIME].to_numpy(dtype=float)
        self.radius_cm = df[COL_RADIUS].to_numpy(dtype=float)
        self.radius_m = self.radius_cm / P.CM_PER_M
        if not np.all(np.diff(self.t) > 0):
            raise AssertionError("附件2 时间列非严格递增")
        if np.any(np.diff(self.radius_m) > 0.0):
            raise AssertionError("附件2 半径出现回升，与收缩物理矛盾")
        self.t_end = float(self.t[-1])
        self.R_start_m = float(self.radius_m[0])
        self.R_min_m = float(self.radius_m.min())
        # 收缩到达末值的时刻（ca_radius_plateau 锚点）
        idx = int(np.argmax(self.radius_m <= self.R_min_m))
        self.t_reach_min_s = float(self.t[idx])

    def R(self, t):
        """半径（m）；端点外保持端点值，不外推。"""
        return np.interp(t, self.t, self.radius_m)

    def R_scalar(self, t: float) -> float:
        return float(self.R(t))

    def Rdot_scalar(self, t: float, dt: float) -> float:
        """后向差商给出 dR/dt（m/s），仅供对照变体与诊断使用。"""
        return (self.R_scalar(t) - self.R_scalar(max(t - dt, 0.0))) / dt


_ENV_CACHE: EnvDriving | None = None
_RADIUS_CACHE: RadiusHistory | None = None


def get_env() -> EnvDriving:
    global _ENV_CACHE
    if _ENV_CACHE is None:
        _ENV_CACHE = EnvDriving()
    return _ENV_CACHE


def get_radius() -> RadiusHistory:
    global _RADIUS_CACHE
    if _RADIUS_CACHE is None:
        _RADIUS_CACHE = RadiusHistory()
    return _RADIUS_CACHE


def data_self_check() -> dict:
    """B-22 / mf_plateau_extrap / mf_moving_domain / tr_* 的运行时复核。"""
    env, rad = get_env(), get_radius()
    far = 2e5
    if abs(env.T_inf_scalar(far) - P.T_INF_PLATEAU_REF) >= 1e-3:
        raise AssertionError(f"T_inf(2e5)={env.T_inf_scalar(far)} 未落在平台参考值 1e-3 内")
    if abs(env.C_inf_scalar(far) - P.C_INF_PLATEAU_REF) >= 1e-5:
        raise AssertionError(f"C_inf(2e5)={env.C_inf_scalar(far)} 未落在平台参考值 1e-5 内")
    if abs(env.T_inf_scalar(0.0) - env.temp[0]) > 1e-12:
        raise AssertionError("t=0 环境温度未取附件1 首点")
    if abs(rad.R_start_m - P.R0_M) > 1e-12:
        raise AssertionError(f"R(0)={rad.R_start_m} != R0={P.R0_M}")
    if abs(rad.R_min_m - P.R_MIN_REF_M) > 1e-9:
        raise AssertionError(f"min R={rad.R_min_m} != {P.R_MIN_REF_M}")
    if abs(rad.R_scalar(-1.0) - P.R0_M) > 1e-12 or abs(rad.R_scalar(1e7) - rad.R_min_m) > 1e-12:
        raise AssertionError("附件2 端点外未按端点保持处理")
    info = {
        "附件1_rows": int(env.t.size),
        "附件2_rows": int(rad.t.size),
        "env_t_end_s": env.t_end,
        "plateau_n": env.n_plateau,
        "T_inf_plateau_degC": env.temp_plateau,
        "C_inf_plateau": env.conc_plateau,
        "T_inf_plateau_std": env.temp_plateau_std,
        "C_inf_plateau_std": env.conc_plateau_std,
        "T_inf_last_sample_degC": float(env.temp[-1]),
        "radius_t_end_s": rad.t_end,
        "R0_m": rad.R_start_m,
        "R_min_m": rad.R_min_m,
        "t_reach_R_min_h": rad.t_reach_min_s / P.SECONDS_PER_HOUR,
    }
    return info


if __name__ == "__main__":
    print(json.dumps(data_self_check(), ensure_ascii=False, indent=2))
    print("[data_io] 附件读取与驱动函数口径 OK")
