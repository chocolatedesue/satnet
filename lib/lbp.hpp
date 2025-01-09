#ifndef LBP_HPP_
#define LBP_HPP_

#include "discoroute.hpp"

class LbpNode : public DisCoRouteNode {
private:
    std::vector<double> Lr;

    int getRegionId(int sat_id) {
        double latitude = sat_lla->at(sat_id)[0];
        for(int i = 0; i <= (Q + 1) / 2 + 1; i++) {
            if(Lr[i] <= latitude && latitude < Lr[i + 1]) {
                return i;
            }
        }
        assert(false);
    }

    int getMovingDirection(int sat_id) {
        return sat_vel->at(sat_id) > 0 ? 1 : 0;
    }

    int computeRoute(int dst) {
        int src = id;
        int as = src / Q;
        int rs = getRegionId(src);
        int ps = getMovingDirection(src);
        int ad = dst / Q;
        int rd = getRegionId(dst);
        int pd = getMovingDirection(dst);
        int dt_a = ad - as;
        int dt_r = rd - rs;

        if(src == dst) {
            return 0;
        }
        if(ps == pd) {
            if(as == ad) {
                if(dt_r == 0) {
                    return calcuNextHop(dst);
                } else if((dt_r > 0 && ps == 1) || (dt_r < 0 && ps == 0)) {
                    return 3;
                } else {
                    return 1;
                }
            } else {
                if((ad > as && dt_a > P / 2 ) || (ad < as && -dt_a <= P / 2)) {
                    return 4;
                } else {
                    return 2;
                }
            }
        } else {
            int dis_north = 2 * ((Q + 1) / 2 + 1) - rs - rd;
            int dis_south = rs + rd;
            if((dis_north == dis_south) || (dis_north < dis_south && ps == 1) || (dis_north > dis_south && ps == 0)) {
                return 3;
            } else {
                return 1;
            }
        }
    }

public:
    LbpNode(json config, int id, World world
        ): DisCoRouteNode(config, id, world) {
            double inclination = config["constellation"]["inclination"];
            double pi = acos(-1);
            double alpha = inclination / 180 * pi;
            Lr.push_back(-90.0);
            for(int i = 0; i <= (Q + 1) / 2; i++) {
                Lr.push_back(asin(sin(alpha) * sin(-pi / 2 + i * 2 * pi / Q)) * 180 / pi);
            }
            Lr.push_back(90.0);
        }

    std::string getName() override {
        return "LBP";
    }

    void compute() override {
        for(int i = 0; i < N; i++) {
            route_table[i] = computeRoute(i);
        }
    }
};

#endif
