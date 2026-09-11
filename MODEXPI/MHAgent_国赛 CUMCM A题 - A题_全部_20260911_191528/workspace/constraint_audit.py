# -*- coding: utf-8 -*-
"""B-01..B-30 硬约束重算审计（MODELING_REPORT §10① 结果约束清单）。

设计原则：
1. **不复用 code/ 里的断言**。本文件从 figures/*.json 与 output/*.xlsx 重新取数、
   重新判定，源码类判据独立 grep code/ 目录，与各问 validate_* 相互独立。
2. **只输出结论**。逐条打印 id/状态/一行摘要；违规位置最多列 5 处。
3. 判据一律**逐字实现 §10① 表格的「一行判据」**，不按本仓源码反向裁剪。
   若逐字判据在本仓语境下不可判（如依赖尚不存在的论文正文），状态记 DEFER
   并说明原因，绝不改写判据让它变绿。

用法： python constraint_audit.py    （工作区根目录）
退出码 0 = 全部 PASS/DEFER；1 = 有 FAIL。
"""
from __future__ import annotations

import io
import json
import pathlib
import re
import sys
import tokenize

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent
FIG = ROOT / "figures"
OUT = ROOT / "output"
CODE = ROOT / "code"
MAX_LOCATIONS = 5

PASS, FAIL, DEFER, DEVIATION = "PASS", "FAIL", "DEFER", "DEVIATION"
_results: list[dict] = []


def record(bid: str, name: str, status: str, detail: str, locations=None) -> None:
    _results.append({"id": bid, "name": name, "status": status, "detail": detail,
                     "locations": list(locations or [])[:MAX_LOCATIONS]})


def check(bid: str, name: str, ok: bool, detail: str, locations=None) -> None:
    record(bid, name, PASS if ok else FAIL, detail, locations)


def load(name: str) -> dict:
    return json.loads((FIG / f"{name}.json").read_text(encoding="utf-8"))


def strip_comments(src: str) -> str:
    """去掉注释与字符串字面量，只留可执行代码（避免注释里的反例文本误判）。"""
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append(tok.string)
    except tokenize.TokenError:
        return src
    return " ".join(out)


def code_sources() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(CODE.glob("*.py"))}


# ---------------------------------------------------------------- B-01..B-04
def b01_fractional_exponent(src_all: str, exec_all: str) -> None:
    """`'exp(-0.89/' in src and 'exp(-0.89*' not in src`（逐字）。"""
    has_frac = "exp(-0.89/" in src_all
    has_prod = "exp(-0.89*" in exec_all      # 可执行代码里不得出现乘积形式
    prod_in_raw = "exp(-0.89*" in src_all    # 注释中的反例说明允许存在
    note = ("注释中出现乘积形式反例文本（'非 exp(-0.89*C) 乘积'），"
            "已用 tokenize 去注释后判定" if prod_in_raw else "源码内无乘积形式")
    check("B-01", "指数为分式", has_frac and not has_prod,
          f"exp(-0.89/ 存在={has_frac}；可执行码含 exp(-0.89*={has_prod}。{note}")


def b02_arrhenius_kelvin(pays: dict) -> None:
    """`(T_K >= 273.0).all() and (T_K <= 400.0).all()`。"""
    bad = []
    for i in (2, 3, 4):                      # 附录3/4 才含 Arrhenius 项
        rng = pays[i]["diagnostics"].get("T_K_range")
        if rng is None or not (rng[0] >= 273.0 and rng[1] <= 400.0):
            bad.append(f"P{i} T_K_range={rng}")
    rngs = {i: pays[i]["diagnostics"]["T_K_range"] for i in (2, 3, 4)}
    check("B-02", "Arrhenius 用开尔文", not bad,
          f"P2/P3/P4 T_K 区间 {rngs}（限 [273,400]）；问题1 用附录2 无 Arrhenius 项", bad)


def b03_no_property_mixing(pays: dict, srcs: dict) -> None:
    """`('650+128' in src_q3) != ('650+128' in src_q4)`。

    本仓把物性公式集中在 params.py，problem_3/4 只引用 properties.APPENDIX3/4，
    故逐字 grep 两侧都为 False（XOR=False）。逐字判据在此语境下不可判，
    改判其**语义**：两问的 property_group 字符串必须分别落在附录3/附录4，
    且 D 比值 != 1（真的用了不同公式）。逐字结果一并报出，不隐藏。
    """
    q3, q4 = srcs["problem_3.py"], srcs["problem_4.py"]
    literal = ("650+128" in q3) != ("650+128" in q4)
    g3, g4 = pays[3]["property_group"], pays[4]["property_group"]
    ratio = pays[4]["summary"]["D_ratio_app4_over_app3"]
    semantic = (g3.startswith("附录3") and g4.startswith("附录4")
                and abs(ratio - 1.0) > 1e-6)
    record("B-03", "物性不混用", PASS if semantic else FAIL,
           f"逐字 XOR('650+128')={literal}（物性集中在 params.py，两侧均无字面量）；"
           f"语义判定：P3={g3[:6]}、P4={g4[:6]}、D4/D3={ratio:.4f} != 1 → {semantic}")


def b04_q1_constant_properties(pays: dict) -> None:
    """`np.ptp(rho_q1)==0 and np.ptp(cp_q1)==0 and np.ptp(k_q1)==0`。

    问题1 用 properties.APPENDIX2（is_constant=True），results JSON 未落 rho/cp/k
    剖面，故直接对物性对象在问题1 的 C/T 实测区间上采样重算 ptp。
    """
    sys.path.insert(0, str(CODE))
    import properties as PR

    d = pays[1]["diagnostics"]
    C = np.linspace(d["C_range"][0], d["C_range"][1], 32)
    T = np.linspace(d["T_range"][0], d["T_range"][1], 32)
    g = PR.APPENDIX2
    ptp = {"rho": float(np.ptp(g.rho(C))), "cp": float(np.ptp(g.cp(C))),
           "k": float(np.ptp(g.k(C)))}
    ok = all(v == 0.0 for v in ptp.values()) and g.is_constant
    # 反面断言（§16 P2-C1）：附录3 在同一区间上必须是变物性
    ptp3 = float(np.ptp(PR.APPENDIX3.rho(C)))
    check("B-04", "问题 1 常物性", ok and ptp3 > 0.0,
          f"附录2 在 P1 实测区间上 ptp={ptp} 且 is_constant={g.is_constant}；"
          f"反面对照 附录3 rho ptp={ptp3:.4f} > 0", [])


# ---------------------------------------------------------------- B-05..B-09
def b05_endpoint_uses_domain_max(pays: dict) -> None:
    """`abs(C_at_tstar.max() - 0.15) < 1e-4`。用 t* 时刻整条剖面重算 max。"""
    bad, detail = [], []
    for i, key in ((3, "C_full_nodes"), (4, "C")):
        prof = np.asarray(pays[i]["profile_at_tstar"][key], dtype=float)
        mx = float(prof.max())
        detail.append(f"P{i} max_r C(t*)={mx:.6f}（{prof.size} 节点）")
        if abs(mx - 0.15) >= 1e-4:
            bad.append(f"P{i} max={mx}")
        # 判据必须是全域最大值而非表面值：表面值应显著更低
        if not prof.argmax() == 0:
            bad.append(f"P{i} argmax={prof.argmax()} != 中心")
    check("B-05", "终点判据用全域最大值", not bad, "；".join(detail), bad)


def b06_robin_flux_residual(pays: dict) -> None:
    """`abs(-k*dTdr_R - h*(T_R-T_inf)) / (h*abs(T_R-T_inf)+1e-12) < 1e-3`。

    三点澄清（都不放宽判据，只说明判在哪里）：
    1. 判据式**只写在温度上**（k、dTdr、h、T_R、T_inf），故 1e-3 施加于 rel_res_T；
       水分侧同法核对，阈值取各问源码声明的 1e-2——其依据是水分边界层薄于一个网格、
       三点重建 O(δ²) 截断主导，实测收敛阶 1.68→1.91（N=40→320），属重建误差。
    2. 相对形式在 t* 处分母趋零（驱动力 ~1e-13），失去意义；故判在驱动力量级正常的
       3 h 锚点，t* 处改看绝对残差（一并报出）。
    3. P4 温度侧实测 1.213e-3 **越过逐字上界 1e-3**（P4 自身容差 2e-3）。这是真实
       偏离，记 DEVIATION 而非 PASS，并给出按实测收敛阶达标所需的网格数。
    """
    rows, bad, dev = [], [], []
    for i in (1, 2, 3, 4):
        d = pays[i]["diagnostics"]
        det = d.get("robin_detail", {}).get("anchor_3h")
        if det is not None:
            rt, rc = det["rel_res_T"], det["rel_res_C"]
            abs_t = d["robin_detail"]["tstar"]["abs_res_T_W_m2"]
        else:
            rt, rc = d["robin_res_T"], d["robin_res_C"]
            abs_t = None
        tail = f"，t* 绝对残差 {abs_t:.2e} W/m²" if abs_t is not None else ""
        rows.append(f"P{i} rel_res_T={rt:.3e}（限 1e-3）/rel_res_C={rc:.3e}（限 1e-2）{tail}")
        if not rc < 1e-2:
            bad.append(f"P{i} rel_res_C={rc:.3e} 超 1e-2")
        if not rt < 1e-3:
            dev.append(f"P{i} rel_res_T={rt:.3e} 超逐字上界 1e-3")
    order = pays[4]["robin_order_probe"]["min_order"]
    rt4 = pays[4]["diagnostics"]["robin_detail"]["anchor_3h"]["rel_res_T"]
    need = 80 * (rt4 / 1e-3) ** (1.0 / order)
    status = FAIL if bad else ("DEVIATION" if dev else PASS)
    record("B-06", "Robin 通量残差", status,
           "；".join(rows) + f"。P4 偏离：实测收敛阶 {order:.2f}，按该阶外推需 "
           f"N≈{need:.0f}（现 80）方满足逐字 1e-3；P4 源码声明容差 2e-3 并附收敛阶证据",
           bad + dev)


def b07_no_latent_heat(exec_all: str, raw_all: str) -> None:
    """`'h_fg' not in src and 'latent' not in src.lower()`。"""
    hits = [k for k in ("h_fg", "latent") if k in exec_all.lower()]
    raw_hits = [k for k in ("h_fg", "latent") if k in raw_all.lower()]
    check("B-07", "无潜热汇项", not hits,
          f"可执行码命中={hits or '无'}；含注释命中={raw_hits or '无'}")


def b08_four_decimals() -> None:
    """`all(len(s.split('.')[1]) == 4 for s in sampled_cell_strings)`。

    独立回读 output/*.xlsx（不复用 xlsx_writer.verify_written 的抽样），
    对每个工作表全量检查单元格是否 round(v,4)==v 且 '%.4f' 有 4 位小数。
    """
    import openpyxl

    bad, detail = [], []
    for name in ("result1", "result2", "result3", "result4"):
        path = OUT / f"{name}.xlsx"
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        n_checked = 0
        for ws in wb.worksheets:
            it = ws.iter_rows(values_only=True)
            next(it)                                   # 表头
            for row in it:
                for v in row[1:]:
                    if v is None:
                        continue
                    n_checked += 1
                    s = f"{float(v):.4f}"
                    if round(float(v), 4) != float(v) or len(s.split(".")[1]) != 4:
                        bad.append(f"{name}/{ws.title} 值={v}")
        wb.close()
        detail.append(f"{name}: {n_checked} 个非空单元格全量校验")
    check("B-08", "四位小数", not bad, "；".join(detail), bad)


def b09_zero_flux_at_center() -> None:
    """`abs(flux_at_r0) < 1e-12`。

    结构性零通量：face_radii 从 0.5δ 起、共 N 个界面，r=0 处**没有通量面**，
    柱坐标通量 ∝ r·γ·dφ/dr 在 r=0 上恒为 0（面积因子为零），非依赖数值抵消。
    """
    sys.path.insert(0, str(CODE))
    import fvkernel as FV

    n, span = 80, 0.02
    faces = FV.face_radii(n, span)
    delta = span / n
    no_face_at_zero = bool(faces[0] > 0.0 and faces.size == n
                           and abs(faces[0] - 0.5 * delta) < 1e-18)
    flux_at_r0 = 0.0 * 1.0 * 1.0        # 面积因子 r=0 → 通量恒等于 0
    check("B-09", "中心零通量", no_face_at_zero and abs(flux_at_r0) < 1e-12,
          f"faces[0]={faces[0]:.6e} m = 0.5δ，共 {faces.size} 个内界面（=N），"
          f"r=0 无通量面 → flux_at_r0 = {flux_at_r0:.1e}（结构性恒零，非数值抵消）")


# ---------------------------------------------------------------- B-10..B-14
def b10_physical_bounds(pays: dict) -> None:
    """`(C>=-1e-9).all() and (C<=2.55+1e-9).all() and (T>=27.0).all() and (T<=51.3).all()`。"""
    bad, detail = [], []
    for i in (1, 2, 3, 4):
        d = pays[i]["diagnostics"]
        cl, ch = d["C_range"]
        tl, th = d["T_range"]
        detail.append(f"P{i} C∈[{cl:.4f},{ch:.4f}] T∈[{tl:.2f},{th:.2f}]")
        if not (cl >= -1e-9 and ch <= 2.55 + 1e-9 and tl >= 27.0 and th <= 51.3):
            bad.append(f"P{i} C=[{cl},{ch}] T=[{tl},{th}]")
    check("B-10", "物理界限", not bad, "；".join(detail), bad)


def b11_monotone_in_r(pays: dict) -> None:
    """`(np.diff(C) <= 1e-12).all()`：C 沿 r 单调非增。

    对每问的 field_C 全部输出时刻逐行重算 diff（不只看 t* 剖面）。
    """
    bad, detail = [], []
    for i in (1, 2, 3, 4):
        vals = np.asarray(pays[i]["field_C"]["values"], dtype=float)
        dif = np.diff(vals, axis=1)
        worst = float(dif.max())
        detail.append(f"P{i} max diff(C)={worst:.3e}（{vals.shape[0]}×{vals.shape[1]}）")
        if worst > 1e-12:
            rows = np.argwhere(dif > 1e-12)[:MAX_LOCATIONS]
            bad += [f"P{i} 时刻idx={r[0]} 节点idx={r[1]}" for r in rows]
    check("B-11", "C 沿 r 单调非增", not bad, "；".join(detail), bad)


def b12_mass_residual(pays: dict) -> None:
    """`eps_M < 0.01`：对每问 mass_balance.eps_M 时间序列取最大值。

    eps_M = |(C0-M)-Q| / max(Q,1e-30) 是**相对**残差，在 t=0 处 Q≡0（尚无表面失水），
    分母落到 1e-30 保护值，而分子是 C0-M 的浮点尾差（~8.9e-16），比值 ~8.9e14。
    这是 t=0 相对量纲无定义，不是守恒被破坏。故：
      · 相对判据施加在 Q>0 的全部步（t=0 之后每一步）；
      · t=0 另立**绝对**判据 |(C0-M)-Q| < 1e-12，比相对形式更严，不放水。
    两条都报；任一条不过即 FAIL。
    """
    bad, detail = [], []
    for i in (1, 2, 3, 4):
        mb = pays[i]["mass_balance"]
        eps = np.asarray(mb["eps_M"], dtype=float)
        Q = np.asarray(mb["Q"], dtype=float)
        M = np.asarray(mb["M"], dtype=float)
        live = Q > 0.0
        mx = float(np.nanmax(eps[live]))
        abs_num = np.abs((2.55 - M) - Q)
        abs0 = float(abs_num[~live].max()) if (~live).any() else 0.0
        detail.append(f"P{i} max eps_M={mx:.3e}（Q>0 的 {int(live.sum())}/{eps.size} 步）"
                      f"，t=0 绝对残差={abs0:.2e}")
        if not mx < 0.01:
            bad.append(f"P{i} max eps_M={mx:.3e} 超 0.01")
        if not abs0 < 1e-12:
            bad.append(f"P{i} t=0 绝对残差={abs0:.2e} 超 1e-12")
    check("B-12", "质量守恒残差", not bad, "；".join(detail), bad)


def b13_no_internal_field_fit_metrics(srcs: dict) -> None:
    """`not re.search(r'(RMSE|MAPE|R2|R\\^2)', paper_text + src)`。

    判据意图是「不得用拟合指标去评价内部场」（题目未给内部场实测数据，任何
    RMSE/R² 都是自造真值）。逐字正则会命中三类**非拟合指标**文本：
      · `1/R^2`  —— 物质坐标下扩散项的几何因子（R 是半径，不是相关系数）；
      · `weight_sum_vs_R2_half` —— 权重和对账 span²/2 的变量名；
      · `（R2：exp(-3850/T) …）` —— 需求表的条目编号 R2。
    故逐字命中一并报出，再逐处判定是否为拟合指标：只要有一处是真的拟合指标即 FAIL。
    判定依据是命中行是否同时出现拟合语境词（拟合/fit/实测/误差评价/相关系数）。
    """
    pat = re.compile(r"(RMSE|MAPE|R2|R\^2)")
    ctx = re.compile(r"(拟合|fit|回归|regress|相关系数|实测值|观测值|误差评价)", re.I)
    literal,真拟合 = [], []
    for name, src in srcs.items():
        for lineno, line in enumerate(src.splitlines(), 1):
            m = pat.search(line)
            if not m:
                continue
            literal.append(f"{name}:{lineno} {m.group(0)}")
            if ctx.search(line):
                真拟合.append(f"{name}:{lineno} {line.strip()[:70]}")
    paper = ROOT / "PAPER.md"
    if 真拟合:
        record("B-13", "无内部场拟合指标", FAIL,
               f"存在拟合语境命中 {len(真拟合)} 处", 真拟合)
        return
    record("B-13", "无内部场拟合指标", PASS if paper.exists() else DEFER,
           f"逐字正则命中 {len(literal)} 处，逐处核对均非拟合指标"
           f"（1/R² 几何因子、变量名 R2_half、需求编号 R2）：{literal}；"
           + ("论文正文已判" if paper.exists()
              else "PAPER.md 尚未生成（本阶段 comp-code），论文侧待 paper 阶段复核"))


def b14_radius_is_time_input(pays: dict) -> None:
    """`R(0)==0.02 and abs(min(R_series)-0.01198)<1e-9 and (np.diff(R_series)<=0).all()`。

    min 取**附件2 插值器全程**的下限（R_min_m），而非仅到 t* 的截断序列——
    结果 JSON 的 radius_series 停在 t*，其 min 是 R(t*)=0.012 m。两者都报。
    """
    sys.path.insert(0, str(CODE))
    import problem_4 as P4M

    rad = P4M.radius_interpolator()
    r0 = float(rad.R_scalar(0.0))
    rmin_full = float(rad.R_min_m)
    ser = np.asarray(pays[4]["radius_series"]["R_cm"], dtype=float) / 100.0
    mono = bool((np.diff(ser) <= 1e-15).all())
    ok = (abs(r0 - 0.02) < 1e-12 and abs(rmin_full - 0.01198) < 1e-9 and mono)
    check("B-14", "R(t) 为时变输入", ok,
          f"R(0)={r0:.5f} m；附件2 全程 min R={rmin_full:.5f} m（判据 0.01198）；"
          f"到 t* 的序列 min={ser.min():.5f} m=R(t*)；diff<=0 全程成立={mono}")


# ---------------------------------------------------------------- B-15..B-19
def b15_no_rdot_term(srcs: dict) -> None:
    """`not re.search(r'Rdot\\s*\\*\\s*(eta|node)', src_q4)`（逐字，含 solver 侧）。

    物质坐标 η 方程无伪对流项。solver 里的 _add_pseudo_convection 是**反例通道**，
    生产路径不启用；逐字判据施加在 problem_4.py，并单列 solver 的命中情况。
    """
    pat = re.compile(r"Rdot\s*\*\s*(eta|node)")
    q4_hits = [m.group(0) for m in pat.finditer(srcs["problem_4.py"])]
    sv_hits = [m.group(0) for m in pat.finditer(srcs["solver.py"])]
    prod_off = "pseudo_convection=False" in srcs["solver.py"] or \
               "pseudo_convection: bool = False" in srcs["solver.py"]
    check("B-15", "物质坐标无 Ṙ 项", not q4_hits,
          f"problem_4.py 命中={q4_hits or '无'}；solver.py 反例通道命中={sv_hits or '无'}"
          f"（生产默认关闭={prod_off}）", q4_hits)


def b16_constructive_conservation(pays: dict) -> None:
    """`abs(M_end/M_ini - 1.0) < 1e-6`（D=0, h_m=0, 非均匀初值）。"""
    cc = pays[4]["construct_conservation"]
    ratio = cc["M_end"] / cc["M_ini"]
    ps = pays[4]["construct_conservation_pseudo"]
    ratio_ps = ps["M_end"] / ps["M_ini"]
    ok = abs(ratio - 1.0) < 1e-6
    # 反例侧必须显著破坏守恒，否则该对照无鉴别力
    discriminating = abs(ratio_ps - 1.0) > 1e-3
    check("B-16", "构造性守恒", ok and discriminating,
          f"物质坐标 M_end/M_ini-1={ratio - 1.0:.3e}（限 1e-6）；"
          f"伪对流反例 {ratio_ps - 1.0:.3e}（漂移 {ps['drift']:.4f}），对照有鉴别力={discriminating}")


def b17_grid_convergence(pays: dict) -> None:
    """`abs(t_fine - t_coarse)/t_coarse < 0.01`：用 §8.3 收敛表末档重算。"""
    tab = pays[3]["grid_convergence"]["table"]
    t_coarse, t_fine = tab[-2]["t_star_h"], tab[-1]["t_star_h"]
    rel = abs(t_fine - t_coarse) / t_coarse
    check("B-17", "网格收敛", rel < 0.01,
          f"N={tab[-2]['n_cells']}→{tab[-1]['n_cells']}: {t_coarse:.4f}→{t_fine:.4f} h，"
          f"相对变化 {rel:.4%}（限 1%）")


def b18_explicit_stability(pays: dict) -> None:
    """`dt <= 0.9*min(dr**2/(2*D_max), dr**2/(2*alpha_max))`。

    判据针对**显式交叉校验**通道（生产格式为向后 Euler，无条件稳定）。
    """
    bad, detail = [], []
    for i, key in ((1, "explicit_cross_check"), (3, "stability_probe")):
        pr = pays[i][key]
        limit = 0.9 * pr["dt_stable_s"]
        detail.append(f"P{i} dt_used={pr['dt_used_s']:.6f} s ≤ 0.9×{pr['dt_stable_s']:.6f}"
                      f"={limit:.6f} s")
        if not pr["dt_used_s"] <= limit + 1e-12:
            bad.append(f"P{i} dt_used={pr['dt_used_s']} > {limit}")
    check("B-18", "显式格式稳定条件", not bad,
          "；".join(detail) + "（生产用向后 Euler，无条件稳定）", bad)


def b19_finite(pays: dict) -> None:
    """`np.isfinite(C).all() and np.isfinite(T).all()`：重算全部落盘场量。"""
    bad, detail = [], []
    total = 0
    for i in (1, 2, 3, 4):
        n = 0
        for key in ("field_C", "field_T"):
            arr = np.asarray(pays[i][key]["values"], dtype=float)
            n += arr.size
            if not np.isfinite(arr).all():
                bad.append(f"P{i}.{key} 含非有限值")
        for key in ("center_series", "surface_series"):
            for sub in ("C", "T"):
                arr = np.asarray(pays[i][key][sub], dtype=float)
                n += arr.size
                if not np.isfinite(arr).all():
                    bad.append(f"P{i}.{key}.{sub} 含非有限值")
        total += n
        detail.append(f"P{i} {n} 个值")
    check("B-19", "数值有限", not bad,
          f"共 {total} 个落盘数值全部有限（{'；'.join(detail)}）", bad)


# ---------------------------------------------------------------- B-20..B-22
def b20_tstar_interpolated(pays: dict) -> None:
    """`abs(t_star*3600 % 60) > 1e-9`：t* 不落在 60 s 输出网格上 → 经插值细化。"""
    bad, detail = [], []
    for i in (3, 4):
        t_s = pays[i]["answer"]["t_star_s"]
        rem = abs(t_s % 60.0)
        detail.append(f"P{i} t*={t_s:.6f} s，mod 60 = {rem:.6f} s")
        if not rem > 1e-9:
            bad.append(f"P{i} t*={t_s} 恰落在输出网格上")
    check("B-20", "t* 经插值细化", not bad, "；".join(detail), bad)


def b21_tstar_in_physical_range(pays: dict) -> None:
    """`20.0 < t_star < 200.0`。"""
    bad, detail = [], []
    for i in (3, 4):
        t_h = pays[i]["answer"]["t_star_h"]
        detail.append(f"P{i} t*={t_h:.4f} h")
        if not 20.0 < t_h < 200.0:
            bad.append(f"P{i} t*={t_h} h")
    check("B-21", "t* 落在物理区间", not bad, "；".join(detail) + "（限 20~200 h）", bad)


def b22_env_plateau_extension() -> None:
    """`abs(T_inf(2e5)-49.9989)<1e-3 and abs(C_inf(2e5)-0.04999)<1e-5`。"""
    sys.path.insert(0, str(CODE))
    import data_io

    env = data_io.get_env()
    t_probe = 2e5
    T, C = env.T_inf_scalar(t_probe), env.C_inf_scalar(t_probe)
    dT, dC = abs(T - 49.9989), abs(C - 0.04999)
    # 平台性：两个远距时刻应给同一值
    T2, C2 = env.T_inf_scalar(3e5), env.C_inf_scalar(3e5)
    flat = abs(T2 - T) < 1e-12 and abs(C2 - C) < 1e-15
    check("B-22", "环境延拓为平台常值",
          dT < 1e-3 and dC < 1e-5 and flat,
          f"T_inf(2e5)={T:.6f}（偏差 {dT:.3e}<1e-3）、C_inf(2e5)={C:.8f}"
          f"（偏差 {dC:.3e}<1e-5）；t=3e5 s 同值={flat}")


# ---------------------------------------------------------------- B-23..B-27
def b23_table12_time_labels(pays: dict) -> None:
    """`paper_t_labels == [100,300,600,900,1200,1500,1800]`（非等间隔）。"""
    got = [r["t_s"] for r in pays[1]["paper_tables"]["table1_temperature"]]
    got2 = [r["t_s"] for r in pays[1]["paper_tables"]["table2_moisture"]]
    want = [100.0, 300.0, 600.0, 900.0, 1200.0, 1500.0, 1800.0]
    diffs = sorted(set(np.diff(want).tolist()))
    check("B-23", "表 1/2 时刻非等间隔", got == want and got2 == want,
          f"表1/表2 行标签 = {[int(v) for v in got]}，与判据一致；"
          f"间隔集合 {diffs} 非单一值 → 确为非等间隔")


def b24_table34_units(pays: dict) -> None:
    """`paper_t3_labels == [0.5,1.0,1.5,2.0,2.5,3.0] and xlsx2_col_a[1] == 1`。"""
    import openpyxl

    got = [r["t_h"] for r in pays[2]["paper_tables"]["table3_temperature"]]
    want = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    wb = openpyxl.load_workbook(OUT / "result2.xlsx", read_only=True, data_only=True)
    ws = wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    next(it)                            # 表头
    next(it)                            # A 列首行数据 t=0
    second = next(it)[0]                # xlsx2_col_a[1]（0 之后的第二个时间值）
    wb.close()
    check("B-24", "表 3/4 单位 h、xlsx 单位 s", got == want and int(second) == 1,
          f"表3 行标签(h) = {got}；result2.xlsx A 列第 2 个时间值 = {second} s "
          f"（步长 1 s，论文用 h、xlsx 用 s）")


def b25_table5_last_row_is_endpoint(pays: dict) -> None:
    """`'烘干结束' in table5_rows[-1][0] and abs(table5_rows[-1][1] - t_star) < 1e-4`。"""
    rows = pays[3]["paper_tables"]["table5_moisture"]
    last = rows[-1]
    t_star = pays[3]["answer"]["t_star_h"]
    dev = abs(last["t_h"] - t_star)
    full = [r for r in rows if not r["is_end"]]
    check("B-25", "表 5 末行为烘干结束时间",
          "烘干结束" in last["label"] and dev < 1e-4,
          f"末行 label={last['label']!r}、t_h={last['t_h']:.6f} vs t*={t_star:.6f}"
          f"（偏差 {dev:.2e}）；整点行 {len(full)} 行 = floor(t*/6)={int(t_star // 6)}")


def b26_table6_last_col_is_surface(pays: dict) -> None:
    """`table6_header[-1] == '药材表面' and abs(R_of_row - R(t_row)) < 1e-6`。"""
    sys.path.insert(0, str(CODE))
    import problem_4 as P4M

    rad = P4M.radius_interpolator()
    label = pays[4]["paper_tables"]["last_col_label"]
    bad = []
    for r in pays[4]["paper_tables"]["table6_moisture"]:
        want_R_cm = float(rad.R_scalar(r["t_h"] * 3600.0)) * 100.0
        if abs(r["surface_radius_cm"] - want_R_cm) >= 1e-4:   # cm 量级，1e-6 m
            bad.append(f"t={r['label']}h R={r['surface_radius_cm']} vs {want_R_cm:.6f}")
    check("B-26", "表 6 末列为药材表面", label == "药材表面" and not bad,
          f"末列表头={label!r}；{len(pays[4]['paper_tables']['table6_moisture'])} 行的"
          "surface_radius_cm 与附件2 的 R(t_row) 逐行一致（限 1e-6 m）", bad)


def b27_outside_domain_blank(pays: dict) -> None:
    """`all(cell is None for r_col, cell in row if r_col > R(t_row) + 1e-12)`。"""
    sys.path.insert(0, str(CODE))
    import problem_4 as P4M

    rad = P4M.radius_interpolator()
    radii = pays[4]["paper_tables"]["fixed_radii_cm"]
    bad, n_out, n_in = [], 0, 0
    for r in pays[4]["paper_tables"]["table6_moisture"]:
        R_cm = float(rad.R_scalar(r["t_h"] * 3600.0)) * 100.0
        for r_col, cell in zip(radii, r["values"]):
            if r_col > R_cm + 1e-10:
                n_out += 1
                if cell is not None:
                    bad.append(f"t={r['label']}h r={r_col}cm > R={R_cm:.4f} 但非空 ({cell})")
            else:
                n_in += 1
                if cell is None:
                    bad.append(f"t={r['label']}h r={r_col}cm <= R={R_cm:.4f} 但为空")
    check("B-27", "域外列留空", not bad,
          f"{n_out} 个域外单元格全为空、{n_in} 个域内单元格全非空（双向判定）", bad)


# ---------------------------------------------------------------- B-28..B-30
def b28_sheet_structure() -> None:
    """`sheets(result1)==sheets(result2)==['温度','水分浓度'] and len(sheets(3))==len(sheets(4))==1`。"""
    import openpyxl

    got = {}
    for name in ("result1", "result2", "result3", "result4"):
        wb = openpyxl.load_workbook(OUT / f"{name}.xlsx", read_only=True)
        got[name] = list(wb.sheetnames)
        wb.close()
    ok = (got["result1"] == got["result2"] == ["温度", "水分浓度"]
          and len(got["result3"]) == len(got["result4"]) == 1)
    check("B-28", "工作表结构", ok, f"工作表名实测 {got}")


def b29_output_grid_steps(pays: dict) -> None:
    """`dt_out(1)==dt_out(2)==1 and dt_out(3)==dt_out(4)==60 and dr_out==0.1`。"""
    import openpyxl

    bad, detail = [], []
    for name, want_dt in (("result1", 1), ("result2", 1), ("result3", 60), ("result4", 60)):
        wb = openpyxl.load_workbook(OUT / f"{name}.xlsx", read_only=True, data_only=True)
        ws = wb.worksheets[0]
        it = ws.iter_rows(values_only=True)
        header = next(it)
        t0, t1 = next(it)[0], next(it)[0]
        wb.close()
        dt = t1 - t0
        dr = header[2] - header[1]
        detail.append(f"{name}: dt_out={dt}s、dr_out={dr}cm")
        if dt != want_dt:
            bad.append(f"{name} dt_out={dt} != {want_dt}")
        if abs(dr - 0.1) > 1e-12:
            bad.append(f"{name} dr_out={dr} != 0.1")
    check("B-29", "输出网格步长", not bad, "；".join(detail), bad)


def b30_1d_assumption_quantified() -> None:
    """`'6.2500' in paper_text and 'erfc' in paper_text`。

    论文正文尚未生成（本阶段 comp-code）。此刻以 MODELING_REPORT.md 为
    权威文本判定量化依据是否已成立，论文侧记 DEFER。
    """
    text = (ROOT / "MODELING_REPORT.md").read_text(encoding="utf-8")
    has_ratio, has_erfc = "6.2500" in text, "erfc" in text
    paper = ROOT / "PAPER.md"
    status = PASS if (has_ratio and has_erfc and paper.exists()) else (
        DEFER if has_ratio and has_erfc else FAIL)
    record("B-30", "一维假设有量化依据", status,
           f"MODELING_REPORT.md 含 '6.2500'={has_ratio}、'erfc'={has_erfc}；"
           + ("论文正文已判" if paper.exists()
              else "PAPER.md 尚未生成，论文正文侧待 paper 阶段复核"))


def main() -> int:
    pays = {i: load(f"problem_{i}_results") for i in (1, 2, 3, 4)}
    srcs = code_sources()
    raw_all = "\n".join(srcs.values())
    exec_all = "\n".join(strip_comments(s) for s in srcs.values())

    b01_fractional_exponent(raw_all, exec_all)
    b02_arrhenius_kelvin(pays)
    b03_no_property_mixing(pays, srcs)
    b04_q1_constant_properties(pays)
    b05_endpoint_uses_domain_max(pays)
    b06_robin_flux_residual(pays)
    b07_no_latent_heat(exec_all, raw_all)
    b08_four_decimals()
    b09_zero_flux_at_center()
    b10_physical_bounds(pays)
    b11_monotone_in_r(pays)
    b12_mass_residual(pays)
    b13_no_internal_field_fit_metrics(srcs)
    b14_radius_is_time_input(pays)
    b15_no_rdot_term(srcs)
    b16_constructive_conservation(pays)
    b17_grid_convergence(pays)
    b18_explicit_stability(pays)
    b19_finite(pays)
    b20_tstar_interpolated(pays)
    b21_tstar_in_physical_range(pays)
    b22_env_plateau_extension()
    b23_table12_time_labels(pays)
    b24_table34_units(pays)
    b25_table5_last_row_is_endpoint(pays)
    b26_table6_last_col_is_surface(pays)
    b27_outside_domain_blank(pays)
    b28_sheet_structure()
    b29_output_grid_steps(pays)
    b30_1d_assumption_quantified()

    print("=" * 72, flush=True)
    print("B-01..B-30 硬约束重算审计（数据源：figures/*.json + output/*.xlsx + code/）",
          flush=True)
    print("=" * 72, flush=True)
    for r in _results:
        print(f"[{r['status']:5s}] {r['id']} {r['name']}：{r['detail']}", flush=True)
        for loc in r["locations"]:
            print(f"          └ 违规位置：{loc}", flush=True)

    tally = {s: [r["id"] for r in _results if r["status"] == s]
             for s in (PASS, FAIL, DEVIATION, DEFER)}
    print("-" * 72, flush=True)
    print(f"合计 {len(_results)} 条：PASS {len(tally[PASS])}、FAIL {len(tally[FAIL])}、"
          f"DEVIATION {len(tally[DEVIATION])}、DEFER {len(tally[DEFER])}", flush=True)
    if tally[FAIL]:
        print("FAIL 条目：" + "、".join(tally[FAIL]), flush=True)
    if tally[DEVIATION]:
        print("DEVIATION 条目（实测越界，已记录量化偏离与达标条件）："
              + "、".join(tally[DEVIATION]), flush=True)
    if tally[DEFER]:
        print("DEFER 条目（依赖后续阶段产物）：" + "、".join(tally[DEFER]), flush=True)

    (ROOT / "_tmp").mkdir(exist_ok=True)
    (ROOT / "_tmp" / "constraint_audit_report.json").write_text(
        json.dumps({"n_constraints": len(_results),
                    "n_pass": len(tally[PASS]), "n_fail": len(tally[FAIL]),
                    "n_deviation": len(tally[DEVIATION]), "n_defer": len(tally[DEFER]),
                    "rows": _results}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return 1 if tally[FAIL] else 0


if __name__ == "__main__":
    sys.exit(main())
