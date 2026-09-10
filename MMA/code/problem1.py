# -*- coding: utf-8 -*-
"""问题1：预热平衡阶段（附录2）温度与水分浓度求解，输出 result1.xlsx。"""
import numpy as np
from common import simulate, write_result_xlsx, DATA

N = 400            # 求解网格（0.005cm 间距，保证四位小数精度）
dt = 0.5           # 时间步长 s
t_end = 1800.0     # 30 min

out_times = np.arange(1.0, t_end + 1e-9, 1.0)          # 每秒
out_r = np.arange(0.0, 0.020001, 0.001)                # 0~2cm 每 0.1cm

res = simulate(1, t_end, dt, N=N, out_times=out_times, out_r=out_r)
T = res['T_out']; C = res['C_out']

# ---- 论文表1/表2 ----
tbl_t = [100, 300, 600, 900, 1200, 1500, 1800]
tbl_r = [0.0, 0.005, 0.010, 0.015, 0.020]             # 0,0.5,1,1.5,2 cm
r_idx = [int(round(rr / 0.001)) for rr in tbl_r]
print('=' * 60)
print('表1  30分钟内药材的温度 (°C)')
print('时间/s    ' + '   '.join(f'{rr*100:>6.1f}cm' for rr in tbl_r))
for tt in tbl_t:
    i = int(round(tt / 1.0)) - 1
    print(f'{tt:>7d}   ' + '   '.join(f'{T[i, j]:>10.4f}' for j in r_idx))
print('=' * 60)
print('表2  30分钟内药材的水分浓度 (kg/kg)')
print('时间/s    ' + '   '.join(f'{rr*100:>6.1f}cm' for rr in tbl_r))
for tt in tbl_t:
    i = int(round(tt / 1.0)) - 1
    print(f'{tt:>7d}   ' + '   '.join(f'{C[i, j]:>10.4f}' for j in r_idx))
print('=' * 60)

# ---- 写 result1.xlsx ----
dist_header = [round(float(x) * 100.0, 1) for x in out_r]   # cm
times = [int(t) for t in out_times]
write_result_xlsx(f'{DATA}/result1.xlsx',
                  sheets=[('温度', T), ('水分浓度', C)],
                  times=times, distances=dist_header)
print('result1.xlsx 已写入：', len(times), '行 x', len(dist_header), '列')
