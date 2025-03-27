import numpy as np
import time
import importlib
from typing import List, Type, Tuple
from pathlib import Path
from loguru import logger
from .config import Config
from .world import World
from .nodes.base_node import BaseNode # Import base class
from .utils import go_and_create # For saving RIBs

class RoutingManager:
    """Manages node instances, triggers computations, and holds routing tables."""

    def __init__(self, config: Config, world: World, node_class: Type[BaseNode]):
        self.config = config
        self.world = world
        self.N = config.N
        self.nodes: List[BaseNode] = []
        self.algorithm_name = "Unknown"

        logger.info(f"RoutingManager: Initializing {self.N} nodes with {node_class.__name__}...")
        for i in range(self.N):
            self.nodes.append(node_class(config, i, world))
        if self.nodes:
            self.algorithm_name = self.nodes[0].get_name()

        # Main routing table store (N x N)
        # route_tables[i, j] = next hop port (1-4) from node i to node j (0 if none)
        self.route_tables: np.ndarray = np.zeros((self.N, self.N), dtype=int)

        # RIB dump setup
        self.dump_rib_flags: np.ndarray = np.zeros(self.N, dtype=int)
        for node_idx in config.dump_rib_nodes:
            if 0 <= node_idx < self.N:
                self.dump_rib_flags[node_idx] = 1
        self.rib_base_dir = Path("rib") # Base directory for RIB dumps


    def compute_and_update_routes(self, time_step: int) -> Tuple[float, float]:
        """
        Triggers computation for all nodes and updates the main routing tables.

        Args:
            time_step: The current simulation time step.

        Returns:
            Tuple (total_compute_time_ms, total_updated_entries).
        """
        total_compute_time_ms = 0.0
        total_updated_entries = 0

        # Consider parallelization here if N is large and node.compute() is expensive
        for i in range(self.N):
            node = self.nodes[i]

            # --- Compute Routing ---
            compute_start_cpu = time.process_time()
            node.compute() # Node updates its internal state/table
            elapsed_cpu_time = time.process_time() - compute_start_cpu
            compute_time_ms = elapsed_cpu_time * 1000.0
            total_compute_time_ms += compute_time_ms
            # --- End Compute ---

            # Get the newly computed routing table row from the node
            new_table_row = node.get_route_table() # Should be 1D array size N

            if new_table_row.shape != (self.N,):
                 logger.info(f"Error: Node {i} returned route table with wrong shape {new_table_row.shape}", file=sys.stderr)
                 continue # Skip update for this node

            # --- Calculate Diff and Update ---
            current_table_row = self.route_tables[i]
            diff_mask = (current_table_row != new_table_row)
            diff_count = np.sum(diff_mask)

            if diff_count > 0:
                # Update only the changed entries
                self.route_tables[i, diff_mask] = new_table_row[diff_mask]

            # Add to total updates (used for statistics)
            total_updated_entries += diff_count
            # --- End Update ---

            # Save RIB if requested for this node
            if self.dump_rib_flags[i]:
                self._save_rib(self.route_tables[i], i, time_step)

        avg_compute = total_compute_time_ms / self.N if self.N > 0 else 0
        logger.info(f"RoutingManager: Update complete. Avg Compute={avg_compute:.3f}ms. Total Changes={total_updated_entries}")
        return total_compute_time_ms, total_updated_entries

    def get_routing_tables(self) -> np.ndarray:
        """Returns the current N x N routing table array."""
        return self.route_tables

    def get_algorithm_name(self) -> str:
        return self.algorithm_name

    def _save_rib(self, rib_row: np.ndarray, src_node: int, time_step: int):
        """Saves the routing table row (RIB) for a specific node."""
        dir_levels = [self.config.name, self.algorithm_name, str(src_node)]
        # Use utils helper to create path relative to RIB base dir
        dir_path = go_and_create(self.rib_base_dir, dir_levels)
        file_path = dir_path / f"{time_step}.txt"
        try:
            # Save as space-separated integers in a single line
            np.savetxt(file_path, rib_row[np.newaxis, :], fmt='%d', delimiter=' ', newline='')
        except Exception as e:
            logger.info(f"Error saving RIB for node {src_node} at time {time_step} to {file_path}: {e}", file=sys.stderr)