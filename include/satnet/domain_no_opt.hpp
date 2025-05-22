// domain_heuristic_node.hpp
#pragma once

#include "base.hpp"
#include "utils.hpp" // 需要 GlobalConfig 和 move 函数
#include <algorithm> // for std::max
#include <concepts>
#include <queue>
#include <stdexcept> // Optional: for error handling
#include <string>
#include <utility> // for std::pair
#include <vector>

// Forward declarations
// class SomeType;


class DomainNodeNoOpt : public BaseNode {

// private:
    
public:
  // --- Constructor ---
  inline static const int Kp = 7, Kn = 10; // 这里的 Kp 和 Kn 是类的成员变量
  std::vector<int> vis;

  DomainNodeNoOpt(int id);

  // static 函数声明需要在使用它们的 lambda 之前（或者至少被声明）
  // calculateDomainId 的声明已在 lambda 之前，这是好的。
  static std::pair<int, int> calcDomainCoords(int satelliteId);
  static int calculateDomainId(int satelliteId);

  void compute() override;
  std::string getName() override;

  static std::pair<double, bool>
  calcE2ePath(int src, int dst,
              const std::vector<std::vector<int>> &route_tables);

  static std::pair<double, bool>
  calcE2ePathWithinDomain(int src, int dst,
                          const std::vector<std::vector<int>> &route_tables);

  static std::pair<double, bool> searchPathRecursively(
      int cur, int dst, int pre_dir, std::vector<bool> &visited, double val,
      bool prefer_right, bool prefer_down, int target_I, int target_J,
      const std::vector<std::vector<int>> &route_tables, int &recurse_cnt);

  static double calcDomainHeuristicScore(int src, int dst);

  static std::vector<std::vector<std::vector<short>>> initializeBorderNodes();

  static double calcEdgeNodeHeuristicScore(int src, int dst);

  inline static const std::vector<std::vector<std::vector<short>>> &
  getBorderNodes() {
    // The static local variable 'instance' will be initialized
    // thread-safely on the first call to getBorderNodes().
    static const std::vector<std::vector<std::vector<short>>> instance =
        initializeBorderNodes();
    return instance;
  }


};

// // --- Include the Template Implementation File ---
// #include "domain_heuristic.tpp"

// // 注意： calculateDomainId 和 move 函数的定义（或声明）
// // 必须在 DomainHeuristicNode 类定义之前被编译器看到，
// // 或者至少 calculateDomainId 的声明要在 lambda 使用它之前。
// // move 函数的定义/声明通常来自你包含的 utils.hpp 或 base.hpp。
// // GlobalConfig::N 也需要来自 utils.hpp。