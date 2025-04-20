#pragma once

#include <array>
#include <map>
#include <optional>
#include <string>
#include <utility> // 需要包含 <utility> 来声明 std::pair
#include <vector>



// --- 类型定义 ---
enum Direction { UP = 1, RIGHT = 2, DOWN = 3, LEFT = 4 };

// --- 函数声明 ---
int check_lla_status();
double getDist(int a, int b); // 移除 static
double calcuDelay(int a, int b);

// --- Struct 定义 (保持在头文件) ---
struct World {
  std::vector<std::array<int, 5>> *cur_banned;
  std::vector<std::array<int, 5>> *futr_banned;
  std::vector<std::array<double, 3>> *sat_pos; // ICRS coordination (km)
  std::vector<std::array<double, 3>>
      *sat_lla;                 // Latitude, longitude, attitude (km)
  std::vector<double> *sat_vel; // Movement direction? (单位?)

  // 构造函数声明（可选：也可以将实现移到 .cpp）
  World(std::vector<std::array<int, 5>> *cur_banned,
        std::vector<std::array<int, 5>> *futr_banned,
        std::vector<std::array<double, 3>> *sat_pos,
        std::vector<std::array<double, 3>> *sat_lla,
        std::vector<double> *sat_vel);

  // 或者，如果构造函数很简单，像原来那样内联定义在结构体内部也是可以的：
  // World(std::vector<std::array<int, 5>> *cur_banned,
  //       std::vector<std::array<int, 5>> *futr_banned,
  //       std::vector<std::array<double, 3>> *sat_pos,
  //       std::vector<std::array<double, 3>> *sat_lla,
  //       std::vector<double> *sat_vel)
  //     : cur_banned(cur_banned), futr_banned(futr_banned), sat_pos(sat_pos),
  //       sat_lla(sat_lla), sat_vel(sat_vel) {}
};

int getPort(int u, int v, int &u_port, int &v_port);
// int is_nearby(int a, int b);
int move(int u, int dir);

int is_forwarder(int u);

class Average {
private:
  double sum, mx;
  int cnt;

public:
  Average() {
    sum = 0.0, cnt = 0;
    mx = 0;
  }
  void add(double val) { sum += val, cnt++; }
  double getResult() { return cnt ? sum / cnt : 0; }
};

// --- 全局配置 (声明) ---
namespace GlobalConfig {
// 使用 extern 声明变量
extern int P, Q, F, N;
extern int proc_delay;      // ms
extern int prop_delay_coef; // km/ms (原始警告变量)
extern double prop_speed;   // km/ms
extern int num_observers;
extern std::vector<std::array<double, 3>> sat_pos;
extern std::vector<std::array<double, 3>> sat_lla;
extern std::vector<double> sat_vel; // Movement direction? (单位?)
extern std::vector<std::pair<int, int>> latency_observers;
extern void loadObserverConfig(std::string observer_config_path);
extern void loadConfig(std::string config_path);

extern std::vector<std::array<int, 5>> cur_banned;
extern std::vector<std::array<int, 5>> futr_banned;
extern std::string sat_vel_dir;

extern std::vector<Average> latency_results;
extern std::vector<Average> failure_rates;

} // namespace GlobalConfig

//   // 定义遍历顺序的类型别名 (现在使用 Direction)
// using TraversalOrder = std::vector<Direction>;

// // --- 定义条件与遍历顺序的映射 ---
// using ConditionKey = std::tuple<bool, bool>;

// const static std::map<ConditionKey, TraversalOrder> traversal_configs = {
//     // 条件: {condition1, condition2} -> 遍历顺序
//     { {true,  true},  {UP, RIGHT, LEFT, DOWN} }, // 对应之前的 {1, 2, 4, 3}
//     逻辑 { {true,  false}, {UP, LEFT, DOWN, RIGHT} }, // 对应之前的 {1, 3, 4,
//     2} 逻辑 (假设) { {false, true},  {DOWN, RIGHT, UP, LEFT} }, // 对应之前的
//     {4, 2, 1, 3} 逻辑 (假设) - 注意 DOWN=3, LEFT=4
//                                                 // 如果想保持之前的 *数字*
//                                                 顺序 {4, 2, 1, 3}，这里应该是
//                                                 {LEFT, RIGHT, UP, DOWN}
//                                                 // 我们这里假设是保持 *方向*
//                                                 逻辑的优先级
//     { {false, false}, {DOWN, LEFT, UP, RIGHT} }  // 对应之前的 {4, 3, 1, 2}
//     逻辑 (假设) - 注意 DOWN=3, LEFT=4
//                                                 // 如果想保持之前的 *数字*
//                                                 顺序 {4, 3, 1, 2}，这里应该是
//                                                 {LEFT, DOWN, UP, RIGHT}
//     // --- 在这里添加更多条件和对应的遍历顺序 ---
// };

// // --- 获取遍历顺序的函数 ---
// // 函数签名和内部逻辑不变，只是处理的类型是 Direction
// std::optional<TraversalOrder> get_traversal_order(bool condition1, bool
// condition2) {
//     ConditionKey key = {condition1, condition2};

//     if (auto it = traversal_configs.find(key); it != traversal_configs.end())
//     {
//         return it->second;
//     } else {
//         return std::nullopt;
//     }
// }

extern const int MAX_RECURSE_CNT;

// Define the logger name globally (optional but good practice)
extern const std::string global_logger_name;

// Declaration of the function that sets up the logger
void setup_logger();