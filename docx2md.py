# -*- coding: utf-8 -*-
"""把 论文.docx 复刻成 Markdown：正文、公式、表格全部保留，图片略去。

公式是 Word 的 OMML（Office Math Markup Language）对象，python-docx 的
paragraph.text 取不到，故需要一个 OMML → LaTeX 的转换器。文里用到的元素只有
sSub / sSup / sSubSup / f / d / nary / eqArr / groupChr / scr 九种，逐一处理即可。

公式尾部的 `#(11)` 是 Word 的编号分隔符，转成 LaTeX 的 \\tag{11}。

输出：论文.md
"""
import os
import re

import docx
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '论文.docx')
DST = os.path.join(HERE, '论文.md')

M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'

# 属性类元素：只影响排版，不产出内容，但 dPr / naryPr / scrPr / groupChrPr 里
# 带着分隔符、n 元运算符、花体字型等配置，由各自的父元素读取，这里一律跳过
SKIP = {
    'rPr', 'ctrlPr', 'argPr', 'sSubPr', 'sSupPr', 'sSubSupPr', 'fPr', 'dPr',
    'naryPr', 'eqArrPr', 'oMathParaPr', 'scrPr', 'groupChrPr', 'limLowPr',
    'limUppPr', 'radPr', 'boxPr', 'barPr', 'accPr', 'funcPr', 'mPr',
}

FUNC_MAP = {'∫': '\\int', '∑': '\\sum', '∏': '\\prod', '∮': '\\oint'}
SCR_MAP = {'script': '\\mathcal', 'fraktur': '\\mathfrak',
           'double-struck': '\\mathbb', 'roman': '\\mathrm'}


def name(el):
    return el.tag.split('}')[-1] if isinstance(el.tag, str) and '}' in el.tag else el.tag


def txt(el):
    return ''.join(t.text or '' for t in el.iter() if name(t) == 't')


def child(el, tag):
    for c in el:
        if name(c) == tag:
            return c
    return None


ABSENT = object()


def prop(el, tag, default=None):
    """从 xPr 里取某个属性值，如 dPr/begChr、scrPr/val。

    必须区分「属性不存在」与「属性存在但值为空串」：OMML 用 begChr="" /
    endChr="" 表示这一侧不画分隔符，若把空串当缺省处理会凭空多出一对括号。
    """
    pr = next((c for c in el if name(c) == tag), None)
    if pr is None:
        return default
    for c in pr:
        if name(c) in ('chr', 'val'):
            v = c.get(M + 'val')
            if v is None:
                v = c.get(qn('w:val'))
            if v is not None:
                return v
    return default


FUNCS = ('inf', 'max', 'min', 'sup', 'exp', 'ln', 'log', 'sin', 'cos', 'tan')
FUNC_RE = re.compile(r'(?<![\\A-Za-z])(' + '|'.join(FUNCS) + r')(?![A-Za-z])')


def fix_funcs(s):
    """把 inf / max 这类函数名转成正体命令；否则会被排成斜体变量。"""
    s = FUNC_RE.sub(r'\\\1 ', s)
    # U+2061 是 Word 的「函数应用」不可见标记，U+200B 是零宽空格，都不该出现在正文里
    return s.replace('⁡', '').replace('', '')


def conv(el):
    """OMML 元素 → LaTeX 片段。"""
    n = name(el)
    if n in SKIP:
        return ''
    if n == 't':
        return el.text or ''
    if n in ('oMath', 'r', 'e', 'num', 'den', 'sub', 'sup', 'box', 'limLow', 'limUpp'):
        return ''.join(conv(c) for c in el)
    if n == 'oMathPara':
        return ''.join(conv(c) for c in el)

    if n == 'sSub':
        return conv(child(el, 'e')) + '_{' + conv(child(el, 'sub')) + '}'
    if n == 'sSup':
        return conv(child(el, 'e')) + '^{' + conv(child(el, 'sup')) + '}'
    if n == 'sSubSup':
        return (conv(child(el, 'e')) + '_{' + conv(child(el, 'sub'))
                + '}^{' + conv(child(el, 'sup')) + '}')
    if n == 'f':
        return '\\frac{' + conv(child(el, 'num')) + '}{' + conv(child(el, 'den')) + '}'
    if n == 'd':
        b = prop(el, 'dPr', '(')          # 缺省圆括号（OMML 规定）
        e = prop(el, 'dPr', ')')
        if e == '':                        # endChr="" ：这一侧不画
            e = '.'
        b = {'{': '\\{', '}': '\\}'}.get(b, b)
        e = {'{': '\\{', '}': '\\}'}.get(e, e)
        body = ''.join(conv(c) for c in el if name(c) == 'e')
        return '\\left' + b + body + '\\right' + e
    if n == 'nary':
        ch = prop(el, 'naryPr', '∫') or '∫'
        op = FUNC_MAP.get(ch, ch)
        lo = conv(child(el, 'sub'))
        up = conv(child(el, 'sup'))
        lim = ('_' + lo if lo else '') + ('^' + up if up else '')
        return op + lim + ' ' + conv(child(el, 'e'))
    if n == 'eqArr':
        rows = [conv(c) for c in el if name(c) == 'e']
        body = ' \\\\ '.join(r for r in rows if r.strip())
        return body if len(rows) == 1 else '\\begin{aligned}' + body + '\\end{aligned}'
    if n == 'groupChr':
        pos = prop(el, 'groupChrPr', 'bot') or 'bot'
        cmd = '\\underbrace' if pos == 'bot' else '\\overbrace'
        return cmd + '{' + conv(child(el, 'e')) + '}'
    if n == 'scr':
        val = prop(el, 'scrPr', 'script') or 'script'
        cmd = SCR_MAP.get(val, '\\mathcal')
        return cmd + '{' + conv(child(el, 'e')) + '}'
    if n == 'rad':
        deg = conv(child(el, 'deg')).strip()
        hide = any(name(c) == 'degHide' for c in el)
        pre = '' if (hide or not deg) else '[' + deg + ']'
        return '\\sqrt' + pre + '{' + conv(child(el, 'e')) + '}'
    if n == 'bar':
        return '\\overline{' + conv(child(el, 'e')) + '}'
    if n == 'acc':
        return '\\hat{' + conv(child(el, 'e')) + '}'

    # 其余容器一律递归
    return ''.join(conv(c) for c in el)


def eq_split(latex):
    """把 Word 的编号分隔符 #(11) 转成 \\tag{11}。

    编号可能落在 \\begin{aligned}...\\end{aligned} 内部，故不能锚定行尾。
    """
    m = re.search(r'#\s*\((\d+)\)', latex)
    if not m:
        return latex, None
    return (latex[:m.start()] + latex[m.end():]).rstrip(), m.group(1)


def para_md(p):
    """一个段落 → Markdown 片段。

    注意不能直接用 p._p.iter()：display 公式是 oMathPara 包着 oMath，
    平铺遍历会把同一条公式数两遍。改为递归下降，遇到 oMathPara / oMath
    就地处理并停止下探。
    """
    parts = []

    def walk(el):
        n = name(el)
        if n == 'oMathPara':
            body, tag = eq_split(fix_funcs(conv(el)))
            tagstr = (' \\tag{%s}' % tag) if tag else ''
            parts.append('\n$$\n' + body.strip() + tagstr + '\n$$\n')
            return
        if n == 'oMath':
            parts.append('$' + fix_funcs(conv(el)).strip() + '$')
            return
        if n == 't' and el.text:
            parts.append(el.text)
            return
        if n in ('drawing', 'pict'):
            return                     # 图片略去，不再下探
        for c in el:
            walk(c)

    for c in p._p:
        walk(c)
    return ''.join(parts).strip()


def heading_level(p, text):
    st = p.style.name or ''
    if 'Heading 1' in st:
        return 1
    if 'Heading 2' in st:
        return 2
    if 'Heading 3' in st:
        return 3
    if re.match(r'^[一二三四五六七八九十]+、', text):
        return 1
    if re.match(r'^\d+\.\d+\.\d+', text):
        return 3
    if re.match(r'^\d+\.\d+[^\d]', text):
        return 2
    if re.match(r'^(参考文献|摘要|关键词|AI 工具使用声明|模型验证与灵敏度分析|'
                r'模型的评价与推广)$', text):
        return 1
    return 0


def cell_text(cell):
    """表格单元格的文本，含公式。cell.text 取不到 OMML，必须逐段走 para_md。"""
    parts = []
    for p in cell.paragraphs:
        t = para_md(p)
        t = t.replace('$$', '$')           # 单元格里一律用行内公式
        if t:
            parts.append(t)
    return re.sub(r'\s+', ' ', ' '.join(parts)).strip().replace('|', '\\|')


def table_md(tbl):
    rows = []
    for r in tbl.rows:
        cells = []
        seen = set()
        for c in r.cells:
            key = id(c._tc)                # 合并单元格会重复返回，去重
            cells.append(cell_text(c) if key not in seen else '')
            seen.add(key)
        rows.append(cells)
    if not rows:
        return ''
    w = max(len(r) for r in rows)
    rows = [r + [''] * (w - len(r)) for r in rows]
    out = ['| ' + ' | '.join(rows[0]) + ' |',
           '|' + '|'.join(['---'] * w) + '|']
    for r in rows[1:]:
        out.append('| ' + ' | '.join(r) + ' |')
    return '\n'.join(out)


def main():
    doc = docx.Document(SRC)
    body = doc.element.body
    out = []
    n_img = 0
    n_tbl = 0

    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            p = Paragraph(child, doc)
            if child.findall('.//' + qn('w:drawing')) or child.findall('.//' + qn('w:pict')):
                n_img += 1
                continue                       # 纯图片段落整段略去
            text = para_md(p)
            if not text:
                continue
            lvl = heading_level(p, text)
            if lvl:
                out.append('#' * lvl + ' ' + text)
            else:
                out.append(text)
            out.append('')
        elif child.tag == qn('w:tbl'):
            n_tbl += 1
            out.append(table_md(Table(child, doc)))
            out.append('')

    md = re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip() + '\n'
    with open(DST, 'w', encoding='utf-8') as f:
        f.write(md)
    print('saved: %s' % DST)
    print('  段落输出 %d 行，表格 %d 张，略去图片段落 %d 处' % (md.count('\n'), n_tbl, n_img))


if __name__ == '__main__':
    main()
