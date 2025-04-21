// domain_heuristic_node.tpp
// No include guard needed here - this file is meant to be included by the .hpp

// Include headers needed specifically for the implementations
#include "base.hpp"
#include "satnet/domain_heuristic.hpp"
#include "satnet/utils.hpp"
#include <cmath> // For std::floor
#include <cstdio>
#include <limits> // Potentially for checking invalid IDs or distances
#include <map>
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
DomainHeuristicNode<Kp, Kn>::createBorderNodes() {

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
template <int Kp, int Kn>
std::pair<double, bool> DomainHeuristicNode<Kp, Kn>::calcE2ePathWithinDomain(
    int src, int dst, const std::vector<std::vector<int>> &route_tables) {
  int val = 0;
  int cur = src;
  while (cur != dst) {
    int nxt_dir = route_tables[cur][dst];
    if (!nxt_dir) {
      return std::make_pair(-1, false);
    }
    int nxt = move(cur, nxt_dir);
    if (nxt == -1) {
      return std::pair<double, bool>(-1, false);
    }
    val += calcuDelay(cur, nxt);
    cur = nxt;
  }
  return std::pair<double, bool>(val, true);
}

template <int Kp, int Kn>
double DomainHeuristicNode<Kp, Kn>::calculateHeuristicScore(int src, int dst) {

  // int n_s = src % GlobalConfig::Q, p_s = src / GlobalConfig::Q;
  // int n_d = dst % GlobalConfig::Q, p_d = dst / GlobalConfig::Q;
  auto [I_s, J_s] = calcDomainCoords(src);
  auto [I_d, J_d] = calcDomainCoords(dst);

  int vertical_dist =
      std::min(std::abs(J_s - J_d  + Kn) % Kn,
               std::abs(J_d - J_s + Kn) % Kn); // 垂直方向上的距离

  int horizontal_dist = std::min(std::abs(I_s - I_d + Kp) % Kp,
                                  std::abs(I_d - I_s + Kp) % Kp);

  return vertical_dist + horizontal_dist;
}

template <int Kp, int Kn>
std::pair<double, bool> DomainHeuristicNode<Kp, Kn>::findPathRecursive(
    int cur, int dst, int pre_dir, std::vector<bool> &visited, double val,
    bool prefer_right, bool prefer_down, int target_I, int target_J,
    const std::vector<std::vector<int>> &route_tables, int recurse_cnt) {

  auto logger = spdlog::get(global_logger_name);
  if (recurse_cnt > MAX_RECURSE_CNT) {
    logger->warn("Recursion limit reached: cur={}, dst={}, pre_dir={}, "
                 "recurse_cnt={}",
                 cur, dst, pre_dir, recurse_cnt);
    return std::make_pair(-1, false);
  }
  const auto &banned = GlobalConfig::futr_banned;
  // 递归基本情况
  if (cur == dst) {
    return std::make_pair(val, true);
  }

  // 标记当前节点为已访问
  visited[cur] = true;

  // 检查当前节点是否已在目标域中
  const auto [cur_I, cur_J] = calcDomainCoords(cur);
  if (cur_I == target_I && cur_J == target_J) {
    // 当前节点已在目标域中，使用域内路由
    std::pair<double, bool> domain_result =
        calcE2ePathWithinDomain(cur, dst, route_tables);

    if (domain_result.second) {
      return std::make_pair(val + domain_result.first, true);
    } else {
      visited[cur] = false; // 回溯
      return std::make_pair(-1, false);
    }
  }

  // 计算水平和垂直方向上的跳数
  // int r_hop_cnt = (target_I - cur_I + Kp) % Kp;    // 右跳数
  // int l_hop_cnt = (cur_I - target_I + Kp) % Kp;    // 左跳数
  // int down_hop_cnt = (target_J - cur_J + Kn) % Kn; // 下跳数
  // int up_hop_cnt = (cur_J - target_J + Kn) % Kn;   // 上跳数

  // 创建方向优先级数组，根据prefer_right和prefer_down设置顺序
  std::vector<std::pair<int, int>> directions; // pair<方向, 跳数>

  // 计算每个方向的启发式评分
  std::map<int, double> direction_scores;

  for (int i = 1; i <= 4; i++) {
    int nxt = move(cur, i);

    int score = calculateHeuristicScore(nxt, dst);
    direction_scores[i] = score;
  }

  // if (r_hop_cnt > 0) {
  //   direction_scores[2] = prefer_right ? 100.0 : 50.0; // 右
  // }
  // if (l_hop_cnt > 0) {
  //   direction_scores[4] = !prefer_right ? 100.0 : 50.0; // 左
  // }

  // // 垂直方向评分
  // if (down_hop_cnt > 0) {
  //   direction_scores[3] = prefer_down ? 80.0 : 40.0; // 下
  // }
  // if (up_hop_cnt > 0) {
  //   direction_scores[1] = !prefer_down ? 80.0 : 40.0; // 上
  // }

  // 转换成vector并按分数排序
  std::vector<std::pair<int, double>> sorted_directions;
  for (const auto &[dir, score] : direction_scores) {
    sorted_directions.push_back({dir, score});
  }

  std::sort(sorted_directions.begin(), sorted_directions.end(),
            [](const auto &a, const auto &b) { return a.second > b.second; });

  // 尝试每个方向
  for (const auto &[dir, score] : sorted_directions) {
    // 如果存在边界节点，尝试路由
    const auto &border_nodes = getBorderNodes();
    for (auto nxt : border_nodes[cur_I][dir]) {
      // 检查是否有路由、是否被禁用、是否已访问
      if (!route_tables[cur][nxt] || banned[nxt][dir] == 1 || visited[nxt]) {
        continue;
      }

      // 计算到边界节点的路径值
      const auto [part_val, success] =
          calcE2ePathWithinDomain(cur, nxt, route_tables);
      if (!success) {
        continue;
      }

      int nxt_nxt = move(nxt, dir);

      if (nxt_nxt == -1 || visited[nxt_nxt]) {
        continue;
      }

      const auto [final_val, path_found] = findPathRecursive(
          nxt_nxt, dst, dir, visited, val + part_val + calcuDelay(nxt, nxt_nxt),
          prefer_right, prefer_down, target_I, target_J, route_tables,
          recurse_cnt + 1);

      // 如果找到路径，返回结果
      if (path_found) {
        return std::make_pair(final_val, true);
      }
    }
  }

  // 回溯：标记当前节点为未访问
  visited[cur] = false;

  // 所有方向都失败，返回失败结果
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
  // logger->debug("Start to calc Path: src=%d, I_src=%d, J_src=%d --> dst=%d, "
  //               "I_dst=%d, J_dst=%d\n",
  //               src, I_src, J_src, dst, I_dst, J_dst);
  // logger->debug(
  //     "Start to calc Path: src={}, I_src={}, J_src={} --> dst={}, I_dst={}, "
  //     "J_dst={}",
  //     src, I_src, J_src, dst, I_dst, J_dst);

  if (I_src == I_dst && J_src == J_dst) {
    return calcE2ePathWithinDomain(src, dst, route_tables);
  } else {

    // I_src = src / GlobalConfig::Q, J_src = src % GlobalConfig::Q;
    // I_dst = dst / GlobalConfig::Q, J_dst = dst % GlobalConfig::Q;

    // printf("Start finding path from %d to %d\n", src, dst);
    std::vector<bool> visited(GlobalConfig::N, false);

    // 计算正确的跨域启发信息
    // int r_hop_cnt = (I_dst - I_src + Kp) % Kp;
    // int l_hop_cnt = (I_src - I_dst + Kp) % Kp;
    // int up_hop_cnt = (J_src - J_dst + Kn) % Kn;
    // int down_hop_cnt = (J_dst - J_src + Kn) % Kn;

    // 确定优先方向
    // bool prefer_right = (r_hop_cnt <= l_hop_cnt);
    // bool prefer_down = (down_hop_cnt <= up_hop_cnt);

    bool prefer_right = 1, prefer_down = 1;

    // 调用递归函数
    return findPathRecursive(src, dst, -1, visited, 0, prefer_right,
                             prefer_down, I_dst, J_dst, route_tables, 0);
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
  return "DomainHeuristicNode";
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