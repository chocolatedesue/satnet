#ifndef DIJKSTRA_HPP_
#define DIJKSTRA_HPP_

#include "discoroute.hpp"

class DijkstraNode : public DisCoRouteNode {
private:
    double proc_delay;
    double prop_delay_coef;
    double prop_speed;
    
    double getDist(int a, int b) {
        double res = 0;
        for(int i = 0; i < 3; i++) {
            double d = sat_pos->at(a)[i] - sat_pos->at(b)[i];
            res += d * d;
        }
        return sqrt(res) * 1000;
    }

protected:
    std::vector<int> vis;
    std::vector<double> dist;

    double calcuDelay(int a, int b) {
        return proc_delay + prop_delay_coef * getDist(a, b) / prop_speed * 1000;
    }
    
public:
    DijkstraNode(json config, int id, World world
        ): DisCoRouteNode(config, id, world),
        vis(N), dist(N) {
            proc_delay = config["ISL_latency"]["processing_delay"];
            prop_delay_coef = config["ISL_latency"]["propagation_delay_coef"];
            prop_speed = config["ISL_latency"]["propagation_speed"];
        }

    virtual std::string getName() override {
        return "DijkstraBase";
    }

    virtual void compute() override {
        for(int i = 0; i < N; i++) {
            vis[i] = 0;
            dist[i] = DBL_MAX;
            route_table[i] = 0;
        }

        std::priority_queue<std::pair<double, int> > pq;
        
        dist[id] = 0;
        pq.push(std::make_pair(0, id));
        while(!pq.empty()) {
            int u = pq.top().second;
            pq.pop();
            
            if(vis[u]) continue;
            vis[u] = 1;

            for(int i = 1; i <= 4; i++) {
                int v = move(u, i);
                double w = calcuDelay(u, v);
                if(dist[u] + w < dist[v]) {
                    dist[v] = dist[u] + w;
                    pq.push(std::make_pair(-dist[v], v));
                    route_table[v] = (u == id ? i : route_table[u]);
                }
            }
        }
    }
};

class DijkstraProbeNode : public DijkstraNode {
protected:
    void computeWithBannedPorts(std::vector<std::array<int, 5> > *banned_ptr) {
        auto &banned = *banned_ptr;
        for(int i = 0; i < N; i++) {
            vis[i] = 0;
            dist[i] = DBL_MAX;
            route_table[i] = 0;
        }

        std::priority_queue<std::pair<double, int> > pq;
        
        dist[id] = 0;
        pq.push(std::make_pair(0, id));
        while(!pq.empty()) {
            int u = pq.top().second;
            pq.pop();
            
            if(vis[u]) continue;
            vis[u] = 1;

            for(int i = 1; i <= 4; i++) {
                int v = move(u, i);
                if(banned[u][i]) {
                    continue;
                }
                double w = calcuDelay(u, v);
                if(dist[u] + w < dist[v]) {
                    dist[v] = dist[u] + w;
                    pq.push(std::make_pair(-dist[v], v));
                    route_table[v] = (u == id ? i : route_table[u]);
                }
            }
        }
    }

public:
    DijkstraProbeNode(json config, int id, World world
        ): DijkstraNode(config, id, world) {}
    
    virtual std::string getName() override {
        return "DijkstraProbe";
    }

    virtual void compute() override {
        computeWithBannedPorts(cur_banned);
    }
};


class DijkstraPredNode : public DijkstraProbeNode {
public:
    DijkstraPredNode(json config, int id, World world
        ): DijkstraProbeNode(config, id, world) {}

    virtual std::string getName() override {
        return "DijkstraPred";
    }

    virtual void compute() override {
        computeWithBannedPorts(futr_banned);
    }
};
#endif