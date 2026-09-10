# -*- coding: utf-8 -*-
"""问题4：附录4变物性 + 半径收缩（附件2），求干燥时长，输出 result4.xlsx。"""
import numpy as np
from common import simulate, write_result_xlsx, DATA

N = 400
dt = 5.0
t_end = 540000.0        # 上限 150 h
THRESH = 0.15

out_times = np.arange(60.0, t_end + 1e-9, 60.0)        # 每 60s
out_r = np.arange(0.0, 0.019001, 0.001)                # 固定距离 0~1.9cm（表面另列）

res = simulate(4, t_end, dt, N=N, out_times=out_times, out_r=out_r,
               shrink=True, drying_thresh=THRESH)
C = res['C_out']; t = res['t_out']; T_end = res['T_end']
C_surf = res['C_surf']; R_out = res['R_out']

print('=' * 60)
print(f'烘干结束时间 T_end = {T_end:.1f} s = {T_end/3600:.4f} h')
print(f'结束时刻 max(C) 应 < {THRESH}，实际 max = {np.nanmax(C[-1]):.6f}')
print(f'结束时刻表面半径 R = {R_out[-1]*100:.4f} cm')
print('=' * 60)
print('表6  药材烘干过程的水分浓度 (kg/kg)')
print('时间/h    ' + '   0.0cm   0.5cm   1.0cm   1.5cm   药材表面')
tbl_t = list(np.arange(21600.0, T_end + 1e-9, 21600.0)) + [T_end]
for th in tbl_t:
    i = int(np.argmin(np.abs(t - th)))
    c0 = C[i, 0]; c5 = C[i, 5]; c10 = C[i, 10]; c15 = C[i, 15]; cs = C_surf[i]
    print(f'{th/3600:>7.2f}   ' + '   '.join(f'{v:>8.4f}' for v in (c0, c5, c10, c15, cs)))
print('=' * 60)

# ---- 写 result4.xlsx ----
C_full = np.column_stack([C, C_surf])                  # 固定距离 + 表面列
dist_header = [round(float(x) * 100.0, 1) for x in out_r] + ['药材表面']
write_result_xlsx(f'{DATA}/result4.xlsx',
                  sheets=[('Sheet1', C_full)],
                  times=[int(round(x)) for x in t], distances=dist_header)
print('result4.xlsx 已写入：', len(t), '行 x', len(dist_header), '列')

# 保存绘图数据
np.savez('/home/user/workspace/code/_p4.npz', t=t, C=C, C_surf=C_surf, R=R_out,
         r=out_r, T_end=T_end)
