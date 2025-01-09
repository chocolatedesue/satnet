import common

alpha = 3

def compute(gs_id, init_state, sat_used, peek_map, max_pitch_change, max_yaw_change):
    visible_set = set(elem[1] for elem in peek_map[0][gs_id])
    opt = (-1e9, -1, 0, 0)
    for sat_id in visible_set:
        if sat_used[sat_id]:
            continue
        gs_state = init_state
        duration = 0
        swcost = 0
        for gs_map in peek_map:
            target_state = (-1, 90, 0)
            for elem in gs_map[gs_id]:
                if elem[1] == sat_id:
                    target_state = (elem[1:4])

            cur_sat_id, cur_pitch_angle, cur_yaw_angle = gs_state
            target_sat_id, target_pitch_angle, target_yaw_angle = target_state

            if target_sat_id == -1:
                break

            cur_pitch_angle, cur_yaw_angle = common.tracing(target_pitch_angle, target_yaw_angle, cur_pitch_angle, cur_yaw_angle, max_pitch_change, max_yaw_change)
            
            flag = True
            if cur_pitch_angle == target_pitch_angle and cur_yaw_angle == target_yaw_angle:        
                if cur_sat_id == target_sat_id:
                    flag = False
                else:
                    cur_sat_id = target_sat_id
            else:
                if cur_sat_id == sat_id:
                    break
                else:
                    cur_sat_id = -1
            if flag:
                swcost += 1

            duration += 1
            gs_state = (cur_sat_id, cur_pitch_angle, cur_yaw_angle)
        
        reward = duration - swcost * alpha
        if reward > opt[0]:
            opt = (reward, sat_id, duration, duration - swcost)

    return opt

def simulate(gs_id, init_state, peek_map, sat_id, duration, max_pitch_change, max_yaw_change):
    gs_state = init_state
    for gs_map in peek_map[:duration]:
        target_state = (-1, 90, 0)

        for elem in gs_map[gs_id]:
            if elem[1] == sat_id:
                target_state = (elem[1:4])

        cur_sat_id, cur_pitch_angle, cur_yaw_angle = gs_state
        target_sat_id, target_pitch_angle, target_yaw_angle = target_state

        if target_sat_id == -1:
            continue

        cur_pitch_angle, cur_yaw_angle = common.tracing(target_pitch_angle, target_yaw_angle, cur_pitch_angle, cur_yaw_angle, max_pitch_change, max_yaw_change)
        
        if cur_pitch_angle == target_pitch_angle and cur_yaw_angle == target_yaw_angle:
            cur_sat_id = target_sat_id
        else:
            cur_sat_id = -1
        
        gs_state = (cur_sat_id, cur_pitch_angle, cur_yaw_angle)

    return gs_state

def run(config):
    begin, end, step = config["begin"], config["end"], config["step"]
    gs_num = config["gs_num"]
    sat_num = config["sat_num"]
    yaw_speed, pitch_speed = config["yaw_speed"], config["pitch_speed"]
    max_pitch_change = step * pitch_speed
    max_yaw_change = step * yaw_speed

    vis_map = []
    for curtime in range(begin, end, step):
        gs_sat_vis = common.loadData(config, curtime)
        gs_map = []
        for _ in range(gs_num):
            gs_map.append([])
        for elem in gs_sat_vis:
            gs_map[elem[0]].append(elem)
        vis_map.append(gs_map)
    vis_len = len(vis_map)

    res = []
    for _ in range(vis_len):
        res.append([-1] * gs_num)

    total_gain = 0
    gs_state = [(-1, 90, 0)] * gs_num
    for cur_idx in range(vis_len):
        sat_used = [False] * sat_num
        for gs_id in range(gs_num):
            if res[cur_idx][gs_id] != -1:
                sat_used[res[cur_idx][gs_id]] = True
        for gs_id in range(gs_num):
            if res[cur_idx][gs_id] == -1:
                _, target_sat, duration, gain = compute(gs_id, gs_state[gs_id], sat_used, vis_map[cur_idx:], max_pitch_change, max_yaw_change)
                total_gain += gain
                gs_state[gs_id] = simulate(gs_id, gs_state[gs_id], vis_map[cur_idx:], target_sat, duration, max_pitch_change, max_yaw_change)
                for idx in range(cur_idx, cur_idx + duration):
                    res[idx][gs_id] = target_sat
                sat_used[target_sat] = True            
    
    print("Est. feeder link usage: {:.2%}".format(total_gain * step / gs_num / (end - begin)))
    return res