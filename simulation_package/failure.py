import numpy as np
import sys

from .config import Config
from .topology import move, get_port # Import topology functions

class FailureManager:
    """Applies random failure models to the simulation state."""

    def __init__(self, config: Config, random_engine: np.random.Generator):
        self.config = config
        self.random_engine = random_engine
        self.link_prob = config.link_failure_probability
        self.node_prob = config.node_failure_probability
        self.N = config.N
        self.P = config.P
        self.Q = config.Q
        self.F = config.F

        if self.link_prob > 0 or self.node_prob > 0:
            print(f"FailureManager: Initialized with Link P={self.link_prob:.2e}, Node P={self.node_prob:.2e}")

    def apply_random_failures(self, cur_banned: np.ndarray):
        """
        Applies configured random failures to the cur_banned array.
        Modifies cur_banned in place.
        """
        nodes_failed_count = self._introduce_independent_node_failures(cur_banned)
        links_failed_count = self._introduce_independent_link_failures(cur_banned)

        if nodes_failed_count > 0 or links_failed_count > 0:
             print(f"FailureManager: Applied {nodes_failed_count} node / {links_failed_count} link random failures.")


    def _introduce_independent_link_failures(self, cur_banned: np.ndarray) -> int:
        """Applies random link failures based on probability. Modifies cur_banned."""
        if self.link_prob <= 0:
            return 0

        links_failed_count = 0
        # Iterate through each potential link uniquely (e.g., u -> u's West/North neighbors)
        for u in range(self.N):
            for direction in [1, 2]: # Check West and North links from u
                v = move(u, direction, self.P, self.Q, self.F)
                # Check if link already banned by predictable events or other failures
                # This avoids double-counting failures and ensures probability is applied correctly.
                u_port, v_port = get_port(u, v, self.P, self.Q, self.F)

                if u_port != 0 and v_port != 0:
                    # Only apply random failure if the link isn't already banned
                    if cur_banned[u, u_port] == 0 and cur_banned[v, v_port] == 0:
                        if self.random_engine.random() < self.link_prob:
                            cur_banned[u, u_port] = 1
                            cur_banned[v, v_port] = 1
                            links_failed_count += 1
        return links_failed_count

    def _introduce_independent_node_failures(self, cur_banned: np.ndarray) -> int:
        """Applies random node failures based on probability. Modifies cur_banned."""
        if self.node_prob <= 0:
            return 0

        nodes_failed_count = 0
        # Determine which nodes fail in this step
        failed_node_indices = np.where(self.random_engine.random(self.N) < self.node_prob)[0]

        if len(failed_node_indices) == 0:
            return 0

        # Apply failures
        for u_failed in failed_node_indices:
            nodes_failed_count += 1
            # Ban all outgoing ports from the failed node
            cur_banned[u_failed, 1:5] = 1

            # Ban incoming ports on neighbors
            for direction in range(1, 5):
                v_neigh = move(u_failed, direction, self.P, self.Q, self.F)
                if v_neigh == u_failed: continue # Skip self

                _ , v_port_to_u = get_port(u_failed, v_neigh, self.P, self.Q, self.F)
                if v_port_to_u != 0:
                    cur_banned[v_neigh, v_port_to_u] = 1

        return nodes_failed_count

    # --- Keep the old method for reference or if probability model is off ---
    def _introduce_random_error_original(self, cur_banned: np.ndarray, futr_banned: np.ndarray):
        """Original random error logic based on count. Modifies arrays."""
        print("FailureManager: Applying original random error logic (count-based).")
        if self.N < 8:
            print("Warning: N < 8, original random error logic does nothing.")
            return

        max_cnt = self.N // 4
        min_cnt = self.N // 8
        if min_cnt >= max_cnt: min_cnt = max(0, max_cnt - 1)

        fail_cnt = 0
        if min_cnt <= max_cnt:
            fail_cnt = self.random_engine.integers(min_cnt, max_cnt + 1)

        for _ in range(fail_cnt):
            u = self.random_engine.integers(0, self.N)
            direction = self.random_engine.integers(1, 5) # Port 1-4
            v = move(u, direction, self.P, self.Q, self.F)
            u_port, v_port = get_port(u, v, self.P, self.Q, self.F)
            if u_port != 0 and v_port != 0:
                cur_banned[u, u_port] = 1
                cur_banned[v, v_port] = 1
                futr_banned[u, u_port] = 1 # Original logic modified future too
                futr_banned[v, v_port] = 1