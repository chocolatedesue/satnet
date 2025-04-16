#pragma once

#include <string>
#include "satnet/baseNode.hpp"

template <class T> class SpaceSimulation {

private:
  std::string config_file_name;

public:
  SpaceSimulation(const std::string &config_file_name);

  void run();
};

#include "space.tpp" // Include the template implementation file