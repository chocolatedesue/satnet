/*
    Next Generation Domain Algorithms 
*/

#ifndef NG_DOMAIN_HPP
#define NG_DOMAIN_HPP

#include "base.hpp"

const double pi = acos(-1);

template<int K, int M>
class NgDomainBridge : public BaseNode {
private:
    std::vector<int> domain;

    std::vector<int> hop_count;
    std::vector<double> metric;
    std::vector<int> next_hop;

    double alpha;
    double proc_delay;
    double prop_delay_coef;
    double prop_speed;

    int rev[5], ord[5];

    double getBridge(int a) {
        double lat = sat_lla->at(a)[0];
        double theta = lat / 180 * pi;
        return cos(theta);
    }

    int getLoopDist(int x, int y) {
        return std::min((y - x + K) % K, (x - y + K) % K);
    }

    /*
    double getDist(int a, int b) {
        double res = 0;
        for(int i = 0; i < 3; i++) {
            double d = sat_pos->at(a)[i] - sat_pos->at(b)[i];
            res += d * d;
        }
        return sqrt(res) * 1000;
    }
    
    double calcuDelay(int a, int b) {
        return proc_delay + prop_delay_coef * getDist(a, b) / prop_speed * 1000;
    }
    */

    void update(int v, double val, int w) {
       if(fabs(val - metric[v]) <= ((1 - cos(alpha)) / M)) {
            if(w == route_table[v]) {
                next_hop[v] = w;
            }
        } else if(val < metric[v]) {
            metric[v] = val;
            next_hop[v] = w;
        } 
    }

public:
    NgDomainBridge(json config, int id, World world): BaseNode(config, id, world),
        domain(N), hop_count(N), metric(N), next_hop(N) {
        double inclination = config["constellation"]["inclination"];
        alpha = inclination / 180 * pi;

        for(int i = 0; i < N; i++) {
            domain[i] = (i / Q) / (P / K);
        }

        proc_delay = config["ISL_latency"]["processing_delay"];
        prop_delay_coef = config["ISL_latency"]["propagation_delay_coef"];
        prop_speed = config["ISL_latency"]["propagation_speed"];

        rev[1] = 3, rev[3] = 1;
        rev[2] = 4, rev[4] = 2;

        ord[1] = 1, ord[2] = 3;
        ord[3] = 2, ord[4] = 4;
    }

    std::string getName() override {
        return "NgDomainBridge_" + std::to_string(K) + "_" + std::to_string(M);
    }

    void compute() override {
        auto &banned = *futr_banned;
        for(int i = 0; i < N; i++) {
            hop_count[i] = -1;
            metric[i] = DBL_MAX;
            next_hop[i] = 0;
        }

        std::queue<int> q;
        hop_count[id] = 0;
        metric[id] = 0;
        q.push(id);

        while(!q.empty()) {
            auto u = q.front();
            q.pop();

            for(int k = 1; k <= 4; k++) {
                auto i = ord[k];
                auto v = move(u, i);
                auto w = (u == id ? i : next_hop[u]);

                if(banned[u][i]) {
                    continue;
                }

                if(domain[u] != domain[v]) {
                    int du = getLoopDist(domain[id], domain[u]);
                    int dv = getLoopDist(domain[id], domain[v]);
                    if(du >= dv) {
                        continue;
                    }
                }

                if(hop_count[v] == -1) {
                    hop_count[v] = hop_count[u] + 1;
                    q.push(v);
                }

                if(hop_count[v] == hop_count[u] + 1) {
                    if(domain[u] == domain[id]) {
                        if(domain[v] == domain[id]) {
                            update(v, metric[u] + (i % 2 == 0 ? getBridge(u) : 1), w);
                        } else {
                            update(v, getBridge(u), w);
                        }
                    } else {
                        if(domain[v] != domain[id]) {
                            update(v, metric[u], w);
                        }
                    }
                }
            }
        }

        for(int i = 0; i < N; i++) {
            route_table[i] = next_hop[i];
        }
    }
};



template<int K, int M>
class DiffDomainBridge : public BaseNode {
private:
    std::vector<int> domain;
    std::vector<int> hop_count;

    std::vector<double> metric[3];
    std::vector<int> next_hop[3];

    double getBridge(int a) {
        double lat = sat_lla->at(a)[0];
        double theta = lat / 180 * pi;
        return cos(theta);
    }

    int getLoopDist(int x, int y) {
        return std::min((y - x + K) % K, (x - y + K) % K);
    }

    void update(int k, int v, double val, int w) {
        if(val < metric[k][v]) {
            metric[k][v] = val;
            next_hop[k][v] = w;
        } 
    }

public:
    DiffDomainBridge(json config, int id, World world): BaseNode(config, id, world),
        domain(N), hop_count(N) {
        for(int i = 0; i < N; i++) {
            domain[i] = (i / Q) / (P / K);
        }
        for(int k = 0; k < 3; k++) {
            metric[k].resize(N);
            next_hop[k].resize(N);
        }
    }

    std::string getName() override {
        return "DiffDomainBridge_" + std::to_string(K) + "_" + std::to_string(M);
    }

    void compute() override {
        auto &banned = *futr_banned;
        for(int i = 0; i < N; i++) {
            hop_count[i] = -1;
        }

        for(int k = 0; k < 3; k++) {
            for(int i = 0; i < N; i++) {
                metric[k][i] = DBL_MAX;
                next_hop[k][i] = 0;
            }
        }

        std::queue<int> q;

        hop_count[id] = 0;
        metric[0][id] = 0;
        next_hop[0][id] = 0;
        q.push(id);

        while(!q.empty()) {
            auto u = q.front();
            q.pop();

            for(int i = 1; i <= 4; i++) {
                auto v = move(u, i);

                if(banned[u][i]) {
                    continue;
                }

                if(domain[u] != domain[v]) {
                    int du = getLoopDist(domain[id], domain[u]);
                    int dv = getLoopDist(domain[id], domain[v]);
                    if(du >= dv) {
                        continue;
                    }
                }

                if(hop_count[v] == -1) {
                    hop_count[v] = hop_count[u] + 1;
                    q.push(v);
                }

                if(hop_count[v] == hop_count[u] + 1) {
                    if(domain[u] == domain[id]) {
                        auto w = (u == id ? i : next_hop[0][u]);
                        if(domain[v] == domain[id]) {
                            update(0, v, metric[0][u] + (i % 2 == 0 ? getBridge(u) : 1), w);
                        } else {
                            update(1, v, getBridge(u), w);
                            update(2, v, hop_count[u], w);
                        }
                    } else {
                        if(domain[v] != domain[id]) {
                            update(1, v, metric[1][u], next_hop[1][u]);
                            update(2, v, metric[2][u], next_hop[2][u]);
                        }
                    }
                }
            }
        }

        for(int i = 0; i < N; i++) {
            if(domain[i] == domain[id]) {
                route_table[i] = next_hop[0][i];
            } else if(getLoopDist(domain[id], domain[i]) % M == 0) {
                route_table[i] = next_hop[1][i];
            } else {
                route_table[i] = next_hop[2][i];
            }
        }
    }
};



template<int K, int M>
class LocalDomainBridge : public BaseNode {
private:
    std::vector<int> domain;
    std::vector<int> hop_count;

    std::vector<double> metric[3];
    std::vector<int> next_hop[3];

    double getBridge(int a) {
        double lat = sat_lla->at(a)[0];
        double theta = lat / 180 * pi;
        return cos(theta);
    }

    int getLoopDist(int x, int y) {
        return std::min((y - x + K) % K, (x - y + K) % K);
    }

    void update(int k, int v, double val, int w) {
        if(val < metric[k][v]) {
            metric[k][v] = val;
            next_hop[k][v] = w;
        } 
    }

public:
    LocalDomainBridge(json config, int id, World world): BaseNode(config, id, world),
        domain(N), hop_count(N) {
        for(int i = 0; i < N; i++) {
            domain[i] = (i / Q) / (P / K);
        }
        for(int k = 0; k < 3; k++) {
            metric[k].resize(N);
            next_hop[k].resize(N);
        }
    }

    std::string getName() override {
        return "LocalDomainBridge_" + std::to_string(K) + "_" + std::to_string(M);
    }

    void compute() override {
        auto &banned = *futr_banned;
        for(int i = 0; i < N; i++) {
            hop_count[i] = -1;
        }

        for(int k = 0; k < 3; k++) {
            for(int i = 0; i < N; i++) {
                metric[k][i] = DBL_MAX;
                next_hop[k][i] = 0;
            }
        }

        std::queue<int> q;

        hop_count[id] = 0;
        metric[0][id] = 0;
        next_hop[0][id] = 0;
        q.push(id);

        while(!q.empty()) {
            auto u = q.front();
            q.pop();

            for(int i = 1; i <= 4; i++) {
                auto v = move(u, i);

                if((domain[u] == domain[id] || domain[v] == domain[id]) && banned[u][i]) {
                    continue;
                }

                if(domain[u] != domain[v]) {
                    int du = getLoopDist(domain[id], domain[u]);
                    int dv = getLoopDist(domain[id], domain[v]);
                    if(du >= dv) {
                        continue;
                    }
                }

                if(hop_count[v] == -1) {
                    hop_count[v] = hop_count[u] + 1;
                    q.push(v);
                }

                if(hop_count[v] == hop_count[u] + 1) {
                    if(domain[u] == domain[id]) {
                        auto w = (u == id ? i : next_hop[0][u]);
                        if(domain[v] == domain[id]) {
                            update(0, v, metric[0][u] + (i % 2 == 0 ? getBridge(u) : 1), w);
                        } else {
                            update(1, v, getBridge(u), w);
                            update(2, v, hop_count[u], w);
                        }
                    } else {
                        if(domain[v] != domain[id]) {
                            update(1, v, metric[1][u], next_hop[1][u]);
                            update(2, v, metric[2][u], next_hop[2][u]);
                        }
                    }
                }
            }
        }

        for(int i = 0; i < N; i++) {
            if(domain[i] == domain[id]) {
                route_table[i] = next_hop[0][i];
            } else if(getLoopDist(domain[id], domain[i]) % M == 0) {
                route_table[i] = next_hop[1][i];
            } else {
                route_table[i] = next_hop[2][i];
            }
        }
    }
};

#endif

