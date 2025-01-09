import os
from scipy.spatial import ConvexHull
import json
import common

frame_num = 600
data_dir = "/home/chenyuxuan/satnet/data/20230927qb/Jan1st"
output_dir_pfx = "/home/chenyuxuan/satnet/visualization/frame_data/Matching (Jan) - "
config_path = "/home/chenyuxuan/satnet/gs-sat/configs/jan.json"
result_pfx = "/home/chenyuxuan/satnet/gs-sat/output/Jan - "

config_file = open(config_path)
config = json.load(config_file)
gs_num = config["gs_num"]
sat_num = config["sat_num"]
begin, end, step = config["begin"], config["end"], config["step"]
yaw_speed, pitch_speed = config["yaw_speed"], config["pitch_speed"]

gs_icrs_dir = os.path.join(data_dir, "gs-geocentric-position")
sat_lla_dir = os.path.join(data_dir, "sat-subpoint-position")
sat_icrs_dir = os.path.join(data_dir, "sat-geocentric-position")

gs_ll_raw = [
    [116.41339, 39.91092],
    [126.54161, 45.80882],
    [87.62444 , 43.83076],
    [76.00031 , 39.47365],
    [91.17846 , 29.65949],
    [110.20672, 20.05211],
    [119.30347 , 26.08043],
    [103.84052 , 36.06724],
    [119.74246 , 49.21822]
]

def load(filename):
    res = []
    with open(filename) as f:
        for line in f.readlines():
            res.append([float(elem) for elem in line.split(' ')])
    return res


for algorithm in [ "max_visible_time", "min_distance", "max_matching", "gs_state_aware_matching", "dp_scheduler"]:
    output_dir = output_dir_pfx + algorithm

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    switch_num = [0] * gs_num
    feeder_time = [0] * gs_num
    gs_state = [(-1, 90, 0)] * gs_num
    max_pitch_change = step * pitch_speed
    max_yaw_change = step * yaw_speed

    result_path = result_pfx + algorithm + ".txt"
    result_file = open(result_path)
    result = [[int(elem) for elem in line.split(' ')] for line in result_file.readlines()]

    curframe = 0
    for curtime, matching in zip(range(begin, end, step), result):
        if curframe >= frame_num:
            break
        output_file = os.path.join(output_dir, "{}.txt".format(curframe))
        curframe += 1

        gs_icrs_file = os.path.join(gs_icrs_dir, "{}.csv".format(curtime))
        sat_lla_file = os.path.join(sat_lla_dir, "{}.csv".format(curtime))
        sat_icrs_file = os.path.join(sat_icrs_dir, "{}.csv".format(curtime))

        vis = common.loadData(config, curtime)
        gs_lla = [[ll[1], ll[0], 0] for ll in gs_ll_raw]
        gs_icrs = load(gs_icrs_file)
        sat_lla = load(sat_lla_file)
        sat_icrs = load(sat_icrs_file)

        nodelist = []
        for i in range(sat_num):
            nodelist.append([sat_lla[i][1], sat_lla[i][0], 0])
        for i in range(gs_num):
            nodelist.append([gs_lla[i][1], gs_lla[i][0], 4])
        
        for elem in vis:
            nodelist[elem[1]][2] = 5

        edgelist = []
        for gs_id in range(gs_num):
            vis_set = []
            for elem in vis:
                if elem[0] == gs_id:
                    vis_set.append(elem[1])
            points = [[sat_lla[sat_id][0], sat_lla[sat_id][1]] for sat_id in vis_set]
            convex = ConvexHull(points).vertices.tolist()
            
            for i in range(len(convex)):
                edgelist.append([vis_set[convex[i]], vis_set[convex[(i + 1) % len(convex)]], 6])

        sat_used = [False] * sat_num
        target_state = [(-1, 90, 0)] * gs_num

        gs_sat_vis = common.loadData(config, curtime)
        for elem in gs_sat_vis:
            gs_id, sat_id, pitch_angle, yaw_angle = elem[:4]
            if sat_id == matching[gs_id]:
                target_state[gs_id] = (sat_id, pitch_angle, yaw_angle)

        for gs_id in range(gs_num):
            cur_sat_id, cur_pitch_angle, cur_yaw_angle = gs_state[gs_id]
            target_sat_id, target_pitch_angle, target_yaw_angle = target_state[gs_id]

            if target_sat_id == -1:
                continue

            cur_pitch_angle, cur_yaw_angle = common.tracing(target_pitch_angle, target_yaw_angle, cur_pitch_angle, cur_yaw_angle, max_pitch_change, max_yaw_change)
            
            fl_type = 7
            if cur_pitch_angle == target_pitch_angle and cur_yaw_angle == target_yaw_angle:            
                if cur_sat_id == target_sat_id:
                    if not sat_used[target_sat_id]:
                        feeder_time[gs_id] += step
                        sat_used[target_sat_id] = True
                        fl_type = 5
                else:
                    cur_sat_id = target_sat_id
                    switch_num[gs_id] += 1
            else:
                cur_sat_id = -1
            edgelist.append([sat_num + gs_id, target_sat_id, fl_type])
            
            gs_state[gs_id] = (cur_sat_id, cur_pitch_angle, cur_yaw_angle)

        nodelist3d = sat_icrs + gs_icrs

        output = open(output_file, "w")
        output.write(" | ".join([" ".join([str(elem) for elem in node]) for node in nodelist]))
        output.write("\n")
        output.write(" | ".join([" ".join([str(elem) for elem in edge]) for edge in edgelist]))
        output.write("\n")
        output.write(" | ".join([" ".join([str(elem) for elem in node3d]) for node3d in nodelist3d]))
        output.write("\n")
        output.close()
