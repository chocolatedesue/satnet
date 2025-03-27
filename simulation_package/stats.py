import numpy as np
from pathlib import Path
import sys
from typing import List, Tuple, Dict, Any

from .config import Config
from .utils import Average
from .world import World # Need world to pass state to _compute_latency
from .data_manager import DataManager # Need access to state arrays via getters
from .physics import calculate_delay_ms # Need physics calculations
from .topology import move # Need topology calculations

class StatisticsCollector:
    """Loads observer configuration and collects simulation statistics."""

    def __init__(self, config: Config):
        self.config = config
        self.N = config.N

        # Observer setup
        self.num_observers: int = 0
        self.latency_observers: List[Tuple[int, int]] = []
        self._load_observer_config(config.observer_config_path)

        # Average trackers
        self.compute_time_result = Average()
        self.update_entry_result = Average()
        self.latency_results: List[Average] = [Average() for _ in range(self.num_observers)]
        self.failure_rates: List[Average] = [Average() for _ in range(self.num_observers)]

        # State for _compute_latency cycle detection
        self.path_timer: int = 0
        self.path_vis: np.ndarray = np.zeros(self.N, dtype=int)


    def _load_observer_config(self, observer_config_path: Path):
        """Loads observer pairs from the configuration file."""
        print(f"StatsCollector: Loading observers from {observer_config_path}")
        try:
            with open(observer_config_path, 'r') as f:
                lines = f.readlines()
                if not lines:
                    print(f"Warning: Observer config file is empty: {observer_config_path}", file=sys.stderr)
                    return

                self.num_observers = int(lines[0].strip())
                for i in range(1, min(len(lines), self.num_observers + 1)):
                    parts = lines[i].split()
                    if len(parts) >= 2:
                        try:
                            src, dst = int(parts[0]), int(parts[1])
                            if 0 <= src < self.N and 0 <= dst < self.N and src != dst:
                                self.latency_observers.append((src, dst))
                            else:
                                print(f"Warning: Invalid observer node ID or src==dst in {observer_config_path}: ({src}, {dst})", file=sys.stderr)
                        except ValueError:
                             print(f"Warning: Invalid line in observer config {observer_config_path}: {lines[i].strip()}", file=sys.stderr)

                # Adjust num_observers if fewer valid pairs were read
                self.num_observers = len(self.latency_observers)
                print(f"StatsCollector: Loaded {self.num_observers} valid observer pairs.")

        except FileNotFoundError:
             # This was already checked in Config, but double-check
             print(f"Error: Observer configuration file not found: {observer_config_path}", file=sys.stderr)
             sys.exit(1)
        except ValueError:
            print(f"Error: Invalid number format in observer config file: {observer_config_path}", file=sys.stderr)
            sys.exit(1)

    def log_compute_update_metrics(self, total_compute_time_ms: float, total_update_count: float, current_time: int):
        """Adds compute time and update count stats from a routing step."""
        if self.N > 0:
            avg_compute = total_compute_time_ms / self.N
            avg_update = total_update_count / self.N
            self.compute_time_result.add(avg_compute)
            # Don't log updates for the very first step (t=start_time)
            if current_time != self.config.start_time:
                 self.update_entry_result.add(avg_update)

    def _compute_latency(self, src: int, dst: int,
                        route_tables: np.ndarray,
                        cur_banned: np.ndarray,
                        sat_pos: np.ndarray) -> Tuple[float, bool]:
        """
        Computes path latency from src to dst using current state.
        Internal helper for compute_observer_metrics.
        """
        cur = src
        latency = 0.0
        success = True

        # Cycle detection reset (simplified from C++)
        # Consider a cleaner approach if this becomes an issue
        if self.path_timer >= sys.maxsize - 10: # Check before potential overflow
            self.path_vis.fill(0)
            self.path_timer = 0

        self.path_timer += 1
        # visited_in_this_path = set() # Alternative cycle detection

        max_hops = self.N * 2 # Safety break
        hops = 0

        while cur != dst and hops < max_hops:
            # visited_in_this_path.add(cur) # For set-based detection

            # Cycle detection using timer/vis array
            if self.path_vis[cur] == self.path_timer:
                 success = False
                 latency = -1.0
                 # print(f"Cycle detected: {src} -> {dst} at node {cur}")
                 break
            self.path_vis[cur] = self.path_timer

            # Get next hop port from routing table
            next_hop_port = route_tables[cur, dst]

            # Check if route exists and link is not banned
            if next_hop_port == 0 or next_hop_port >= cur_banned.shape[1] or cur_banned[cur, next_hop_port]:
                success = False
                latency = -1.0
                # print(f"Path break: {src} -> {dst}. Node {cur}, next hop port {next_hop_port}, banned={cur_banned[cur,next_hop_port] if next_hop_port>0 else 'N/A'}")
                break

            # Find neighbor ID
            neigh = move(cur, next_hop_port, self.config.P, self.config.Q, self.config.F)

            # Calculate one-hop latency
            one_hop_latency = calculate_delay_ms(
                sat_pos[cur], sat_pos[neigh],
                self.config.proc_delay, self.config.prop_delay_coef, self.config.prop_speed
            )
            latency += one_hop_latency
            cur = neigh
            hops += 1

        if hops >= max_hops and cur != dst: # Failed due to hop limit
             success = False
             latency = -1.0
             # print(f"Path failed (hop limit): {src} -> {dst}")
        elif cur != dst and success: # Should not happen if logic is correct, but safety check
            success = False
            latency = -1.0
            # print(f"Path failed (unexpected): {src} -> {dst}")


        return latency, success


    def compute_observer_metrics(self, route_tables: np.ndarray, data_manager: DataManager):
        """Computes latency and failure rate for all observers."""
        if self.num_observers == 0: return

        cur_banned = data_manager.get_current_banned()
        sat_pos = data_manager.get_positions()

        for i in range(self.num_observers):
            src, dst = self.latency_observers[i]
            latency, success = self._compute_latency(src, dst, route_tables, cur_banned, sat_pos)

            if success:
                self.failure_rates[i].add(0.0)
                self.latency_results[i].add(latency)
                # print(f"Observer {i} [{src}->{dst}]: Success, Latency={latency:.3f} ms")
            else:
                self.failure_rates[i].add(1.0)
                self.latency_results[i].add(-1.0) # Signal failure to Average class
                # print(f"Observer {i} [{src}->{dst}]: Failed")

    def get_results(self) -> Dict[str, Any]:
        """Returns a dictionary containing the current average results."""
        observer_stats = []
        for i in range(self.num_observers):
            observer_stats.append({
                "src": self.latency_observers[i][0],
                "dst": self.latency_observers[i][1],
                "latency": self.latency_results[i].get_result(),
                "failure_rate": self.failure_rates[i].get_result()
            })

        return {
            "compute_time_avg_ms": self.compute_time_result.get_result(),
            "update_entry_avg": self.update_entry_result.get_result(),
            "num_observers": self.num_observers,
            "observer_stats": observer_stats
        }