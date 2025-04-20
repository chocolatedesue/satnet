#pragma once

#include <array>
#include <cmath>
#include <limits>
#include <queue>
#include <string>
#include <vector>

// #include "json.hpp"
#include "satnet/base.hpp"
#include "utils.hpp"

// using json = nlohmann::json;

/**
 * @brief Base class for Dijkstra routing nodes.
 */
class DijkstraNode : public BaseNode { // Or potentially public DisCoRouteNode
private:
  double getDist(int a, int b); // Calculate distance between nodes a and b

protected:
  std::vector<int> vis;     // Visited flags (size N)
  std::vector<double> dist; // Distance array (size N)
  // route_table is assumed inherited

  double calcuDelay(int a, int b); // Calculate link delay between a and b

public:
  DijkstraNode(int id);
  virtual ~DijkstraNode() = default;

  virtual std::string getName() override;
  virtual void compute() override; // Compute routes using standard Dijkstra

  
};

/**
 * @brief Dijkstra variant considering currently banned ports.
 */
class DijkstraProbeNode : public DijkstraNode {
protected:
  // Compute routes avoiding specific ports
  void
  computeWithBannedPorts(const std::vector<std::array<int, 5>> *banned_ptr);

public:
  DijkstraProbeNode(int id);
  virtual ~DijkstraProbeNode() = default;

  virtual std::string getName() override;
  // Compute routes using current banned ports (cur_banned)
  virtual void compute() override;

};

/**
 * @brief Dijkstra variant considering predicted future banned ports.
 */
class DijkstraPredNode : public DijkstraProbeNode {
public:
  DijkstraPredNode(int id);
  virtual ~DijkstraPredNode() = default;

  virtual std::string getName() override;
  // Compute routes using future predicted banned ports (futr_banned)
  virtual void compute() override;

  
};