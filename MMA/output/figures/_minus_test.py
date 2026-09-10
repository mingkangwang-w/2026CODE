# -*- coding: utf-8 -*-
"""负号(U+2212)字形渲染测试：比较不同 mathtext 字体配置。"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CONFIGS = {
    'cm': dict(fontset='cm'),
    'custom_dejavu': dict(fontset='custom', rm='DejaVu Sans',
                          it='DejaVu Sans:italic', bf='DejaVu Sans:bold'),
    'stix': dict(fontset='stix'),
}

fig, axes = plt.subplots(1, len(CONFIGS), figsize=(11, 2.8))
for ax, (name, cfg) in zip(axes, CONFIGS.items()):
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['SimSun', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['mathtext.fontset'] = cfg['fontset']
    if cfg['fontset'] == 'custom':
        plt.rcParams['mathtext.rm'] = cfg['rm']
        plt.rcParams['mathtext.it'] = cfg['it']
        plt.rcParams['mathtext.bf'] = cfg['bf']
    ax.semilogy([0, 1], [1e-3, 1e1])
    ax.set_xlim(-1, 1)
    ax.set_title(f'{name}\n中文 $D=7\\times10^{{-9}}$', fontsize=10)
    ax.set_xlabel(r'ASCII负号 -5   数学 $-\mathrm{d}\bar{C}/\mathrm{d}t$')

fig.tight_layout()
fig.savefig('_minus_test.png', dpi=160, bbox_inches='tight')
print('saved _minus_test.png')
