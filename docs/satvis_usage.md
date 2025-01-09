## 如何使用 SATVIS 卫星网络可视化平台

### 生成帧数据

1. 获取 SATNET 可执行程序：http://gitlab.fir.ac.cn/chenyxuan/satnet

2. 编写可视化配置

    配置参考 http://gitlab.fir.ac.cn/chenyxuan/satnet/-/blob/main/configs/visualization/sample.json
    
    详细数据格式参考 http://gitlab.fir.ac.cn/chenyxuan/satnet/-/blob/main/docs/data_format.md

    "constellation" 和 "ISL_latency" 分别为星座配置和延迟参数，应与数据源保持一致。

    "start_time"、"step_length"、"duration" 表示仿真的开始时间、时间粒度和持续时间，仿真将从 start_time 时刻开始，每过 step_length 秒生成一帧，持续 duration 秒，在 start_time + duration 时刻结束。

    "update_period": 路由表更新周期，路由表会在 update_period 倍数的时刻更新；在第一次路由表更新前，所有路由表项的值为 0（丢弃数据包）。

    "refresh_period": 仿真状态的刷新周期。

    "isl_state_dir": 卫星链路状态数据所在目录。

    "sat_position_dir": 以地球为中心的卫星 ICRS 坐标数据所在目录。
    
    "sat_lla_dir": 卫星经纬度和高度数据所在目录。
    
    "sat_velocity_dir": 卫星运行方向数据所在目录。

    "dawn_dusk_dir": （可选）晨昏线数据所在目录。

    "report_dir": 仿真报告所在目录。

    "visualization": 可视化参数，含义如下
    
    - 当 source 与 destination 都为 -1 时，帧内容包括卫星网络拓扑与晨昏线

    - 当 source 与 destination 都不为 -1 时，帧内容包括卫星网络拓扑与 source 到 destination 的路由路径。

    - 当 source 不为 -1，destination 为 -1 时，帧内容包括卫星网络拓扑与 source 的路由表。

    - "frames_dir" 表示帧存放的目标目录。

    - "scenario" 表示场景及算法的名称，格式为应 "\<scene-name\> - \<algo-name\>"，其中 \<algo-name\> 可以留空。

    - "diff_table" 表示路由表可视化内容，0 表示只展示与 source 升降轨情况相同的节点的表项，1 表示只展示与 source 升降轨情况不同的节点的表项，2 表示展示所有节点的表项。

3. 运行 SATNET 程序

    运行指令为 \<main-prog\> \<config-file\> \<algo-id\>，例如：./main configs/test.json 1000

    其中 main-prog 为 SATNET 执行程序，config-file 为配置文件路径，algo-id 为[算法 ID](http://gitlab.fir.ac.cn/chenyxuan/satnet/-/blob/main/main.cpp)。

### 查看结果

SATVIS 平台地址：http://192.168.1.14/satvis/

配置选项：Scenario - 选择场景，Option - 选择算法，Mode - 选择展示模式（地球静止视角/卫星拓扑视角/以太阳为参考系的3D视角）

基本操作：空格 - 播放/暂停，Z - 上一帧，X - 下一帧，C - 复位，WASD - 调整 3D 视角，F - 向左旋转（3D视角），G - 向右旋转（3D视角）


### 常见问题

1. Q: 运行 SATNET 程序发生 Segment Fault
    
    A1: sudo \<main-prog\> \<config-file\> \<algo-id\>
    A2: 检查配置路径是否正确，如路径是否存在

2. Q: 运行 SATNET 程序时 JSON Parser 报错

    A: 检查 \<config-file\> 路径是否正确
