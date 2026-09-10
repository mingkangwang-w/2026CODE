# -*- coding: utf-8 -*-
"""
一键生成本目录下的全部新增插图。

用法（在本目录下）：
    py run_all.py            # 生成全部
    py run_all.py A B        # 只生成图A、图B
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

SCRIPTS = [
    ('A', 'figA_biot.py', '毕渥数演化'),
    ('B', 'figB_mass_balance.py', '质量守恒校验'),
    ('C', 'figC_p1_vs_p2.py', '常物性 vs 变物性'),
    ('D', 'figD_drying_curve.py', '特性干燥曲线'),
    ('E', 'figE_moving_boundary.py', '收缩域时空云图'),
    ('F', 'figF_drying_front.py', '干燥前沿推进'),
]


def main():
    want = [a.upper() for a in sys.argv[1:]]
    todo = [s for s in SCRIPTS if not want or s[0] in want]
    if not todo:
        print('没有匹配的图，可选:', ' '.join(s[0] for s in SCRIPTS))
        return 1

    ok, fail = [], []
    for key, script, desc in todo:
        print(f'\n{"="*58}\n图{key}  {desc}  ({script})\n{"="*58}')
        t0 = time.time()
        p = subprocess.run([sys.executable, os.path.join(HERE, script)],
                           cwd=HERE)
        if p.returncode == 0:
            print(f'  完成，用时 {time.time()-t0:.1f} s')
            ok.append(key)
        else:
            print(f'  失败（返回码 {p.returncode}）')
            fail.append(key)

    print(f'\n{"="*58}')
    print('成功:', ' '.join(ok) if ok else '无')
    if fail:
        print('失败:', ' '.join(fail))
    print('输出目录:', HERE)
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
