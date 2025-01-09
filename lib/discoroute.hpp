#ifndef DISCOROUTE_HPP_
#define DISCOROUTE_HPP_

#include "base.hpp"

class DisCoRouteNode : public BaseNode {
protected:
    int getHopCount(int dst,int &hs,int &vs,int &hd,int &vd) {
        int src = id;
        int sx = src / Q;
        int sy = src % Q;
        int dx = dst / Q;
        int dy = dst % Q;

        int rs, ry;
        if(sx <= dx) {
            rs = dx - sx;
            ry = sy;
        } else {
            rs = P + dx - sx;
            ry = (sy + F) % Q;
        }
        int rus, rds;
        rds = (dy - ry + Q) % Q;
        rus = (ry - dy + Q) % Q;

        int ls, ly;
        if(dx <= sx) {
            ls = sx - dx;
            ly = sy;
        } else {
            ls = P + sx - dx;
            ly = (sy - F + Q) % Q;
        }
        int lus, lds;
        lds = (dy - ly + Q) % Q;
        lus = (ly - dy + Q) % Q;

        int hor_hop_count[] = {rs, rs, ls, ls};
        int ver_hop_count[] = {rus, rds, lus, lds};
        int hor_next_hop[] = {2, 2, 4, 4};
        int ver_next_hop[] = {1, 3, 1, 3};

        int min_hop_count = INT_MAX;
        
        for(int i = 0; i < 4; i++) {
            int cur_hop_count = hor_hop_count[i] + ver_hop_count[i];
            if(cur_hop_count < min_hop_count) {
                min_hop_count = cur_hop_count;
                hs = hor_hop_count[i];
                vs = ver_hop_count[i];
                hd = hor_next_hop[i];
                vd = ver_next_hop[i];
            }
        }

        return min_hop_count;
    }

    int determine(int dst,int hs,int vs,int hd,int vd) {
        auto &vel = *sat_vel;
        auto &lla = *sat_lla;

        int src = id;
        if((vel[src] > 0) == (vel[dst] > 0)) {
            int rhd = (hd == 2 ? 4 : 2);
            int src_next = move(src, hd);
            int dst_next = move(dst, rhd);

            if(vs == 0) {
                return hd;
            }

            for(int r = 0; r < hs; r++) {
                double rwd_src = fabs(lla[src][0] + lla[src_next][0]);
                double rwd_dst = fabs(lla[dst][0] + lla[dst_next][0]);

                if(rwd_src < rwd_dst) {
                    dst = dst_next;
                    dst_next = move(dst, rhd);
                } else {
                    return hd;
                }
            }

            return vd;

        } else {
            int rvd = (vd == 1 ? 3 : 1);
            int src_next = move(src, vd);
            int dst_next = move(dst, rvd);

            if(hs == 0) {
                return vd;
            }

            for(int r = 0; r < vs; r++) {
                double rwd_src = fabs(lla[src][0] + lla[src_next][0]);
                double rwd_dst = fabs(lla[dst][0] + lla[dst_next][0]);

                if(rwd_src < rwd_dst) {
                    return vd;
                } else {
                    dst = dst_next;
                    dst_next = move(dst, rvd);
                }
            }

            return hd;
        }
    }

    int calcuNextHop(int dst) {
        if(id == dst) {
            return 0;
        }
        int hs, vs, hd, vd;
        int hop_count = getHopCount(dst, hs, vs, hd, vd);
        return determine(dst, hs, vs, hd, vd);
    }

public:
    DisCoRouteNode(json config, int id, World world
        ): BaseNode(config, id, world) {}
    
    std::vector<int>& getRouteTable() {
        return route_table;
    }

    virtual std::string getName() {
        return "DisCoRouteBase";
    }
    
    virtual void compute() {
        for(int dst = 0; dst < N; dst++) {
            route_table[dst] = calcuNextHop(dst);
        }
    }    
};



class DisCoRouteProbeNode : public DisCoRouteNode {
protected:
    void computeWithBannedPorts(std::vector<std::array<int, 5> > *banned_ptr) {
        auto &banned = *banned_ptr;
        
        for(int dst = 0; dst < N; dst++) {
            if(dst == id) {
                route_table[dst] = 0;
            } else {
                int hs, vs, hd, vd;
                int hop_count = getHopCount(dst, hs, vs, hd, vd);
                if(hs == 0) {
                    route_table[dst] = vd;
                } else if(vs == 0) {
                    route_table[dst] = hd;
                } else {
                    if(banned[id][vd]) {
                        route_table[dst] = hd;
                    } else if(banned[id][hd]) {
                        route_table[dst] = vd;
                    } else {
                        route_table[dst] = determine(dst, hs, vs, hd, vd);
                    }
                }
            }
        }
    }

public:
    DisCoRouteProbeNode(json config, int id, World world
        ): DisCoRouteNode(config, id, world) {}
    
    virtual std::string getName() override {
        return "DisCoRouteProbe";
    }

    virtual void compute() override {
        computeWithBannedPorts(cur_banned);
    }
};

class DisCoRoutePredNode : public DisCoRouteProbeNode {
public:
    DisCoRoutePredNode(json config, int id, World world
        ): DisCoRouteProbeNode(config, id, world) {}

    virtual std::string getName() override {
        return "DisCoRoutePred";
    }

    virtual void compute() override {
        computeWithBannedPorts(futr_banned);
    }
};
#endif