#pragma once

#include <string>
#include <vector>
#include "satnet/baseNode.hpp"

template <class T> class SpaceSimulation {

private:


  int start_time;
  int step;
  int duration;
  int update_period;
  int refresh_period;

  unsigned int seed;

  std::string config_file_name;

  std::vector<T> nodes;
  std::vector<std::vector<int>> route_tables;


public:
  SpaceSimulation(const std::string &config_file_name);

  void run();
};

#include "space.tpp" // Include the template implementation file