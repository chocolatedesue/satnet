#ifndef UTILS_H_
#define UTILS_H_

#include <array>
#include <vector>
#include <utility> // 需要包含 <utility> 来声明 std::pair

// --- 类型定义 ---
enum Direction { UP = 1, RIGHT = 2, DOWN = 3, LEFT = 4 };

// --- 全局配置 (声明) ---
namespace GlobalConfig {
    // 使用 extern 声明变量
    extern int P, Q, F, N;
    extern int proc_delay;      // ms
    extern int prop_delay_coef; // km/ms (原始警告变量)
    extern double prop_speed;   // km/ms
    extern std::vector<std::array<double, 3>> sat_pos;
    extern std::vector<std::array<double, 3>> sat_lla;
    extern std::vector<std::pair<int, int>> latency_observers;

} // namespace GlobalConfig

// --- 函数声明 ---
int check_lla_status();
double getDist(int a, int b); // 移除 static
double calcuDelay(int a, int b);

// --- Struct 定义 (保持在头文件) ---
struct World {
    std::vector<std::array<int, 5>> *cur_banned;
    std::vector<std::array<int, 5>> *futr_banned;
    std::vector<std::array<double, 3>> *sat_pos; // ICRS coordination (km)
    std::vector<std::array<double, 3>> *sat_lla; // Latitude, longitude, attitude (km)
    std::vector<double> *sat_vel;                // Movement direction? (单位?)

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

#endif // UTILS_H_