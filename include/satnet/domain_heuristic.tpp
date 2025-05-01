// domain_heuristic_node.tpp
// No include guard needed here - this file is meant to be included by the .hpp

// Include headers needed specifically for the implementations
#include "base.hpp"
#include "satnet/domain_heuristic.hpp"
#include "satnet/utils.hpp"
#include <cmath> // For std::floor
#include <cstdio>
#include <cstdlib>
#include <limits> // Potentially for checking invalid IDs or distances
#include <map>
#include <set>
#include <stdexcept> // For potential error handling (e.g., invalid config)
// --- Constructor Definition ---
#include <concepts>
#include <spdlog/spdlog.h>

//  border_nodes(            // Initialize the 3D vector border_nodes
//   std::max(Kp, Kn),    // Dimension 1 size = max(Kp, Kn)
//   std::vector<std::vector<short>>( // The value for the outer vector (a
//                                    // 2D vector)
//       5,                           // Dimension 2 size = 5
//       std::vector<short>()         // The value for the middle vector:
//                                    // A default-constructed (empty)
//                                    // std::vector<short>
//       ))

template <int Kp, int Kn>
DomainHeuristicNode<Kp, Kn>::DomainHeuristicNode(int id)
    : BaseNode(id),           // Initialize base class
      vis(GlobalConfig::N, 0) // Initialize vis (keeping previous logic)
{

  if (GlobalConfig::Q <= 0 || GlobalConfig::P <= 0) {
    throw std::runtime_error(
        "GlobalConfig::Q and GlobalConfig::P must be positive.");
  }

  if (Kp <= 0 || Kn <= 0) {
    throw std::runtime_error("Kp and Kn must be positive.");
  }

  if (GlobalConfig::P % Kp != 0) {
    throw std::runtime_error("GlobalConfig::P must be divisible by Kp.");
  }

  if (GlobalConfig::Q % Kn != 0) {
    throw std::runtime_error("GlobalConfig::Q must be divisible by Kn.");
  }
}

template <int Kp, int Kn>
std::vector<std::vector<std::vector<short>>>
DomainHeuristicNode<Kp, Kn>::initializeBorderNodes() {

  // 1. Create the vector structure
  // Use std::max with an initializer list for clarity if Kp or Kn could be 0
  size_t domain_max_side_length = static_cast<size_t>(
      std::max({Kp * Kn + 1, 1})); // Ensure size >= 1 maybe?
  std::vector<std::vector<std::vector<short>>> nodes(
      domain_max_side_length,
      std::vector<std::vector<short>>(5, std::vector<short>()));

  auto logger = spdlog::get(global_logger_name);

  // printf("Creating border nodes...\n");
  // printf("Kp=%d, Kn=%d, domain_max_side_length=%zu\n", Kp, Kn,
  //        domain_max_side_length);

  logger->info("Creating border nodes...");
  logger->info("Kp={}, Kn={}, domain_max_side_length={}", Kp, Kn,
               domain_max_side_length);

  // 2. Perform initialization logic
  for (int i = 0; i < GlobalConfig::N; ++i) {
    int cur_dmid = calculateDomainId(i);

    for (int j = 1; j < 5; ++j) { // Directions 1-4
      int nxt = move(i, j);       // Assumes move is accessible
      if (nxt == -1)
        continue;

      int nxt_dmid = calculateDomainId(nxt);
      // Optional: Check nxt_dmid validity too

      if (nxt_dmid != cur_dmid) {
        // printf("Adding border node: cur_dmid=%d, nxt_dmid=%d, i=%d, j=%d\n",
        //        cur_dmid, nxt_dmid, i, j);
        nodes[cur_dmid][j].push_back(static_cast<short>(i));
      }
    }
  }
  // 3. Return the initialized vector
  return nodes;
}

// 域内路由辅助函数
// TODO: fix possible bug
template <int Kp, int Kn>
std::pair<double, bool> DomainHeuristicNode<Kp, Kn>::calcE2ePathWithinDomain(
    int src, int dst, const std::vector<std::vector<int>> &route_tables) {
  int val = 0;
  int cur = src;
  auto logger = spdlog::get(global_logger_name);
  // std::set<int> visited; // Changed from std::set<int> visited();
  // visited.insert(cur);
  // return std::make_pair(-1, false);
  int cnt = 0;
  int cur_dmid = calculateDomainId(cur);
  while (cur != dst) {

    cnt++;
    if (cnt * Kp * Kn > 2 * GlobalConfig::N) {
      // logger->error("Infinite loop detected in calcE2ePathWithinDomain");
      // logger->flush();
      return std::make_pair(-1, false);
    }
    int nxt_dir = route_tables[cur][dst];

    if (nxt_dir == -1) {

      return std::make_pair(-1, false);
    }
    int nxt = move(cur, nxt_dir);
    int nxt_dmid = calculateDomainId(nxt);
    // if (nxt == -1 || nxt_dmid != cur_dmid ) {

    //   return std::pair<double, bool>(-1, false);
    // }
    // visited.insert(nxt);

    if (nxt == -1 || nxt_dmid != cur_dmid ||
        GlobalConfig::cur_banned[cur][nxt_dir] == 1) {
      // logger->error("Invalid move from {} to {} in direction {}", cur, nxt,
      //               nxt_dir);
      // logger->flush();
      return std::pair<double, bool>(-1, false);
    }

    val += calcuDelay(cur, nxt);
    cur = nxt;
  }
  return std::pair<double, bool>(val, true);
}

template <int Kp, int Kn>
double DomainHeuristicNode<Kp, Kn>::calcDomainHeuristicScore(int src_dmid,
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

  return static_cast<double>(-(vertical_dist * 4 + horizontal_dist));
}

template <int Kp, int Kn>
double DomainHeuristicNode<Kp, Kn>::calcEdgeNodeHeuristicScore(int src,
                                                               int dst) {
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

template <int Kp, int Kn>
std::pair<double, bool> DomainHeuristicNode<Kp, Kn>::searchPathRecursively(
    int current, int destination, int previous_direction,
    std::vector<bool> &visited, double current_cost, bool prefer_right,
    bool prefer_down, int target_domain_i, int target_domain_j,
    const std::vector<std::vector<int>> &route_tables, int &recursion_depth) {

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
  visited[current] = true;

  // Calculate current domain coordinates and ID
  const auto [current_domain_i, current_domain_j] = calcDomainCoords(current);
  int current_domain_id = calculateDomainId(current);

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
      visited[current] = false;
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
    if (border_nodes[current_domain_id][direction].empty() || banned_links[current][direction] == 1) {
      continue;
    }

    // Use the first border node to estimate the domain we'd reach
    int sample_border_node = border_nodes[current_domain_id][direction][0];
    int next_node = move(sample_border_node, direction);

    // Skip if move would be invalid
    if (next_node == -1) {
      continue;
    }

    int next_domain_id = calculateDomainId(next_node);
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
    // auto self = this; // <--- 移除这一行

    sort(border_nodes_in_direction.begin(), border_nodes_in_direction.end(),
         [destination](int a, int b) { // <--- 移除 self 捕获
           // 使用类名:: 方式调用 static 函数
           return DomainHeuristicNode<Kp, Kn>::calcEdgeNodeHeuristicScore(
                      a, destination) >
                  DomainHeuristicNode<Kp, Kn>::calcEdgeNodeHeuristicScore(
                      b, destination);
         });

    // Process each border node in the chosen direction
    for (auto border_node : border_nodes_in_direction) {
      //   // Skip the current node as we already processed it above
      if (border_node == current) {
        continue;
      }

      //   // Skip if route doesn't exist, link is banned, or node already
      //   visited
      if (!route_tables[current][border_node] ||
          banned_links[border_node][direction] == 1 || visited[border_node]) {
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

      if (next_domain_node == -1 || visited[next_domain_node]) {
        continue;
      }

      // visited[next_domain_node] = true;
      visited[border_node] = true;

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
      visited[border_node] = false;
    }
  }
  // Backtrack: mark current node as unvisited
  visited[current] = false;

  // All directions failed, return failure result
  return std::make_pair(-1, false);
}

template <int Kp, int Kn>
std::pair<double, bool> DomainHeuristicNode<Kp, Kn>::calcE2ePath(
    int src, int dst, const std::vector<std::vector<int>> &route_tables) {

  // return std::pair<double,bool>(-1,false);
  const auto [I_src, J_src] = calcDomainCoords(src);
  const auto [I_dst, J_dst] = calcDomainCoords(dst);

  // Debugging output

  auto logger = spdlog::get(global_logger_name);

  logger->debug(
      "Start to calc Path: src={}, I_src={}, J_src={} --> dst={}, I_dst={}, "
      "J_dst={}",
      src, I_src, J_src, dst, I_dst, J_dst);

  if (I_src == I_dst && J_src == J_dst) {
    return calcE2ePathWithinDomain(src, dst, route_tables);
  } else {

    // I_src = src / GlobalConfig::Q, J_src = src % GlobalConfig::Q;
    // I_dst = dst / GlobalConfig::Q, J_dst = dst % GlobalConfig::Q;

    // printf("Start finding path from %d to %d\n", src, dst);
    std::vector<bool> visited(GlobalConfig::N * 2, false);

    bool prefer_right = 1, prefer_down = 1;

    int recurse_cnt = 0;

    // 调用递归函数
    return searchPathRecursively(src, dst, -1, visited, 0, prefer_right,
                                 prefer_down, I_dst, J_dst, route_tables,
                                 recurse_cnt);
  }
  printf(
      "Fail to find path from %d to %d in DomainHeuristicNode::calcE2ePath\n",
      src, dst);
  return std::pair<double, bool>(-1, false);
}

template <int Kp, int Kn>
std::pair<int, int>
DomainHeuristicNode<Kp, Kn>::calcDomainCoords(int satelliteId) {

  int p_s = satelliteId / GlobalConfig::Q;
  int n_s = satelliteId % GlobalConfig::Q;

  // Use static_cast for clarity. Ensure P isn't zero.
  int I_s = static_cast<int>(
      std::floor(static_cast<double>(p_s) / (GlobalConfig::P / Kp)));
  int J_s = static_cast<int>(
      std::floor(static_cast<double>(n_s) / (GlobalConfig::Q / Kn)));

  return std::make_pair(I_s, J_s);
}

// --- Member Function Definitions ---

template <int Kp, int Kn> std::string DomainHeuristicNode<Kp, Kn>::getName() {
  // Simple override
  return "DomainHeuristic_" + std::to_string(Kp) + "_" + std::to_string(Kn);
}

template <int Kp, int Kn>
int DomainHeuristicNode<Kp, Kn>::calculateDomainId(int satelliteId) {
  // Relies on the static helper function and template parameter Kp
  auto [I_s, J_s] = calcDomainCoords(satelliteId);
  // Potential issue if Kp or Kn is 0, resulting in non-unique IDs or division
  // by zero downstream.
  return I_s * Kn + J_s;
}

template <int Kp, int Kn> void DomainHeuristicNode<Kp, Kn>::compute() {

  int current_domain_id = calculateDomainId(id); // Calculate only once per node
  for (int i = 0; i < GlobalConfig::N; ++i) {
    // int node_dm_id = calculateDomainId(i);
    // if (node_dm_id != current_domain_id) {
    //   continue; // Skip nodes in different domains
    // }
    route_table[i] = 0; // Initialize route_table
    vis[i] = 0;
  }

  const auto &banned =
      GlobalConfig::cur_banned; // Assuming pointer access is correct

  auto logger = spdlog::get(global_logger_name);

  std::queue<int> q;

  q.push(id);
  vis[id] = 1;

  while (!q.empty()) {
    int cur = q.front();
    q.pop();

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
      // if (calculateDomainId(nxt) != current_domain_id) {
      //   continue; // Skip neighbors in different domains
      // }
      int nxt_dm_id = calculateDomainId(nxt);

      if (nxt == -1) {
        continue; // Skip invalid moves or different domains
      }

      // Standard BFS check: if neighbor not visited yet
      if (vis[nxt] == 0) {
        vis[nxt] = vis[cur] + 1;
        // route_table[nxt] = direction; // Store predecessor in route_table
        if (nxt_dm_id == current_domain_id)
          q.push(nxt);
      }

      if (this->vis[nxt] == this->vis[cur] + 1) {

        int first_direction =
            (cur == this->id) ? direction : this->route_table[cur];

        if (this->route_table[nxt] == 0 ||
            first_direction < this->route_table[nxt]) {
          this->route_table[nxt] = first_direction;
        }
      }
    }
  }
}