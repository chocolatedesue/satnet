import json
import random


IN_PATH = "./configs/full.json"
OUT_PATH = "./data/326gen/observers.txt"


def move(id_val, direction, Q, P, F):
    """
    模拟 C++ 的 move 函数。

    Args:
        id_val: 节点的ID。
        direction: 移动方向 (1, 2, 3, 4)。
        Q: 网格的列数。
        P: 网格的行数。
        F: 方向 2 和 4 中的 F 参数。

    Returns:
        移动后的节点的ID。
    """
    x = id_val // Q
    y = id_val % Q

    if direction == 1:
        y = (y - 1 + Q) % Q
    elif direction == 2:
        if x == P - 1:
            x = 0
        else:
            x += 1
        y = (y + F) % Q
    elif direction == 3:
        y = (y + 1) % Q
    elif direction == 4:
        if x == 0:
            x = P - 1
        else:
            x -= 1
        y = (y - F + Q) % Q
    else:
        # do nothing
        pass # Python 中使用 pass 表示空操作

    return x * Q + y



with open ( IN_PATH, "r" , encoding="utf-8") as f:
    config = json.load(f)

    P = config["constellation"]["num_of_orbit_planes"]
    Q = config["constellation"]["num_of_satellites_per_plane"]
    F = config["constellation"]["relative_spacing"]
    N = P * Q

    num_observers = config["num_latency_observers"]
    if config.get("seed") is None:
        seed = 42
    else:
        seed = config["seed"]

    random.seed(seed) # 设置随机种子

    observer_set = set()
    latency_observers = []
    count = 0
    while count < num_observers:
        while True:
            u = random.randint(0, N - 1)
            direct = random.randint(0, 3) # 0, 1, 2, 3  对应 move 函数的 1+direct 是 1, 2, 3, 4
            v = move(u, 1 + direct, Q, P, F) # 使用 move 函数计算 v
            if u != v:
                break
        observer_pair = (u, v)
        if observer_pair not in observer_set:
            observer_set.add(observer_pair)
            latency_observers.append(observer_pair)
            count += 1

    # 写入../data/326gen/observers.txt

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for observer in latency_observers:
            f.write(f"{observer[0]} {observer[1]}\n")
    
    print (f"Generated {num_observers} observers in {OUT_PATH}")