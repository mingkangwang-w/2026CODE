# -*- coding: utf-8 -*-
"""问题 1 的半解析解（验证用）：

无限长圆柱、常物性、Robin 边界、时变环境驱动（Duhamel 叠加）。

温度场：alpha = k/(rho*cp)，Bi = h*R/k；
水分场：取 D=D(C0) 常数近似（注意：Q1 中表面 C 由 2.55 降至 ~1.51，D(C) 实际变化约 21%，
常 D 半解析与数值解的偏差 (~0.04 kg/kg) 正是该非线性效应的量级；
偏差集中在 ~0.3 cm 的扩散渗透层内，故仍构成有效的交叉验证）：alpha->D，Bi_m = h_m*R/D。

阶跃响应 Phi(x,s) = 1 - sum_n A_n J0(lam_n x) exp(-lam_n^2 alpha s / R^2)，
特征根 lam_n 满足 lam*J1(lam) = Bi*J0(lam)，系数 A_n = 2*J1(lam)/(lam*(J0^2+J1^2))。
环境值分段线性（段斜率 m_j），Duhamel：
  phi(x,t) = phi0 + sum_j m_j [ G(x, t-ta_j) - G(x, t-tb_j) ]
  G(x,s) = s - (R^2/alpha) sum_n (A_n/lam_n^2) J0(lam_n x) (1 - exp(-alpha lam_n^2 s/R^2))，s>0；s<=0 时 G=0。
"""
import numpy as np
from scipy.optimize import brentq
from scipy.special import j0, j1, jn_zeros


class CylinderSemiAnalytic:
    def __init__(self, alpha, Bi, R, n_modes=200):
        self.alpha = alpha
        self.Bi = Bi
        self.R = R
        zeros = jn_zeros(0, n_modes)                     # J0 的零点作 bracket
        f = lambda lam: lam * j1(lam) - Bi * j0(lam)
        roots = []
        lo = 1e-12
        for hi in zeros:
            if f(lo) * f(hi) < 0:
                roots.append(brentq(f, lo, hi, xtol=1e-14))
            lo = hi
        self.lam = np.array(roots)
        self.A = 2.0 * j1(self.lam) / (self.lam * (j0(self.lam)**2 + j1(self.lam)**2))

    def G_vec(self, x_arr, s):
        """积分核 G(x, s)，x_arr 为位置数组，s 为单一时间。"""
        x_arr = np.asarray(x_arr, float)
        if s <= 0:
            return np.zeros_like(x_arr)
        Jx = j0(np.outer(self.lam, x_arr))                                # (n, nx)
        expo = np.exp(-self.lam**2 * self.alpha * s / self.R**2)          # (n,)
        coef = self.A * (1.0 - expo) / self.lam**2                        # (n,)
        return s - (self.R**2 / self.alpha) * (coef[:, None] * Jx).sum(axis=0)

    def step_response(self, x_arr, s):
        """单位阶跃响应 Phi(x,s)：零初始场、环境值 t=0 跳变到 1 的解。"""
        x_arr = np.asarray(x_arr, float)
        if s <= 0:
            return np.zeros_like(x_arr)
        Jx = j0(np.outer(self.lam, x_arr))
        expo = np.exp(-self.lam**2 * self.alpha * s / self.R**2)
        return 1.0 - (self.A[:, None] * expo[:, None] * Jx).sum(axis=0)

    def response(self, x_arr, t, t_seg, val_seg, phi0):
        """环境值 val_seg（分段线性）驱动、初始场 phi0 均匀的解。

        对 g(τ)=val_seg(τ)-phi0 做 Duhamel：g(0) 的跳变贡献 g(0)*Phi(x,t)，
        各段斜率贡献 m_j*[G(x,t-ta)-G(x,t-tb)]。
        """
        t_seg = np.asarray(t_seg, float)
        g = np.asarray(val_seg, float) - phi0
        out = g[0] * self.step_response(x_arr, t)
        for j in range(len(t_seg) - 1):
            ta, tb = t_seg[j], t_seg[j + 1]
            if ta >= t:
                break
            m = (g[j + 1] - g[j]) / (tb - ta)
            if m != 0.0:
                out = out + m * (self.G_vec(x_arr, t - ta) - self.G_vec(x_arr, t - tb))
        return phi0 + out
