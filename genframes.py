import summary
import json
import os
algorithmDict = summary.getAlgoritmIdDict("main.cpp")

simulationConfig = {
    "name": "GW-A59-3 Visualization",
    "constellation": {
        "num_of_orbit_planes": 60,
        "num_of_satellites_per_plane": 60,
        "relative_spacing": 1,
        "inclination": 53,
        "altitude": 550
    },
    
    "ISL_latency": {
        "processing_delay": 0.5,
        "propagation_delay_coef": 1.00,
        "propagation_speed": 299792458
    },

    "duration": 600,
    "step_length": 10,   

    "isl_state_dir": "data/xw-sat-data/isl-sun-outage",
    "sat_position_dir": "data/xw-sat-data/sat-geocentric-position",
    "sat_lla_dir": "data/xw-sat-data/sat-subpoint-position",
    "sat_velocity_dir": "data/xw-sat-data/sat-move-direction",
    "report_dir": "output"
}

frameDir = "visualization/frame_data"
serverDir = "visualization/backend"
serverConfig = {}
serverConfig["file_list"] = []

def genFrameData(src, dst, algo, filename):
    simulationConfig["visualization"] = {
        "source": src,
        "destination": dst,
        "frames_dir": frameDir,
        "file_name": filename
    }
    json.dump(simulationConfig, open("configs/visualization.json", "w"))

    algoId = algorithmDict[algo.lower()]
    serverConfig["file_list"].append(filename)
    if not os.path.exists(os.path.join(frameDir, filename)):
        os.system("./main configs/visualization.json {}".format(algoId))

def registerScenario(sname):
    fname = sname + " - .txt"
    serverConfig["file_list"].append(fname)
    serverConfig["config"][sname] = []
    
genFrameData(-1, -1, "DisCoRoute", "default.txt")

serverConfig["config"] = {}

registerScenario("Sun Outage (24 hours)")
registerScenario("Sun Outage Autumn (24 hours)")
registerScenario("Orbit")
registerScenario("Orbit Autumn")
registerScenario("Jan")
registerScenario("Apr")
registerScenario("Jul")
registerScenario("Oct")

'''
for scenario in [[825, 895], [895, -1]]:
    src = scenario[0]
    dst = scenario[1]
    assert(src != -1)
    sname = "Sat_{}_to_".format(src) + ("Sat_{}".format(dst) if dst != -1 else "all")
    algoList = ["DisCoRoutePred", "CoinFlipPred", "DijkstraPred", "DagShortPred"]
    algoList += ["MinHopCount",  "DomainRouting_6", "DomainDagShort_6"]
    algoList += ["DomainBridge_6_0", "DomainBridge_6_1", "DomainBridge_6_2"]
        
    for algo in algoList:
        fname = sname + " - {}.txt".format(algo)
        genFrameData(scenario[0], scenario[1], algo, fname)

    serverConfig["config"][sname] = algoList
'''

json.dump(serverConfig, open(os.path.join(serverDir, "config.json"), "w"))