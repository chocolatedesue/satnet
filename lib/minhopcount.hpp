#ifndef MINHOPCOUNT_HPP_
#define MINHOPCOUNT_HPP_

#include "dagshort.hpp"

class MinHopCountNode : public DagShortPredNode {
public:
    MinHopCountNode(json config, int id, World world
        ): DagShortPredNode(config, id, world) {}

    std::string getName() override {
        return "MinHopCount";
    }

    void compute() override {
        auto &banned = *futr_banned;

        for(int i = 0; i < N; i++) {
            vis[i] = 0;
            route_table[i] = 0;
        }

        std::queue<int> q;
        vis[id] = 1;
        q.push(id);

        while(!q.empty()) {
            auto u = q.front();
            q.pop();

            for(int i = 1; i <= 4; i++) {
                if(banned[u][i]) {
                    continue;
                }
                auto v = move(u, i);
                if(vis[v] == 0) {
                    vis[v] = vis[u] + 1;
                    q.push(v);
                }
                if(vis[v] == vis[u] + 1) {
                    int w = (u == id ? i : route_table[u]);
                    if(route_table[v] == 0 || w < route_table[v]) {
                        route_table[v] = w;
                    }
                }
            }
        }
    }
};

#endif