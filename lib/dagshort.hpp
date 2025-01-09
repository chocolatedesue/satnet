#ifndef DAGSHORT_HPP_
#define DAGSHORT_HPP_

#include "dijkstra.hpp"

class DagShortNode : public DijkstraNode {
public:
    DagShortNode(json config, int id, World world
        ): DijkstraNode(config, id, world) {}

    virtual std::string getName() override {
        return "DagShortBase";
    }

    virtual void compute() override {
        for(int i = 0; i < N; i++) {
            vis[i] = 0;
            dist[i] = DBL_MAX;
            route_table[i] = 0;
        }

        std::queue<int> q;
        dist[id] = 0;
        vis[id] = 1;
        q.push(id);

        while(!q.empty()) {
            auto u = q.front();
            q.pop();

            for(int i = 1; i <= 4; i++) {
                auto v = move(u, i);
                if(vis[v] == 0) {
                    vis[v] = vis[u] + 1;
                    q.push(v);
                }
                if(vis[v] == vis[u] + 1) {
                    double w = calcuDelay(u, v);
                    if(dist[u] + w < dist[v]) {
                        dist[v] = dist[u] + w;
                        route_table[v] = (u == id ? i : route_table[u]);
                    }
                }
            }
        }
    }
};

class DagShortProbeNode : public DagShortNode {
protected:
    virtual void computeWithBannedPorts(std::vector<std::array<int, 5> > *banned_ptr)  {
        auto &banned = *banned_ptr;
        for(int i = 0; i < N; i++) {
            vis[i] = 0;
            dist[i] = DBL_MAX;
            route_table[i] = 0;
        }

        std::queue<int> q;
        dist[id] = 0;
        vis[id] = 1;
        q.push(id);

        while(!q.empty()) {
            auto u = q.front();
            q.pop();

            for(int i = 1; i <= 4; i++) {
                auto v = move(u, i);
                if(banned[u][i]) {
                    continue;
                }
                if(vis[v] == 0) {
                    vis[v] = vis[u] + 1;
                    q.push(v);
                }
                if(vis[v] == vis[u] + 1) {
                    double w = calcuDelay(u, v);
                    if(dist[u] + w < dist[v]) {
                        dist[v] = dist[u] + w;
                        route_table[v] = (u == id ? i : route_table[u]);
                    }
                }
            }
        }
    }

public:
    DagShortProbeNode(json config, int id, World world
        ): DagShortNode(config, id, world) {}

    virtual std::string getName() override {
        return "DagShortProbe";
    }

    virtual void compute() override {
        computeWithBannedPorts(cur_banned);
    }
};

class DagShortPredNode : public DagShortProbeNode {
public:
    DagShortPredNode(json config, int id, World world
        ): DagShortProbeNode(config, id, world) {}

    virtual std::string getName() override {
        return "DagShortPred";
    }

    virtual void compute() override {
        computeWithBannedPorts(futr_banned);
    }
};

template<int norm>
class DagShortNormNode : public DagShortPredNode {
public:
    DagShortNormNode(json config, int id, World world
        ): DagShortPredNode(config, id, world) {}

    std::string getName() override {
        return "DagShortNorm_" + std::to_string(norm);
    }

    void compute() override {
        auto &banned = *futr_banned;
        for(int i = 0; i < N; i++) {
            vis[i] = 0;
            dist[i] = DBL_MAX;
            route_table[i] = 0;
        }

        std::queue<int> q;
        dist[id] = 0;
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
                    double w = ceil(calcuDelay(u, v) / (norm * 0.1));
                    int fwd = (u == id ? i : route_table[u]);
                    if(dist[u] + w < dist[v]) {
                        dist[v] = dist[u] + w;
                        route_table[v] = fwd;
                    } else if(dist[u] + w == dist[v] && fwd < route_table[v]) {
                        route_table[v] = fwd;
                    }
                }
            }
        }
    }
};


#endif