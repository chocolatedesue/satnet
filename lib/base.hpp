#ifndef BASE_HPP_
#define BASE_HPP_

#include <vector>
#include <array>
#include <string>
#include "utils.hpp"
#include "json.hpp"

class BaseNode {
protected:
    int id;
    int P, Q, F, N;
    std::vector<std::array<int, 5> > *cur_banned;
    std::vector<std::array<int, 5> > *futr_banned;
    std::vector<std::array<double, 3> > *sat_pos;
    std::vector<std::array<double, 3> > *sat_lla;
    std::vector<double> *sat_vel;

    std::vector<int> route_table;

    int move(int id,int dir) {
        int x = id / Q;
        int y = id % Q;
        if(dir == 1) {
            y = (y - 1 + Q) % Q;
        } else if(dir == 2) {
            if(x == P - 1) {
                x = 0;
                y = (y + F) % Q;
            } else {
                x = x + 1;
            }
        } else if(dir == 3) {
            y = (y + 1) % Q;
        } else if(dir == 4) {
            if(x == 0) {
                x = P - 1;
                y = (y - F + Q) % Q;
            } else {
                x = x - 1;
            }
        } else {
            // do nothing   
        }
        return x * Q + y;
    }

public:
    BaseNode(nlohmann::json config, int id, World world
        ): id(id) {
        P = config["constellation"]["num_of_orbit_planes"];
        Q = config["constellation"]["num_of_satellites_per_plane"];
        F = config["constellation"]["relative_spacing"];
        N = P * Q;
        
        cur_banned = world.cur_banned;
        futr_banned = world.futr_banned;
        sat_pos = world.sat_pos;
        sat_lla = world.sat_lla;
        sat_vel = world.sat_vel;

        route_table = std::vector<int>(N);
    }
    
    virtual std::string getName() {
        return "Base";
    }
    
    virtual void compute() {
        for(int dst = 0; dst < N; dst++) {
            if(dst == id) {
                route_table[dst] = 0;
            } else if(dst / Q == id / Q) {
                route_table[dst] = 1;
            } else {
                route_table[dst] = 2;
            }
        }
    }    

    std::vector<int>& getRouteTable() {
        return route_table;
    }
};

#endif