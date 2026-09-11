# -*- coding: utf-8 -*-
"""物性经验公式：附录2（问题1）、附录3（问题2/3）、附录4（问题4）。

约定：
  C : 干基含水率 kg/kg（可为标量或 ndarray）
  T : 温度 °C（D 的 Arrhenius 项内部换算为 K —— 硬约束 HC-02）
  D 的指数为分数形式 e^{-a/C} —— 硬约束 HC-01
"""
import numpy as np


class Props:
    def __init__(self, name):
        assert name in ('app2', 'app3', 'app4'), name
        self.name = name

    def rho(self, C):
        C = np.asarray(C, float)
        if self.name == 'app2':
            return np.full_like(C, 820.0)
        if self.name == 'app3':
            return 650.0 + 128.0 * C
        return 760.0 + 90.0 * C

    def cp(self, C):
        C = np.asarray(C, float)
        if self.name == 'app2':
            return np.full_like(C, 2600.0)
        if self.name == 'app3':
            return 1450.0 + 2736.0 * C / (C + 1.0)
        return 1850.0 + 2150.0 * C / (C + 1.0)

    def k(self, C):
        C = np.asarray(C, float)
        if self.name == 'app2':
            return np.full_like(C, 0.36)
        if self.name == 'app3':
            return 0.21 + 0.38 * C / (C + 1.0)
        return 0.12 + 0.20 * C / (C + 1.0)

    def D(self, C, T):
        C = np.maximum(np.asarray(C, float), 1e-12)
        TK = np.asarray(T, float) + 273.15          # 开尔文换算
        assert np.all(TK > 273.0) and np.all(TK < 400.0), 'T 超出合理范围'
        if self.name == 'app2':
            return 7e-9 * np.exp(-0.89 / C)
        if self.name == 'app3':
            return 2.4e-3 * np.exp(-0.45 / C) * np.exp(-3850.0 / TK)
        return 4.2e-4 * np.exp(-0.30 / C) * np.exp(-3850.0 / TK)


# 对流系数（全部子问题通用 —— HC-06）
H_CONV = 25.0       # W/(m2·K)
HM_CONV = 8e-7      # m/s

# 初始条件与几何
T0 = 28.0           # °C
C0 = 2.55           # kg/kg
R0 = 0.02           # m
L_HERB = 0.25       # m
C_THRESHOLD = 0.15  # 烘干合格阈值 kg/kg
