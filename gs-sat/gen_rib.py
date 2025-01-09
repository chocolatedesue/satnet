import sys
import os
class RouteModel:
    def __init__(self, P, Q, F) -> None:
        self.P = P
        self.Q = Q
        self.F = F

    def moveHorizontally(self, cur, hd):
        assert(hd in [0, -1, 1])

        P, Q, F = self.P, self.Q, self.F

        if cur // Q == P - 1 and hd == 1:
            return (cur + Q + F) % Q
        if cur // Q == 0 and hd == -1:
            return (P - 1) * Q + (cur - Q - F) % Q
        return cur + Q * hd

    def moveVertically(self, cur, vd):
        assert(vd in [0, -1, 1])
        
        Q = self.Q

        return (cur // Q) * Q + (cur % Q + vd) % Q

    def minHopCount(self, src, dst):
        Q = self.Q
        min_hop_count = -1
        
        for hor_direction in [-1, 1]:
            for ver_direction in [-1, 1]:
                cur = src
                hor_hop_count = 0
                ver_hop_count = 0
                while cur // Q != dst // Q:
                    cur = self.moveHorizontally(cur, hor_direction)
                    hor_hop_count += 1
                while cur % Q != dst % Q:
                    cur = self.moveVertically(cur, ver_direction)
                    ver_hop_count += 1
                assert(cur == dst)
                hop_count = hor_hop_count + ver_hop_count
                if min_hop_count == -1 or hop_count < min_hop_count:
                    min_hop_count = hop_count
                    Hh = hor_hop_count
                    Hv = ver_hop_count        
                    hd = hor_direction
                    vd = ver_direction

        return Hh, Hv, hd, vd


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: please specify configuration file!")
        exit(0)

    input_filename = sys.argv[1]

    if "[Eval]" not in input_filename:
        print("Error: invalid input file!")
        exit(0)

    task_name = input_filename.replace(".txt", "")
    output_dir = task_name
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    P, Q, F = 60, 60, 1
    route_model = RouteModel(P, Q, F)

    gs_num = 9
    fwd_matrix = []
    for _ in range(P * Q):
        fwd_matrix.append([-1] * gs_num)

    fin = open(input_filename)
    for idx, line in enumerate(fin.readlines()):
        output_filename = os.path.join(output_dir, str(idx)) + ".txt"
        feeders = [int(sat_id) for sat_id in line.split(' ')]
        fout = open(output_filename, "w")
        print(output_filename)
        for cur in range(P * Q):
            nexthop = []
            for fsat in feeders:
                if fsat == -1:
                    nexthop.append(-1)
                elif cur == fsat:
                    nexthop.append(0)
                else:
                    hh, vh, hd, vd = route_model.minHopCount(cur, fsat)
                    if hh > 0:
                        nexthop.append(1 if hd == 1 else 2)
                    elif vh > 0:
                        nexthop.append(3 if vd == 1 else 4)
                    else:
                        print("Error: invalid output from route model!")
                        exit(0)
            for i in range(gs_num):
                if fwd_matrix[cur][i] != nexthop[i]:
                    fwd_matrix[cur][i] = nexthop[i]
                    fout.write("{} | {} | {}\n".format(cur, i, nexthop[i]))
        fout.close()