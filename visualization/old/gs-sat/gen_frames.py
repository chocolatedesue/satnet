import os
from scipy.spatial import ConvexHull

data_dir = "/home/chenyuxuan/20230930qb_ddl/Jan1st"
output_dir_pfx = "/home/chenyuxuan/satnet/visualization/frame_data/Visibility (1day) - "
begin = 0
end = 86400
step = 600

P = 60
Q = 60
N = P * Q
gs_num = 9

vis_dir = os.path.join(data_dir, "gs-sat-visibility")
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

def getdist(a, b):
    res = 0
    for i in range(3):
        res += (a[i] - b[i]) * (a[i] - b[i])
    return res

for peek in range(0, gs_num + 1):
    sfx = "All" if peek == gs_num else "GS {}".format(peek)
    output_dir = output_dir_pfx + sfx

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    curframe = 0
    for curtime in range(begin, end, step):
        output_file = os.path.join(output_dir, "{}.txt".format(curframe))
        curframe += 1

        vis_file = os.path.join(vis_dir, "{}.txt".format(curtime))
        gs_icrs_file = os.path.join(gs_icrs_dir, "{}.csv".format(curtime))
        sat_lla_file = os.path.join(sat_lla_dir, "{}.csv".format(curtime))
        sat_icrs_file = os.path.join(sat_icrs_dir, "{}.csv".format(curtime))

        vis = load(vis_file)
        gs_lla = [[ll[1], ll[0], 0] for ll in gs_ll_raw]
        gs_icrs = load(gs_icrs_file)
        sat_lla = load(sat_lla_file)
        sat_icrs = load(sat_icrs_file)

        nodelist = []
        for i in range(N):
            nodelist.append([sat_lla[i][1], sat_lla[i][0], 0])
        for i in range(gs_num):
            nodelist.append([gs_lla[i][1], gs_lla[i][0], 4])
        
        for vis_pair in vis:
            if peek == gs_num or vis_pair[0] == peek:
                nodelist[int(vis_pair[1])][2] = 5

        edgelist = []
        for gs_id in range(gs_num):
            if peek == gs_num or gs_id == peek: 
                sat = 0
                dis = getdist(gs_icrs[gs_id], sat_icrs[0])
                for i in range(1, N):
                    curdist = getdist(gs_icrs[gs_id], sat_icrs[i])
                    if curdist < dis:
                        dis = curdist
                        sat = i
                edgelist.append([N + gs_id, sat, 5])

        for gs_id in range(gs_num):
            if peek == gs_num or gs_id == peek: 
                vis_set = []
                for vis_pair in vis:
                    if vis_pair[0] == gs_id:
                        vis_set.append(int(vis_pair[1]))
                points = [[sat_lla[sat_id][0], sat_lla[sat_id][1]] for sat_id in vis_set]
                convex = ConvexHull(points).vertices.tolist()
                
                for i in range(len(convex)):
                    edgelist.append([vis_set[convex[i]], vis_set[convex[(i + 1) % len(convex)]], 6])


        nodelist3d = sat_icrs + gs_icrs

        output = open(output_file, "w")
        output.write(" | ".join([" ".join([str(elem) for elem in node]) for node in nodelist]))
        output.write("\n")
        output.write(" | ".join([" ".join([str(elem) for elem in edge]) for edge in edgelist]))
        output.write("\n")
        output.write(" | ".join([" ".join([str(elem) for elem in node3d]) for node3d in nodelist3d]))
        output.write("\n")
        output.close()
