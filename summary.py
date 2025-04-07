"""
卫星网络路由算法性能分析工具

此脚本用于分析不同路由算法在卫星网络模拟中的性能表现，
包括计算时间、更新条目数、失败率和延迟等指标。
"""

import os
import re
from typing import Dict, List, Tuple, Any
from scipy import stats
import numpy as np


def read_report_file(file_path: str, target_name: str) -> Dict[str, Any]:
    """
    从报告文件中读取数据

    Args:
        file_path: 报告文件路径
        target_name: 目标场景名称

    Returns:
        包含报告数据的字典，如果不匹配目标名称则返回None
    """
    with open(file_path) as f:
        report_data = {}
        
        # 读取元数据
        while True:
            line = f.readline()
            key, value = line.split(":")
            key = key.strip()
            value = value.strip()
            report_data[key] = value
            if key == "number of observers":
                break
        
        # 检查名称是否匹配
        if report_data["name"] != target_name:
            return None
        
        # 读取路径信息
        num_observers = int(report_data["number of observers"])
        route_paths = []
        for _ in range(num_observers):
            path_name = f.readline()
            latency = f.readline().split(":")[1]
            failure = f.readline().split(":")[1]
            route_paths.append([path_name, latency, failure])
        
        report_data["path info"] = route_paths
        return report_data


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
    files = sorted(os.listdir(directory))
    
    for filename in files:
        if "report" not in filename:
            continue
            
        file_path = os.path.join(directory, filename)
        report_data = read_report_file(file_path, target_name)
        
        if report_data:
            records.append(report_data)
            print(f"处理文件: {file_path}")
    
    return records


def calculate_statistics(record: Dict[str, Any]) -> Tuple[str, float, float, float, float, float, float, float]:
    """
    计算记录的统计数据

    Args:
        record: 报告记录

    Returns:
        算法名称、计算时间、更新条目数、平均失败率、平均延迟、50%延迟、90%延迟和99%延迟
    """
    algorithm_name = record["algorithm"]
    compute_time = float(record["compute time"])
    update_entry = float(record["update entry"])
    paths = record["path info"]
    num_observers = int(record["number of observers"])
    
    # 计算平均值
    latencies = []
    total_failure_rate = 0.0
    total_latency = 0.0
    
    for i in range(num_observers):
        latency = float(paths[i][1])
        failure_rate = float(paths[i][2])
        
        total_latency += latency
        total_failure_rate += failure_rate
        latencies.append(latency)
    
    avg_failure_rate = total_failure_rate / num_observers
    avg_latency = total_latency / num_observers
    
    # 计算百分位数
    latencies.sort()
    percentile_50 = latencies[int(num_observers * 0.50)]
    percentile_90 = latencies[int(num_observers * 0.90)]
    percentile_99 = latencies[int(num_observers * 0.99)]
    
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


def get_algorithm_id_dict(file_path: str) -> Dict[str, int]:
    """
    从源文件中提取算法ID映射

    Args:
        file_path: 包含算法定义的源文件路径

    Returns:
        算法名称到ID的映射字典
    """
    algorithm_ids = {}
    
    with open(file_path) as f:
        lines = f.readlines()
        for line in lines:
            if "#define" in line:
                continue
                
            match = re.search(r'CASE\((.*), (.*)\)', line)
            if match:
                algorithm_id = match.group(1)
                algorithm_name = match.group(2)
                
                # 标准化算法名称
                name = (algorithm_name
                       .replace("Node", "")
                       .replace("COMMA", "_")
                       .replace("<", "_")
                       .replace(">", "")
                       .replace(" ", "")
                       .replace("Base", "")
                       .lower())
                       
                algorithm_ids[name] = int(algorithm_id)
                
    algorithm_ids["oracle"] = 0
    return algorithm_ids


def create_summary_report(target_name: str, records: List[Dict[str, Any]], 
                         algorithm_mapping: Dict[str, str]) -> None:
    """
    创建性能汇总报告

    Args:
        target_name: 目标场景名称
        records: 报告记录列表
        algorithm_mapping: 算法名称映射字典
    """
    output_filename = f"summary [{target_name}].csv"
    
    # 首先获取基准值（来自DijkstraPred算法）
    base_update, base_latency = 1, 1
    base_p50, base_p90, base_p99 = 1, 1, 1
    
    for record in records:
        if record["algorithm"] == "DijkstraPred":
            _, _, base_update, _, base_latency, base_p50, base_p90, base_p99 = calculate_statistics(record)
            break
    
    with open(output_filename, 'w') as f:
        # 写入标题行
        f.write("name, compute_time, update_entry, avg_failure_rate, avg_latency, pct_50, pct_90, pct_99\n")
        
        # 写入每个算法的数据
        for record in records:
            stats = calculate_statistics(record)
            algorithm_name, compute_time, update_entry = stats[0:3]
            avg_failure_rate, avg_latency = stats[3:5]
            p50, p90, p99 = stats[5:8]
            
            # 计算相对值
            rel_update = (update_entry - base_update) / base_update
            rel_latency = (avg_latency - base_latency) / base_latency
            rel_p50 = (p50 - base_p50) / base_p50
            rel_p90 = (p90 - base_p90) / base_p90
            rel_p99 = (p99 - base_p99) / base_p99
            
            # 格式化更新条目
            update_entry_text = f"{update_entry:.2f}"
            if rel_update < 2 and algorithm_name != "Oracle":
                update_entry_text += f"({rel_update:+.2%})"
            
            # 使用友好的算法名称
            display_name = algorithm_mapping.get(algorithm_name, algorithm_name)
            
            # 写入格式化的行
            line = (f"{display_name}, {compute_time:.2f}, {update_entry_text}, {avg_failure_rate:.4%}, "
                   f"{avg_latency:.2f}({rel_latency:+.2%}), {p50:.2f}({rel_p50:+.2%}), "
                   f"{p90:.2f}({rel_p90:+.2%}), {p99:.2f}({rel_p99:+.2%})\n")
            f.write(line)


def generate_latency_distribution(record: Dict[str, Any], algorithm_name: str) -> None:
    """
    生成延迟分布数据文件

    Args:
        record: 报告记录
        algorithm_name: 算法名称
    """
    # 提取所有路径的延迟数据
    latency_data = np.array([float(path[1]) for path in record["path info"]])
    
    # 计算相对频率
    latency_freq = stats.relfreq(latency_data, defaultreallimits=(0, 300), numbins=1000)
    
    # 生成绘图数据
    plot_x = latency_freq.lowerlimit + np.linspace(0, 
                                                  latency_freq.binsize * latency_freq.frequency.size,
                                                  latency_freq.frequency.size)
    plot_y = np.cumsum(latency_freq.frequency)
    
    # 保存到文件
    os.makedirs("plot_data", exist_ok=True)
    with open(f"plot_data/{algorithm_name}.csv", "w") as pf:
        pf.write("latency, fraction\n")
        for x, y in zip(plot_x, plot_y):
            pf.write(f"{x:.6f}, {y:.6f}\n")


def main():
    """主函数"""
    # 获取算法ID映射
    algorithm_id_dict = get_algorithm_id_dict("main.cpp")
    algorithm_id_dict["Base"] = 1000
    algorithm_id_dict["CoinFlipBase"] = 2001

    print ("算法ID映射:", algorithm_id_dict)
    
    # 定义目标场景
    target_list = ["full example - Apr", "full gw - Oct"]
    
    # 定义算法名称映射
    algorithm_mapping = {
        "DiffDomainBridge_10_3": "DomainBridge",
        "DiffDomainBridge_10_1": "DomainBridge_1",
        "LocalDomainBridge_10_3": "LocalDM",
        "LocalDomainBridge_10_1": "LocalDM_1",
        "DiffDomainBridge_8_3": "DomainBridge",
        "DisCoRouteBase": "DisCoRoute",
        "DijkstraPred": "DT-DVTR",
        "MinHopCount": "FSA-LA",
        "LBP": "LBP",
        "DijkstraBase": "DijkstraBase"
    }
    
    # 预定义的算法排序顺序
    algorithm_order = [
        "DijkstraPred", "MinHopCount", "DisCoRouteBase", "LBP", 
        "DiffDomainBridge_10_3", "DiffDomainBridge_10_1", 
        "LocalDomainBridge_10_3", "LocalDomainBridge_10_1"
    ]
    
    # 处理每个目标场景
    for target_name in target_list:
        # 获取所有记录
        records = get_records("output", target_name)
        
        # 按算法ID排序
        records.sort(key=lambda r: algorithm_id_dict[r["algorithm"].replace("Base", "").lower()])
        
        # 按预定义顺序排序
        records.sort(
            key=lambda r: algorithm_order.index(r["algorithm"]) 
            if r["algorithm"] in algorithm_order 
            else len(algorithm_order)
        )
        
        # 创建汇总报告
        create_summary_report(target_name, records, algorithm_mapping)


if __name__ == "__main__":
    main()