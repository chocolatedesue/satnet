import os
import json 
import common
import re

load_dir = "/home/chenyuxuan/satnet/gs-sat/output"
output_name = "summary.csv"
config_dir = "/home/chenyuxuan/satnet/gs-sat/configs"

file_name_list = os.listdir(load_dir)
file_name_list.sort()
file_name_list.reverse()

fout = open(output_name, "w")
fout.write("task,algorithm,switch_frequency,resource_usage,breakdown_rate\n")


for file_name in file_name_list:
    if file_name.find("[Eval]") != -1:
        continue
    task_name, algorithm = file_name.split('.')[0].split(' - ')
    
    fin = open(os.path.join(load_dir, file_name))
    res = []
    for line in fin.readlines():
        matching = [int(target) for target in line.split(' ')]
        res.append(matching)
    fin.close()

    if task_name.find("Silk") != -1:
        matchObj = re.search(r'\((.*)\)', task_name)
        config_name = "{}-silk.json".format(matchObj.group(1).lower())
    else:
        config_name = "{}.json".format(task_name.lower())
    
    fin = open(os.path.join(config_dir, config_name))
    config = json.load(fin)
    fin.close()

    switch_freq, resource_usage, breakdown_rate = common.eval(config, res, algorithm)
    if algorithm == "max_visible_time":
        base_switch_freq = switch_freq
        base_resource_usage = resource_usage
        base_bk_rate = breakdown_rate
    if algorithm == "gs_state_aware_matching":
        freq_change = switch_freq / base_switch_freq - 1
        usage_change = resource_usage / base_resource_usage - 1
        bkrate_change = breakdown_rate / base_bk_rate - 1

    if algorithm == "gs_state_aware_matching":
        fout.write("{},{},{:.2f}({:.2%}),{:.2%}({:.2%}),{:.2%}({:.2%})\n".format(task_name, algorithm, switch_freq, freq_change, resource_usage, usage_change, breakdown_rate, bkrate_change))    
    else:
        fout.write("{},{},{:.2f},{:.2%},{:.2%}\n".format(task_name, algorithm, switch_freq, resource_usage, breakdown_rate))

fout.close()