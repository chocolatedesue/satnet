import os
import sys

begin = 0
end = 86400
step = 10
ant_num = 1
gs_num = 1
multi_ant_gs_num = 0

for date in ["Jan1st", "Apr1st", "Jul1st", "Oct1st"]:
    
    input_dir = "/home/chenyuxuan/20231027qb-gs-sat/{}/gs-sat-visibility".format(date)
    output_dir = "/home/chenyuxuan/satnet/data/gs-sat-bj-only/{}".format(date)

    mapping = []
    cnt = 0
    for i in range(gs_num):
        cur = []
        if i < multi_ant_gs_num:
            for _ in range(ant_num):
                cur.append(cnt)
                cnt += 1
        else:
            cur.append(cnt)
            cnt += 1
        mapping.append(cur)

    for t in range(begin, end, step):
        input_file = os.path.join(input_dir, "{}.txt".format(t))
        output_file = os.path.join(output_dir, "{}.txt".format(t))
        fin = open(input_file)
        fout = open(output_file, "w")
        for line in fin.readlines():
            gs_id, sat_id, pitch, yaw, dist = line.split()
            gs_id = int(gs_id)
            if gs_id == 0:
                fout.write(line)
            
            '''
            for new_gs_id in mapping[gs_id]:
                fout.write("{} {} {} {} {}\n".format(new_gs_id, sat_id, pitch, yaw, dist))
            '''
        fin.close()
        fout.close()
