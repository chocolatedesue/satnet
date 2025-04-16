#pragma once

#include "space.hpp"
#include "utils.hpp"
// Constructor definition
#include <fstream>
#include "nlohmann/json.hpp"

using json = nlohmann::json;

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
      
      for (int i = 0; i < GlobalConfig::N; ++i) {
        nodes.push_back(T(i));
      }


}

// run method definition
template <class T> void SpaceSimulation<T>::run() {
  
  for (int i = 0; i < nodes.size(); ++i) {
    // Perform simulation steps for each node
      nodes[i].compute();
  }
}