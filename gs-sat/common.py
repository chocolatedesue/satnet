import os
import math
import numpy as np
import sys
import matplotlib.pyplot as plt
import random

def loadFile(filename):
    res = []
    with open(filename) as f:
        for line in f.readlines():
            gs_id, sat_id, pitch_angle, yaw_angle, dist = line.split(' ')
            res.append([int(gs_id), int(sat_id), float(pitch_angle), float(yaw_angle), float(dist)])
    return res

def loadData(config, curtime):
    data_dir = config["data_dir"]
    vis_file = os.path.join(data_dir, "{}.txt".format(curtime))
    gs_sat_vis = loadFile(vis_file)
    return gs_sat_vis

def output(config, result, algo, eval=False):
    output_name = ("[Eval] " if eval else "") + "{} - {}.txt".format(config["task"], algo)
    
    output_file = os.path.join(config["output_dir"], output_name)
    fout = open(output_file, "w")
    for matching in result:
        fout.write(" ".join([str(sat_id) for sat_id in matching]))
        fout.write("\n")
    fout.close()

def tracing(target_pitch_angle, target_yaw_angle, cur_pitch_angle, cur_yaw_angle, max_pitch_change, max_yaw_change):
    delta_yaw = target_yaw_angle - cur_yaw_angle
    yaw_cost = min(math.fabs(delta_yaw), math.fabs(delta_yaw - 360), math.fabs(delta_yaw + 360))
    if max_yaw_change >= yaw_cost:
        cur_yaw_angle = target_yaw_angle
    else:
        if math.fabs(delta_yaw) == yaw_cost:
            cur_yaw_angle += np.sign(delta_yaw) * max_yaw_change
        elif math.fabs(delta_yaw - 360) == yaw_cost:
            cur_yaw_angle += np.sign(delta_yaw - 360) * max_yaw_change
        elif math.fabs(delta_yaw + 360) == yaw_cost:
            cur_yaw_angle += np.sign(delta_yaw + 360) * max_yaw_change

        if cur_yaw_angle >= 360:
            cur_yaw_angle -= 360
        if cur_yaw_angle < 0:
            cur_yaw_angle += 360

    delta_pitch = target_pitch_angle - cur_pitch_angle
    if max_pitch_change >= math.fabs(delta_pitch):
        cur_pitch_angle = target_pitch_angle
    else:
        cur_pitch_angle += np.sign(delta_pitch) * max_pitch_change
    
    return cur_pitch_angle, cur_yaw_angle

def eval(config, result, algo):
    gs_num = config["gs_num"]
    sat_num = config["sat_num"]
    mode = config["mode"]
    begin, end, step = config["begin"], config["end"], config["step"]
    yaw_speed, pitch_speed = config["yaw_speed"], config["pitch_speed"]
    switch_num = [0] * gs_num
    feeder_time = [0] * gs_num
    gs_state = [(-1, 90, 0)] * gs_num
    max_pitch_change = step * pitch_speed
    max_yaw_change = step * yaw_speed

    '''
    duration = [0] * gs_num
    last = [-1] * gs_num
    dstats = []
    for cur in result:
        for gs_id in range(gs_num):
            if last[gs_id] == cur[gs_id]:
                duration[gs_id] += 1
            else:
                if last[gs_id] != -1:
                    dstats.append(duration[gs_id] * 10)
                duration[gs_id] = 0
        last = cur
    for gs_id in range(gs_num):
        if duration[gs_id] > 0:
            dstats.append(duration[gs_id])
            duration[gs_id] = 0
    rstats = []
    '''

    eval_res = []
    for curtime, matching in zip(range(begin, end, step), result):
        sat_used = [False] * sat_num
        target_state = [(-1, 90, 0)] * gs_num
        eval_matching = [-1] * gs_num

        gs_sat_vis = loadData(config, curtime)
        for elem in gs_sat_vis:
            gs_id, sat_id, pitch_angle, yaw_angle = elem[:4]
            if sat_id == matching[gs_id]:
                target_state[gs_id] = (sat_id, pitch_angle, yaw_angle)

        for gs_id in range(gs_num):
            cur_sat_id, cur_pitch_angle, cur_yaw_angle = gs_state[gs_id]
            target_sat_id, target_pitch_angle, target_yaw_angle = target_state[gs_id]

            if target_sat_id == -1:
                continue

            cur_pitch_angle, cur_yaw_angle = tracing(target_pitch_angle, target_yaw_angle, cur_pitch_angle, cur_yaw_angle, max_pitch_change, max_yaw_change)

            flag = False                
            if cur_pitch_angle == target_pitch_angle and cur_yaw_angle == target_yaw_angle:            
                if cur_sat_id == target_sat_id:
                    if not sat_used[target_sat_id]:
                        flag = True
                else:
                    cur_sat_id = target_sat_id
                    switch_num[gs_id] += 1
            else:
                cur_sat_id = -1
            
            if flag:
                feeder_time[gs_id] += step
                sat_used[target_sat_id] = True
                eval_matching[gs_id] = target_sat_id
                '''
                duration[gs_id] += 1
                '''
            '''
            else:
                if duration[gs_id] > 0:
                    rstats.append(duration[gs_id] * 10)
                    duration[gs_id] = 0
            '''
            gs_state[gs_id] = (cur_sat_id, cur_pitch_angle, cur_yaw_angle)

        eval_res.append(eval_matching)
        if mode == "debug":
            print(gs_state)

    if "multi_ant_gs_num" in config:
        multi_ant_gs_num = config["multi_ant_gs_num"]
    else:
        multi_ant_gs_num = 0
    
    if "ant_num" in config:
        ant_num = config["ant_num"]
    else:
        ant_num = 1

    real_gs_num = gs_num - (ant_num - 1) * multi_ant_gs_num
    gs_sw_num = [0] * real_gs_num
    gs_fr_usage = [0] * real_gs_num
    for i in range(gs_num):
        if i < ant_num * multi_ant_gs_num:
            real_gs_id = i // ant_num
        else:
            real_gs_id = i - (ant_num - 1) * multi_ant_gs_num
        gs_sw_num[real_gs_id] += switch_num[i]
        gs_fr_usage[real_gs_id] += feeder_time[i]
    for i in range(multi_ant_gs_num):
        gs_sw_num[i] /= ant_num
        gs_fr_usage[i] /= ant_num
    avg_switch_freq = sum(gs_sw_num) / real_gs_num / (end - begin) * 60 * 60
    avg_resource_usage = sum(gs_fr_usage) / real_gs_num / (end - begin)

    '''
    max_vel = 300
    hist, bin_edges = np.histogram(dstats, bins = range(0, max_vel, 10))
    print(hist, bin_edges)
    y = [freq / len(dstats) for freq in hist] + [0]
    x = range(0, max_vel, 10)
    plt.plot(x, y, 'b-', label="expected time", lw=1.2, alpha=0.6)
    hist, bin_edges = np.histogram(rstats, bins = range(0, max_vel, 10))
    print(hist, bin_edges)
    y = [freq / len(rstats) for freq in hist] + [0]
    x = range(0, max_vel, 10)
    plt.plot(x, y, 'r-', label="actual time", lw=1.2, alpha=0.6)
    plt.xticks(range(0, max_vel + 1, 50))
    plt.xlim((0, max_vel))
    plt.ylim((0, 0.3))
    plt.xlabel("connection time")
    plt.title("the distribution of connection time")
    plt.legend()
    plt.savefig("plot_figs/connection_time.png")
    plt.close()

    for gs_id in range(gs_num):
        if gs_state[gs_id][0] != -1:
            rstats.append(duration[gs_id])
        duration[gs_id] = 0
    '''
    print("Number of switches:", switch_num)
    print("Total duration of feeder links:", feeder_time)

    print("Average switch frequency: {:.3f}/h".format(avg_switch_freq))
    print("Average feeder resource usage: {:.2%}".format(avg_resource_usage))

    output(config, eval_res, algo, True)

    sample_num = 100000
    random.seed(20231109)
    
    service_samples = []
    for _ in range(sample_num):
        pv = random.paretovariate(1.0)
        service_duration = min(len(eval_res), int(pv))
        service_begin = random.randint(0, len(eval_res) - service_duration)
        service_end = service_begin + service_duration
        if multi_ant_gs_num == real_gs_num:  
            service_gs = random.randint(0, real_gs_num - 1)
        elif multi_ant_gs_num == 0:
            service_gs = random.randint(0, real_gs_num - 1)
        else:
            if random.random() < 0.9:
                service_gs = random.randint(0, multi_ant_gs_num - 1)
            else:
                service_gs = random.randint(multi_ant_gs_num, real_gs_num - 1)

        service_breakdown_duration = 0
        for service_time in range(service_begin, service_end):
            bkdown = True
            if service_gs < multi_ant_gs_num:
                for gs_id in range(service_gs * ant_num, (service_gs + 1) * ant_num):
                    if eval_res[service_time][gs_id] != -1:
                        bkdown = False
            else:
                gs_id = service_gs + (ant_num - 1) * multi_ant_gs_num
                if eval_res[service_time][gs_id] != -1:
                    bkdown = False
            if bkdown:
                service_breakdown_duration += 1
        service_samples.append(service_breakdown_duration / service_duration)
           
    breakdown_rate = sum(service_samples) / len(service_samples)
    print("Average breakdown rate: {:.2%}".format(breakdown_rate))
    return avg_switch_freq, avg_resource_usage,  breakdown_rate