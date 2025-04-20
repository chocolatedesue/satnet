

#include <array>
#include <cmath> // 因为 getDist 使用了 sqrt
#include <fstream>
#include <iostream>
#include <limits>     // 可选：用于返回无穷大等
#include <sys/stat.h> // 用于 struct stat

#include "satnet/utils.hpp" // 包含对应的头文件

#include "nlohmann/json.hpp"

using json = nlohmann::json;

// --- 全局配置 (定义) ---
namespace GlobalConfig {
// 提供变量的实际定义和初始化
int P = 0; // 示例初始化，根据需要修改
int Q = 0;
int F = 0;
int N = 0;
int proc_delay = 0;      // ms
int prop_delay_coef = 0; // km/ms
double prop_speed = 0;   // km/ms
int num_observers = 0;
std::vector<std::array<double, 3>> sat_pos;
std::vector<std::array<double, 3>> sat_lla;
std::vector<std::pair<int, int>> latency_observers;

std::vector<std::array<int, 5>> cur_banned;
std::vector<std::array<int, 5>> futr_banned;
std::vector<double> sat_vel;
std::vector<Average> latency_results;
std::vector<Average> failure_rates;

void loadConfig(std::string config_path) {
  auto config = json::parse(std::ifstream(config_path));

  // using namespace GlobalConfig;
  GlobalConfig::proc_delay = config["ISL_latency"]["processing_delay"];
  GlobalConfig::prop_delay_coef =
      config["ISL_latency"]["propagation_delay_coef"];
  GlobalConfig::prop_speed = config["ISL_latency"]["propagation_speed"];

  GlobalConfig::P = config["constellation"]["num_of_orbit_planes"];
  GlobalConfig::Q = config["constellation"]["num_of_satellites_per_plane"];
  GlobalConfig::F = config["constellation"]["relative_spacing"];
  GlobalConfig::N = GlobalConfig::P * GlobalConfig::Q;

  // GlobalConfig::num_observers = config["num_observers"];
  GlobalConfig::loadObserverConfig(config["observer_config_path"]);

  GlobalConfig::sat_pos = std::vector<std::array<double, 3>>(GlobalConfig::N);
  GlobalConfig::sat_lla = std::vector<std::array<double, 3>>(GlobalConfig::N);

  GlobalConfig::cur_banned =
      std::vector<std::array<int, 5>>(GlobalConfig::N, {0, 0, 0, 0, 0});
  GlobalConfig::futr_banned =
      std::vector<std::array<int, 5>>(GlobalConfig::N, {0, 0, 0, 0, 0});
  GlobalConfig::sat_vel = std::vector<double>(GlobalConfig::N, 0.0);

  GlobalConfig::latency_results =
      std::vector<Average>(GlobalConfig::num_observers);
  GlobalConfig::failure_rates =
      std::vector<Average>(GlobalConfig::num_observers);
}

void loadObserverConfig(std::string observer_config_path) {
  // check if the file exists
  struct stat buffer;
  if (stat(observer_config_path.c_str(), &buffer) != 0) {
    std::cerr << "Observer config file not found: " << observer_config_path
              << std::endl;
    exit(1);
  }
  auto ifs = std::ifstream(observer_config_path);
  ifs >> GlobalConfig::num_observers;
  for (int i = 0; i < GlobalConfig::num_observers; i++) {
    int src, dst;
    ifs >> src >> dst;
    GlobalConfig::latency_observers.push_back(std::make_pair(src, dst));
  }
}

} // namespace GlobalConfig

// --- 函数定义 ---
int check_lla_status() {
  // 如果有更复杂的逻辑，在这里实现
  return 1;
}

// 注意：移除了 static
double getDist(int a, int b) {
  // 添加基本的边界检查是个好主意
  if (a < 0 || static_cast<size_t>(a) >= GlobalConfig::sat_pos.size() ||
      b < 0 || static_cast<size_t>(b) >= GlobalConfig::sat_pos.size()) {
    // 处理错误，例如抛出异常或返回一个特殊值 (NaN)
    // throw std::out_of_range("Index out of bounds in getDist");
    return std::nan(""); // 返回 Not-a-Number
  }

  double res = 0;
  for (int i = 0; i < 3; i++) {
    double d = GlobalConfig::sat_pos[a][i] - GlobalConfig::sat_pos[b][i];
    res += d * d;
  }
  // 原始代码在这里乘以 1000，检查这是否符合你的意图（距离单位？）
  return sqrt(res) * 1000;
}

double calcuDelay(int a, int b) {
  double dist_scaled = getDist(a, b); // 注意 getDist 可能返回 NaN

  // 处理 getDist 可能返回的错误
  if (std::isnan(dist_scaled)) {
    return std::nan(""); // 或者传播错误
  }

  // 避免除以零
  if (GlobalConfig::prop_speed == 0) {
    return std::numeric_limits<double>::infinity();
  }

  return GlobalConfig::proc_delay + GlobalConfig::prop_delay_coef *
                                        dist_scaled / GlobalConfig::prop_speed *
                                        1000;
}

// --- Struct World 构造函数定义 (如果不在头文件中内联定义) ---
World::World(std::vector<std::array<int, 5>> *cur_banned,
             std::vector<std::array<int, 5>> *futr_banned,
             std::vector<std::array<double, 3>> *sat_pos,
             std::vector<std::array<double, 3>> *sat_lla,
             std::vector<double> *sat_vel)
    : cur_banned(cur_banned), futr_banned(futr_banned), sat_pos(sat_pos),
      sat_lla(sat_lla), sat_vel(sat_vel) {
  // 构造函数体，如果需要更多初始化代码
}

int getPort(int u, int v, int &u_port, int &v_port) {
  u_port = v_port = 0;
  for (int i = 1; i <= 4; i++) {
    if (move(u, i) == v) {
      u_port = i;
    }
    if (move(v, i) == u) {
      v_port = i;
    }
    /*
    std::cerr << u << ' ' << i << ' ' << move(u, i) << std::endl;
    std::cerr << v << ' ' << i << ' ' << move(v, i) << std::endl;
    */
  }
  return u_port != 0 && v_port != 0;
}

int move(int u, int dir) {
  using namespace GlobalConfig;
  int x = u / Q;
  int y = u % Q;
  if (dir == 1) {
    y = (y - 1 + Q) % Q;
  } else if (dir == 2) {
    if (x == P - 1) {
      x = 0;
      y = (y + F) % Q;
    } else {
      x = x + 1;
    }
  } else if (dir == 3) {
    y = (y + 1) % Q;
  } else if (dir == 4) {
    if (x == 0) {
      x = P - 1;
      y = (y - F + Q) % Q;
    } else {
      x = x - 1;
    }
  } else {
    // do nothing
    return -1;
  }
  return x * Q + y;
}

int is_forwarder(int u) {
  int banned_cnt = 0;
  for (int i = 1; i < 5; i++) {
    banned_cnt += GlobalConfig::cur_banned[u][i];
  }

  return banned_cnt > 1;
}

const int MAX_RECURSE_CNT = 1e6;