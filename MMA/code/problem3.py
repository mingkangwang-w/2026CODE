# -*- coding: utf-8 -*-
"""问题3：附录3变物性，求水分浓度处处 < 0.15 kg/kg 的干燥时间，输出 result3.xlsx。"""
import numpy as np
from common import simulate, write_result_xlsx, DATA

N = 400
dt = 5.0
t_end = 360000.0        # 上限 100 h
THRESH = 0.15

out_times = np.arange(60.0, t_end + 1e-9, 60.0)        # 每 60s
out_r = np.arange(0.0, 0.020001, 0.001)                # 0~2cm

res = simulate(3, t_end, dt, N=N, out_times=out_times, out_r=out_r,
               drying_thresh=THRESH)
T = res['T_out']; C = res['C_out']; t = res['t_out']; T_end = res['T_end']
C_surf = res['C_surf']

print('=' * 60)
print(f'烘干结束时间 T_end = {T_end:.1f} s = {T_end/3600:.4f} h')
print(f'结束时刻 max(C) 应 < {THRESH}，实际 max = {np.nanmax(C[-1]):.6f}')
print('=' * 60)
print('表5  药材烘干过程的水分浓度 (kg/kg)')
tbl_r = [0.0, 0.005, 0.010, 0.015, 0.020]
r_idx = [int(round(rr / 0.001)) for rr in tbl_r]
print('时间/h    ' + '   '.join(f'{rr*100:>6.1f}cm' for rr in tbl_r))
tbl_t = list(np.arange(21600.0, T_end + 1e-9, 21600.0)) + [T_end]
for th in tbl_t:
    i = int(np.argmin(np.abs(t - th)))
    print(f'{th/3600:>7.2f}   ' + '   '.join(f'{C[i, j]:>10.4f}' for j in r_idx))
print('=' * 60)

# ---- 写 result3.xlsx ----
dist_header = [round(float(x) * 100.0, 1) for x in out_r]
write_result_xlsx(f'{DATA}/result3.xlsx',
                  sheets=[('Sheet1', C)],
                  times=[int(round(x)) for x in t], distances=dist_header)
print('result3.xlsx 已写入：', len(t), '行 x', len(dist_header), '列')

# 保存绘图数据
np.savez('/home/user/workspace/code/_p3.npz', t=t, C=C, T=T, r=out_r,
         C_surf=C_surf, T_end=T_end)
