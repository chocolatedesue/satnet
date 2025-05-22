
#include "satnet/base.hpp" // Assuming this is the correct path
#include "satnet/domain_no_opt.hpp" 
#include "satnet/utils.hpp" // Assuming move, calcuDelay, getInverseDirection are here
#include <cmath> // For std::floor, std::abs

#include <cstdio>
#include <cstdlib>
#include <limits>    // Potenti`ly for checking invalid IDs or distances
#include <map>
#include <set>
#include <stdexcept> // For potential error handling (e.g., invalid config)
#include <algorithm> // For std::sort, std::find, std::min, std::max
#include <vector>

// --- Constructor Definition ---
#include <spdlog/spdlog.h> // Assuming spdlog is used as in original

// Definition for Kp and Kn are in the HPP:
// static const int Kp = 7, Kn = 10;

DomainNodeNoOpt::DomainNodeNoOpt(int id)
    : BaseNode(id),             // Initialize base class
      vis(GlobalConfig::N, 0) // Initialize vis (instance member)
{
  if (GlobalConfig::Q <= 0 || GlobalConfig::P <= 0) {
    throw std::runtime_error(
        "GlobalConfig::Q and GlobalConfig::P must be positive.");
  }

  // Kp and Kn are now static members of DomainNodeNoOpt
  if (DomainNodeNoOpt::Kp <= 0 || DomainNodeNoOpt::Kn <= 0) {
    throw std::runtime_error("DomainNodeNoOpt::Kp and DomainNodeNoOpt::Kn must be positive.");
  }

  if (GlobalConfig::P % DomainNodeNoOpt::Kp != 0) {
    throw std::runtime_error("GlobalConfig::P must be divisible by DomainNodeNoOpt::Kp.");
  }

  if (GlobalConfig::Q % DomainNodeNoOpt::Kn != 0) {
    throw std::runtime_error("GlobalConfig::Q must be divisible by DomainNodeNoOpt::Kn.");
  }
  // route_table is an instance member, typically initialized in compute()
  // If a default size is needed here, it would be for 'this->route_table'
  // For example: this->route_table.resize(GlobalConfig::N);
  // However, the original code initializes it in compute().
}

std::vector<std::vector<std::vector<short>>>
DomainNodeNoOpt::initializeBorderNodes() {
  // Use Kp and Kn as static members
  size_t domain_max_side_length = static_cast<size_t>(
      std::max({DomainNodeNoOpt::Kp * DomainNodeNoOpt::Kn + 1, 1}));
  std::vector<std::vector<std::vector<short>>> nodes(
      domain_max_side_length,
      std::vector<std::vector<short>>(5, std::vector<short>()));

  auto logger = spdlog::get(global_logger_name); // Assuming global_logger_name is defined

  logger->info("Creating border nodes...");
  logger->info("Kp={}, Kn={}, domain_max_side_length={}", DomainNodeNoOpt::Kp, DomainNodeNoOpt::Kn,
               domain_max_side_length);

  for (int i = 0; i < GlobalConfig::N; ++i) {
    int cur_dmid = DomainNodeNoOpt::calculateDomainId(i);

    for (int j = 1; j < 5; ++j) { // Directions 1-4
      int nxt = move(i, j); // Assuming move is in Utils
      if (nxt == -1)
        continue;

      int nxt_dmid = DomainNodeNoOpt::calculateDomainId(nxt);

      if (nxt_dmid != cur_dmid) {
        nodes[cur_dmid][j].push_back(static_cast<short>(i));
      }
    }
  }
  return nodes;
}

std::pair<double, bool> DomainNodeNoOpt::calcE2ePathWithinDomain(
    int src, int dst, const std::vector<std::vector<int>> &route_tables) {
  double val = 0; // Changed from int to double to match return type's first element
  int cur = src;
  auto logger = spdlog::get(global_logger_name);

  int cnt = 0;
  int cur_dmid = DomainNodeNoOpt::calculateDomainId(cur); // Use static Kp, Kn via calculateDomainId

  while (cur != dst) {
    cnt++;
    // Use Kp and Kn as static members for loop break condition
    if (cnt * DomainNodeNoOpt::Kp * DomainNodeNoOpt::Kn > 2 * GlobalConfig::N) {
      // logger->error("Infinite loop detected in calcE2ePathWithinDomain src={}, dst={}", src, dst);
      // logger->flush();
      return std::make_pair(-1.0, false);
    }

    // Ensure route_tables has the data for 'cur'
    if (static_cast<size_t>(cur) >= route_tables.size() || route_tables[cur].empty()) {
        // logger->error("Route table for current node {} is missing or empty.", cur);
        // logger->flush();
        return std::make_pair(-1.0, false);
    }
    // Ensure 'dst' is a valid index for the specific route_table entry
    // This depends on how route_tables is structured. If route_tables[cur] is a map or 
    // if it's a vector indexed by destination, checks are needed.
    // Assuming route_tables[cur] is a vector indexed by destination ID (up to GlobalConfig::N)
    if (static_cast<size_t>(dst) >= route_tables[cur].size()){
        // logger->error("Destination {} out of bounds for route_table of node {}.", dst, cur);
        // logger->flush();
        return std::make_pair(-1.0, false);
    }

    int nxt_dir = route_tables[cur][dst];

    if (nxt_dir == 0 || nxt_dir == -1) { // Assuming 0 can also mean no path or is not a valid direction
      // logger->warn("No route from {} to {} in route_tables.", cur, dst);
      return std::make_pair(-1.0, false);
    }

    int nxt = move(cur, nxt_dir); // Assuming move is in Utils
    
    // Check for invalid move or banned link *before* calculating next domain ID
    if (nxt == -1 || GlobalConfig::cur_banned[cur][nxt_dir] == 1) {
        // logger->error("Invalid or banned move from {} in direction {}", cur, nxt_dir);
        // logger->flush();
        return std::make_pair(-1.0, false);
    }

    int nxt_dmid = DomainNodeNoOpt::calculateDomainId(nxt); // Use static Kp, Kn

    if (nxt_dmid != cur_dmid) { // Path must stay within the domain
        // logger->error("Path from {} to {} wandered out of domain {}.", src, dst, cur_dmid);
        // logger->flush();
        return std::make_pair(-1.0, false);
    }
    
    val += calcuDelay(cur, nxt); // Assuming calcuDelay is in Utils
    cur = nxt;
  }
  return std::make_pair(val, true);
}

// calcDomainHeuristicScore was commented out in HPP, so not implemented here.

// template <int Kp, int Kn>
double DomainNodeNoOpt::calcDomainHeuristicScore(int src_dmid,
                                                  int dst_dmid) {

  // auto [I_s, J_s] = calcDomainCoords(src);
  // auto [I_d, J_d] = calcDomainCoords(dst);
  int I_s = src_dmid / Kn, J_s = src_dmid % Kn;
  int I_d = dst_dmid / Kn, J_d = dst_dmid % Kn;

  int vertical_dist =
      std::min(std::abs(J_s - J_d + Kn) % Kn,
               std::abs(J_d - J_s + Kn) % Kn); // 垂直方向上的距离

  int horizontal_dist =
      std::min(std::abs(I_s - I_d + Kp) % Kp, std::abs(I_d - I_s + Kp) % Kp);

  // int n_s = src % GlobalConfig::Q, p_s = src / GlobalConfig::Q;
  // int n_d = dst % GlobalConfig::Q, p_d = dst / GlobalConfig::Q;

  // int vertical_dist =
  //     std::min(std::abs(n_s - n_d + GlobalConfig::Q) % GlobalConfig::Q,
  //              std::abs(n_d - n_s + GlobalConfig::Q) % GlobalConfig::Q);

  // int horizontal_dist =
  //     std::min(std::abs(p_s - p_d + GlobalConfig::P) % GlobalConfig::P,
  //              std::abs(p_d - p_s + GlobalConfig::P) % GlobalConfig::P);

  return static_cast<double>(-(vertical_dist ));
  // return static_cast<double>(-(vertical_dist + horizontal_dist));
}



double DomainNodeNoOpt::calcEdgeNodeHeuristicScore(int src, int dst) {
  // This function did not use Kp, Kn directly, so no changes related to them.
  int n_s = src % GlobalConfig::Q, p_s = src / GlobalConfig::Q;
  int n_d = dst % GlobalConfig::Q, p_d = dst / GlobalConfig::Q;

  int vertical_dist =
      std::min(std::abs(n_s - n_d + GlobalConfig::Q) % GlobalConfig::Q,
               std::abs(n_d - n_s + GlobalConfig::Q) % GlobalConfig::Q);

  int horizontal_dist =
      std::min(std::abs(p_s - p_d + GlobalConfig::P) % GlobalConfig::P,
               std::abs(p_d - p_s + GlobalConfig::P) % GlobalConfig::P);

  return static_cast<double>(-(vertical_dist * 4 + horizontal_dist));
}




// template <int Kp, int Kn>
std::pair<double, bool> DomainNodeNoOpt::searchPathRecursively(
    int current, int destination, int previous_direction,
    std::vector<bool> &visited, double current_cost, bool prefer_right,
    bool prefer_down, int target_domain_i, int target_domain_j,
    const std::vector<std::vector<int>> &route_tables, int &recursion_depth) {

  int current_domain_id = calculateDomainId(current);
  if (visited[current_domain_id
  ]) {
    return std::make_pair(-1, false);
  }

  auto logger = spdlog::get(global_logger_name);
  recursion_depth++;
  // if (recursion_depth > 3) {
  //   logger->warn("Recursion depth: {}", recursion_depth);
  //   logger->warn("Current node: {}, Destination node: {}, "
  //                "Previous direction: {}, Current cost: {}",
  //                current, destination, previous_direction, current_cost);
  //   logger->flush();
  // }

  // Check recursion depth limit
  if (recursion_depth > MAX_RECURSE_CNT) {
    // logger->warn("Recursion limit reached: current={}, destination={}, "
    //              "previous_direction={}, recursion_depth={}",
    //              current, destination, previous_direction, recursion_depth);
    // logger->flush();
    return std::make_pair(-1, false);
  }

  const auto &banned_links = GlobalConfig::cur_banned;

  // Base case: we've reached the destination
  if (current == destination) {
    return std::make_pair(current_cost, true);
  }

  // Mark current node as visited
  visited[current_domain_id] = true;

  // Calculate current domain coordinates and ID
  const auto [current_domain_i, current_domain_j] = calcDomainCoords(current);

  // Check if we've reached the target domain
  if (current_domain_i == target_domain_i &&
      current_domain_j == target_domain_j) {
    // We're in the target domain, use intra-domain routing
    std::pair<double, bool> domain_result =
        calcE2ePathWithinDomain(current, destination, route_tables);

    if (domain_result.second) {
      return std::make_pair(current_cost + domain_result.first, true);
    } else {
      // Backtrack if no path found
      visited[current_domain_id] = false;
      return std::make_pair(-1, false);
    }
  }

  // Calculate heuristic scores for each direction
  std::map<int, double> direction_scores;
  int destination_domain_id = calculateDomainId(destination);
  const auto &border_nodes = getBorderNodes();

  // Evaluate each possible direction (1=up, 2=right, 3=down, 4=left)
  for (int direction = 1; direction <= 4; direction++) {
    // Skip if no border nodes in this direction
    if (previous_direction == getInverseDirection(direction))
      continue;

    int sample_border_node = border_nodes[current_domain_id][direction][0];
    int next_node = move(sample_border_node, direction);
    if (next_node == -1) {
      continue;
    }
    int next_domain_id = calculateDomainId(next_node);

    if (border_nodes[current_domain_id][direction].empty() ||
        visited[next_domain_id]) {
      continue;
    }

    double heuristic_score =
        calcDomainHeuristicScore(next_domain_id, destination_domain_id);
    direction_scores[direction] = heuristic_score;
  }

  // Sort directions by heuristic score (highest first)
  std::vector<std::pair<int, double>> sorted_directions;
  for (const auto &[direction, score] : direction_scores) {
    sorted_directions.push_back({direction, score});
  }

  std::sort(sorted_directions.begin(), sorted_directions.end(),
            [](const auto &a, const auto &b) { return a.second > b.second; });

  // Try each direction in order of preference
  for (const auto &[direction, score] : sorted_directions) {
    // First check if the current node itself is a border node in this direction
    auto border_nodes_in_direction = border_nodes[current_domain_id][direction];
    bool is_current_border_node =
        std::find(border_nodes_in_direction.begin(),
                  border_nodes_in_direction.end(),
                  current) != border_nodes_in_direction.end();

    if (is_current_border_node && banned_links[current][direction] != 1) {
      // Current node is a border node - try moving directly to the next domain
      int next_domain_node = move(current, direction);

      if (next_domain_node != -1 && !visited[next_domain_node]) {
        // Recursively try to find a path from the next domain
        double link_cost = calcuDelay(current, next_domain_node);
        const auto [final_cost, path_found] = searchPathRecursively(
            next_domain_node, destination, direction, visited,
            current_cost + link_cost, prefer_right, prefer_down,
            target_domain_i, target_domain_j, route_tables, recursion_depth);

        // If path found, return the result
        if (path_found) {
          return std::make_pair(final_cost, true);
        }
      }
    }
    // random the border nodes in this direction

    std::random_shuffle(border_nodes_in_direction.begin(),
                        border_nodes_in_direction.end());

    // Process each border node in the chosen direction
    for (auto border_node : border_nodes_in_direction) {
      //   // Skip the current node as we already processed it above
      if (border_node == current) {
        continue;
      }

      //   // Skip if route doesn't exist, link is banned, or node already
      //   visited
      if (!route_tables[current][border_node] ||
          banned_links[border_node][direction] == 1) {
        continue;
      }

      int border_node_dmi = calculateDomainId(border_node);
      if (border_node_dmi != current_domain_id) {
        logger->error(
            "Border node {} is not in the same domain as current node {}. "
            "Current domain ID: {}, Border node domain ID: {}",
            border_node, current, current_domain_id, border_node_dmi);
        logger->flush();
        exit(1);
      }

      const auto [path_cost, success] =
          calcE2ePathWithinDomain(current, border_node, route_tables);

      if (!success) {
        continue;
      }

      //   // Find the node in the next domain
      int next_domain_node = move(border_node, direction);

      if (next_domain_node == -1) {
        continue;
      }

      // visited[next_domain_node] = true;
      // visited[border_node] = true;
      

      //   // Recursively try to find a path from the next domain
      double new_cost =
          current_cost + path_cost + calcuDelay(border_node, next_domain_node);
      const auto [final_cost, path_found] = searchPathRecursively(
          next_domain_node, destination, direction, visited, new_cost,
          prefer_right, prefer_down, target_domain_i, target_domain_j,
          route_tables, recursion_depth);

      // If path found, return the result
      if (path_found) {
        return std::make_pair(final_cost, true);
      }
      // visited[border_node] = false;
    }
  }
  // Backtrack: mark current node as unvisited
  visited[current_domain_id] = false;

  // All directions failed, return failure result
  return std::make_pair(-1, false);
}



std::pair<double, bool> DomainNodeNoOpt::calcE2ePath(
    int src, int dst, const std::vector<std::vector<int>> &route_tables) {

  auto [I_src, J_src] = DomainNodeNoOpt::calcDomainCoords(src);
  auto [I_dst, J_dst] = DomainNodeNoOpt::calcDomainCoords(dst);

  auto logger = spdlog::get(global_logger_name);
  // logger->debug(
  //     "Start to calc Path: src={}, I_src={}, J_src={} --> dst={}, I_dst={}, J_dst={}",
  //     src, I_src, J_src, dst, I_dst, J_dst);

  if (I_src == I_dst && J_src == J_dst) {
    return DomainNodeNoOpt::calcE2ePathWithinDomain(src, dst, route_tables);
  } else {
    // Size of visited_domains should be Kp * Kn for domain IDs
    std::vector<bool> visited_domains(DomainNodeNoOpt::Kp * DomainNodeNoOpt::Kn, false);
    int recurse_cnt = 0;
    bool placeholder_prefer_right = true; // Placeholder, as their role in guided DFS is minor
    bool placeholder_prefer_down = true;  // Placeholder

    return DomainNodeNoOpt::searchPathRecursively(src, dst, 0, // 0 for initial pre_dir
                                            visited_domains, 0.0,
                                            placeholder_prefer_right, placeholder_prefer_down,
                                            I_dst, J_dst, // Target domain coordinates
                                            route_tables, recurse_cnt);
  }
//   logger->warn("Failed to find path from {} to {} in DomainNodeNoOpt::calcE2ePath", src, dst);
  return std::make_pair(-1.0, false); // Should be unreachable if searchPathRecursively returns
}

std::pair<int, int>
DomainNodeNoOpt::calcDomainCoords(int satelliteId) {
  int p_s = satelliteId / GlobalConfig::Q;
  int n_s = satelliteId % GlobalConfig::Q;

  // Use static Kp, Kn
  // Ensure GlobalConfig::P and GlobalConfig::Q are not zero, and Kp, Kn are not zero.
  // Constructor checks Kp, Kn, P, Q > 0 and divisibility.
  
  int I_s = static_cast<int>(
      std::floor(static_cast<double>(p_s) / (GlobalConfig::P / DomainNodeNoOpt::Kp)));
  int J_s = static_cast<int>(
      std::floor(static_cast<double>(n_s) / (GlobalConfig::Q / DomainNodeNoOpt::Kn)));

  return std::make_pair(I_s, J_s);
}

std::string DomainNodeNoOpt::getName() {
  // Use static Kp, Kn
  return "DomainNodeNoOpt_" + std::to_string(DomainNodeNoOpt::Kp) + "_" + std::to_string(DomainNodeNoOpt::Kn);
}

int DomainNodeNoOpt::calculateDomainId(int satelliteId) {
  auto [I_s, J_s] = DomainNodeNoOpt::calcDomainCoords(satelliteId);
  // Use static Kn
  return I_s * DomainNodeNoOpt::Kn + J_s;
}

void DomainNodeNoOpt::compute() {
  // This is an instance method, uses this->id, this->vis, this->route_table
  // Kp, Kn are not directly used here, but calculateDomainId uses them.
  
  // Initialize route_table for this node (instance member)
  // Assuming route_table is std::vector<int> as in original logic
  // If it's meant to be part of the global route_tables for calcE2ePathWithinDomain,
  // then this function would populate its row in that global table.
  // The original code seems to imply this->route_table is for paths *from this->id*.
  this->route_table.assign(GlobalConfig::N, 0); // Initialize route_table for this specific node
  this->vis.assign(GlobalConfig::N, 0);

  int current_node_domain_id = DomainNodeNoOpt::calculateDomainId(this->id);

  const auto &banned_links = GlobalConfig::cur_banned; // Future banned links for planning
  auto logger = spdlog::get(global_logger_name);

  std::queue<int> q;
  q.push(this->id);
  this->vis[this->id] = 1;

  while (!q.empty()) {
    int cur = q.front();
    q.pop();

    for (int direction = 1; direction <= 4; ++direction) {
      if (banned_links[cur][direction] == 1) {
        continue;
      }

      int nxt = move(cur, direction);
      if (nxt == -1) {
        continue;
      }
      
      // Compute is for intra-domain routing table
      int next_node_domain_id = DomainNodeNoOpt::calculateDomainId(nxt);
      if (next_node_domain_id != current_node_domain_id) {
          continue; // Only consider neighbors in the same domain for this BFS
      }

      if (this->vis[nxt] == 0) { // If not visited yet (in this BFS)
        this->vis[nxt] = this->vis[cur] + 1; // Distance
        
        // Store the first direction taken from `this->id` to reach `cur`, then to `nxt`
        if (cur == this->id) {
            this->route_table[nxt] = direction;
        } else {
            this->route_table[nxt] = this->route_table[cur]; // Propagate first step
        }
        q.push(nxt);
      } 
      // Tie-breaking: if same distance, prefer smaller first_direction
      // This part of the original code for route_table was specific.
      // The logic below is from the original snippet to preserve its tie-breaking for SP.
      else if (this->vis[nxt] == this->vis[cur] + 1) {
          int first_direction_to_cur = (cur == this->id) ? direction : this->route_table[cur];
          // If route_table[nxt] is 0 (uninitialized for path) or new path has better first_direction
          if (this->route_table[nxt] == 0 || first_direction_to_cur < this->route_table[nxt]) {
              this->route_table[nxt] = first_direction_to_cur;
              // Note: q.push(nxt) is not called here as nxt is already visited or at same level.
              // Standard BFS for shortest path usually doesn't re-add to queue if vis[nxt]!=0.
              // If this is for multi-path or specific tie-breaking for routes, it's kept.
              // However, for simple shortest path, one usually doesn't update route_table if vis[nxt] != 0 and vis[nxt] <= vis[cur]+1.
              // The original logic `if (this->route_table[nxt] == 0 || first_direction < this->route_table[nxt])`
              // suggests `this->route_table[nxt]` stores the *first hop direction* from `this->id`.
          }
      }
    }
  }
}