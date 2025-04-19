// domain_heuristic_node.hpp
#pragma once // Keep include guard

// Necessary includes for declarations
#include "base.hpp" // For BaseNode, World, potentially futr_banned type, route_table type
#include "utils.hpp" // For GlobalConfig (used by static calcDomainCoords, maybe others)
#include <concepts> // <--- Include for concepts
#include <queue> // Often needed by BFS implementation details, maybe move to .tpp if purely internal to compute()
#include <string> // For getName() return type
#include <vector> // For vis, route_table parameter

// Forward declarations if possible (reduces compile times if full definitions
// aren't needed) class SomeType; // Example

template <int Kp, int Kn> class DomainHeuristicNode : public BaseNode {

  std::vector<int> vis;
  // Assuming 'route_table' and 'futr_banned' are accessible via BaseNode or
  // elsewhere

public:
  // --- Constructor ---
  DomainHeuristicNode(int id);

  static std::pair<int, int> calcDomainCoords(int satelliteId);

  // Calculates the flat domain ID for a given satellite ID
  static int calculateDomainId(int satelliteId);

  // Computes the intra-domain routing table (populates 'route_table') using BFS
  void compute() override;

  // --- Member Functions ---
  std::string getName() override;

  static std::pair<double, bool> CalcE2ePath(int src, int dst,
    const std::vector<std::vector<int>> &route_tables) ;

};

// --- Include the Template Implementation File ---
// This line effectively brings the definitions into any file that includes this
// header.
#include "domain_heuristic.tpp"