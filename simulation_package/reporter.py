from pathlib import Path
import time # For timestamp in filename (optional)
import sys
from typing import Dict, Any

from .config import Config
from .stats import StatisticsCollector # Need stats results
from .utils import create_dir_recursive # For report dir

class Reporter:
    """Generates simulation progress and summary reports."""

    def __init__(self, config: Config, algorithm_name: str, node_class_name: str):
        self.config = config
        self.report_dir = config.report_dir
        self.sim_name = config.name
        self.algo_name = algorithm_name
        self.node_type_name = node_class_name

        # Format filename (similar to C++ but without timestamp for simplicity now)
        self.report_filename = f"report [{self.sim_name}] {self.algo_name}.txt"
        self.report_filepath = self.report_dir / self.report_filename

        # Ensure report directory exists
        create_dir_recursive(self.report_dir)
        print(f"Reporter: Reports will be saved to {self.report_filepath}")


    def generate_report(self, current_sim_time: int,
                        stats_results: Dict[str, Any],
                        elapsed_wall_time: float):
        """Generates and saves/prints the report."""

        sim_start_time = self.config.start_time
        sim_duration = self.config.duration
        sim_step = self.config.step

        # Correct calculation for time elapsed/remaining in simulation steps/units
        sim_time_elapsed_units = max(1, current_sim_time - sim_start_time + sim_step)
        sim_time_remaining_units = max(0, (sim_start_time + sim_duration) - (current_sim_time + sim_step))

        # ETA calculation based on wall time and simulation time progress
        eta_seconds = (elapsed_wall_time / sim_time_elapsed_units) * sim_time_remaining_units if sim_time_elapsed_units > 0 else 0

        # --- Prepare report content ---
        report_lines = []
        report_lines.append(f"name: {self.sim_name}")
        report_lines.append(f"algorithm: {self.algo_name}")
        report_lines.append(f"node type: {self.node_type_name}")
        report_lines.append(f"simulation time: {current_sim_time}")
        report_lines.append(f"real-world time: {elapsed_wall_time:.6f}")
        report_lines.append(f"estimated time of arrival (s): {eta_seconds:.6f}")

        comp_avg = stats_results.get('compute_time_avg_ms', 0.0)
        update_avg = stats_results.get('update_entry_avg', 0.0)
        report_lines.append(f"compute time avg (ms): {comp_avg:.6f}")
        report_lines.append(f"update entry avg: {update_avg:.6f}")

        num_obs = stats_results.get('num_observers', 0)
        report_lines.append(f"number of observers: {num_obs}")
        observer_stats = stats_results.get('observer_stats', [])
        for obs_stat in observer_stats:
            src, dst = obs_stat['src'], obs_stat['dst']
            latency = obs_stat['latency']
            fail_rate = obs_stat['failure_rate']
            report_lines.append(f"route path [{src}, {dst}]")
            report_lines.append(f"\tlatency avg (ms): {latency:.6f}")
            report_lines.append(f"\tfailure rate avg: {fail_rate:.6f}")

        report_content = "\n".join(report_lines) + "\n"

        # --- Print summary to console ---
        print("-" * 20)
        print(f"REPORT at Sim Time {current_sim_time}")
        print(f"Wall Time Elapsed: {elapsed_wall_time:.2f} s")
        print(f"ETA: {eta_seconds:.2f} s")
        print(f"Avg Compute Time: {comp_avg:.3f} ms")
        print(f"Avg Update Entries: {update_avg:.2f}")
        for obs_stat in observer_stats:
            print(f"  Observer [{obs_stat['src']}->{obs_stat['dst']}]: Latency={obs_stat['latency']:.3f} ms, FailRate={obs_stat['failure_rate']:.3%}")
        print("-" * 20)

        # --- Write report to file ---
        try:
            with open(self.report_filepath, 'w') as f:
                f.write(report_content)
        except IOError as e:
            print(f"Error writing report file {self.report_filepath}: {e}", file=sys.stderr)