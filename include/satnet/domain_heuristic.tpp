// domain_heuristic_node.tpp
// No include guard needed here - this file is meant to be included by the .hpp

// Include headers needed specifically for the implementations
#include "base.hpp"
#include "satnet/domain_heuristic.hpp"
#include "satnet/utils.hpp"
#include <cmath>  // For std::floor
#include <limits> // Potentially for checking invalid IDs or distances
#include <map>
#include <stdexcept> // For potential error handling (e.g., invalid config)
// --- Constructor Definition ---
#include <concepts>

template <int Kp, int Kn>
DomainHeuristicNode<Kp, Kn>::DomainHeuristicNode(int id)
    : BaseNode(id), vis(GlobalConfig::N, 0) // Initialize base class
{}

template <int Kp, int Kn>
std::pair<double, bool> DomainHeuristicNode<Kp, Kn>::calcE2ePath(
    int src, int dst, const std::vector<std::vector<int>> &route_tables) {
  return std::pair<double, bool>(-1, false);
  // // Assumptions: check_lla_status() and calcuDelay(a, b) are globally
  // available or static in another accessible class.
  // // Ensure route_table access is within bounds.
  // int is_vertical = check_lla_status(); // Assuming it exists
  // // (Note: is_vertical is calculated but not used in the provided snippet)

  // auto [I_src, J_src] = calcDomainCoords(src);
  // auto [I_dst, J_dst] = calcDomainCoords(dst);

  // if (I_src == I_dst && J_src == J_dst) {
  //     // Path calculation within the same domain
  //     int val = 0;
  //     int cur = src;
  //     while (cur != dst) {
  //         int nxt = nodes[cur].route_table[dst]; // Assuming route_table is
  //         accessible and valid val += calcuDelay(cur, nxt); // Assuming it
  //         exists and handles nodes correctly cur = nxt;
  //     }

  //     return val ;
  //     // TODO: What should be done with 'val'? Return it? Log it?
  //     // Function currently returns void.
  //     // if (cur == dst) { /* Path found, maybe return val */ }
  //     // else { /* Path not found or error */ }
  // } else {
  //     // Nodes are in different domains, this function only handles
  //     intra-domain.
  //     // Maybe log this or return an error code/special value if the function
  //     returned something.
  // }
  // return;
}

template <int Kp, int Kn>
std::pair<int, int>
DomainHeuristicNode<Kp, Kn>::calcDomainCoords(int satelliteId) {
  // Assumption: GlobalConfig::Q and GlobalConfig::P are valid positive
  // integers.
  if (GlobalConfig::Q <= 0 || GlobalConfig::P <= 0) {
    throw std::runtime_error(
        "GlobalConfig::Q and GlobalConfig::P must be positive.");
  }
  int n_s = satelliteId % GlobalConfig::Q;
  int p_s = satelliteId / GlobalConfig::Q;

  // Use static_cast for clarity. Ensure P isn't zero.
  int I_s = static_cast<int>(
      std::floor(static_cast<double>(p_s) * Kp / GlobalConfig::P));
  int J_s = static_cast<int>(
      std::floor(static_cast<double>(n_s) * Kn / GlobalConfig::P));

  return std::make_pair(I_s, J_s);
}

// --- Member Function Definitions ---

template <int Kp, int Kn> std::string DomainHeuristicNode<Kp, Kn>::getName() {
  // Simple override
  return "DomainHeuristicNode";
}

template <int Kp, int Kn>
int DomainHeuristicNode<Kp, Kn>::calculateDomainId(int satelliteId) {
  // Relies on the static helper function and template parameter Kp
  auto [I_s, J_s] = calcDomainCoords(satelliteId);
  // Potential issue if Kp or Kn is 0, resulting in non-unique IDs or division
  // by zero downstream.
  return J_s * Kp + I_s;
}

template <int Kp, int Kn> void DomainHeuristicNode<Kp, Kn>::compute() {

  const auto &banned =
      GlobalConfig::futr_banned; // Assuming pointer access is correct

  // Reset state for this computation run
  std::fill(vis.begin(), vis.end(), -1);
  // Also reset route_table if it's being computed here
  // std::fill(route_table.begin(), route_table.end(), -1); // Assuming
  // route_table is accessible & needs reset

  std::queue<int> q;

  // vis[id] = ;
  q.push(id);

  while (!q.empty()) {
    int cur = q.front();
    q.pop();

    int current_domain_id =
        calculateDomainId(cur); // Calculate only once per node

    for (int direction = 1; direction <= 4;
         ++direction) { // Loop directions 1 to 4
      // Check bounds before accessing banned table if necessary
      // if (cur >= banned.size() || direction >= banned[cur].size()) continue;
      // // Example bounds check

      if (banned[cur][direction] == 1) { // Check if link is banned
        continue;
      }

      int nxt = move(cur, direction); // Get neighbor

      // Check if the neighbor is in the same domain
      if (calculateDomainId(nxt) != current_domain_id) {
        continue; // Skip neighbors in different domains
      }

      // Standard BFS check: if neighbor not visited yet
      if (vis[nxt] == -1) {
        vis[nxt] = vis[cur] + 1;
        route_table[nxt] = direction; // Store predecessor in route_table
        q.push(nxt);
      }
    }
  }
}