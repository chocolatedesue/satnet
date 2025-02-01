# SpaceSimulation 参数说明

`SpaceSimulation` 类通过读取 JSON 配置文件来初始化空间仿真环境。以下是对构造函数 `SpaceSimulation(std::string config_file_name)` 中使用的配置参数的详细说明。

## 1. 配置文件 (config_file_name)

该参数指定 JSON 配置文件的路径。该文件包含了仿真所需的所有参数。以下是配置文件的详细结构：

### 1.1 顶级配置

* **`name` (string)**: 仿真任务的名称，用于生成报告文件名。
* **`constellation` (object)**: 星座参数，包含以下子参数：
    * **`num_of_orbit_planes` (`P`) (integer)**:  轨道面的数量。
    * **`num_of_satellites_per_plane` (`Q`) (integer)**: 每个轨道面上的卫星数量。
    * **`relative_spacing` (`F`) (integer)**:  相邻轨道面上的卫星相对间隔。
    * `N = P * Q`: 星座中卫星的总数。
* **`ISL_latency` (object)**: 星间链路（ISL）延迟参数，包含以下子参数：
    * **`processing_delay` (double)**:  处理延迟，单位为秒。
    * **`propagation_delay_coef` (double)**: 传播延迟系数。
    * **`propagation_speed` (double)**:  传播速度，单位为米/秒。
* **`step_length` (double)**:  仿真步长，单位为秒。
* **`duration` (double)**: 仿真持续时间，单位为秒。
* **`update_period` (double, *可选*)**:  路由更新周期，单位为秒。如果未指定，默认与 `duration` 相同。
* **`refresh_period` (double, *可选*)**:  状态刷新周期，单位为秒。如果未指定，默认与 `update_period` 相同。
* **`start_time` (double, *可选*)**:  仿真起始时间，单位为秒。如果未指定，默认为 0。
* **`isl_state_dir` (string)**: 存储 ISL 状态的目录路径。
* **`sat_position_dir` (string)**: 存储卫星位置 (XYZ) 数据的目录路径。
* **`sat_lla_dir` (string)**: 存储卫星位置 (LLA) 数据的目录路径。
* **`sat_velocity_dir` (string)**: 存储卫星速度数据的目录路径。
* **`report_dir` (string)**: 存储仿真报告的目录路径。
* **`dawn_dusk_dir` (string, *可选*)**: 存储晨昏线数据的目录路径。
* **`dawn_dusk_icrs_dir` (string, *可选*)**: 存储晨昏线 ICRS 数据的目录路径。

### 1.2 可视化配置 (visualization, *可选*)

*   **`visualization` (object, *可选*)**: 可视化配置，如果存在则开启可视化功能，包含以下子参数：
    *   **`source` (string)**: 可视化数据的来源目录路径。
    *   **`destination` (string)**: 可视化数据输出目录路径。
    *   **`frames_dir` (string)**:  存储帧图像的目录路径。
    *   **`scenario` (string)**:  可视化场景的描述。
    *  **`diff_table` (integer, *可选*)**: 是否显示差异表，默认为0不显示。

    
### 1.3 延迟观察器配置 (num_latency_observers, *可选*)

* **`num_latency_observers` (integer, *可选*)**: 延迟观察器数量，用于记录特定卫星对之间的延迟和故障率。
    *  如果设置为 `-1`，则所有卫星对都将被监控。
    *  如果设置为大于 0 的整数，将随机选择指定数量的卫星对进行监控。
    *  如果未指定或设置为0，则不会监控任何卫星对。
    *  **`random_seed` (integer, *可选*)**: 随机数生成器的种子，用于随机选择延迟观察器。

### 1.4 RIB 节点配置 (dump_rib_nodes, *可选*)

* **`dump_rib_nodes` (array of integers, *可选*)**:  需要转储路由信息库（RIB）的卫星节点ID列表。如果未指定，则默认不转储任何节点的RIB。

## 2. 类成员变量

基于配置文件，`SpaceSimulation` 类会初始化以下成员变量：

* **`name` (std::string)**: 仿真名称。
* **`P`, `Q`, `F`, `N` (int)**: 星座参数。
* **`proc_delay`, `prop_delay_coef`, `prop_speed` (double)**:  ISL延迟参数。
* **`step`, `duration`, `update_period`, `refresh_period`, `start_time` (double)**: 仿真时间参数。
* **`isl_state_dir`, `sat_pos_dir`, `sat_lla_dir`, `sat_vel_dir`, `report_dir`, `dawn_dust_dir`, `dawn_dusk_icrs_dir` (std::string)**: 文件路径。
* **`output_frames` (bool)**: 是否输出可视化帧。
* **`vis_src`, `vis_dst`, `frames_dir`, `frame_scenario` (std::string)**: 可视化参数。
* **`show_diff_table`(int)** : 是否显示差异表。
* **`num_observers` (int)**: 延迟观察器数量。
* **`latency_observers` (std::vector<std::pair<int, int>>)**: 存储延迟观察器 (卫星对) 的列表。
* **`dump_rib` (std::vector<int>)**: 用于指示是否转储 RIB 的向量，大小为 `N`，元素为 0 或 1。
* **`nodes` (std::vector<T>)**: 节点向量，包含 `N` 个节点。 `T` 表示节点类型，在 `SpaceSimulation` 类中实例化为具体的节点类。
* **`algorithm` (std::string)**:  使用的路由算法名称。
* **`cur_banned` (std::vector<std::array<int, 5>>)**, **`futr_banned` (std::vector<std::array<int, 5>>)**, **`sat_pos` (std::vector<std::array<double, 3>>)**, **`sat_lla` (std::vector<std::array<double, 3>>)**, **`sat_vel` (std::vector<double>)**:  卫星相关的数据容器。
* **`route_tables` (std::vector<std::vector<int>>)**: 路由表容器。
* **`path_timer` (int), `path_vis` (std::vector<int>)**: 路径相关参数。
* **`latency_results` (std::vector<Average>)**: 存储延迟结果的向量。
* **`failure_rates` (std::vector<Average>)**: 存储故障率结果的向量。
* **`report_filename` (char[256])**: 报告文件名。

## 3. 示例配置 (config.json)

```json
{
  "name": "my_simulation",
  "constellation": {
    "num_of_orbit_planes": 6,
    "num_of_satellites_per_plane": 10,
    "relative_spacing": 2
  },
  "ISL_latency": {
    "processing_delay": 0.001,
    "propagation_delay_coef": 1.0,
    "propagation_speed": 299792458.0
  },
  "step_length": 1,
  "duration": 3600,
  "update_period": 600,
  "refresh_period": 600,
  "start_time": 0,
  "isl_state_dir": "data/isl_states",
  "sat_position_dir": "data/sat_positions",
  "sat_lla_dir": "data/sat_lla",
  "sat_velocity_dir": "data/sat_velocities",
  "report_dir": "reports",
    "dawn_dusk_dir": "data/dawn_dusk",
    "dawn_dusk_icrs_dir": "data/dawn_dusk_icrs",
  "visualization": {
    "source": "data",
    "destination": "vis",
    "frames_dir": "vis/frames",
    "scenario": "orbit",
    "diff_table": 1
  },
  "num_latency_observers": 10,
  "random_seed": 42,
    "dump_rib_nodes": [0, 1, 2, 3]
}