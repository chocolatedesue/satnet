import os
import re
from scipy import stats
import numpy as np

def getRecords(dir, target_name):
    records = []
    files = os.listdir(dir)
    files.sort()
    for file in files:
        if file.find("report") == -1:
            continue
        file_path = os.path.join(dir, file)
        with open(file_path) as f:
            fdict = {}
            while True:
                line = f.readline()
                key, value = line.split(":")
                key = key.strip()
                value = value.strip()
                fdict[key] = value
                if key ==  "number of observers":
                    break
            '''
            if "NgDomainBridge" not in fdict["algorithm"] and "DijkstraPred" not in fdict["algorithm"]:
                continue
            '''
            
            if fdict["name"] == target_name:
                records.append(fdict)
            else:
                continue
    
            print(file_path)

            num_observers = int(fdict["number of observers"])
            route_paths = []
            for _ in range(num_observers):
                path_name = f.readline()
                latency = f.readline().split(":")[1]
                failure = f.readline().split(":")[1]
                route_paths.append([path_name, latency, failure])            
            fdict["path info"] = route_paths
  
    return records


def extractRecord(record):
    algorithm_name = record["algorithm"]
    compute_time = float(record["compute time"])
    update_entry = float(record["update entry"])
    paths = record["path info"]
    num_observers = int(record["number of observers"])
    avg_fr = 0.0
    avg_lat = 0.0
    pct_lat = []
    for i in range(num_observers):
        lat = float(paths[i][1])
        fr = float(paths[i][2])
        avg_lat += lat
        avg_fr += fr
        pct_lat.append(lat)
    avg_fr /= num_observers
    avg_lat /= num_observers
    pct_lat.sort()
    pct_50 = pct_lat[int(num_observers * 0.50)]
    pct_90 = pct_lat[int(num_observers * 0.90)]
    pct_99 = pct_lat[int(num_observers * 0.99)]
    return algorithm_name, compute_time, update_entry, avg_fr, avg_lat, pct_50, pct_90, pct_99


def getAlgoritmIdDict(file_path):
    res = {}
    with open(file_path) as f:
        lines = f.readlines()
        for line in lines:
            if line.find("#define") != -1:
                continue
            searchObj = re.search(r'CASE\((.*), (.*)\)', line)
            if searchObj:
                id = searchObj.group(1)
                name = searchObj.group(2)
                name = name.replace("Node", "")
                name = name.replace("COMMA", "_")
                name = name.replace("<", "_")
                name = name.replace(">", "")
                name = name.replace(" ", "")
                name = name.replace("Base", "")
                name = name.lower()
                res[name] = int(id)
    res["oracle"] = 0
    return res

if __name__ == "__main__":
    algorithmIdDict = getAlgoritmIdDict("main.cpp")
    target_list = []
#    target_list += ["GW-A59-3 - Transit"]
    # target_list += ["GW-A59-3 (24 hour) - Jan", "GW-A59-3 (24 hour) - Apr", "GW-A59-3 (24 hour) - Jul", "GW-A59-3 (24 hour) - Oct"]
#    target_list += ["GW-A59-2 (24 hour) - Jan", "GW-A59-2 (24 hour) - Apr", "GW-A59-2 (24 hour) - Jul", "GW-A59-2 (24 hour) - Oct"]
#    target_list += ["GW-2-1 (24 hour) - Jan", "GW-2-1 (24 hour) - Apr", "GW-2-1 (24 hour) - Jul", "GW-2-1 (24 hour) - Oct"]

    target_list += ["full example - dijkstraBase"]

    algo_mapping = {
        "DiffDomainBridge_10_3" : "DomainBridge",
        "DiffDomainBridge_10_1" : "DomainBridge_1",
        "LocalDomainBridge_10_3" : "LocalDM",
        "LocalDomainBridge_10_1" : "LocalDM_1",
        "DiffDomainBridge_8_3" : "DomainBridge",
        "DisCoRouteBase" : "DisCoRoute",
        "DijkstraPred" : "DT-DVTR",
        "MinHopCount" : "FSA-LA",
        "LBP" : "LBP",
        "DijkstraBase" : "DijkstraBase"
    }
    

    for target_name in target_list:
        records = getRecords("output", target_name)
        records.sort(key=lambda record : algorithmIdDict[record["algorithm"].replace("Base", "").lower()])
        base_upd, base_lat, base_50, base_90, base_99 = 1, 1, 1, 1, 1

        with open("summary [{}].csv".format(target_name), 'w') as f:
            f.write("name, compute_time, update_entry, avg_failure_rate, avg_latency, pct_50, pct_90, pct_99\n")
    #        f.write("algorithm name, failure rate\n")

            for record in records:
                if record["algorithm"] == "DijkstraPred":
                    _, _, base_upd, _, base_lat, base_50, base_90, base_99 = extractRecord(record)

            for record in records:
                algorithm_name, compute_time, update_entry, avg_fr, avg_lat, pct_50, pct_90, pct_99 = extractRecord(record)
                rel_upd = (update_entry - base_upd) / base_upd
                rel_lat = (avg_lat - base_lat) / base_lat
                rel_50 = (pct_50 - base_50) / base_50
                rel_90 = (pct_90 - base_90) / base_90
                rel_99 = (pct_99 - base_99) / base_99
                upd_grid = "{:.2f}".format(update_entry) + ("({:+.2%})".format(rel_upd) if rel_upd < 2 and algorithm_name != "Oracle" else "")
                algorithm_name = algo_mapping[algorithm_name]
                line = "{}, {:.2f}, {}, {:.4%}, {:.2f}({:+.2%}) , {:.2f}({:+.2%}), {:.2f}({:+.2%}), {:.2f}({:+.2%})\n".format(algorithm_name, compute_time, upd_grid, avg_fr, avg_lat, rel_lat, pct_50, rel_50, pct_90, rel_90, pct_99, rel_99)
    #            line = "{}, {:.10f}\n".format(algorithm_name, avg_fr)
                f.write(line)
                continue
                lat_data = np.array([float(path[1]) for path in record["path info"]])
                lat_freq = stats.relfreq(lat_data, defaultreallimits=(0, 300), numbins=1000)
                plot_x = lat_freq.lowerlimit + np.linspace(0, lat_freq.binsize * lat_freq.frequency.size,  lat_freq.frequency.size)
                plot_y = np.cumsum(lat_freq.frequency)
                
                pf = open("plot_data/{}.csv".format(algorithm_name), "w")
                pf.write("latency, fraction\n")
                for x, y in zip(plot_x, plot_y):
                    pf.write("{:.6f}, {:.6f}\n".format(x, y))
                pf.close()