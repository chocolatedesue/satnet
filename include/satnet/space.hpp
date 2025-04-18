#pragma once

#include "satnet/utils.hpp"
#include <string>
#include <vector>


template <class T> class SpaceSimulation {

private:

  double run_start;
  int cur_time;
  int start_time;
  int step;
  int duration;
  int update_period;
  int refresh_period;


  std::string isl_state_dir;
  std::string sat_pos_dir;
  std::string sat_lla_dir;
  std::string sat_vel_dir;
  std::string report_dir;
  Average compute_time_result;
  Average update_entry_result;

  std::vector<Average> latency_results;
  std::vector<Average> failure_rates;
  // std::string frames_dir;
  // std::string dawn_dust_dir;
  // std::string dawn_dusk_icrs_dir;
  // std::string frame_scenario;

  unsigned int seed;

  std::string config_file_name;

  std::vector<T> nodes;
  std::vector<std::vector<int>> route_tables;

  void load_cur_banned();
  void load_futr_banned();
  void load_sat_pos();
  void load_sat_lla();

  void readIslStateFlie(int time, std::vector<std::array<int, 5>> &banned) ;
  void load_sat_vel();
  


public:
  SpaceSimulation(const std::string &config_file_name);

  void run();
};

#include "space.tpp" // Include the template implementation file