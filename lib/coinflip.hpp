#ifndef COINFLIP_HPP_
#define COINFLIP_HPP_

#include "discoroute.hpp"

class CoinFlipNode : public DisCoRouteNode {
public:
    CoinFlipNode(json config, int id, World world
        ): DisCoRouteNode(config, id, world) {}

    std::string getName() override {
        return "CoinFlipBase";
    }

    void compute() override {
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
                    if(rand() & 1) {
                        route_table[dst] = hd;
                    } else {
                        route_table[dst] = vd;
                    }
                }
            }
        }
    }
};

class CoinFlipProbeNode : public CoinFlipNode {
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
                        if(rand() & 1) {
                            route_table[dst] = hd;
                        } else {
                            route_table[dst] = vd;
                        }
                    }
                }
            }
        }
    }
public:
    CoinFlipProbeNode(json config, int id, World world
        ): CoinFlipNode(config, id, world) {}

    std::string getName() override {
        return "CoinFlipProbe";
    }

    void compute() override {
        computeWithBannedPorts(cur_banned);
    }
};

class CoinFlipPredNode : public CoinFlipProbeNode {
public:
    CoinFlipPredNode(json config, int id, World world
        ): CoinFlipProbeNode(config, id, world) {}

    std::string getName() override {
        return "CoinFlipPred";
    }

    void compute() override {
        computeWithBannedPorts(futr_banned);
    }
};

#endif