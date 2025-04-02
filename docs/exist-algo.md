
参考 resnet 行文结构

写作注意事项： https://github.com/hzwer/WritingAIPaper

读者能够学到什么




## introd:

1. 我这个问题很重要，改善有 benefit

2. 目前有一个问题之前的工作没有很好的解决，（三选一）| 将传统方法应用，有一个xx问题

3. 验证了一下 效果很棒，横有潜力，拿出数据证明的结果




## 相关工作

分成几个小部分

几个小部分是如何发展的

我的工作和之前的不同，或者是如何继承的




## model explain

主要架构或者问题拆解

你的算法在各个子问题怎么操作的




## 实验设置

1. 数据集来源

2. 实验充分说明你之前的假设







## 对比工作




LBP:  

将leo运动方向作为转发路径的启发式信息, 缺陷在于容易出现在日凌故障处，导致链路故障率较高


# LBP (Logical Boundary Partition) Algorithm Explanation

The LBP algorithm is a distributed routing algorithm for satellite networks that uses logical regions and satellite positions to determine routing paths.

## Core Concepts

1. **Region Partitioning**:
   - The algorithm divides the Earth into latitude regions (`Lr` vector)
   - Regions are calculated based on the constellation's inclination angle
   - Each satellite is assigned to a region based on its current latitude

2. **Satellite Attributes**:
   - Orbital plane: `as = id / Q` (where Q is satellites per plane)
   - Region ID: based on latitude boundaries
   - Movement direction: determined by velocity (1 for northbound, 0 for southbound)

3. **Routing Decision Logic**:
   The algorithm returns a routing direction (0-4) where:
   - 0: No routing (destination is self)
   - 1: South direction
   - 2: East direction (within same plane)
   - 3: North direction
   - 4: West direction (within same plane)

## Algorithm Flow

1. If source and destination are identical: return 0

2. If source and destination have the same movement direction:
   - If they're in the same orbital plane:
     - If in same region: use direct routing
     - If in different regions: move north/south based on directions
   - If in different orbital planes:
     - Choose east/west routing based on shortest path calculation

3. If source and destination have different movement directions:
   - Calculate distances via north and south paths
   - Choose north/south route based on shortest distance and current direction

The algorithm makes routing decisions purely on logical positions rather than physical coordinates, making it efficient for distributed routing in satellite constellations.

---







    algo_mapping = {
        "DiffDomainBridge_10_3" : "DomainBridge",
        "DiffDomainBridge_10_1" : "DomainBridge_1",
        "LocalDomainBridge_10_3" : "LocalDM",
        "LocalDomainBridge_10_1" : "LocalDM_1",
        "DiffDomainBridge_8_3" : "DomainBridge",
        "DisCoRouteBase" : "DisCoRoute",
        "DijkstraPred" : "DT-DVTR", （基准算法）
        "MinHopCount" : "FSA-LA",
        "LBP" : "LBP",
        "DijkstraBase" : "DijkstraBase"
    }
    





---

# 域路由算法(Domain Routing)解析

## 基本概念

`DomainRoutingNode`和`DomainDagShortNode`算法都是基于"域"的卫星网络路由算法。这种方法将卫星星座划分为逻辑域，简化了路由决策过程。

### 域划分方式

```cpp
for(int i = 0; i < N; i++) {
    if((i / Q) / k == (id / Q) / k) {
        domain[i] = 1;  // 同域
    } else {
        domain[i] = 0;  // 不同域
    }
}
```

其中:
- `Q`: 每个轨道平面上的卫星数量
- `k`: 每个域包含的相邻轨道平面数
- `(i / Q)`: 卫星i所在的轨道平面
- `(i / Q) / k`: 卫星i所在的域

## 路由算法逻辑

### 1. 域内路由(Intra-Domain Routing)
- 使用广度优先搜索(BFS)在同一域内查找最优路径
- `DomainRoutingNode`基于跳数优化路径
- `DomainDagShortNode`基于延迟优化路径：`dist[v] = dist[u] + calcuDelay(u, v)`

### 2. 域间路由(Inter-Domain Routing)
- 算法找出两条可能的出域路径：
  - `left_route`（西向，i=4）
  - `right_route`（东向，i=2）
- 选择路径时计算域间距离：
  ```cpp
  int rs = (dst_dm - src_dm + num_dms) % num_dms;  // 向右距离
  int ls = (src_dm - dst_dm + num_dms) % num_dms;  // 向左距离
  if(rs <= ls) {
      route_table[dst] = right_route;  // 向右路径更短
  } else {
      route_table[dst] = left_route;   // 向左路径更短
  }
  ```

### 3. 特殊处理
- 对于外部域的卫星，算法检查其端口状态：`banned_ports >= 2`时跳过
- 选择最优出域点：基于到边界的距离`vis[u]`和路由策略`w`

## 算法优势
- 降低路由复杂性，将网络划分为可管理的域
- 域内使用详细路由，域间使用简化路由
- 在保持合理路径效率的同时，最小化路由表大小
- 适合大型卫星星座的分布式路由方案

这种层次化方法有效平衡了路由精度和计算效率，适合动态变化的卫星网络环境。其中:
- `Q`: 每个轨道平面上的卫星数量
- `k`: 每个域包含的相邻轨道平面数
- `(i / Q)`: 卫星i所在的轨道平面
- `(i / Q) / k`: 卫星i所在的域

## 路由算法逻辑

### 1. 域内路由(Intra-Domain Routing)
- 使用广度优先搜索(BFS)在同一域内查找最优路径
- `DomainRoutingNode`基于跳数优化路径
- `DomainDagShortNode`基于延迟优化路径：`dist[v] = dist[u] + calcuDelay(u, v)`

### 2. 域间路由(Inter-Domain Routing)
- 算法找出两条可能的出域路径：
  - `left_route`（西向，i=4）
  - `right_route`（东向，i=2）
- 选择路径时计算域间距离：
  ```cpp
  int rs = (dst_dm - src_dm + num_dms) % num_dms;  // 向右距离
  int ls = (src_dm - dst_dm + num_dms) % num_dms;  // 向左距离
  if(rs <= ls) {
      route_table[dst] = right_route;  // 向右路径更短
  } else {
      route_table[dst] = left_route;   // 向左路径更短
  }
  ```

### 3. 特殊处理
- 对于外部域的卫星，算法检查其端口状态：`banned_ports >= 2`时跳过
- 选择最优出域点：基于到边界的距离`vis[u]`和路由策略`w`

## 算法优势
- 降低路由复杂性，将网络划分为可管理的域
- 域内使用详细路由，域间使用简化路由
- 在保持合理路径效率的同时，最小化路由表大小
- 适合大型卫星星座的分布式路由方案

这种层次化方法有效平衡了路由精度和计算效率，适合动态变化的卫星网络环境。




---

# NgDomain算法解析

ngdomain.hpp文件包含了三个基于域的卫星路由算法实现，我将为您解释其核心逻辑。

## 共同概念

1. **域划分**：
   ```cpp
   for(int i = 0; i < N; i++) {
       domain[i] = (i / Q) / (P / K);
   }
   ```
   - 将卫星星座划分为K个域
   - 每个域包含相邻的几个轨道平面

2. **桥接值(Bridge Value)**：
   ```cpp
   double getBridge(int a) {
       double lat = sat_lla->at(a)[0];
       double theta = lat / 180 * pi;
       return cos(theta);
   }
   ```
   - 使用卫星纬度计算桥接权重
   - 赤道附近的卫星权重更高

3. **循环距离**：
   ```cpp
   int getLoopDist(int x, int y) {
       return std::min((y - x + K) % K, (x - y + K) % K);
   }
   ```
   - 计算域间最短环形距离

## NgDomainBridge算法

1. **路由搜索逻辑**：
   - 使用BFS从源节点开始探索网络
   - 跨域路由时确保朝目标域前进：
     ```cpp
     if(du >= dv) { continue; } // 只允许向目标域靠近
     ```

2. **度量更新策略**：
   - 域内路由：`metric[u] + (i % 2 == 0 ? getBridge(u) : 1)`
   - 出域路由：直接使用桥接值`getBridge(u)`
   - 域外路由：保持度量值不变

3. **容错机制**：
   ```cpp
   if(fabs(val - metric[v]) <= ((1 - cos(alpha)) / M))
   ```
   - 使用基于倾角的容差区间

## DiffDomainBridge算法

1. **多度量系统**：
   - `metric[0]`：用于同域内路由
   - `metric[1]`：用于特定跨域路由
   - `metric[2]`：用于一般跨域路由

2. **路由决策**：
   ```cpp
   if(domain[i] == domain[id]) {
       route_table[i] = next_hop[0][i];  // 同域路由
   } else if(getLoopDist(domain[id], domain[i]) % M == 0) {
       route_table[i] = next_hop[1][i];  // 特定跨域路由
   } else {
       route_table[i] = next_hop[2][i];  // 一般跨域路由
   }
   ```

## LocalDomainBridge算法

- 在DiffDomainBridge基础上改进了禁用链路处理：
  ```cpp
  if((domain[u] == domain[id] || domain[v] == domain[id]) && banned[u][i])
  ```
  - 只在源域相关的链路上考虑禁用状态
  - 为域间路由提供更大灵活性

## 算法优势

1. 通过域划分降低复杂度
2. 使用桥接值优化跨域路由
3. 多度量系统针对不同类型的路由需求
4. 灵活处理禁用链路，提高可靠性

这些算法共同提供了一个解决卫星网络中复杂路由问题的多层次方案，平衡了路由效率和计算复杂度。


