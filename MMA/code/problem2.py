# -*- coding: utf-8 -*-
"""问题2：整个烘干过程模型（附录3变物性），报告 3h 内结果，输出 result2.xlsx。"""
import numpy as np
from common import simulate, write_result_xlsx, DATA

N = 400            # 求解网格
dt = 1.0           # 时间步长 s
t_end = 10800.0    # 3 h

out_times = np.arange(1.0, t_end + 1e-9, 1.0)          # 每秒
out_r = np.arange(0.0, 0.020001, 0.001)                # 0~2cm

res = simulate(2, t_end, dt, N=N, out_times=out_times, out_r=out_r)
T = res['T_out']; C = res['C_out']

# ---- 论文表3/表4 ----
tbl_t = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]                  # h
tbl_r = [0.0, 0.005, 0.010, 0.015, 0.020]
r_idx = [int(round(rr / 0.001)) for rr in tbl_r]
print('=' * 60)
print('表3  3小时内药材的温度 (°C)')
print('时间/h    ' + '   '.join(f'{rr*100:>6.1f}cm' for rr in tbl_r))
for th in tbl_t:
    i = int(round(th * 3600.0)) - 1
    print(f'{th:>7.1f}   ' + '   '.join(f'{T[i, j]:>10.4f}' for j in r_idx))
print('=' * 60)
print('表4  3小时内药材的水分浓度 (kg/kg)')
print('时间/h    ' + '   '.join(f'{rr*100:>6.1f}cm' for rr in tbl_r))
for th in tbl_t:
    i = int(round(th * 3600.0)) - 1
    print(f'{th:>7.1f}   ' + '   '.join(f'{C[i, j]:>10.4f}' for j in r_idx))
print('=' * 60)

# ---- 写 result2.xlsx ----
dist_header = [round(float(x) * 100.0, 1) for x in out_r]
times = [int(t) for t in out_times]
write_result_xlsx(f'{DATA}/result2.xlsx',
                  sheets=[('温度', T), ('水分浓度', C)],
                  times=times, distances=dist_header)
print('result2.xlsx 已写入：', len(times), '行 x', len(dist_header), '列')

# 保存用于绘图的关键轨迹
np.savez('/home/user/workspace/code/_p2.npz', t=out_times, T=T, C=C, r=out_r)
