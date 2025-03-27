# Note: Renamed from DijkstraNode to avoid conflict if other Dijkstra variants exist
#       and to better reflect its role as a base for Probe/Pred.
import numpy as np
import heapq  # For priority queue (min-heap)
import sys

# Import base class and types
from .base_node import BaseNode
from ..config import Config
from ..world import World
# Import helpers needed directly (alternatively, pass them if preferred)
from ..topology import move
from ..physics import calculate_delay_ms

# Import the assumed parent class
# try:
#     from .discoroute_node import DiscoRouteNode
# except ImportError:
#     print("Warning: Could not import DiscoRouteNode. Falling back to BaseNode for DijkstraBaseNode.")
#     # Fallback to BaseNode if DiscoRouteNode is not implemented/available yet
#     # This allows basic structure check but inheritance might be incorrect.
#     DiscoRouteNode = BaseNode


class DijkstraNode(BaseNode):
    """
    Base implementation for Dijkstra-based routing.
    Computes shortest paths based on latency, ignoring banned links by default.
    Inherits state/methods potentially from DiscoRouteNode (or BaseNode as fallback).
    """

    def __init__(self, config: Config, node_id: int, world: World):
        super().__init__(config, node_id, world) # Call parent constructor

        # Latency parameters (could be inherited if parent handles them)
        # self.proc_delay = config.proc_delay
        # self.prop_delay_coef = config.prop_delay_coef
        # self.prop_speed = config.prop_speed

        # Dijkstra specific state arrays
        self._dist = np.full(self.N, sys.float_info.max, dtype=float)
        # No explicit 'vis' needed if we check distance before processing heap element

        # Pre-calculate own position for efficiency if needed often
        # self._my_pos = self.world.sat_pos[self.node_id] # Requires world.sat_pos

        # Initialize route table (fill with 0, meaning no route/next-hop)
        self._route_table.fill(0)

    def get_name(self) -> str:
        return "DijkstraBase"

    # --- Re-implement physics helpers if not reliably inherited or for clarity ---
    # It's often better to use the centralized physics module functions.
    # def _get_dist_m(self, pos_a: np.ndarray, pos_b: np.ndarray) -> float:
    #     diff_km = pos_a - pos_b
    #     dist_km_sq = np.sum(diff_km * diff_km)
    #     return math.sqrt(dist_km_sq) * 1000.0

    # def _calculate_delay_ms(self, u_id: int, v_id: int) -> float:
    #     pos_u = self.world.sat_pos[u_id]
    #     pos_v = self.world.sat_pos[v_id]
    #     dist_m = self._get_dist_m(pos_u, pos_v)
    #     prop_delay = self.prop_delay_coef * dist_m / self.prop_speed
    #     return self.proc_delay + prop_delay
    # --- End Re-implementation ---

    def _compute_dijkstra(self, banned_links: np.ndarray):
        """
        Core Dijkstra computation. Uses the provided banned_links array.

        Args:
            banned_links: The (N, 5) array indicating which links are banned.
                          Use world.cur_banned or world.futr_banned.
        """
        # Reset state for this computation
        self._dist.fill(sys.float_info.max)
        self._route_table.fill(0) # No route initially

        # Access shared state via self.world
        sat_pos = self.world.sat_pos # Get current satellite positions

        # Priority queue: stores (distance, node_id, first_hop_port_from_source)
        # first_hop_port_from_source is crucial for reconstructing the path's *first* step
        pq = [(0.0, self.node_id, 0)] # Distance to self is 0, first hop is 0 (none)
        self._dist[self.node_id] = 0.0

        # Keep track of visited nodes to avoid reprocessing (optional but efficient)
        visited = np.zeros(self.N, dtype=bool)


        while pq:
            # Get node with the smallest distance
            d, u, _ = heapq.heappop(pq) # We don't need first_hop_port here

            # If we found a shorter path already, skip
            # Also handles the C++ 'vis[u]' check implicitly
            if d > self._dist[u] or visited[u]:
                continue

            visited[u] = True

            # Explore neighbors
            for port in range(1, 5): # Ports 1, 2, 3, 4
                # Check if this outgoing link is banned
                if banned_links[u, port]:
                    continue

                v = move(u, port, self.config.P, self.config.Q, self.config.F)
                if v == u: continue # Skip self-loops if move allows them

                # Calculate edge weight (latency)
                try:
                    # Use centralized physics calculation
                    weight = calculate_delay_ms(
                        sat_pos[u], sat_pos[v],
                        self.config.proc_delay, self.config.prop_delay_coef, self.config.prop_speed
                    )
                except IndexError:
                    print(f"Error accessing sat_pos for edge {u} -> {v}", file=sys.stderr)
                    continue # Skip edge if position data is bad

                # Relaxation step
                new_dist = self._dist[u] + weight
                if new_dist < self._dist[v]:
                    self._dist[v] = new_dist

                    # Determine the *first* hop port from the source (self.node_id)
                    # If u is the source, the first hop is the current port 'i'
                    # Otherwise, inherit the first hop from the path to u
                    first_hop_port = port if u == self.node_id else self._route_table[u]

                    # Update the route table for node v: store the first hop port
                    self._route_table[v] = first_hop_port

                    # Push the new shorter path candidate to the heap
                    heapq.heappush(pq, (new_dist, v, first_hop_port)) # Store first hop in PQ if needed for debugging

    def compute(self) -> None:
        """
        Default Dijkstra compute: uses an effectively empty ban list.
        Subclasses should override this or call _compute_dijkstra directly.
        """
        # Create a dummy empty ban list for the base case
        # Alternatively, could check `if not np.any(banned_links)` inside _compute_dijkstra
        # but passing explicitly might be clearer for subclasses.
        no_bans = np.zeros_like(self.world.cur_banned)
        self._compute_dijkstra(no_bans)

    # get_route_table() is inherited from BaseNode and returns self._route_table