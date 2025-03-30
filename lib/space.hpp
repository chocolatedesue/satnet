#ifndef SATSIM_SPACE_HPP_
#define SATSIM_SPACE_HPP_

#include <bits/stdc++.h>
#include <sys/stat.h>
#include <sys/types.h>
#include "dirent.h"

#include "utils.h"

#include "json.hpp"
using json = nlohmann::json;

#include "base.hpp"
#include "discoroute.hpp"
#include "coinflip.hpp"
#include "dijkstra.hpp"
#include "dagshort.hpp"
#include "domain.hpp"
#include "minhopcount.hpp"
#include "lbp.hpp"
#include "ngdomain.hpp"

class Average {
private:
    double sum;
    int cnt;

public:
    Average() {
        sum = 0.0, cnt = 0;
    }
    void add(double val) {
        sum += val, cnt++;
    }
    double getResult() {
        return cnt ? sum / cnt : 0;
    }
};

template<class T>
class SpaceSimulation {
private:
    std::string name;
    std::string algorithm;

    int P, Q, F, N;

    double proc_delay;
    double prop_delay_coef;
    double prop_speed;

    int start_time;
    int step;
    int duration;
    int update_period;
    int refresh_period;

    int num_observers;
    unsigned seed;
    std::vector<std::pair<int,int> > latency_observers;

    std::vector<T> nodes;
    std::vector<std::vector<int> > route_tables;

    Average compute_time_result;
    Average update_entry_result;
    std::vector<Average> latency_results;
    std::vector<Average> failure_rates;

    std::string isl_state_dir;
    std::string sat_pos_dir;
    std::string sat_lla_dir;
    std::string sat_vel_dir;
    std::string report_dir;
    std::string frames_dir;
    std::string dawn_dust_dir;
    std::string dawn_dusk_icrs_dir;
    std::string frame_scenario;

    std::vector<std::array<int, 5> > cur_banned;
    std::vector<std::array<int, 5> > futr_banned;
    std::vector<std::array<double, 3> > sat_pos;
    std::vector<std::array<double, 3> > sat_lla;
    std::vector<double> sat_vel;


    char report_filename[100];

    double run_start;
    int cur_time;
    
    bool output_frames;
    int vis_src, vis_dst;
    int frame_id = 0;

    int path_timer;
    std::vector<int> path_vis;
    
    std::vector<int> dump_rib;

    int show_diff_table;

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

    double getDist(int a, int b) {
        double res = 0;
        for(int i = 0; i < 3; i++) {
            double d = sat_pos[a][i] - sat_pos[b][i];
            res += d * d;
        }
        return sqrt(res) * 1000;
    }

    double calcuDelay(int a, int b) {
        return proc_delay + prop_delay_coef * getDist(a, b) / prop_speed * 1000;
    }

    std::pair<double, bool> computeLatency(int src, int dst) {
        int cur = src;
        double latency = 0;
        bool success = true;

        if(path_timer >= 1e8) {
            for(int i = 0; i < N; i++) {
                path_vis[i] = 0;
            }
            path_timer = 0;
        }
        ++path_timer;
        while(cur != dst) {
            auto &route_table = route_tables[cur];
            int next_hop = route_table[dst];
            if(next_hop == 0 || cur_banned[cur][next_hop] || path_vis[cur] == path_timer) {
                success = false;
                break;
            }
            path_vis[cur] = path_timer;
            int neigh = move(cur, next_hop);
            double one_hop_latency = calcuDelay(cur, neigh);
            latency += one_hop_latency;
            cur = neigh;
        }
        return std::make_pair(latency, success);
    }

    bool getPort(int u,int v,int &u_port,int &v_port) {
        u_port = v_port = 0;
        for(int i = 1; i <= 4; i++) {
            if(move(u, i) == v) {
                u_port = i;
            }
            if(move(v, i) == u) {
                v_port = i;
            }
            /*
            std::cerr << u << ' ' << i << ' ' << move(u, i) << std::endl;
            std::cerr << v << ' ' << i << ' ' << move(v, i) << std::endl;
            */
        }
        return u_port != 0 && v_port != 0;
    }

    void readIslStateFlie(int time, std::vector<std::array<int, 5> > &banned) {
        std::string isl_state_filename = isl_state_dir + "/" + std::to_string(time) + ".txt";
        auto ifs = std::ifstream(isl_state_filename);
        int u, v;
        while(ifs >> u >> v) {
            int u_port, v_port;
//            std::cerr << u << ' ' << v << std::endl;
            assert(getPort(u, v, u_port, v_port));
            banned[u][u_port] = 1;
            banned[v][v_port] = 1;
        }            
    }

    void clearIslState(std::vector<std::array<int, 5> > &banned) {
        for(int i = 0; i < N; i++) {
            for(int j = 0; j <= 4; j++) {
                banned[i][j] = 0;
            }
        }
    }

    void load_cur_banned() {
        clearIslState(cur_banned);
        readIslStateFlie(cur_time, cur_banned);
    }

    void load_futr_banned() {
        clearIslState(futr_banned);
        for(int futr_time = cur_time;
            futr_time < cur_time + update_period && futr_time < start_time + duration;
            futr_time += step) {
            readIslStateFlie(futr_time, futr_banned);
        }
    }

    void report() {
        double past_time = cur_time - start_time + 1;
        double rw_time = (clock() -  run_start) / CLOCKS_PER_SEC;
        double eta = rw_time / past_time * std::max(duration - past_time, 0.0);
        std::cerr << "Real-world time: " << rw_time << std::endl;
        std::cerr << "Simulation time: " << cur_time << std::endl;
        std::cerr << "ETA: " << eta << std::endl;


        auto open_path = report_dir + "/" + std::string(report_filename);
        auto fout = fopen(open_path.c_str(), "w");
        fprintf(fout, "name: %s\n", name.c_str());
        fprintf(fout, "algorithm: %s\n", algorithm.c_str());
        fprintf(fout, "node type: %s\n", typeid(T).name());
        fprintf(fout, "simulation time: %d\n", cur_time);
        fprintf(fout, "real-world time: %f\n", rw_time);
        fprintf(fout, "estimated time of arrival: %f\n", eta);
        fprintf(fout, "compute time: %f\n", compute_time_result.getResult());
        fprintf(fout, "update entry: %f\n", update_entry_result.getResult());
        fprintf(fout, "number of observers: %d\n", num_observers);
        for(int i = 0; i < num_observers; i++) {
            auto src = latency_observers[i].first;
            auto dst = latency_observers[i].second; 
            auto latency = latency_results[i].getResult();
            auto failure_rate = failure_rates[i].getResult();
            fprintf(fout, "route path [%d, %d]\n\tlatency: %f\n\tfailure rate: %f\n", src, dst, latency, failure_rate);
        }
        fclose(fout);
    }

    void loadObserverConfig(std::string observer_config_path) {
        // check if the file exists
        struct stat buffer;
        if (stat(observer_config_path.c_str(), &buffer) != 0) {
            std::cerr << "Observer config file not found: " << observer_config_path << std::endl;
            exit(1);
        }
        auto ifs = std::ifstream(observer_config_path);
        ifs >> num_observers;
        for(int i = 0; i < num_observers; i++) {
            int src, dst;
            ifs >> src >> dst;
            latency_observers.push_back(std::make_pair(src, dst));
        }
    }

public:
    SpaceSimulation(std::string config_file_name) {
        auto config = json::parse(std::ifstream(config_file_name));

        name = config["name"];
        P = config["constellation"]["num_of_orbit_planes"];
        Q = config["constellation"]["num_of_satellites_per_plane"];
        F = config["constellation"]["relative_spacing"];
        N = P * Q;

        proc_delay = config["ISL_latency"]["processing_delay"];
        prop_delay_coef = config["ISL_latency"]["propagation_delay_coef"];
        prop_speed = config["ISL_latency"]["propagation_speed"];

        step = config["step_length"];
        duration = config["duration"];
        if(config.count("update_period")) {
            update_period = config["update_period"];
        } else {
            update_period = duration;
        }
        if(config.count("refresh_period")) {
            refresh_period = config["refresh_period"];
        } else {
            refresh_period = update_period;
        }
        if(config.count("start_time")) {
            start_time = config["start_time"];
        } else {
            start_time = 0;
        }

        isl_state_dir = config["isl_state_dir"];
        sat_pos_dir = config["sat_position_dir"];
        sat_lla_dir = config["sat_lla_dir"];
        sat_vel_dir = config["sat_velocity_dir"];
        report_dir = config["report_dir"];
        if(config.count("dawn_dusk_dir")) {
            dawn_dust_dir = config["dawn_dusk_dir"];
        }
        if(config.count("dawn_dusk_icrs_dir")) {
            dawn_dusk_icrs_dir = config["dawn_dusk_icrs_dir"];
        }
        

        if(config.count("visualization")) {
            output_frames = true;
            vis_src = config["visualization"]["source"];
            vis_dst = config["visualization"]["destination"];
            frames_dir = config["visualization"]["frames_dir"];
            frame_scenario = config["visualization"]["scenario"];
            if(config["visualization"].count("diff_table")) {
                show_diff_table = config["visualization"]["diff_table"];
            } else {
                show_diff_table = 0;
            }
        } else {
            output_frames = false;
        }

        // if(config.count("num_latency_observers")) {
        //     num_observers = config["num_latency_observers"];
        //     if(num_observers == -1) {
        //         for(int i = 0; i < N; i++) {
        //             for(int j = 0; j < N; j++) {
        //                 if(i != j) {
        //                     latency_observers.push_back(std::make_pair(i, j));
        //                 }
        //             }
        //         }
        //         num_observers = latency_observers.size();
        //     } else {
        //         seed = config["random_seed"];
        //         srand(seed);
        //         for(int i = 0; i < num_observers; i++) {
        //             int u, v;
        //             do {
        //                 u = rand() % N;
        //                 v = rand() % N;
        //             } while(u == v);
        //             latency_observers.push_back(std::make_pair(u, v));
        //         }
        //     }
        // } else {
        //     num_observers = 0;
        // }

        if (!config.count("observer_config_path")) {
            std::cout << "No observer_config_path found in config json" << std::endl;
            exit(1);
        }

        seed = 42;
        srand(seed);

        loadObserverConfig(config["observer_config_path"]);

        

        dump_rib = std::vector<int>(N, 0);
        if(config.count("dump_rib_nodes")) {
            std::vector<int> node_list = config["dump_rib_nodes"];
            for(auto node : node_list) {
                dump_rib[node] = 1;
            }
        }

        World world(&cur_banned, &futr_banned, &sat_pos, &sat_lla, &sat_vel);
        for(int i = 0; i < N; i++) {
            nodes.push_back(T(config, i, world));
        }
        algorithm = nodes[0].getName();

        cur_banned = std::vector<std::array<int, 5> >(N);
        futr_banned = std::vector<std::array<int, 5> >(N);
        sat_pos = std::vector<std::array<double, 3> >(N);
        sat_lla = std::vector<std::array<double, 3> >(N);
        sat_vel = std::vector<double>(N);
        route_tables = std::vector<std::vector<int> >(N, std::vector<int>(N));

        path_timer = 0;
        path_vis = std::vector<int>(N);

        latency_results = std::vector<Average>(num_observers);
        failure_rates = std::vector<Average>(num_observers);

        auto now = std::chrono::system_clock::now();
        time_t utc_tm = std::chrono::system_clock::to_time_t(now);
        utc_tm += 8 * 60 * 60;

        auto my_tm = localtime(&utc_tm);
        sprintf(report_filename, "report [%s] %s.txt",
            name.c_str(), algorithm.c_str());
        /*
        sprintf(report_filename, "report [%s] %s %d-%02d-%02d %02d:%02d:%02d.txt",
            name.c_str(), algorithm.c_str(), my_tm->tm_year + 1900, my_tm->tm_mon + 1, my_tm->tm_mday,
            my_tm->tm_hour, my_tm->tm_min, my_tm->tm_sec);
        */
    }


    void run() {
        cur_time = start_time;
        run_start = clock();
        

        for(; cur_time < start_time + duration; cur_time += step) {
            load_cur_banned();
            load_sat_pos();
            load_sat_lla();
            load_sat_vel();

            if(cur_time % update_period == 0) {
                load_futr_banned();
                for(int i = 0; i < N; i++) {
                    auto &node = nodes[i];
                    auto &cur_table = route_tables[i];

                    auto compute_start = clock();
                    node.compute();
                    auto elpased_s = (clock() -  compute_start) * 1.0 / CLOCKS_PER_SEC;
                    auto elpased_ms = elpased_s * 1000;
                    compute_time_result.add(elpased_ms);
                    
                    auto &new_table = node.getRouteTable();
                    int diff = 0;
                    for(int j = 0; j < N; j++) {
                        if(cur_table[j] != new_table[j]) {
                            cur_table[j] = new_table[j];
                            diff++;
                        }
                    }
                    if(cur_time != 0) {
                        update_entry_result.add(diff);
                    }

                    if(dump_rib[i]) {
                        save_rib(cur_table, i);
                    }
                }
            }

            if(cur_time % refresh_period == 0) {
                report();
            }

            if(output_frames) {
                dump_nodes();
                dump_edges();
                
                if(vis_dst != -1) {
                    dump_path(vis_src, vis_dst);
                } else if(vis_src != -1) {
                    dump_table(vis_src);
                } else {
                    dump_dawn_dust_line();
                }
                save_frame();
            }


            for(int i = 0; i < num_observers; i++) {
                auto src = latency_observers[i].first;
                auto dst = latency_observers[i].second;
                auto [latency, success] = computeLatency(src, dst);
                if(success) {
                    latency_results[i].add(latency);
                    failure_rates[i].add(0);
                } else {
                    failure_rates[i].add(1);
                }
            }
        }
        report();

    }

private:
    std::vector<std::pair<std::pair<double, double>,int> > frame_nodes;
    std::vector<std::pair<std::pair<int, int>, int> > frame_edges;
    std::vector<std::vector<double> > frame_nodes_3d;

    void dump_nodes() {
        for(int i = 0; i < N; i++) {
            auto node_pos = std::make_pair(sat_lla[i][1], sat_lla[i][0]);
            auto node = std::make_pair(node_pos, 0);
            frame_nodes.push_back(node);
            frame_nodes_3d.push_back(std::vector<double>({sat_pos[i][0], sat_pos[i][1], sat_pos[i][2]}));
        }
    }

    void dump_edges() {
        for(int u = 0; u < N; u++) {
            for(int i = 1; i <= 2; i++) {
                int v = move(u, i);
                if(cur_banned[u][i] == 0) {
                    auto endpoints = std::make_pair(u, v);
                    auto edge = std::make_pair(endpoints, i);
                    frame_edges.push_back(edge);
                }
            }
        }

        for(int u = 0; u < N; u++) {
            for(int i = 1; i <= 2; i++) {
                int v = move(u, i);
                if(cur_banned[u][i] == 1) {
                    auto endpoints = std::make_pair(u, v);
                    auto edge = std::make_pair(endpoints, 0);
                    frame_edges.push_back(edge);
                }
            }
        }
    }
    

    void dump_path(int src, int dst) {
        frame_nodes[src].second = 1;
        frame_nodes[dst].second = 1;

        int cur = src;
        while(cur != dst) {
            auto &route_table = route_tables[cur];
            int next_hop = route_table[dst];
            if(next_hop == 0 || cur_banned[cur][next_hop]) {
                break;
            }
            int neigh = move(cur, next_hop);
            frame_edges.push_back(std::make_pair(std::make_pair(cur, neigh), 3)); 
            cur = neigh;
        }
        
    }

    void dump_table(int src) {
        for(int i = 0; i < N; i++) { 
            if(i != src) {
                if(show_diff_table == 0) {
                    if((sat_vel[src] > 0) == (sat_vel[i] > 0)) {
                        frame_nodes[i].second = route_tables[src][i] + 2;
                    }
                } else if(show_diff_table == 1) {
                    if((sat_vel[src] > 0) != (sat_vel[i] > 0)) {
                        frame_nodes[i].second = route_tables[src][i] + 2;
                    }
                } else if(show_diff_table == 2) {
                    frame_nodes[i].second = route_tables[src][i] + 2;
                }
            } else {
                frame_nodes[i].second = 7;
            }
        }
    }

    void dump_dawn_dust_line() {
        std::ifstream ifs(dawn_dust_dir + "/" + std::to_string(cur_time) + ".txt");
        std::ifstream icrs_ifs(dawn_dusk_icrs_dir + "/" + std::to_string(cur_time) + ".txt");
        double longitude, latitude;

        int sz = frame_nodes.size();
        while(ifs >> latitude >> longitude) {
            auto node = std::make_pair(std::make_pair(longitude, latitude), 8);
            frame_nodes.push_back(node);
        }
        for(int i = sz; i + 1< frame_nodes.size(); i++) {
            auto edge = std::make_pair(std::make_pair(i, i + 1), 4);
            frame_edges.push_back(edge);
        }

        double x, y, z;
        while(icrs_ifs >> x >> y >> z && frame_nodes_3d.size() < frame_nodes.size()) {
            auto node = std::vector<double>({x, y, z});
            frame_nodes_3d.push_back(node);
        }
    }

    void save_frame() {
        std::vector<std::string> dir_levels;
        dir_levels.push_back(frames_dir);
        dir_levels.push_back(frame_scenario);
        std::string open_dir = go_and_create(dir_levels);
        std::string open_path = open_dir + std::to_string(frame_id) + ".txt";
        frame_id++;
        auto fout = fopen(open_path.c_str(), "w");
        bool first = true;
        for(auto node : frame_nodes) {
            if(first) {
                first = false;
            } else {
                fprintf(fout, " | ");
            }
            fprintf(fout, "%f %f %d", node.first.first, node.first.second, node.second);    
        }
        fprintf(fout, "\n");
        first = true;
        for(auto edge : frame_edges) {
            if(first) {
                first = false;
            } else {
                fprintf(fout, " | ");
            }
            fprintf(fout, "%d %d %d", edge.first.first, edge.first.second, edge.second);    
        }
        fprintf(fout, "\n");
        first = true;
        for(auto node_3d : frame_nodes_3d) {
            if(first) {
                first = false;
            } else {
                fprintf(fout, " | ");
            }
            fprintf(fout, "%f %f %f", node_3d[0], node_3d[1], node_3d[2]);    
        }
        fprintf(fout, "\n");
        fclose(fout);
        frame_nodes.clear();
        frame_edges.clear();
        frame_nodes_3d.clear();
    }

    
    void load_sat_lla() {
        std::string sat_lla_filename = sat_lla_dir + "/" + std::to_string(cur_time) + ".csv";
        auto ifs = std::ifstream(sat_lla_filename);
        for(int i = 0; i < N; i++) {
            ifs >> sat_lla[i][0] >> sat_lla[i][1] >> sat_lla[i][2];
        }
    }

    void load_sat_pos() {
        auto ifs = std::ifstream(sat_pos_dir + "/" + std::to_string(cur_time) + ".csv");
        for(int i = 0; i < N; i++) {
            ifs >> sat_pos[i][0] >> sat_pos[i][1] >> sat_pos[i][2];
        }
    }

    void load_sat_vel() {
        auto ifs = std::ifstream(sat_vel_dir + "/" + std::to_string(cur_time) + ".csv");
        for(int i = 0; i < N; i++) {
            ifs >> sat_vel[i];
        }
    }

    void create_dir(std::string dir_path) {
        if(opendir(dir_path.c_str()) == NULL) {
            mkdir(dir_path.c_str(), S_IRWXU | S_IRWXG | S_IRWXO);
        }
    } 

    std::string go_and_create(std::vector<std::string> dir_levels) {
        std::string cur_dir = "";
        for(auto dir_level : dir_levels) {
            cur_dir += dir_level + "/";
            create_dir(cur_dir);
        }
        return cur_dir;
    }

    void save_rib(std::vector<int> &rib, int src) {
        std::vector<std::string> dir_levels;
        dir_levels.push_back("rib");
        dir_levels.push_back(name);
        dir_levels.push_back(algorithm);
        dir_levels.push_back(std::to_string(src));
        std::string dir_path = go_and_create(dir_levels);
        std::string file_path = dir_path + std::to_string(cur_time) + ".txt";
        auto fout = fopen(file_path.c_str(), "w");
        for(int i = 0; i < N; i++) {
            fprintf(fout, "%d ", rib[i]);
        }
        fclose(fout);
    }

};

#endif