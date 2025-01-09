import common
import numpy as np
from scipy.optimize import linear_sum_assignment
import time
import multiprocessing

max_stable_time = 20
active_state_num = 10
processor_num = multiprocessing.cpu_count() - 1

def compute(init_state, peek_map, gs_num, sat_num, max_pitch_change, max_yaw_change):
    cost = np.empty([gs_num, sat_num], dtype=int)
    for gs_id in range(gs_num):
        for sat_id in range(sat_num):
            weight = 0
            cur_sat_id, cur_pitch_angle, cur_yaw_angle = init_state[gs_id]
            for gs_map in peek_map:
                target_state = (-1, 90, 0)
                for elem in gs_map[gs_id]:
                    if elem[1] == sat_id:
                        target_state = (elem[1:4])
                        break
                target_sat_id, target_pitch_angle, target_yaw_angle = target_state
                if target_sat_id == -1:
                    continue
                cur_pitch_angle, cur_yaw_angle = common.tracing(target_pitch_angle, target_yaw_angle, cur_pitch_angle, cur_yaw_angle, max_pitch_change, max_yaw_change)

                if cur_pitch_angle == target_pitch_angle and cur_yaw_angle == target_yaw_angle:            
                    if cur_sat_id == target_sat_id:
                        weight += 1
                    else:
                        cur_sat_id = target_sat_id
                else:
                    cur_sat_id = -1
            cost[gs_id][sat_id] = -weight

    _, matching = linear_sum_assignment(cost)
    return matching

def simulate(gs_state, peek_map, gs_num, sat_num, matching, max_pitch_change, max_yaw_change, step):
    gain = 0
    for gs_map in peek_map:
        sat_used = [False] * sat_num
        target_state = [(-1, 90, 0)] * gs_num

        for gs_id in range(gs_num):
            for elem in gs_map[gs_id]:
                if elem[1] == matching[gs_id]:
                    target_state[gs_id] = (elem[1:4])

        for gs_id in range(gs_num):
            cur_sat_id, cur_pitch_angle, cur_yaw_angle = gs_state[gs_id]
            target_sat_id, target_pitch_angle, target_yaw_angle = target_state[gs_id]

            if target_sat_id == -1:
                continue

            cur_pitch_angle, cur_yaw_angle = common.tracing(target_pitch_angle, target_yaw_angle, cur_pitch_angle, cur_yaw_angle, max_pitch_change, max_yaw_change)
            
            if cur_pitch_angle == target_pitch_angle and cur_yaw_angle == target_yaw_angle:            
                if cur_sat_id == target_sat_id:
                    if not sat_used[target_sat_id]:
                        gain += step
                        sat_used[target_sat_id] = True
                else:
                    cur_sat_id = target_sat_id
            else:
                cur_sat_id = -1
            
            gs_state[gs_id] = (cur_sat_id, cur_pitch_angle, cur_yaw_angle)
    return gs_state, gain

def get_next_state(args):
    peek_map, cur_gs_state, cur_matching, cur_idx, next_idx, gs_num, sat_num, max_pitch_change, max_yaw_change, cur_fl_duration, step = args
    target_matching = compute(cur_gs_state, peek_map, gs_num, sat_num, max_pitch_change, max_yaw_change)
    next_gs_state, fl_duration_gain = simulate(cur_gs_state, peek_map, gs_num, sat_num, target_matching, max_pitch_change, max_yaw_change, step)
    next_matching = tuple([state[0] for state in next_gs_state])
    next_antenna = [[state[1], state[2]] for state in next_gs_state]
    next_fl_duration = cur_fl_duration + fl_duration_gain
    return [next_idx, next_matching, next_fl_duration, next_antenna, target_matching, cur_idx, cur_matching]

def run(config):
    begin, end, step = config["begin"], config["end"], config["step"]
    gs_num = config["gs_num"]
    sat_num = config["sat_num"]
    yaw_speed, pitch_speed = config["yaw_speed"], config["pitch_speed"]
    max_pitch_change = step * pitch_speed
    max_yaw_change = step * yaw_speed

    pool = multiprocessing.Pool(processor_num)
    vis_map = []
    for curtime in range(begin, end, step):
        gs_sat_vis = common.loadData(config, curtime)
        gs_map = []
        for _ in range(gs_num):
            gs_map.append([])
        for elem in gs_sat_vis:
            gs_map[elem[0]].append(elem)
        vis_map.append(gs_map)

    dp = []
    dp.append({
        tuple([-1] * gs_num) : 
        [0, [[90, 0]] * gs_num, [-1] * gs_num, -1, [-1] * gs_num]
        })
    
    num_slices = len(vis_map)
    for _ in range(num_slices):
        dp.append({})
    
    clock_begin = time.time()
    for cur_idx in range(num_slices):
        print("Processing... {}/{}".format(cur_idx + 1, num_slices))
        elpased = time.time() - clock_begin
        print("Elpased time: {:.2f}s".format(elpased))
        eta = elpased * (num_slices / cur_idx - 1) if cur_idx > 0 else 0
        print("ETA: {:.2f}s".format(eta))
        fl_duration_list = []
        for value in dp[cur_idx].values():
            fl_duration = value[0]
            fl_duration_list.append(fl_duration)
        
        fl_duration_list.sort(reverse=True)
        fl_duration_threshold = fl_duration_list[:active_state_num][-1]

        task_list = []
        for key, value in dp[cur_idx].items():
            cur_matching = key
            cur_fl_duration = value[0]
            cur_antenna = value[1]

            if cur_fl_duration < fl_duration_threshold:
                continue

            cur_gs_state = []
            for gs_id in range(gs_num):
                cur_gs_state.append((cur_matching[gs_id], cur_antenna[gs_id][0], cur_antenna[gs_id][1])) 

            for peek in range(1, max_stable_time // step):
                next_idx = cur_idx + peek
                if next_idx > num_slices:
                    break
                peek_map = vis_map[cur_idx: next_idx]
                task_list.append((peek_map, cur_gs_state, cur_matching, cur_idx, next_idx, gs_num, sat_num, max_pitch_change, max_yaw_change, cur_fl_duration, step))
    
        next_state_list = pool.map(get_next_state, task_list)
        for next_state in next_state_list:
            next_idx, next_matching, next_fl_duration = next_state[:3]
            if next_matching not in dp[next_idx] or next_fl_duration > dp[next_idx][next_matching][0]:
                dp[next_idx][next_matching] = next_state[2:]

    max_fl_duration = -1
    opt_key = None
    for key, value in dp[num_slices].items():
        if value[0] > max_fl_duration:
            max_fl_duration = value[0]
            opt_key = key
    print(max_fl_duration)

    res = []
    cur_idx, cur_key = num_slices, opt_key
    while True:
        matching, from_idx, from_key = dp[cur_idx][cur_key][2:]
        if from_idx == -1:
            break
        for _ in range(from_idx, cur_idx):
            res.append(matching)
        cur_idx, cur_key = from_idx, from_key
    
    res.reverse()
    return res