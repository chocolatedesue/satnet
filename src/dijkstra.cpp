#include "satnet/dijkstra.hpp"
#include "satnet/utils.hpp" // 包含对应的头文件
#include <cmath>
#include <limits>
#include <queue>
#include <stdexcept>

// Note: Assumes N, GlobalConfig::sat_pos, move, cur_banned, futr_banned,
// route_table
//       are accessible and correctly defined via included headers.

// --- DijkstraNode Implementation ---

DijkstraNode::DijkstraNode(int id)
    : BaseNode(id), // Or DisCoRouteNode(...)
      vis(GlobalConfig::N), dist(GlobalConfig::N) {}

double DijkstraNode::getDist(int id_a, int id_b) {

  double res_sq = 0.0;
  for (int i = 0; i < 3; ++i) { // Assuming 3D coordinates
    double d =
        GlobalConfig::sat_pos.at(id_a)[i] - GlobalConfig::sat_pos.at(id_b)[i];
    res_sq += d * d;
  }
  return sqrt(res_sq) * 1000.0; // Assumes coords in km, result in meters
}

double DijkstraNode::calcuDelay(int a, int b) {
  double distance = getDist(a, b);

  // proc + prop delay (ms)
  return GlobalConfig::proc_delay + GlobalConfig::prop_delay_coef * distance /
                                        GlobalConfig::prop_speed * 1000.0;
}

std::string DijkstraNode::getName() { return "DijkstraBase"; }

void DijkstraNode::compute() {
  for (int i = 0; i < GlobalConfig::N; ++i) {
    vis[i] = 0;
    dist[i] = std::numeric_limits<double>::max();
    route_table[i] = 0; // 0 usually means invalid/no route or self
  }

  // Min-heap: stores {-distance, node_id}
  std::priority_queue<std::pair<double, int>> pq;

  dist[id] = 0.0;
  pq.push({0.0, id});

  while (!pq.empty()) {
    double d_u = -pq.top().first;
    int u = pq.top().second;
    pq.pop();

    if (d_u > dist[u])
      continue; // Skip if found shorter path already
    vis[u] = 1;

    // Explore neighbors (ports 1-4)
    for (int port = 1; port <= 4; ++port) {
      int v = move(u, port);
      if (v < 0 || v >= GlobalConfig::N)
        continue;

      double w = calcuDelay(u, v);
      if (w == std::numeric_limits<double>::max())
        continue;

      // Relaxation
      if (dist[u] + w < dist[v]) {
        dist[v] = dist[u] + w;
        pq.push({-dist[v], v});
        // Update next hop: port from source, or same as path to u
        route_table[v] = (u == id) ? port : route_table[u];
      }
    }
  }
}

// --- DijkstraProbeNode Implementation ---

DijkstraProbeNode::DijkstraProbeNode(int id) : DijkstraNode(id) {}

std::string DijkstraProbeNode::getName() { return "DijkstraProbe"; }

void DijkstraProbeNode::compute() {
  if (!cur_banned) {
    DijkstraNode::compute(); // Fallback if no banned data
    return;
  }
  computeWithBannedPorts(cur_banned);
}

void DijkstraProbeNode::computeWithBannedPorts(
    const std::vector<std::array<int, 5>> *banned_ptr) {
  const auto &banned = *banned_ptr;

  for (int i = 0; i < GlobalConfig::N; ++i) {
    vis[i] = 0;
    dist[i] = std::numeric_limits<double>::max();
    route_table[i] = 0;
  }

  std::priority_queue<std::pair<double, int>> pq;

  dist[id] = 0.0;
  pq.push({0.0, id});

  while (!pq.empty()) {
    double d_u = -pq.top().first;
    int u = pq.top().second;
    pq.pop();

    if (d_u > dist[u])
      continue;
    vis[u] = 1;

    for (int port = 1; port <= 4; ++port) {
      // Added bounds check for safety.
      if (u < 0 || u >= banned.size() || port < 0 || port >= banned[u].size()) {
        continue;
      }
      // Skip if this port is banned for node u
      if (banned[u][port]) {
        continue;
      }

      int v = move(u, port);
      if (v < 0 || v >= GlobalConfig::N)
        continue;

      double w = calcuDelay(u, v);
      if (w == std::numeric_limits<double>::max())
        continue;

      if (dist[u] + w < dist[v]) {
        dist[v] = dist[u] + w;
        pq.push({-dist[v], v});
        route_table[v] = (u == id) ? port : route_table[u];
      }
    }
  }
}

// --- DijkstraPredNode Implementation ---

DijkstraPredNode::DijkstraPredNode(int id) : DijkstraProbeNode(id) {}

std::string DijkstraPredNode::getName() { return "DijkstraPred"; }

void DijkstraPredNode::compute() {
  if (!futr_banned) {
    DijkstraNode::compute(); // Fallback
    return;
  }
  // Reuses probe logic with future banned data
  computeWithBannedPorts(futr_banned);
}