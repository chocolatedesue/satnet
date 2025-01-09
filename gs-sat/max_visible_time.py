import common
import math
import matplotlib.pyplot as plt
import numpy as np

def get_visible_set(gs_id, gs_sat_vis):
    visible_set = set()
    for elem in gs_sat_vis:
        if elem[0] == gs_id:
          visible_set.add(elem[1])
    return visible_set

def find(gs_id, idx, vis_series, sat_used):
    candidates = set()
    for visible_sat in get_visible_set(gs_id, vis_series[idx]):
        if not sat_used[visible_sat]:
            candidates.add(visible_sat)

    if len(candidates) == 0:
        return -1
    
    res = next(iter(candidates))
    for gs_sat_vis in vis_series[idx + 1:]:
        candidates.intersection_update(get_visible_set(gs_id, gs_sat_vis))
        if len(candidates) == 0:
            break
        else:
            res = next(iter(candidates))

    return res

def run(config):
    begin, end, step = config["begin"], config["end"], config["step"]
    gs_num = config["gs_num"]
    sat_num = config["sat_num"]

    gs_sat_vis_series = []
    for curtime in range(begin, end, step):
        gs_sat_vis = common.loadData(config, curtime)
        gs_sat_vis_series.append(gs_sat_vis)

    last_msat = [-1] * gs_num
    
    '''
    stats = []
    '''
    res = []
    for cur_idx, gs_sat_vis in enumerate(gs_sat_vis_series):
        cur_msat = [-1] * gs_num
        sat_used = [False] * sat_num
        for elem in gs_sat_vis:
            gs_id, sat_id = elem[:2]
            if sat_id == last_msat[gs_id]:
                cur_msat[gs_id] = sat_id
                sat_used[sat_id] = True

        for gs_id in range(gs_num):
            if cur_msat[gs_id] == -1:
                target = find(gs_id, cur_idx, gs_sat_vis_series, sat_used)
                if target == -1:
                    continue
                cur_msat[gs_id] = target
                sat_used[target] = True
                '''
                if last_msat[gs_id] == -1:
                    continue
                for elem in gs_sat_vis_series[cur_idx - 1]:
                    if elem[0] == gs_id and elem[1] == last_msat[gs_id]:
                        last_yaw = elem[3]
                for elem in gs_sat_vis:
                    if elem[0] == gs_id and elem[1] == cur_msat[gs_id]:
                        cur_yaw = elem[3]
                yaw_change = cur_yaw - last_yaw
                stats.append(min(math.fabs(yaw_change - 360), math.fabs(yaw_change), math.fabs(yaw_change + 360)))
                '''
        res.append(cur_msat)
        last_msat = cur_msat

    '''
    max_vel = 200
    hist, bin_edges = np.histogram(stats, bins = range(0, max_vel, 10))
    print(hist, bin_edges)
    y = [0] + [freq / len(stats) for freq in hist]
    x = range(0, max_vel, 10)
    plt.xticks(range(0, max_vel + 20, 20))
    plt.xlim((0, max_vel))
    plt.ylim((0, 0.3))
    plt.plot(x, y, 'b-', lw=1.2, alpha=0.6)
    plt.xlabel("yaw change (degrees)")
    plt.title("the distribution of yaw change while switching satelites")
    plt.savefig("plot_figs/yaw_change_dist.png")
    plt.close()
    common.eval(config, res)
    '''
    return res