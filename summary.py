import os
# import re # 不再需要 re 模块
from typing import Dict, List, Tuple, Any
from scipy import stats
import numpy as np
# from enum import Enum # 如果想用Python Enum也可以，但直接用字典更简单直观

# --- 新增：直接定义算法名称到 ID 的映射 ---
# 这个字典需要包含所有可能出现在报告文件中的算法名称及其对应的ID
# ID 来自 C++ enum class 和之前的特殊定义
# 注意：键 (key) 应该是报告文件中 'algorithm' 字段的确切字符串
ALGORITHM_ID_MAP = {
    "Oracle": 0,                # 特殊定义
    "Base": 1000,               # 基于 C++ enum BASE_NODE (假设报告中是 "Base")
    "CoinFlipBase": 2001,       # 特殊定义 (或对应某个未显示的 C++ enum?)
    "CoinFlipPred": 2003,     # 基于 C++ enum COIN_FLIP_PRED_NODE (假设报告中是 "CoinFlipPred")
    "DijkstraPred": 3003,     # 基于 C++ enum DIJKSTRA_PRED_NODE (假设报告中是 "DijkstraPred")
    "MinHopCount": 5001,      # 基于 C++ enum MIN_HOP_COUNT_NODE (假设报告中是 "MinHopCount")
    "DomainHeuristic": 5100,  # 基于 C++ enum DOMAIN_HEURISTIC_NODE (假设报告中是 "DomainHeuristic")
    # --- 添加其他可能出现在报告中的算法及其（推测的或指定的）ID ---
    # 例如，如果 DisCoRouteBase 等需要基于ID排序，需要给它们分配合适的ID
    # 如果它们不需要基于ID排序，那么在排序时使用 .get() 的默认值即可
    "DisCoRouteBase": 9000,   # 示例：分配一个ID，如果需要的话
    "LBP": 9001,              # 示例
    "DiffDomainBridge_10_3": 9100, # 示例
    "DiffDomainBridge_10_1": 9101, # 示例
    "LocalDomainBridge_10_3": 9200, # 示例
    "LocalDomainBridge_10_1": 9201, # 示例
    "DijkstraBase": 1001,     # 示例 (可能需要确认)
    # ... 其他任何可能出现的算法名称
}

# --- 原有函数保持不变 (除了 get_algorithm_id_dict 被删除) ---

def read_report_file(file_path: str, target_name: str) -> Dict[str, Any] | None:
    """
    从报告文件中读取数据

    Args:
        file_path: 报告文件路径
        target_name: 目标场景名称

    Returns:
        包含报告数据的字典，如果不匹配目标名称则返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f: # 指定编码是个好习惯
            report_data = {}

            # 读取元数据
            while True:
                line = f.readline()
                if not line or ':' not in line: # 处理文件末尾或空行/格式不符
                    # 如果元数据不完整或格式错误，可以选择返回 None 或抛出异常
                    print(f"警告: 文件 {file_path} 格式不正确或元数据不完整。")
                    return None
                key, value = line.split(":", 1) # 使用 split 1 次，避免值中包含冒号时出错
                key = key.strip()
                value = value.strip()
                report_data[key] = value
                if key == "number of observers":
                    break

            # 检查名称是否匹配
            if report_data.get("name") != target_name:
                return None

            # 检查 number of observers 是否是有效数字
            try:
                num_observers = int(report_data["number of observers"])
            except (ValueError, KeyError):
                print(f"警告: 文件 {file_path} 中的 'number of observers' 无效。")
                return None

            # 读取路径信息
            route_paths = []
            for _ in range(num_observers):
                path_name_line = f.readline()
                latency_line = f.readline()
                failure_line = f.readline()

                # 添加健壮性检查，确保能读取到预期行且格式正确
                if not path_name_line or not latency_line or not failure_line or \
                   ':' not in latency_line or ':' not in failure_line:
                    print(f"警告: 文件 {file_path} 中的路径信息不完整或格式错误。")
                    # 根据策略决定是跳过该文件还是部分读取
                    return None # 这里选择跳过整个文件

                path_name = path_name_line.strip() # 通常路径名称就是一行
                # 提取 latency 和 failure 时更健壮
                try:
                    latency = latency_line.split(":", 1)[1].strip()
                    failure = failure_line.split(":", 1)[1].strip()
                    # 尝试转换确保是数字，虽然 calculate_statistics 会做，但提前检查更好
                    float(latency)
                    float(failure)
                except (IndexError, ValueError):
                    print(f"警告: 文件 {file_path} 中解析 latency/failure 时出错。行: '{latency_line.strip()}', '{failure_line.strip()}'")
                    return None # 跳过文件

                route_paths.append([path_name, latency, failure])

            report_data["path info"] = route_paths
            return report_data
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 未找到。")
        return None
    except Exception as e:
        print(f"读取文件 {file_path} 时发生未知错误: {e}")
        return None


def get_records(directory: str, target_name: str) -> List[Dict[str, Any]]:
    """
    获取指定目录下所有匹配目标名称的记录

    Args:
        directory: 包含报告文件的目录
        target_name: 目标场景名称

    Returns:
        报告记录列表
    """
    records = []
    try:
        files = sorted(os.listdir(directory))
    except FileNotFoundError:
        print(f"错误: 目录 '{directory}' 不存在。")
        return []

    for filename in files:
        if "report" not in filename or not filename.endswith(".txt"): # 假设报告是 .txt
            continue

        file_path = os.path.join(directory, filename)
        report_data = read_report_file(file_path, target_name)

        if report_data:
            records.append(report_data)
            print(f"处理文件: {file_path}")
        # else: # 选择性打印跳过的文件
        #     print(f"跳过文件 (名称不匹配或格式错误): {file_path}")

    return records


def calculate_statistics(record: Dict[str, Any]) -> Tuple[str, float, float, float, float, float, float, float] | None:
    """
    计算记录的统计数据

    Args:
        record: 报告记录

    Returns:
        元组包含统计数据，如果数据无效则返回 None
        (算法名称, 计算时间, 更新条目数, 平均失败率, 平均延迟, 50%延迟, 90%延迟, 99%延迟)
    """
    try:
        algorithm_name = record["algorithm"]
        compute_time = float(record["compute time"])
        update_entry = float(record["update entry"])
        paths = record["path info"]
        num_observers = int(record["number of observers"])

        if num_observers <= 0: # 避免除以零和索引错误
            print(f"警告: 算法 {algorithm_name} 的记录中 observers 数量为零或负数。")
            return None

        # 计算平均值
        latencies = []
        total_failure_rate = 0.0
        total_latency = 0.0

        for i in range(num_observers):
            # 再次检查路径数据格式，尽管 read_report_file 可能已检查
            try:
                latency = float(paths[i][1])
                failure_rate = float(paths[i][2])
            except (IndexError, ValueError):
                print(f"警告: 算法 {algorithm_name} 的路径数据无效: {paths[i]}")
                return None # 或者选择跳过该条路径数据

            total_latency += latency
            total_failure_rate += failure_rate
            latencies.append(latency)

        avg_failure_rate = total_failure_rate / num_observers
        avg_latency = total_latency / num_observers

        # 计算百分位数
        latencies.sort()
        # 使用 numpy 的 percentile 函数更精确，尤其是在样本量不大时
        percentile_50 = np.percentile(latencies, 50)
        percentile_90 = np.percentile(latencies, 90)
        percentile_99 = np.percentile(latencies, 99)
        # # 原来的简单索引方法 (适用于非常大的样本量)
        # percentile_50 = latencies[min(int(num_observers * 0.50), num_observers - 1)]
        # percentile_90 = latencies[min(int(num_observers * 0.90), num_observers - 1)]
        # percentile_99 = latencies[min(int(num_observers * 0.99), num_observers - 1)]


        return (
            algorithm_name,
            compute_time,
            update_entry,
            avg_failure_rate,
            avg_latency,
            percentile_50,
            percentile_90,
            percentile_99
        )
    except (KeyError, ValueError, TypeError) as e:
        print(f"计算统计数据时出错: {e}. 记录: {record.get('algorithm', '未知算法')}")
        return None

# --- get_algorithm_id_dict 函数已被删除 ---

def create_summary_report(target_name: str, records: List[Dict[str, Any]],
                          algorithm_mapping: Dict[str, str]) -> None:
    """
    创建性能汇总报告

    Args:
        target_name: 目标场景名称
        records: 报告记录列表 (已排序)
        algorithm_mapping: 算法名称到友好显示名称的映射字典
    """
    output_filename = f"summary [{target_name}].csv"
    print(f"\n正在为场景 '{target_name}' 创建汇总报告: {output_filename}")

    # 首先获取基准值（来自 DijkstraPred 算法）
    base_update, base_latency = 1.0, 1.0 # 默认值以防找不到基准
    base_p50, base_p90, base_p99 = 1.0, 1.0, 1.0
    base_found = False

    for record in records:
        if record.get("algorithm") == "DijkstraPred":
            stats = calculate_statistics(record)
            if stats:
                _, _, base_update, _, base_latency, base_p50, base_p90, base_p99 = stats
                 # 防止基准值为0导致除零错误
                base_update = base_update if base_update != 0 else 1.0
                base_latency = base_latency if base_latency != 0 else 1.0
                base_p50 = base_p50 if base_p50 != 0 else 1.0
                base_p90 = base_p90 if base_p90 != 0 else 1.0
                base_p99 = base_p99 if base_p99 != 0 else 1.0
                base_found = True
                print(f"找到基准算法 DijkstraPred: Update={base_update:.2f}, Latency={base_latency:.2f}")
                break
    if not base_found:
         print("警告: 未找到基准算法 'DijkstraPred' 的有效数据，相对值可能不准确。")


    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            # 写入标题行
            f.write("Algorithm Name,Compute Time (s),Update Entry (#),Update Entry (Relative %),Failure Rate (%),Avg Latency (ms),Avg Latency (Relative %),P50 Latency (ms),P50 Latency (Relative %),P90 Latency (ms),P90 Latency (Relative %),P99 Latency (ms),P99 Latency (Relative %)\n")

            # 写入每个算法的数据
            for record in records:
                stats = calculate_statistics(record)
                if not stats:
                    print(f"跳过无效记录: {record.get('algorithm', '未知算法')}")
                    continue # 跳过无法计算统计数据的记录

                algorithm_name, compute_time, update_entry, avg_failure_rate, avg_latency, p50, p90, p99 = stats

                # 计算相对值 (更安全地处理除零)
                rel_update = (update_entry - base_update) / base_update if base_update else 0
                rel_latency = (avg_latency - base_latency) / base_latency if base_latency else 0
                rel_p50 = (p50 - base_p50) / base_p50 if base_p50 else 0
                rel_p90 = (p90 - base_p90) / base_p90 if base_p90 else 0
                rel_p99 = (p99 - base_p99) / base_p99 if base_p99 else 0

                # 格式化更新条目
                update_entry_text = f"{update_entry:.2f}"
                # # 显示相对值的条件可以调整
                # if abs(rel_update) < 2 and algorithm_name != "Oracle": # 原来的条件
                #     update_entry_text += f" ({rel_update:+.2%})" # 百分比放后面

                # 使用友好的算法名称
                display_name = algorithm_mapping.get(algorithm_name, algorithm_name) # 如果映射中没有，则使用原始名称

                # 写入格式化的行 (将相对值放在单独的列中，更清晰)
                line = (f"{display_name},"
                        f"{compute_time:.2f},"
                        f"{update_entry:.2f},"
                        f"{rel_update:+.2%}," # 相对更新条目单独一列
                        f"{avg_failure_rate:.4%},"
                        f"{avg_latency:.2f},"
                        f"{rel_latency:+.2%}," # 相对延迟单独一列
                        f"{p50:.2f},"
                        f"{rel_p50:+.2%},"    # 相对P50单独一列
                        f"{p90:.2f},"
                        f"{rel_p90:+.2%},"    # 相对P90单独一列
                        f"{p99:.2f},"
                        f"{rel_p99:+.2%}\n")  # 相对P99单独一列
                f.write(line)
        print(f"成功写入汇总报告: {output_filename}")

    except IOError as e:
        print(f"写入文件 {output_filename} 时出错: {e}")
    except Exception as e:
        print(f"创建汇总报告时发生未知错误: {e}")


def generate_latency_distribution(record: Dict[str, Any], algorithm_name: str) -> None:
    """
    生成延迟分布数据文件

    Args:
        record: 报告记录
        algorithm_name: 算法名称 (用于文件名)
    """
    try:
        paths = record.get("path info", [])
        if not paths:
            print(f"警告: 算法 {algorithm_name} 没有路径信息，无法生成延迟分布。")
            return

        # 提取所有路径的延迟数据，添加错误处理
        latency_data = []
        for path in paths:
            try:
                latency_data.append(float(path[1]))
            except (IndexError, ValueError):
                 print(f"警告: 算法 {algorithm_name} 发现无效延迟数据: {path}")
                 #可以选择跳过这条数据或整个文件
        if not latency_data:
             print(f"警告: 算法 {algorithm_name} 没有有效的延迟数据点。")
             return

        latency_data = np.array(latency_data)

        # 定义延迟范围和分箱数量 (可以根据数据调整)
        min_latency = max(0, np.min(latency_data) - 10) # 略小于最小值
        max_latency = np.max(latency_data) + 10      # 略大于最大值
        num_bins = 100 # 或根据数据量动态调整

        # 计算频率分布 (使用 numpy.histogram)
        # hist, bin_edges = np.histogram(latency_data, bins=num_bins, range=(min_latency, max_latency), density=False)
        # cumulative_freq = np.cumsum(hist)
        # total_count = len(latency_data)
        # cumulative_fraction = cumulative_freq / total_count
        # bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

        # 或者使用 scipy.stats.cumfreq 更直接获取累积分布点
        # 注意：cumfreq 的默认分箱可能与之前不同，可能需要调整 numbins 或 defaultreallimits
        # 使用一个合理的上限，比如预期最大延迟的1.2倍或一个固定大值
        realistic_upper_bound = max(300, np.percentile(latency_data, 99.9) * 1.2 if len(latency_data)>10 else 300)
        cumfreq_result = stats.cumfreq(latency_data, numbins=200, defaultreallimits=(0, realistic_upper_bound))

        # 提取绘图数据点
        plot_x = cumfreq_result.lowerlimit + np.linspace(0, cumfreq_result.binsize * cumfreq_result.cumcount.size, cumfreq_result.cumcount.size)
        plot_y = cumfreq_result.cumcount / len(latency_data) # 转换为分数 (0 to 1)

        # 保存到文件
        output_dir = "output/plot_data"
        os.makedirs(output_dir, exist_ok=True,parents=True) # 确保目录存在
        # 清理算法名称，使其适合做文件名
        safe_algo_name = "".join(c if c.isalnum() else "_" for c in algorithm_name)
        output_path = os.path.join(output_dir, f"{safe_algo_name}_latency_cdf.csv")

        with open(output_path, "w", encoding='utf-8') as pf:
            pf.write("Latency (ms),Cumulative Fraction\n")
            # 写入 (0, 0) 点使图形从原点开始
            if plot_x[0] > 0:
                 pf.write("0.000000,0.000000\n")
            for x, y in zip(plot_x, plot_y):
                # 过滤掉可能的无效计算结果（虽然不太可能）
                if np.isfinite(x) and np.isfinite(y):
                    pf.write(f"{x:.6f},{y:.6f}\n")
            # 确保最后一个点是 (max_latency, 1.0) 如果需要的话
            # if plot_y[-1] < 1.0:
            #      pf.write(f"{plot_x[-1]:.6f},1.000000\n") # 或者用实际的最大延迟

        print(f"已生成延迟分布数据: {output_path}")

    except (KeyError, ValueError, TypeError, IOError) as e:
        print(f"为算法 {algorithm_name} 生成延迟分布时出错: {e}")
    except Exception as e:
         print(f"为算法 {algorithm_name} 生成延迟分布时发生未知错误: {e}")


def main():
    """主函数"""
    # --- 使用硬编码的算法ID映射 ---
    # ALGORITHM_ID_MAP 在文件顶部定义

    print("使用的算法ID映射:")
    for name, id_val in ALGORITHM_ID_MAP.items():
        print(f"  - {name}: {id_val}")
    print("-" * 20)

    # 定义目标场景
    # target_list = ["full full-gw-2000 - Jan", "startlink-v2-group5-Jan", "startlink-v2-group5-Apr","startlink-v2-group5-Jul"]
    # 测试用，只选一个
    target_list = ["startlink-v2-group5-Apr"]


    # 定义算法名称到友好显示名称的映射
    algorithm_display_mapping = {
        "DiffDomainBridge_10_3": "DomainBridge",
        "DiffDomainBridge_10_1": "DomainBridge_1",
        "LocalDomainBridge_10_3": "LocalDM",
        "LocalDomainBridge_10_1": "LocalDM_1",
        "DiffDomainBridge_8_3": "DomainBridge(8_3)", # 保持区分度
        "DisCoRouteBase": "DisCoRoute",
        "DijkstraPred": "DT-DVTR",
        "MinHopCount": "FSA-LA",
        "LBP": "LBP",
        "DijkstraBase": "DijkstraBase",
        "CoinFlipPred": "CoinFlipPred", # 添加映射（如果需要友好名称）
        "DomainHeuristic": "DomainHeuristic" # 添加映射
        # ... 其他算法的友好名称
    }
    print("使用的算法显示名称映射:")
    for orig, disp in algorithm_display_mapping.items():
        print(f"  - '{orig}' -> '{disp}'")
    print("-" * 20)

    # 预定义的算法在汇总报告中的排序顺序
    # 这个顺序会覆盖基于ID的排序，决定最终输出文件的行顺序
    algorithm_output_order = [
        "DijkstraPred",      # DT-DVTR
        "MinHopCount",       # FSA-LA
        "DisCoRouteBase",    # DisCoRoute
        "LBP",               # LBP
        "DiffDomainBridge_10_3", # DomainBridge
        "DiffDomainBridge_10_1", # DomainBridge_1
        "LocalDomainBridge_10_3",# LocalDM
        "LocalDomainBridge_10_1",# LocalDM_1
        # 添加其他你想固定顺序的算法
        "DomainHeuristic",
        "CoinFlipPred",
        "DijkstraBase",
        "Base",
        "Oracle",            # 通常放最后或最前？
    ]
    print("汇总报告中的算法输出顺序:", algorithm_output_order)
    print("-" * 20)


    # 处理每个目标场景
    for target_name in target_list:
        print(f"\n===== 开始处理场景: {target_name} =====")
        # 获取所有记录
        records = get_records("output", target_name) # 假设报告在 'output' 目录下

        if not records:
            print(f"场景 '{target_name}' 没有找到匹配的报告文件或有效数据。")
            continue

        # --- 排序逻辑 ---
        # 1. (可选) 首先按算法ID排序。如果ID主要用于分组或初步排序，可以保留。
        #    使用 .get() 处理映射中可能不存在的算法名，将它们排在后面。
        DEFAULT_SORT_ID = float('inf') # 未知ID的算法排在最后
        records.sort(key=lambda r: ALGORITHM_ID_MAP.get(r.get("algorithm", ""), DEFAULT_SORT_ID))
        print("记录已按算法ID初步排序 (未知ID排最后)")

        # 2. 按预定义的输出顺序排序。这是决定最终CSV文件顺序的关键步骤。
        #    不在预定义顺序列表中的算法会排在列表之后（顺序取决于上一步ID排序或保持稳定）。
        order_dict = {name: index for index, name in enumerate(algorithm_output_order)}
        records.sort(
            key=lambda r: order_dict.get(r.get("algorithm", ""), len(algorithm_output_order))
        )
        print("记录已按预定义的输出顺序最终排序")
        print("最终处理顺序中的算法:")
        for rec in records: print(f"  - {rec.get('algorithm')}")


        # 创建汇总报告
        create_summary_report(target_name, records, algorithm_display_mapping)

        # （可选）为每个算法生成延迟分布数据
        print("\n开始生成延迟分布数据...")
        for record in records:
             algo_name = record.get("algorithm")
             if algo_name:
                 generate_latency_distribution(record, algo_name)

        print(f"===== 完成处理场景: {target_name} =====")

if __name__ == "__main__":
    main()