import common
import numpy as np
from scipy.optimize import linear_sum_assignment

def run(config):
    begin, end, step = config["begin"], config["end"], config["step"]
    gs_num = config["gs_num"]
    sat_num = config["sat_num"]

    res = []
    for curtime in range(begin, end, step):
        gs_sat_vis = common.loadData(config, curtime)

        cost = np.zeros([gs_num, sat_num], dtype=int)
        for elem in gs_sat_vis:
            cost[elem[0], elem[1]] = -1

        _, matching = linear_sum_assignment(cost)

        res.append(matching)
    return res