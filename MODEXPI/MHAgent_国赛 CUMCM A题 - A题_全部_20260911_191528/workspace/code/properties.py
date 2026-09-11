# -*- coding: utf-8 -*-
"""物性本构（MODELING_REPORT §4）。三组公式按问题分列，不得混用。

统一 T_K = T + 273.15；含水率指数为分式 exp(-a/C)（a<0 已含在系数里）。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import params as P


def to_kelvin(T_degC):
    """摄氏转开尔文（R2：exp(-3850/T) 中 T 必须是绝对温度）。"""
    return np.asarray(T_degC, dtype=float) + P.KELVIN_OFFSET


def _c_safe(C):
    """仅对 C->0 时 exp(-a/C) 的浮点下溢做保护，阈值远低于判据 0.15。"""
    return np.maximum(np.asarray(C, dtype=float), P.C_FLOOR)


@dataclass(frozen=True)
class PropertyGroup:
    """一组物性本构。const 型（附录2）与 C 依赖型（附录3/4）共用同一接口。"""

    name: str
    formula_note: str
    rho_const: float
    rho_coef_C: float
    cp_const: float
    cp_coef_frac: float
    k_const: float
    k_coef_frac: float
    D_pre: float
    D_exp_C: float
    D_exp_T: float          # 0.0 表示 D 不依赖温度（附录2）

    def rho(self, C):
        return self.rho_const + self.rho_coef_C * np.asarray(C, dtype=float)

    def cp(self, C):
        Cf = np.asarray(C, dtype=float)
        return self.cp_const + self.cp_coef_frac * Cf / (Cf + 1.0)

    def k(self, C):
        Cf = np.asarray(C, dtype=float)
        return self.k_const + self.k_coef_frac * Cf / (Cf + 1.0)

    def capacity(self, C):
        """能量方程容量项 rho(C)*cp(C)。"""
        return self.rho(C) * self.cp(C)

    def D(self, C, T_degC, pre_scale: float = 1.0, exp_C_scale: float = 1.0,
          exp_T_scale: float = 1.0, product_exponent: bool = False):
        """水分扩散系数。分式指数 exp(a/C)；product_exponent=True 仅供 §9.2 证伪对照。"""
        Cs = _c_safe(C)
        a_C = self.D_exp_C * exp_C_scale
        term_C = np.exp(a_C * Cs) if product_exponent else np.exp(a_C / Cs)
        val = self.D_pre * pre_scale * term_C
        if self.D_exp_T != 0.0:
            T_K = to_kelvin(T_degC)
            if np.any(T_K < 273.0) or np.any(T_K > 400.0):
                raise AssertionError(f"T_K 越界 {float(np.min(T_K))}~{float(np.max(T_K))}，疑误用摄氏度")
            val = val * np.exp(self.D_exp_T * exp_T_scale / T_K)
        return val

    def is_constant(self) -> bool:
        return self.rho_coef_C == 0.0 and self.cp_coef_frac == 0.0 and self.k_coef_frac == 0.0


APPENDIX2 = PropertyGroup(
    name="附录2", formula_note=P.FORMULA_D_A2,
    rho_const=P.RHO_A2, rho_coef_C=0.0,
    cp_const=P.CP_A2, cp_coef_frac=0.0,
    k_const=P.K_A2, k_coef_frac=0.0,
    D_pre=P.D_A2_PRE, D_exp_C=P.D_A2_EXP_C, D_exp_T=0.0,
)

APPENDIX3 = PropertyGroup(
    name="附录3", formula_note=P.FORMULA_D_A3,
    rho_const=P.RHO_A3_CONST, rho_coef_C=P.RHO_A3_COEF_C,
    cp_const=P.CP_A3_CONST, cp_coef_frac=P.CP_A3_COEF_FRAC,
    k_const=P.K_A3_CONST, k_coef_frac=P.K_A3_COEF_FRAC,
    D_pre=P.D_A3_PRE, D_exp_C=P.D_A3_EXP_C, D_exp_T=P.D_A3_EXP_T,
)

APPENDIX4 = PropertyGroup(
    name="附录4", formula_note=P.FORMULA_D_A4,
    rho_const=P.RHO_A4_CONST, rho_coef_C=P.RHO_A4_COEF_C,
    cp_const=P.CP_A4_CONST, cp_coef_frac=P.CP_A4_COEF_FRAC,
    k_const=P.K_A4_CONST, k_coef_frac=P.K_A4_COEF_FRAC,
    D_pre=P.D_A4_PRE, D_exp_C=P.D_A4_EXP_C, D_exp_T=P.D_A4_EXP_T,
)


def volume_ratio_dry_basis(C, group: PropertyGroup):
    """绝干质量守恒给出的体积比 V/V0 = ((1+C)/rho(C)) / ((1+C0)/rho(C0))。"""
    Cf = np.asarray(C, dtype=float)
    return ((1.0 + Cf) / group.rho(Cf)) / ((1.0 + P.C0) / group.rho(P.C0))


def predict_radius_radial_only(C, group: PropertyGroup):
    """仅径向收缩：V/V0=(R/R0)^2 → R_pred = R0*sqrt(体积比)。正向预测，不由 R 反演 C。"""
    return P.R0_M * np.sqrt(volume_ratio_dry_basis(C, group))


def predict_radius_isotropic(C, group: PropertyGroup):
    """各向同性收缩对照：V/V0=(R/R0)^3。"""
    return P.R0_M * volume_ratio_dry_basis(C, group) ** (1.0 / 3.0)


def _self_check() -> dict:
    """物性口径复核：常物性零方差、变物性正方差、Arrhenius 用开尔文。"""
    C_field = np.linspace(P.C_TH, P.C0, 11)
    if not APPENDIX2.is_constant():
        raise AssertionError("附录2 应为常物性")
    if np.ptp(APPENDIX2.rho(C_field)) != 0.0 or np.ptp(APPENDIX2.cp(C_field)) != 0.0 \
            or np.ptp(APPENDIX2.k(C_field)) != 0.0:
        raise AssertionError("B-04：问题1 物性出现 C 依赖")
    for grp in (APPENDIX3, APPENDIX4):
        if np.ptp(grp.rho(C_field)) <= 0.0 or np.ptp(grp.cp(C_field)) <= 0.0 or np.ptp(grp.k(C_field)) <= 0.0:
            raise AssertionError(f"mf_variable_props：{grp.name} 物性方差为 0")
    T_ref = P.T_INF_PLATEAU_REF
    d3 = float(APPENDIX3.D(P.C0, T_ref))
    d4 = float(APPENDIX4.D(P.C0, T_ref))
    if not d4 < d3:
        raise AssertionError("附录4 的 D 应小于附录3（bd_tstar_q4_range 起点）")
    # 分式读法下 D 随 C 下降而减小（吸湿性物料的正确定性行为）；
    # 乘积误读在判据区间 C=0.15 附近反而给出大一个量级的 D，故 t* 只有 16 h 级（§9.2）。
    if not float(APPENDIX3.D(P.C_TH, T_ref)) < d3:
        raise AssertionError("R1：分式指数下 D 应随 C 下降而减小")
    d3_product_at_th = float(APPENDIX3.D(P.C_TH, T_ref, product_exponent=True))
    if not d3_product_at_th > float(APPENDIX3.D(P.C_TH, T_ref)):
        raise AssertionError("§9.2 乘积误读应在判据区间给出更大的 D")
    R_pred_a4 = float(predict_radius_radial_only(0.05, APPENDIX4))
    R_pred_a3 = float(predict_radius_radial_only(0.05, APPENDIX3))
    R_pred_iso = float(predict_radius_isotropic(0.05, APPENDIX4))
    return {
        "D_A3_at_C0_50C": d3,
        "D_A4_at_C0_50C": d4,
        "D_A3_at_Cth_50C": float(APPENDIX3.D(P.C_TH, T_ref)),
        "D_A3_product_at_Cth": d3_product_at_th,
        "rho_A3_at_C0": float(APPENDIX3.rho(P.C0)),
        "rho_A4_at_C0": float(APPENDIX4.rho(P.C0)),
        "R_pred_a4_radial_cm": R_pred_a4 * P.CM_PER_M,
        "R_pred_a3_radial_cm": R_pred_a3 * P.CM_PER_M,
        "R_pred_a4_isotropic_cm": R_pred_iso * P.CM_PER_M,
    }


if __name__ == "__main__":
    for key, val in _self_check().items():
        print(f"  {key} = {val:.6g}")
    print("[properties] 物性本构口径 OK")
