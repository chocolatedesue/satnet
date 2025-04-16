#pragma once

#include "base.hpp"
#include "json.hpp"
#include "utils.hpp"
// #include <iostream>
#include <queue>


template <int Kp, int Kn> 
class DomainHeuristicNode : public BaseNode {

  std::vector<int> vis;
  


public:
  DomainHeuristicNode(nlohmann::json config, int id, World world)
      : BaseNode(config, id, world) {
    // vis.resize(Kp * Kn, -1);
    // route_table.resize(Kp * Kn, 0);
  }

  static void DfsE2ePath(int src, int dst, const std::vector<int> route_table) {
    int is_vertical = check_lla_status();
    auto [I_src, J_src] =
        calcDomainCoords(src); // 计算源节点的分域坐标
    auto [I_dst, J_dst] =
        calcDomainCoords(dst); // 计算目标节点的分域坐标

    if (I_src == I_dst && J_src == J_dst) {
      int val = 0, cur = src;
      while (cur != dst) {
        int nxt = route_table[cur];
        val += calcuDelay(cur, nxt);
        cur = nxt ;
      }
    }
    return;
  }


  std::string getName() override { return "DomainHeuristicNode"; }

  // std::vector<int> getRouteTable() {
  //   // Return the route table for this node
  //   return route_table;
  // }

  static std::pair<int, int> calcDomainCoords(int satelliteId) {
    // 1. 反解 p(s) 和 n(s)
    int n_s = satelliteId % GlobalConfig::Q;
    int p_s = satelliteId / GlobalConfig::Q; // 使用整数除法

    // 2. 应用分域函数
    int I_s =
        floor((double)p_s * Kp / GlobalConfig::P); // 显式转换为 double 以避免整数除法问题
    int J_s =
        floor((double)n_s * Kn / GlobalConfig::P); // 显式转换为 double 以避免整数除法问题

    return std::make_pair(I_s, J_s);
  }

  int calculateDomainId(int satelliteId) {

    auto [I_s, J_s] = calcDomainCoords(satelliteId);
    return J_s * Kp + I_s;
  }

  void compute() override {
    auto &banned = *futr_banned;
    // impl bfs
    std::queue<int> q;
    q.push(id);
    vis[id] = 1;
    while (!q.empty()) {
      int cur = q.front();
      q.pop();
      for (int i = 1; i < 5; i++) {
        if (banned[cur][i] == 1) {
          continue;
        }
        int nxt = move(cur,i);
        if (calculateDomainId(cur) != calculateDomainId(nxt)) {
          continue;
        }
        if (vis[nxt] == -1) {
          vis[nxt] = 1;
          q.push(nxt);
          route_table[nxt] = cur;
        }
      }
    }
  }
};