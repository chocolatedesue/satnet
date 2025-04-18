#pragma once

#include "omp.h"
#include "space.hpp"
#include "utils.hpp"
// Constructor definition
#include "nlohmann/json.hpp"
#include <algorithm>
#include <array>
#include <filesystem> // 需要 C++17
#include <fstream>
#include <iostream>
#include <string>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <vector>

using json = nlohmann::json;
namespace fs = std::filesystem;

template <class T>
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

  isl_state_dir = config["isl_state_dir"];

  sat_vel_dir = config["sat_velocity_dir"];
  report_dir = config["report_dir"].get<std::string>();

  fs::path report_dir_path(report_dir);
  std::error_code ec;

  // 尝试创建目录，如果已存在则返回 false，出错则设置 ec
  bool created = fs::create_directories(report_dir_path, ec);

  if (!ec) {
    if (created) {
      std::cout << "report_dir: " << report_dir_path.string() << " created\n";
    } else {
      std::cout << "report_dir: " << report_dir_path.string()
                << " already exists\n";
    }
  }
  seed = 42;
  srand(seed);

  route_tables = std::vector<std::vector<int>>(
      GlobalConfig::N, std::vector<int>(GlobalConfig::N));

  for (int i = 0; i < GlobalConfig::N; ++i) {
    nodes.push_back(T(i));
  }

  
}

template <class T> void SpaceSimulation<T>::load_sat_pos() {
  auto ifs = std::ifstream(sat_pos_dir + "/" + std::to_string(cur_time) +
                           std::string(".csv"));
  for (int i = 0; i < GlobalConfig::N; i++) {
    ifs >> GlobalConfig::sat_pos[i][0] >> GlobalConfig::sat_pos[i][1] >>
        GlobalConfig::sat_pos[i][2];
  }
}

template <class T> void SpaceSimulation<T>::load_sat_lla() {
  auto ifs = std::ifstream(sat_lla_dir + "/" + std::to_string(cur_time) +
                           std::string(".csv"));
  for (int i = 0; i < GlobalConfig::N; i++) {
    ifs >> GlobalConfig::sat_lla[i][0] >> GlobalConfig::sat_lla[i][1] >>
        GlobalConfig::sat_lla[i][2];
  }
}

template <class T> void SpaceSimulation<T>::load_sat_vel() {
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

template <class T>
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
      std::cerr << "Error: Not consistent with the topology" << std::endl; // Prefer std::cerr for errors
      std::cerr << "Edge: " << u << " <-> " << v << std::endl;
      std::cerr << "Ports: u_port=" << u_port << ", v_port=" << v_port << std::endl;
    
      // Use std::exit from <cstdlib>
      std::exit(EXIT_FAILURE); // EXIT_FAILURE is often preferred over magic numbers like 1 for error exits
    }
    banned[u][u_port] = 1;
    banned[v][v_port] = 1;
  }
}

template <class T> void SpaceSimulation<T>::load_cur_banned() {
  clearIslState(GlobalConfig::cur_banned);
  readIslStateFlie(cur_time, GlobalConfig::cur_banned);
}

template <class T> void SpaceSimulation<T>::load_futr_banned() {
  clearIslState(GlobalConfig::futr_banned);
  for (int futr_time = cur_time; futr_time < cur_time + update_period &&
                                 futr_time < start_time + duration;
       futr_time += step) {
    readIslStateFlie(futr_time, GlobalConfig::futr_banned);
  }
}

// run method definition
template <class T> void SpaceSimulation<T>::run() {

  cur_time = start_time;
  run_start = clock();

  for (; cur_time < start_time + duration; cur_time += step) {
    load_cur_banned();
    load_sat_pos();
    load_sat_lla();
    // load_sat_vel();

    if (cur_time % update_period == 0) {
      load_futr_banned();
      // 替换注释掉的聚合代码
      double total_compute_time = 0.0;
      int total_diff_count = 0;

#pragma omp parallel for reduction(+ : total_compute_time, total_diff_count)
      for (int i = 0; i < GlobalConfig::N; i++) {
        auto &node = nodes[i];
        auto &cur_table = route_tables[i];

        auto compute_start = clock();
        node.compute();
        auto elapsed_s = (clock() - compute_start) * 1.0 / CLOCKS_PER_SEC;
        auto elapsed_ms = elapsed_s * 1000;
        total_compute_time += elapsed_ms;

        auto &new_table = node.getRouteTable();
        int diff = 0;
        for (int j = 0; j < GlobalConfig::N; j++) {
          if (cur_table[j] != new_table[j]) {
            cur_table[j] = new_table[j];
            diff++;
          }
        }
        if (cur_time != 0) {
          total_diff_count += diff;
        }

        // #pragma omp critical
        // {
        //     if(dump_rib[i]) {
        //         save_rib(cur_table, i);
        //     }
        // }
      }

      // 单次添加汇总数据，避免循环
      compute_time_result.add(total_compute_time / GlobalConfig::N);
      if (cur_time != 0) {
        update_entry_result.add(static_cast<double>(total_diff_count) /
                                GlobalConfig::N);
      }
    }

    if (cur_time % refresh_period == 0) {
      std::cout << "Begin to report at time " << cur_time << std::endl;
      // TODO report();
    }

    // 计算延迟

  //   for (int i = 0; i < GlobalConfig::num_observers; i++) {
  //     auto src = GlobalConfig::latency_observers[i].first;
  //     auto dst = GlobalConfig::latency_observers[i].second;
  //     // TODO: auto [latency, success] = computeLatency(src, dst);
  //     int latency = -1, success = 0;
  //     if (success) {
  //       failure_rates[i].add(0);
  //     } else {
  //       failure_rates[i].add(1);
  //       latency = -1;
  //     }
  //     if (latency != -1)
  //       latency_results[i].add(latency);
  //   }
  }
  // TODO: report();
}
