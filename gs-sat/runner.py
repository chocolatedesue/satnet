import sys
import json
import max_visible_time
import min_distance
import max_matching
import dp_scheduler
import common
import time
import gs_state_aware_matching

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Error: please specify configuration file!")
        exit(0)
    
    json_f = open(sys.argv[1])
    config = json.loads(json_f.read())

    if len(sys.argv) < 3:
        print("Error: please specify an algorithm!")
        exit(0)

    begin_time = time.time()
    algo = sys.argv[2]
    if algo == "max_visible_time":
        res = max_visible_time.run(config)
    elif algo == "min_distance":
        res = min_distance.run(config)
    elif algo == "max_matching":
        res = max_matching.run(config)
    elif algo == "dp_scheduler":
        res = dp_scheduler.run(config)
    elif algo == "gs_state_aware_matching":
        res = gs_state_aware_matching.run(config)
    else:
        print("Error: invalid algorithm name!")
        exit(0)

    common.output(config, res, algo)
    common.eval(config, res, algo)

    end_time = time.time()

    print("Elapsed time: {:.2f}s".format(end_time - begin_time))