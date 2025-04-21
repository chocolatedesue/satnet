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

template <int Kp, int Kn> class DomainHeuristicNode : public BaseNode {

  std::vector<int> vis;

public:
  // --- Constructor ---
  DomainHeuristicNode(int id);

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

  static std::pair<double, bool>
  findPathRecursive(int cur, int dst, int pre_dir, std::vector<bool> &visited,
                    double val, bool prefer_right, bool prefer_down,
                    int target_I, int target_J,
                    const std::vector<std::vector<int>> &route_tables, int recurse_cnt);

  static double calculateHeuristicScore(int src, int dst);

  static std::vector<std::vector<std::vector<short>>> createBorderNodes();
  
  inline static const std::vector<std::vector<std::vector<short>>> &
  getBorderNodes() {
    // The static local variable 'instance' will be initialized
    // thread-safely on the first call to getBorderNodes().
    static const std::vector<std::vector<std::vector<short>>> instance =
        createBorderNodes();
    return instance;
  }

  // 使用 IILE 初始化 inline static 成员
  // inline static std::vector<std::vector<std::vector<short>>> border_nodes =
  // [] {
  //   // 1. 创建最终要返回的 vector 结构
  //   //    使用 std::max 来确定第一维的大小
  //   std::vector<std::vector<std::vector<short>>> nodes(
  //       std::max(Kp, Kn),
  //       std::vector<std::vector<short>>(5, std::vector<short>()));

  //   // 2. 执行你的初始化逻辑
  //   //    确保 GlobalConfig::N, calculateDomainId, 和 move 在此作用域可见
  //   //    calculateDomainId 是本类的静态成员，可以直接调用
  //   //    move 假设是全局函数或可通过包含 utils.hpp 访问
  //   //    GlobalConfig::N 假设可通过包含 utils.hpp 访问

  //   if (nodes.empty() && GlobalConfig::N > 0) {
  //     // 如果 Kp 和 Kn 都是 0，但 N > 0，可能存在问题
  //     // 可以根据需要添加错误处理或日志
  //     // throw std::logic_error("DomainHeuristicNode: Kp and Kn cannot both
  //     be
  //     // zero if N > 0"); 或者根据实际情况调整
  //   }

  //   for (int i = 0; i < GlobalConfig::N; ++i) {
  //     int cur_dmid = calculateDomainId(i);

  //     // 安全检查：确保 cur_dmid 是有效索引
  //     if (cur_dmid < 0 || static_cast<size_t>(cur_dmid) >= nodes.size()) {
  //       // 处理无效的 domain ID，例如抛出异常或记录错误
  //       // fprintf(stderr, "Warning: Invalid current domain ID %d calculated
  //       for
  //       // satellite %d\n", cur_dmid, i);
  //       continue; // 跳过这个卫星
  //     }

  //     for (int j = 1; j < 5; ++j) { // 方向从 1 到 4
  //       // 假设 move 函数在 utils.hpp 或 base.hpp 中定义或声明
  //       int nxt = move(i, j);
  //       if (nxt == -1) {
  //         continue; // 没有邻居或移动无效
  //       }

  //       int nxt_dmid = calculateDomainId(nxt);
  //       // 可选：对 nxt_dmid 也进行检查

  //       if (nxt_dmid != cur_dmid) {
  //         // 确保 cur_dmid 和 j 是有效索引 (j 已经是 1-4，所以
  //         // nodes[cur_dmid][j] 应该是安全的)
  //         nodes[cur_dmid][j].push_back(
  //             static_cast<short>(i)); // 将 int 转换为 short
  //       }
  //     }
  //   }

  //   // 3. 返回初始化完成的 vector
  //   return nodes;
  // }(); // 注意这里的 () 立即调用 lambda
};

// --- Include the Template Implementation File ---
#include "domain_heuristic.tpp"

// 注意： calculateDomainId 和 move 函数的定义（或声明）
// 必须在 DomainHeuristicNode 类定义之前被编译器看到，
// 或者至少 calculateDomainId 的声明要在 lambda 使用它之前。
// move 函数的定义/声明通常来自你包含的 utils.hpp 或 base.hpp。
// GlobalConfig::N 也需要来自 utils.hpp。