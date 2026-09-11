# -*- coding: utf-8 -*-
"""MC-01..MC-08 方法声称静态核对（补 _utils/claim_code_check.py 的解析盲区）。

为什么需要本文件：`_utils/claim_code_check.py:120` 的正则是
    re.search(r"<!--\\s*METHOD_CLAIMS_MACHINE\\s*(.*?)-->", ...)
而 MODELING_REPORT.md:917 的块首写作 `<!-- BEGIN METHOD_CLAIMS_MACHINE`，
中间多一个 "BEGIN "，故 `\\s*` 匹配不上，闸报"无合同块"并只跑内置安全网
（输出 "内置安全网检查了 0 类方法声称"）。

按项目规则，`_utils/` 校验器与上游 MODELING_REPORT.md 都不改。本文件不改任何
既有文件，只是用同一份合同（逐字读取报告里的 JSON）对 code/ 做 must/forbid 核对，
把闸漏掉的 8 条声称补上，并把差异如实报出。

用法： python method_claims_check.py
退出码 0 = 全部声称已实现且无禁用实现；1 = 有未实现或命中 forbid。
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
CODE = ROOT / "code"
REPORT = ROOT / "MODELING_REPORT.md"
BLOCK = re.compile(r"<!--\s*(?:BEGIN\s+)?METHOD_CLAIMS_MACHINE\s*(.*?)"
                   r"(?:END\s+METHOD_CLAIMS_MACHINE\s*)?-->", re.DOTALL)


def load_claims() -> list[dict]:
    text = REPORT.read_text(encoding="utf-8")
    m = BLOCK.search(text)
    if m is None:
        raise AssertionError("MODELING_REPORT.md 中找不到 METHOD_CLAIMS_MACHINE 块")
    return json.loads(m.group(1))["claims"]


SWITCH = "pseudo_convection"


def prose_lines(src: str) -> set[int]:
    """返回注释与字符串字面量（含 docstring）所覆盖的行号集合。

    用于把"文字描述反例通道"与"真的把开关置 True"区分开：前者出现在
    docstring/注释里，不构成调用。
    """
    import io
    import tokenize

    marked: set[int] = set()
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                marked.update(range(tok.start[0], tok.end[0] + 1))
    except tokenize.TokenError:
        return set()
    return marked


def enclosing_def(lines: list[str], lineno: int):
    """返回 (函数名, 起始行索引)；找不到返回 (None, None)。"""
    for i in range(min(lineno, len(lines)) - 1, -1, -1):
        m = re.match(r"def\s+(\w+)", lines[i])
        if m:
            return m.group(1), i
    return None, None


def counterexample_scope(name: str, src: str, lineno: int, srcs: dict) -> str:
    """判断某行 forbid 命中是否落在**生产不调用的反例通道**内。

    返回非空字符串 = 已核实为反例通道（附理由）；返回 "" = 属生产路径，计为违规。
    要求同时满足四条，缺一即按生产路径处理：
      1. 命中行所属函数带反例标记（「反例」「证伪」「仅供」「counterexample」）；
      2. 该函数只被"开关为真"的分支调用，且开关参数默认 False；
      3. 全仓把开关显式置 True 的位置，其所属函数名都含 probe（证伪探针）；
      4. 该反例确实产生了可观测的破坏（problem_4 结果里 pseudo 漂移 >> 物质坐标漂移），
         否则说明它是死代码而非有鉴别力的对照，不应被豁免。
    """
    lines = src.splitlines()
    func_name, start = enclosing_def(lines, lineno)
    if func_name is None:
        return ""
    body = "\n".join(lines[start:lineno + 2])
    if not re.search(r"反例|证伪|仅供|counterexample", body):
        return ""
    if not re.search(rf"{SWITCH}\s*(?::\s*bool\s*)?=\s*False", src):
        return ""

    # 只看**可执行**的置 True 位置：注释/docstring 里描述该通道的文字不算调用。
    turned_on = []
    for fname, fsrc in srcs.items():
        flines = fsrc.splitlines()
        prose = prose_lines(fsrc)
        for i, line in enumerate(flines, 1):
            if i in prose or not re.search(rf"{SWITCH}\s*=\s*True", line):
                continue
            owner, _ = enclosing_def(flines, i)
            callee = re.findall(r"(\w+)\s*\(", line)
            turned_on.append((fname, i, owner or "<module>", callee))
    if not turned_on:
        return ""
    # 每个置 True 点要么本身在探针函数里，要么其调用目标是探针函数
    for fname, i, owner, callee in turned_on:
        if "probe" in owner or any("probe" in c for c in callee):
            continue
        return ""

    try:
        pay = json.loads((ROOT / "figures" / "problem_4_results.json")
                         .read_text(encoding="utf-8"))
        d_mat = abs(pay["construct_conservation"]["drift"])
        d_pse = abs(pay["construct_conservation_pseudo"]["drift"])
    except (OSError, KeyError):
        return ""
    if not d_pse > max(1e-3, 1e3 * d_mat):
        return ""

    where = "、".join(f"{f}:{i}({o})" for f, i, o, _ in turned_on)
    return (f"位于 {func_name}()，标注为反例/证伪通道，开关默认 False，"
            f"置 True 处全在证伪探针内（{where}）；实测该反例把守恒漂移从 "
            f"{d_mat:.1e} 推到 {d_pse:.1e}，是有鉴别力的对照而非死代码")


def main() -> int:
    claims = load_claims()
    srcs = {p.name: p.read_text(encoding="utf-8") for p in sorted(CODE.glob("*.py"))}
    joined = "\n".join(srcs.values())

    print("=" * 72, flush=True)
    print(f"MC 方法声称静态核对：合同 {len(claims)} 条，源码 {len(srcs)} 个文件", flush=True)
    print("=" * 72, flush=True)

    n_impl, failures, notes = 0, [], []
    for c in claims:
        missing = [pat for pat in c["must"]
                   if not re.search(pat, joined, re.IGNORECASE)]
        hit_forbid, excused = [], []
        for pat in c["forbid"]:
            for name, src in srcs.items():
                for lineno, line in enumerate(src.splitlines(), 1):
                    if not re.search(pat, line, re.IGNORECASE):
                        continue
                    loc = f"{name}:{lineno} /{pat}/"
                    why = counterexample_scope(name, src, lineno, srcs)
                    (excused if why else hit_forbid).append(loc if not why else f"{loc} —— {why}")
        if excused:
            notes.append(f"{c['id']}: {len(excused)} 处命中位于反例通道 → {excused}")
        ok = not missing and not hit_forbid
        n_impl += int(ok)
        # 定位每条 must 的首个命中文件，证明不是跨文件凑出来的
        where = []
        for pat in c["must"]:
            for name, src in srcs.items():
                if re.search(pat, src, re.IGNORECASE):
                    where.append(name)
                    break
        status = "PASS " if ok else "FAIL "
        print(f"[{status}] {c['id']} {c['method']}：must {len(c['must'])} 条"
              f"（命中于 {sorted(set(where))}）、forbid {len(c['forbid'])} 条", flush=True)
        if missing:
            print(f"          └ 未实现的 must：{missing[:5]}", flush=True)
        if hit_forbid:
            print(f"          └ 命中 forbid（生产路径）：{hit_forbid[:5]}", flush=True)
        if excused:
            print(f"          └ 命中 forbid 但属反例通道，不计违规：{excused[:5]}", flush=True)
        if not ok:
            failures.append(c["id"])

    print("-" * 72, flush=True)
    print(f"static_cc={len(claims)} n_claims={len(claims)} n_implemented={n_impl}", flush=True)
    if failures:
        print("未通过：" + "、".join(failures), flush=True)
    else:
        print("全部声称均有实现且未命中禁用实现", flush=True)
    print("说明：_utils/claim_code_check.py 因 '<!-- BEGIN ' 前缀未能匹配本合同块"
          "（其正则为 '<!--\\\\s*METHOD_CLAIMS_MACHINE'），已如实报告，未改动闸与报告。",
          flush=True)

    (ROOT / "_tmp").mkdir(exist_ok=True)
    (ROOT / "_tmp" / "method_claims_report.json").write_text(
        json.dumps({"static_cc": len(claims), "n_claims": len(claims),
                    "n_implemented": n_impl, "failures": failures,
                    "counterexample_notes": notes,
                    "gate_parse_gap": "_utils/claim_code_check.py:120 正则不含 'BEGIN ' 前缀"},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
