## 如何导出路由表


1. 获取 SATNET 可执行程序：http://gitlab.fir.ac.cn/chenyxuan/satnet

2. 编写可视化配置

    配置参考 http://gitlab.fir.ac.cn/chenyxuan/satnet/-/blob/main/configs/dump-rib.json
    
    详细数据格式参考 http://gitlab.fir.ac.cn/chenyxuan/satnet/-/blob/main/docs/data_format.md

    "name"：配置名称。

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

    "dump-rib-nodes": 导出路由表的节点列表。

3. 运行 SATNET 程序

    运行指令为 \<main-prog\> \<config-file\> \<algo-id\>，例如：./main configs/test.json 1000

### 查看结果

路由表导出目录为：当前目录/rib/\<config-name\>/\<algo-name\>/\<dump-node\>

其中 config-name 为配置名称，algo-name 为算法名称，dump-node 为导出路由表的节点

### 常见问题

1. Q: 运行 SATNET 程序发生 Segment Fault
    
    A1: sudo \<main-prog\> \<config-file\> \<algo-id\>
    A2: 检查配置路径是否正确，如路径是否存在

2. Q: 运行 SATNET 程序时 JSON Parser 报错

    A: 检查 \<config-file\> 路径是否正确
