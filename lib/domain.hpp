#ifndef DOMAIN_HPP_
#define DOMAIN_HPP_

#include "dagshort.hpp"

template<int k>
class DomainRoutingNode : public DagShortPredNode {
private:
    std::vector<int> domain;
public:
    DomainRoutingNode(json config, int id, World world
        ): DagShortPredNode(config, id, world), domain(N) {
        for(int i = 0; i < N; i++) {
            if((i / Q) / k == (id / Q) / k) {
                domain[i] = 1;
            } else {
                domain[i] = 0;
            }
        }
    }

    std::string getName() override {
        return "DomainRouting_" + std::to_string(k);
    }

    void compute() override {
        auto &banned = *futr_banned;

        for(int i = 0; i < N; i++) {
            vis[i] = 0;
            route_table[i] = 0;
        }
        
        assert(domain[id]);

        std::queue<int> q;
        vis[id] = 1;
        q.push(id);

        int left_cost = INT_MAX;
        int left_route = 0;

        int right_cost = INT_MAX;
        int right_route = 0;

        while(!q.empty()) {
            auto u = q.front();
            q.pop();

            for(int i = 1; i <= 4; i++) {
                if(banned[u][i]) {
                    continue;
                }
                auto v = move(u, i);
                int w = (u == id ? i : route_table[u]);

                if(domain[v]) {
                    if(vis[v] == 0) {
                        vis[v] = vis[u] + 1;
                        q.push(v);
                    }
                    if(vis[v] == vis[u] + 1) {
                        if(route_table[v] == 0 || w < route_table[v]) {
                            route_table[v] = w;
                        }
                    }
                } else {
                    int banned_ports = 0;
                    for(int j = 1; j <= 4; j++) {
                        banned_ports += banned[v][j];
                    }
                    if(banned_ports >= 2) continue;

                    if(i == 2) {
                        if(vis[u] < right_cost) {
                            right_cost = vis[u];
                            right_route = w;
                        } else if(vis[u] == right_cost && w < right_route) {
                            right_route = w;
                        }
                    } else if(i == 4) {
                        if(vis[u] < left_cost) {
                            left_cost = vis[u];
                            left_route = w;
                        } else if(vis[u] == left_cost && w < left_route) {
                            left_route = w;
                        }
                    }
                }
            }
        }

        int num_dms = P / k;
        int src_dm = (id / Q) / k;
        for(int dst = 0; dst < N; dst++) {
            if(domain[dst] == 0) {
                int dst_dm = (dst / Q) / k;
                int rs = (dst_dm - src_dm + num_dms) % num_dms;
                int ls = (src_dm - dst_dm + num_dms) % num_dms;
                if(rs <= ls) {
                    route_table[dst] = right_route;
                } else {
                    route_table[dst] = left_route;
                }
            }
        }
        
    }
};


template<int k>
class DomainDagShortNode : public DagShortPredNode {
private:
    std::vector<int> domain;
public:
    DomainDagShortNode(json config, int id, World world
        ): DagShortPredNode(config, id, world), domain(N) {
            for(int i = 0; i < N; i++) {
                if((i / Q) / k == (id / Q) / k) {
                    domain[i] = 1;
                } else {
                    domain[i] = 0;
                }
            }
        }

    std::string getName() override {
        return "DomainDagShort_" + std::to_string(k);
    }

    virtual void compute() override {
        auto &banned = *futr_banned;
        for(int i = 0; i < N; i++) {
            vis[i] = 0;
            dist[i] = DBL_MAX;
            route_table[i] = 0;
        }
        
        assert(domain[id]);

        std::queue<int> q;
        dist[id] = 0;
        vis[id] = 1;
        q.push(id);

        int left_cost = INT_MAX;
        int left_route = 0;

        int right_cost = INT_MAX;
        int right_route = 0;

        while(!q.empty()) {
            auto u = q.front();
            q.pop();

            for(int i = 1; i <= 4; i++) {
                if(banned[u][i]) {
                    continue;
                }
                auto v = move(u, i);
                int w = (u == id ? i : route_table[u]);

                if(domain[v]) {
                    if(vis[v] == 0) {
                        vis[v] = vis[u] + 1;
                        q.push(v);
                    }
                    if(vis[v] == vis[u] + 1) {
                        double tmp = dist[u] + calcuDelay(u, v);
                        if(tmp < dist[v]) {
                            dist[v] = tmp;
                            route_table[v] = w;
                        }
                    }
                } else {
                    int banned_ports = 0;
                    for(int j = 1; j <= 4; j++) {
                        banned_ports += banned[v][j];
                    }
                    if(banned_ports >= 2) continue;

                    if(i == 2) {
                        if(vis[u] < right_cost) {
                            right_cost = vis[u];
                            right_route = w;
                        } else if(vis[u] == right_cost && w < right_route) {
                            right_route = w;
                        }
                    } else if(i == 4) {
                        if(vis[u] < left_cost) {
                            left_cost = vis[u];
                            left_route = w;
                        } else if(vis[u] == left_cost && w < left_route) {
                            left_route = w;
                        }
                    }
                }
            }
        }

        int num_dms = P / k;
        int src_dm = (id / Q) / k;
        for(int dst = 0; dst < N; dst++) {
            if(domain[dst] == 0) {
                int dst_dm = (dst / Q) / k;
                int rs = (dst_dm - src_dm + num_dms) % num_dms;
                int ls = (src_dm - dst_dm + num_dms) % num_dms;
                if(rs <= ls) {
                    route_table[dst] = right_route;
                } else {
                    route_table[dst] = left_route;
                }
            }
        }
        
    }
};

template<int k, int e>
class DomainBridgeNode : public DagShortPredNode {
private:
    std::vector<int> domain;
    double eps;

    void update(int v, double val, int w) {
        if(fabs(dist[v] - val) < eps) {
            if(w < route_table[v]) {
                route_table[v] = w;
            }
        } else if(val < dist[v]) {
            dist[v] = val;
            route_table[v] = w;
        }
    }

public:
    DomainBridgeNode(json config, int id, World world
        ): DagShortPredNode(config, id, world), 
        domain(N), eps(e * 0.1) {
            int num_dms = P / k;
            int src_dm = (id / Q) / k;
            for(int dst = 0; dst < N; dst++) {
                int dst_dm = (dst / Q) / k;
                if(src_dm == dst_dm) {
                    domain[dst] = 1;
                } else {
                    domain[dst] = 2;
                }
            }
        }

    std::string getName() override {
        return "DomainBridge_" + std::to_string(k) + "_" + std::to_string(e);
    }

    void compute() override {
        auto &banned = *futr_banned;
        for(int i = 0; i < N; i++) {
            vis[i] = 0;
            dist[i] = DBL_MAX;
            route_table[i] = 0;
        }

        assert(domain[id] == 1);

        std::queue<int> q;
        dist[id] = 0;
        vis[id] = 1;
        q.push(id);

        while(!q.empty()) {
            auto u = q.front();
            q.pop();

            int id_dm = (id / Q) / k;
            int u_dm = (u / Q) / k;

            for(int i = 1; i <= 4; i++) {
                if(abs(id_dm - u_dm) <= 1 && banned[u][i]) {
                    continue;
                }
                auto v = move(u, i);
                int w = (u == id ? i : route_table[u]);

                if(domain[u] == 1 && domain[v] == 1) {
                    if(vis[v] == 0) {
                        vis[v] = vis[u] + 1;
                        q.push(v);
                    }
                    if(vis[v] == vis[u] + 1) {
                        update(v, dist[u] + calcuDelay(u, v), w);
                    }
                } else if(domain[u] == 1 && domain[v] != 1) {
                    int num_banned = 0;
                    for(int j = 1; j <= 4; j++) {
                        num_banned += banned[v][j];
                    }
                    if(num_banned >= 2) continue;
                    if(vis[v] == 0) {
                        vis[v] = vis[u] + 1;
                        q.push(v);
                    }
                    if(vis[v] == vis[u] + 1) {
                        update(v, calcuDelay(u, v), w);
                    }
                } else if(domain[u] == domain[v]) {
                    if(vis[v] == 0) {
                        vis[v] = vis[u] + 1;
                        q.push(v);
                    }
                    if(vis[v] == vis[u] + 1) {
                        update(v, dist[u], w);
                    }
                }
            }
        }
    }
};
#endif