import common
import sys
import json
import math
import numpy as np
import matplotlib.pyplot as plt

if len(sys.argv) < 2:
    print("Error: please specify configuration file!")
    exit(0)

json_f = open(sys.argv[1])
config = json.loads(json_f.read())
begin, end, step = config["begin"], config["end"], config["step"]
gs_num = config["gs_num"]
sat_num = config["sat_num"]

res = []
for curtime in range(begin + step, end, step):
    cur_gs_sat_vis = common.loadData(config, curtime)
    last_gs_sat_vis = common.loadData(config, curtime - step)
    
    for gs_id in range(gs_num):    
        for last_elem in last_gs_sat_vis:
            for cur_elem in cur_gs_sat_vis:
                if last_elem[1] == cur_elem[1]:
                    last_yaw = last_elem[3]
                    cur_yaw = cur_elem[3]
                    yaw_change = cur_yaw - last_yaw
                    req_yaw_speed = min(math.fabs(yaw_change - 360), math.fabs(yaw_change), math.fabs(yaw_change + 360)) / step
                    res.append(req_yaw_speed)
                    break


max_vel = 20
hist, bin_edges = np.histogram(res, bins = range(0, max_vel, 1))
print(hist, bin_edges)
y = [0] + [freq / len(res) for freq in hist]
x = range(0, max_vel, 1)
plt.xticks(range(0, max_vel + 2, 2))
plt.xlim((0, max_vel))
plt.ylim((0, 1))
plt.plot(x, y, 'b-', lw=1.2, alpha=0.6)
plt.axvline(x=3, color='r', linestyle='--', linewidth=0.8)
plt.xlabel("angular velocity (degrees per second)")
plt.title("the distribution of angular velocity of satellites")
plt.savefig("plot_figs/angular_velocity_dist.png")
plt.close()

print(max(res))