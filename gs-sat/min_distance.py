import common

def run(config):
    begin, end, step = config["begin"], config["end"], config["step"]
    gs_num = config["gs_num"]
    sat_num = config["sat_num"]

    res = []
    for curtime in range(begin, end, step):
        gs_sat_vis = common.loadData(config, curtime)
        gs_nsat = [-1] * gs_num
        gs_ndist = [0] * gs_num
        sat_used = [False] * sat_num

        for elem in gs_sat_vis:
            gs_id, sat_id = elem[:2]
            if len(res) > 0 and res[-1][gs_id] == sat_id:
                gs_nsat[gs_id] = sat_id
                sat_used[sat_id] = True

        for elem in gs_sat_vis:
            gs_id, sat_id = elem[:2]
            cur_dist = elem[4]
            if sat_used[sat_id]:
                continue
        
            if gs_nsat[gs_id] == -1:
                gs_nsat[gs_id] = sat_id
                gs_ndist[gs_id] = cur_dist
                sat_used[sat_id] = True
            else:
                if cur_dist < gs_ndist[gs_id]:
                    sat_used[gs_nsat[gs_id]] = False
                    gs_nsat[gs_id] = sat_id
                    gs_ndist[gs_id] = cur_dist
                    sat_used[sat_id] = True
        res.append(gs_nsat)
    return res