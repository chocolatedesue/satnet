#pragma once

// #include <iostream>
#include <array>
#include <concepts>
#include <string>
#include <vector>

class BaseNode {
public:
  int id;
  std::vector<int> route_table;

  std::vector<std::array<int, 5>> *cur_banned;
  std::vector<std::array<int, 5>> *futr_banned;
  std::vector<std::array<double, 3>> *sat_pos;
  std::vector<std::array<double, 3>> *sat_lla;

  BaseNode(int id);
  virtual ~BaseNode() = default;

  // virtual int move(int id, int dir);

  virtual void compute();

  virtual std::string getName();
  // This function is called when the node is created.
  virtual void init();

  static std::pair<double, bool>
  calcE2ePath(int src, int dst,
              const std::vector<std::vector<int>> &route_tables) ;
  virtual const std::vector<int> &getRouteTable() const { return route_table; }
// virtual const int &getDirectionByIdInRouteTable(int id) const {
//     return route_table[id];
//   }
};

// 定义一个概念：T 必须“派生自” BaseNode（或就是 BaseNode）
template <typename T>
concept DerivedFromBaseNode = std::derived_from<T, BaseNode>;
