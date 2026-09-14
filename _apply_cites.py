# -*- coding: utf-8 -*-
"""在 论文.md 正文中插入参考文献标注（紫色上标），并标注两条参考文献本身的问题。

原稿列了 10 条参考文献，但正文里一个 [n] 标注都没有——读者无法判断哪句话
出自哪篇文献。本脚本按各文献的内容择位插入。

标注用紫色 #7030A0，与已有的三种修订色区分：
    红 #C00000 内容更正 / 蓝 #1F6FB2 新增说明 / 橙 #B26B00 编号调整 / 紫 引用标注
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '论文.md')
PUR = '#7030A0'


def P(nums):
    """紫色上标引用标注。"""
    return '<sup style="color:%s">[%s]</sup>' % (PUR, ']['.join(nums))


# (原文, 替换为) —— 引用标注插在句末标点之前（GB/T 7714 顺序编码制）
CITES = [
    # [2] 杨世铭《传热学》 [5] Crank《扩散的数学》→ 两场控制方程
    ('在一维径向轴对称下，能量守恒与水分（干基）质量守恒方程为',
     '在一维径向轴对称下，能量守恒与水分（干基）质量守恒方程为' + P(['2', '5'])),

    # [2] → Robin 第三类边界条件
    ('表面两个Robin条件的通量平衡如图4所示。',
     '表面两个Robin条件的通量平衡如图4所示' + P(['2']) + '。'),

    # [5] → 扩散系数的分式指数形式
    ('图表函数指数项一律为$e^{−a/C}$：',
     '图表函数指数项一律为$e^{−a/C}$' + P(['5']) + '：'),

    # [3] 陶文铨《数值传热学》 [4] Patankar → 控制体划分
    ('其中$j=0$与$j=N$为半控制体。',
     '其中$j=0$与$j=N$为半控制体' + P(['3', '4']) + '。'),

    # [3] → 离散通量守恒
    ('使离散层面的通量守恒成为恒等式，如',
     '使离散层面的通量守恒成为恒等式' + P(['3']) + '，如'),

    # [1] Crank–Nicolson 原文 → 问题一的时间离散
    ('Crank–Nicolson 隐式格式在时间离散。',
     'Crank–Nicolson 隐式格式在时间离散' + P(['1']) + '。'),

    # [1] → CN 格式表达式
    ('记离散后系统为$du/dt=Lu+b$，Crank--Nicolson 格式为',
     '记离散后系统为$du/dt=Lu+b$' + P(['1']) + '，Crank--Nicolson 格式为'),

    # [8] Carslaw & Jaeger《固体中的热传导》→ 圆柱径向导热的特征时间
    ('相差 34 倍的直接体现。',
     '相差 34 倍的直接体现' + P(['8']) + '。'),

    # [6] 潘永康《现代干燥技术》 [7] Mujumdar → 预热平衡与恒温干燥两阶段
    ('处理方式包含预热平衡和恒温干燥两个阶段，烘房的温湿度环境会发生变化。',
     '处理方式包含预热平衡和恒温干燥两个阶段' + P(['6', '7'])
     + '，烘房的温湿度环境会发生变化。'),

    # [9] → 全局灵敏度（此条引用本身存疑，见文末说明）
    ('以置换重要性（permutation importance）量化各参数贡献',
     '以置换重要性（permutation importance）量化各参数贡献' + P(['9'])),
]

# 参考文献本身的问题，直接标在条目上
REF_NOTES = [
    # [10] 与 [5] 是同一本书
    ('[10] CRANK J. The mathematics of diffusion[M]. 2nd ed. Oxford: Oxford University Press, 1975.',
     '[10] CRANK J. The mathematics of diffusion[M]. 2nd ed. Oxford: Oxford University Press, 1975.'
     '<span style="color:#C00000"> ← **与 [5] 重复**：Crank 的《The Mathematics of Diffusion》'
     '第 2 版 1975 年由 Clarendon Press（Oxford）出版，[5] 已列，此条应删。</span>'),

    # [9] 与 7.4 实际使用的方法不符
    ('[9] LUNDBERG S M, LEE S I. A unified approach to interpreting model predictions[J]. Advances in Neural Information Processing Systems, 2017, 30.',
     '[9] LUNDBERG S M, LEE S I. A unified approach to interpreting model predictions[J]. Advances in Neural Information Processing Systems, 2017, 30.'
     '<span style="color:#C00000"> ← **与实际方法不符**：该文是 SHAP 方法的原文，'
     '而 7.4 节用的是置换重要性（permutation importance），并非 SHAP。'
     '建议改为随机森林原文（Breiman L. Random forests[J]. Machine Learning, 2001, 45(1): 5-32）'
     '或置换重要性原文（Fisher A, Rudin C, Dominici F. All models are wrong, but many are useful'
     '[J]. Journal of Machine Learning Research, 2019, 20(177): 1-81）。</span>'),
]

# 修订说明里的图例补一行
LEGEND_OLD = ('> - <span style="color:#B26B00">**橙色**</span>：编号／交叉引用调整（图表号重排）\n')
LEGEND_NEW = (LEGEND_OLD
              + '> - <span style="color:#7030A0">**紫色上标**</span>：参考文献引用标注\n')

# 文末补一节
TAIL = """

## 参考文献引用标注说明

原稿列了 10 条参考文献，但正文中没有任何 `[n]` 标注，读者无法判断哪句话出自哪篇文献。本次已按各文献内容择位补标：

| 文献 | 标注位置 | 依据 |
|---|---|---|
| [1] Crank & Nicolson 1947 | 6.1.1 时间离散、式(10) | 问题一采用 Crank–Nicolson 格式，系该文提出 |
| [2] 杨世铭《传热学》 | 5.1.2 控制方程、表面 Robin 条件 | 能量方程与第三类边界条件的传热学基础 |
| [3] 陶文铨《数值传热学》 | 5.2.1 控制体划分、界面通量守恒 | 守恒型离散与界面处理的依据 |
| [4] Patankar 1980 | 5.2.1 控制体划分 | 有限体积法（控制体积法）的经典著作 |
| [5] Crank《扩散的数学》 | 5.1.2 水分方程、5.1.3 指数形式 | 扩散方程的数学基础与分式指数形式 |
| [6] 潘永康《现代干燥技术》 | 1.2 预热平衡与恒温干燥两阶段 | 干燥过程分期的工艺依据 |
| [7] Mujumdar《工业干燥手册》 | 1.2 同上 | 同上 |
| [8] Carslaw & Jaeger 1959 | 6.1.3 圆柱径向导热的特征时间 | 圆柱体导热的经典解与特征时间估计 |
| [9] Lundberg & Lee 2017 | 7.4 参数贡献量化 | **存疑**，见下 |
| [10] Crank 1975 | 未标注 | **与 [5] 重复**，建议删除 |

**两处需要作者处理：**

1. **[10] 与 [5] 是同一本书**（Crank, *The Mathematics of Diffusion*, 2nd ed., 1975），仅出版社写法不同（Clarendon Press 与 Oxford University Press）。保留 [5] 即可，删去 [10] 后全文编号顺延。

2. **[9] 与实际使用的方法不符**。7.4 节用的是置换重要性（permutation importance），而 [9] 是 SHAP 方法的原文，两者不是同一种归因方法。已在原文该处标出，建议替换为随机森林原文（Breiman, 2001）或置换重要性原文（Fisher et al., 2019）；若保留 [9]，则应在 7.4 节补做 SHAP 分析使引用成立。
"""


def main():
    s = io.open(SRC, encoding='utf-8').read()
    ok, miss = 0, []
    for old, new in CITES + REF_NOTES:
        if old in s:
            s = s.replace(old, new, 1)
            ok += 1
        else:
            miss.append(old[:44])
    s = s.replace(LEGEND_OLD, LEGEND_NEW, 1)
    s = s.rstrip() + TAIL
    io.open(SRC, 'w', encoding='utf-8').write(s)
    print('插入标注 %d 处' % ok)
    for m in miss:
        print('  [未匹配]', m)


if __name__ == '__main__':
    main()
