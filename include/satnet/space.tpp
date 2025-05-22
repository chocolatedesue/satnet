#pragma once

// #include "omp.h"
// #include "space.hpp"
// #include "utils.hpp"
// Constructor definition
#include "nlohmann/json.hpp"
#include "satnet/base.hpp"
#include "satnet/space.hpp"
#include <algorithm>
#include <array>
#include <chrono>
#include <filesystem> // 需要 C++17
#include <fstream>
#include <iostream>

#include <concepts>
#include <string>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <vector>

using json = nlohmann::json;
namespace fs = std::filesystem;

template <DerivedFromBaseNode T>
SpaceSimulation<T>::SpaceSimulation(const std::string &config_path)
    : config_file_name(config_path) {
  GlobalConfig::loadConfig(config_path);

  auto config = json::parse(std::ifstream(config_path));

  step = config["step_length"];
  duration = config["duration"];
  if (config.count("update_period")) {
    update_period = config["update_period"];
  } else {
    update_period = duration;
  }
  if (config.count("refresh_period")) {
    refresh_period = config["refresh_period"];
  } else {
    refresh_period = update_period;
  }
  if (config.count("start_time")) {
    start_time = config["start_time"];
  } else {
    start_time = 0;
  }
  config_name = config["name"];
  isl_state_dir = config["isl_state_dir"];
  sat_pos_dir = config["sat_position_dir"];
  sat_vel_dir = config["sat_velocity_dir"];

  std::string report_dir_str = config["report_dir"].get<std::string>();
  // std::string config_name = config["name"];

  fs::path target_dir_path = fs::path(report_dir_str) / config_name;

  fs::create_directories(target_dir_path.parent_path());
  fs::create_directories(target_dir_path);

  report_dir = target_dir_path.string();

  seed = 42;
  srand(seed);

  route_tables = std::vector<std::vector<int>>(
      GlobalConfig::N, std::vector<int>(GlobalConfig::N));

  // backup_route_tables = std::vector<std::vector<short>>(
  // GlobalConfig::N, std::vector<short>(GlobalConfig::N));

  for (int i = 0; i < GlobalConfig::N; ++i) {
    nodes.push_back(new T(i));
  }

  config_name = config["name"];
  algorithm_name = nodes[0]->getName();

  sprintf(report_filename, "report [%s] %s.txt", algorithm_name.c_str(),
          algorithm_name.c_str());

  path_vis = std::vector<int>(GlobalConfig::N);
}

template <DerivedFromBaseNode T> void SpaceSimulation<T>::load_sat_pos() {
  auto ifs = std::ifstream(sat_pos_dir + "/" + std::to_string(cur_time) +
                           std::string(".csv"));
  for (int i = 0; i < GlobalConfig::N; i++) {
    ifs >> GlobalConfig::sat_pos[i][0] >> GlobalConfig::sat_pos[i][1] >>
        GlobalConfig::sat_pos[i][2];
  }
}

template <DerivedFromBaseNode T> void SpaceSimulation<T>::load_sat_lla() {
  auto ifs = std::ifstream(sat_lla_dir + "/" + std::to_string(cur_time) +
                           std::string(".csv"));
  for (int i = 0; i < GlobalConfig::N; i++) {
    ifs >> GlobalConfig::sat_lla[i][0] >> GlobalConfig::sat_lla[i][1] >>
        GlobalConfig::sat_lla[i][2];
  }
}

template <DerivedFromBaseNode T> void SpaceSimulation<T>::load_sat_vel() {
  auto ifs = std::ifstream(sat_vel_dir + "/" + std::to_string(cur_time) +
                           std::string(".csv"));
  for (int i = 0; i < GlobalConfig::N; i++) {
    ifs >> GlobalConfig::sat_vel[i];
  }
}

void clearIslState(std::vector<std::array<int, 5>> &banned) {
  // if (banned.size() != static_cast<size_t>(GlobalConfig::N)) {
  //   banned.resize(GlobalConfig::N);
  // }
  for (int i = 0; i < GlobalConfig::N; i++) {
    for (int j = 0; j < 4; j++) {
      banned[i][j] = 0;
    }
  }
}

template <DerivedFromBaseNode T>
void SpaceSimulation<T>::readIslStateFlie(
    int time, std::vector<std::array<int, 5>> &banned) {
  std::string isl_state_filename =
      isl_state_dir + "/" + std::to_string(time) + ".txt";
  auto ifs = std::ifstream(isl_state_filename);
  int u, v;
  while (ifs >> u >> v) {
    int u_port, v_port;
    //            std::cerr << u << ' ' << v << std::endl;
    int res = getPort(u, v, u_port, v_port);
    if (!res) {
      // Use std::cout and std::endl consistently
      std::cerr << "Error: Not consistent with the topology"
                << std::endl; // Prefer std::cerr for errors
      std::cerr << "Edge: " << u << " <-> " << v << std::endl;
      std::cerr << "Ports: u_port=" << u_port << ", v_port=" << v_port
                << std::endl;

      // Use std::exit from <cstdlib>
      std::exit(EXIT_FAILURE); // EXIT_FAILURE is often preferred over magic
                               // numbers like 1 for error exits
    }
    banned[u][u_port] = 1;
    banned[v][v_port] = 1;
  }
}

template <DerivedFromBaseNode T> void SpaceSimulation<T>::load_cur_banned() {
  clearIslState(GlobalConfig::cur_banned);
  readIslStateFlie(cur_time, GlobalConfig::cur_banned);
}

template <DerivedFromBaseNode T> void SpaceSimulation<T>::load_futr_banned() {
  clearIslState(GlobalConfig::futr_banned);
  // for (int futr_time = cur_time; futr_time < cur_time + update_period - step
  // &&
  //                                futr_time < start_time + duration;
  //      futr_time += step) {
  //   readIslStateFlie(futr_time, GlobalConfig::futr_banned);
  // }

  for (int futr_time = cur_time; futr_time < cur_time + update_period;
       futr_time += step) {
    if (futr_time >= start_time + duration) {
      break;
    }
    readIslStateFlie(futr_time, GlobalConfig::futr_banned);
  }
}

// run method definition
template <DerivedFromBaseNode T> void SpaceSimulation<T>::run() {

  auto logger = spdlog::get(global_logger_name);
  logger->info("Simulation started with config: {}", config_file_name);
  int first_record = 0, is_specical_cal = 0;
  cur_time = start_time;
  // cur_time = 600, duration = 900;
  run_start = std::chrono::steady_clock::now();
  bool is_sp_update =
      algorithm_name.find("DomainHeuristic") != std::string::npos;
  // is_sp_update = true;
  is_sp_update = false;
  for (; cur_time < start_time + duration; cur_time += step) {
    load_cur_banned();
    load_sat_pos();
    load_sat_lla();
    // load_sat_vel();

    double pre_compute_time = 0.0;
    int total_diff_count = 0;
    if (cur_time % update_period == 0 || is_sp_update) {

      if (!is_specical_cal && cur_time % update_period != 0) {
        is_specical_cal = 1;
        logger->warn("Special full update enabled mode\n");
      }
      load_futr_banned();
      // 替换注释掉的聚合代码
      pre_compute_time = 0.0;
      total_diff_count = 0;

#pragma omp parallel for reduction(+ : pre_compute_time, total_diff_count)
      for (int i = 0; i < GlobalConfig::N; i++) {
        auto &node = nodes[i];
        auto &cur_table = route_tables[i];

        auto compute_start = std::chrono::high_resolution_clock::now();
        node->compute();
        auto compute_end = std::chrono::high_resolution_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
            compute_end - compute_start);
        auto elapsed_ms =
            elapsed.count() / 1000.0; // Convert microseconds to milliseconds
        pre_compute_time += elapsed_ms;

        auto &new_table = node->getRouteTable();
        int diff = 0;
        for (int j = 0; j < GlobalConfig::N; j++) {
          if (cur_table[j] != new_table[j]) {
            cur_table[j] = new_table[j];
            // backup_route_tables[i][j] = new_table[j];
            diff++;
          }
        }
        if (cur_time != start_time) {
          total_diff_count += diff;
        }
      }

      // 单次添加汇总数据，避免循环
      // compute_time_result.add(total_compute_time / GlobalConfig::N);
      if (cur_time != start_time) {

        update_entry_result.add(static_cast<double>(total_diff_count) /
                                GlobalConfig::N);
        total_diff_count = 0;

        compute_time_result.add(pre_compute_time / GlobalConfig::N);

        pre_compute_time = 0;
      }
    }

    if (cur_time % refresh_period == 0) {

      logger->info("Begin to report at time {}", cur_time);
      if (cur_time != start_time)
        report();
    }

    logger->info("Begin to calculate latency at time {}", cur_time);

    // if (cur_time > 600 && cur_time < 1400) {
    //   logger->info(
    //       "Skip latency calculation at time {} because it is not in the "
    //       "specified range",
    //       cur_time);
    //   logger->flush();
    //   continue;
    // }

    double e2e_path_compute_time = 0;

    for (int i = 0; i < GlobalConfig::num_observers; i++) {

      auto src = GlobalConfig::latency_observers[i].first;
      auto dst = GlobalConfig::latency_observers[i].second;

      if (src > dst) {
        logger->warn(
            "Error: src > dst in latency observer config, swapping values");
        std::swap(src, dst);
      }
      double latency = -1;
      bool success = false;

      // if (cur_time < 600 || (cur_time > 1201 && cur_time < 3600) ||
      //     (cur_time > 4201 && cur_time < 6100)) {
      //   std::tie(latency, success) = T::calcE2ePath(src, dst, route_tables);
      // }
      auto compute_start = std::chrono::high_resolution_clock::now();
      std::tie(latency, success) = T::calcE2ePath(src, dst, route_tables);
      auto compute_end = std::chrono::high_resolution_clock::now();
      auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
          compute_end - compute_start);
      auto elapsed_ms =
          elapsed.count() / 1000.0; // Convert microseconds to milliseconds
      // if (cur_time % update_period == 0)
      e2e_path_compute_time += elapsed_ms;

      logger->debug(
          "Calculate latency from {} to {}: {} ms, success: {} at time {}", src,
          dst, latency, success, cur_time);
      // logger->flush();
      if (success) {
        GlobalConfig::failure_rates[i].add(0);
        GlobalConfig::latency_results[i].add(latency);
      } else {
        GlobalConfig::failure_rates[i].add(1);
        latency = -1;
      }
      if (latency != -1)
        GlobalConfig::latency_results[i].add(latency);
      if (i < 10) {
        if (first_record == 0) {
          first_record = 1;
          auto graph_data_filename =
              report_dir + "/" + algorithm_name + std::string(".csv");
          auto fout = fopen(graph_data_filename.c_str(), "w");
          fprintf(fout, "time,src,dst,latency\n");
          fclose(fout);
        } else {
          auto graph_data_filename =
              report_dir + "/" + algorithm_name + std::string(".csv");
          auto fout = fopen(graph_data_filename.c_str(), "a");
          fprintf(fout, "%d,%d,%d,%f\n", cur_time, src, dst, latency);
          fclose(fout);
        }
      }
    }
    if (e2e_path_compute_time != 0) {
      compute_time_result.add(e2e_path_compute_time /
                              GlobalConfig::num_observers);
      e2e_path_compute_time = 0;
    }
  }
  report();
}

// template <DerivedFromBaseNode T>
// std::pair<double, bool> SpaceSimulation<T>::computeLatency(int src, int dst)
// {
//   int cur = src;
//   double latency = 0;
//   bool success = true;

//   if (path_timer >= 1e8) {
//     for (int i = 0; i < GlobalConfig::N; i++) {
//       path_vis[i] = 0;
//     }
//     path_timer = 0;
//   }
//   ++path_timer;
//   while (cur != dst) {
//     auto &route_table = route_tables[cur];
//     int next_hop = route_table[dst];
//     if (next_hop == 0 || GlobalConfig::cur_banned[cur][next_hop] ||
//         path_vis[cur] == path_timer) {
//       success = false;
//       break;
//     }
//     path_vis[cur] = path_timer;
//     int neigh = move(cur, next_hop);
//     double one_hop_latency = calcuDelay(cur, neigh);
//     latency += one_hop_latency;
//     cur = neigh;
//   }
//   //  向 log 文件里写入延迟
//   // if (success) {
//   //   std::cout << "Latency from " << src << " to " << dst << ": " <<
//   latency
//   //             << std::endl;
//   // } else {
//   //   std::cout << "No path from " << src << " to " << dst << std::endl;
//   // }
//   return std::make_pair(latency, success);
// }

// template <DerivedFromBaseNode T>
// void SpaceSimulation<DerivedFromBaseNode T>::save_graph_data() {
//   auto graph_data_filename =
//       report_dir + "/" + std::string(typeid(T).name()) + std::string(".csv");
//       // time,latency,is_success
//   auto fout = fopen(graph_data_filename.c_str(), "w");
//   for (int i = 0; i < GlobalConfig::N; i++) {
//     for (int j = 0; j < GlobalConfig::N; j++) {
//       fprintf(fout, "%d ", route_tables[i][j]);
//     }
//     fprintf(fout, "\n");
//   }
//   fclose(fout);
// }

template <DerivedFromBaseNode T> void SpaceSimulation<T>::report() {
  double past_time = cur_time - start_time + 1;
  auto run_duration = (std::chrono::steady_clock::now() - run_start);
  std::chrono::duration<double> rw_time = run_duration;
  double eta =
      rw_time.count() / past_time * std::max(duration - past_time, 0.0);
  std::cerr << "Real-world time: " << rw_time.count() << std::endl;
  std::cerr << "Simulation time: " << cur_time << std::endl;
  std::cerr << "ETA: " << eta << std::endl;

  auto open_path = report_dir + "/" + std::string(report_filename);
  auto fout = fopen(open_path.c_str(), "w");
  fprintf(fout, "name: %s\n", config_name.c_str());
  fprintf(fout, "algorithm: %s\n", algorithm_name.c_str());
  fprintf(fout, "node type: %s\n", typeid(T).name());
  fprintf(fout, "simulation time: %d\n", cur_time);
  fprintf(fout, "real-world time: %f\n", rw_time.count());
  fprintf(fout, "estimated time of arrival: %f\n", eta);
  fprintf(fout, "compute time: %f\n", compute_time_result.getResult());
  fprintf(fout, "update entry: %f\n", update_entry_result.getResult());
  fprintf(fout, "number of observers: %d\n", GlobalConfig::num_observers);

  for (int i = 0; i < GlobalConfig::num_observers; i++) {
    auto src = GlobalConfig::latency_observers[i].first;
    auto dst = GlobalConfig::latency_observers[i].second;
    auto latency = GlobalConfig::latency_results[i].getResult();
    auto failure_rate = GlobalConfig::failure_rates[i].getResult();
    fprintf(fout, "route path [%d, %d]\n\tlatency: %f\n\tfailure rate: %f\n",
            src, dst, latency, failure_rate);
  }
  fclose(fout);
}

template <DerivedFromBaseNode T> SpaceSimulation<T>::~SpaceSimulation() {
  for (auto node : nodes) {
    delete node;
  }
}
