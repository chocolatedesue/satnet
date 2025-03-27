import numpy as np
from pathlib import Path
import sys
from typing import List, Tuple, Dict, Any

from .config import Config
from .data_manager import DataManager
from .topology import move # Need topology functions
from .utils import go_and_create # For creating frame directories

class Visualizer:
    """Handles generation and saving of visualization frames."""

    def __init__(self, config: Config):
        self.config = config
        self.enabled = config.visualization_enabled
        if not self.enabled:
            print("Visualizer: Disabled.")
            return

        self.frames_base_dir = config.vis_frames_dir
        self.scenario = config.vis_scenario
        self.vis_src = config.vis_src
        self.vis_dst = config.vis_dst
        self.show_diff_table = config.vis_show_diff_table
        self.frame_id = 0

        # Ensure base frame directory exists
        # create_dir_recursive(self.frames_base_dir)
        if not Path(self.frames_base_dir).exists():
            Path(self.frames_base_dir).mkdir(parents=True, exist_ok=True)
        print(f"Visualizer: Enabled. Frames saving to '{self.frames_base_dir / self.scenario}'")

        # Internal frame data storage (cleared each step)
        self._frame_nodes: list = []
        self._frame_edges: list = []
        self._frame_nodes_3d: list = []

    def generate_and_save_frame(self, time: int, data_manager: DataManager, route_tables: np.ndarray):
        """Generate and save a single visualization frame if enabled."""
        if not self.enabled:
            return

        # Clear previous frame data
        self._frame_nodes.clear()
        self._frame_edges.clear()
        self._frame_nodes_3d.clear()

        # --- Generate frame content ---
        self._dump_nodes(data_manager)
        self._dump_edges(data_manager)

        if self.vis_dst != -1 and self.vis_src != -1:
            self._dump_path(self.vis_src, self.vis_dst, route_tables, data_manager.get_current_banned())
        elif self.vis_src != -1:
            self._dump_table(self.vis_src, route_tables, data_manager.get_velocities())
        else:
            # If dawn_dust dir is specified in config and exists
            if self.config.dawn_dust_dir and self.config.dawn_dusk_icrs_dir:
                self._dump_dawn_dust_line(time)
        # --- End Generation ---

        self._save_frame()


    def _dump_nodes(self, data_manager: DataManager):
        sat_lla = data_manager.get_lla()
        sat_pos = data_manager.get_positions()
        for i in range(self.config.N):
            # Node format: ((longitude, latitude), type_code)
            # Assuming LLA is Lat, Lon, Alt
            node_pos = (sat_lla[i, 1], sat_lla[i, 0]) # lon, lat
            node_type = 0 # Default type
            self._frame_nodes.append((node_pos, node_type))
            # Node 3D format: [x, y, z]
            self._frame_nodes_3d.append(sat_pos[i].tolist())

    def _dump_edges(self, data_manager: DataManager):
        cur_banned = data_manager.get_current_banned()
        P, Q, F = self.config.P, self.config.Q, self.config.F
        N = self.config.N

        # Dump only West (1) and North (2) links from each node to avoid duplicates
        for u in range(N):
            for i in range(1, 3): # Directions 1 (West) and 2 (North)
                v = move(u, i, P, Q, F)
                endpoints = (u, v)
                if cur_banned[u, i] == 0:
                    edge_type = i # 1 or 2 for active intra/inter-plane
                    self._frame_edges.append((endpoints, edge_type))
                else:
                    # Check reverse ban too? Original C++ didn't seem to, but maybe safer?
                    # _, v_port = get_port(u, v, P, Q, F)
                    # if cur_banned[v, v_port] == 1:
                    edge_type = 0 # Banned
                    self._frame_edges.append((endpoints, edge_type))

    def _dump_path(self, src: int, dst: int, route_tables: np.ndarray, cur_banned: np.ndarray):
        if not (0 <= src < self.config.N and 0 <= dst < self.config.N): return

        # Mark src and dst nodes (type 1)
        if src < len(self._frame_nodes): self._frame_nodes[src] = (self._frame_nodes[src][0], 1)
        if dst < len(self._frame_nodes): self._frame_nodes[dst] = (self._frame_nodes[dst][0], 1)

        cur = src
        max_hops = self.config.N # Limit path dump length
        hops = 0
        visited_dump = set()
        P, Q, F = self.config.P, self.config.Q, self.config.F

        while cur != dst and hops < max_hops:
            if cur in visited_dump: break # Cycle detected during dump
            visited_dump.add(cur)

            next_hop_port = route_tables[cur, dst]
            if next_hop_port == 0 or next_hop_port >= cur_banned.shape[1] or cur_banned[cur, next_hop_port]:
                break # Path broken

            neigh = move(cur, next_hop_port, P, Q, F)
            # Add path edge (type 3)
            self._frame_edges.append(((cur, neigh), 3))
            cur = neigh
            hops += 1

    def _dump_table(self, src: int, route_tables: np.ndarray, sat_vel: np.ndarray):
        if not (0 <= src < self.config.N): return

        # Mark src node (type 7)
        if src < len(self._frame_nodes): self._frame_nodes[src] = (self._frame_nodes[src][0], 7)

        src_vel_positive = (sat_vel[src] > 0)

        for i in range(self.config.N):
            if i == src: continue
            if i >= len(self._frame_nodes): continue # Safety check

            i_vel_positive = (sat_vel[i] > 0)
            show_node = False

            if self.show_diff_table == 0: # Show same direction
                if src_vel_positive == i_vel_positive: show_node = True
            elif self.show_diff_table == 1: # Show different direction
                if src_vel_positive != i_vel_positive: show_node = True
            elif self.show_diff_table == 2: # Show all
                show_node = True

            if show_node:
                # Node type based on next hop port + 2 (ports 1-4 -> types 3-6)
                # Port 0 maps to type 2
                node_type = route_tables[src, i] + 2
                self._frame_nodes[i] = (self._frame_nodes[i][0], node_type)


    def _dump_dawn_dust_line(self, time: int):
        # Requires dawn_dusk dirs to be set in config
        if not self.config.dawn_dust_dir or not self.config.dawn_dusk_icrs_dir:
             return

        dawn_dust_file = self.config.dawn_dust_dir / f"{time}.txt"
        icrs_file = self.config.dawn_dusk_icrs_dir / f"{time}.txt"

        # Read 2D points (Lat/Lon)
        try:
            start_idx = len(self._frame_nodes)
            new_nodes_2d = []
            if dawn_dust_file.exists():
                 with open(dawn_dust_file, 'r') as f:
                      for line in f:
                           parts = line.split()
                           if len(parts) >= 2:
                               try:
                                   # Assuming file is Lat Lon
                                   lat, lon = float(parts[0]), float(parts[1])
                                   node_pos = (lon, lat) # Vis format wants Lon, Lat
                                   node_type = 8 # Dawn/dusk line point type
                                   new_nodes_2d.append((node_pos, node_type))
                               except ValueError: continue # Skip invalid lines

            # Add edges between consecutive line points (type 4)
            if new_nodes_2d:
                 self._frame_nodes.extend(new_nodes_2d)
                 for i in range(start_idx, len(self._frame_nodes) - 1):
                      self._frame_edges.append(((i, i + 1), 4))

            # Read 3D points (ICRS) if available
            if icrs_file.exists():
                 num_3d_needed = len(new_nodes_2d)
                 num_3d_read = 0
                 with open(icrs_file, 'r') as f:
                      for line in f:
                          if num_3d_read >= num_3d_needed: break
                          parts = line.split()
                          if len(parts) >= 3:
                              try:
                                  x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                                  self._frame_nodes_3d.append([x, y, z])
                                  num_3d_read += 1
                              except ValueError: continue # Skip invalid lines
                 # Pad with zeros if fewer 3D points than 2D points? Or just let it be shorter?
                 # C++ code seems to just append while file has data and space exists. Let's match.

        except IOError as e:
            print(f"Warning: Error reading dawn/dusk file(s) for time {time}: {e}", file=sys.stderr)


    def _save_frame(self):
        """Saves the collected frame data to a file."""
        # Use utils helper to create scenario directory under base frames dir
        open_dir = go_and_create(self.frames_base_dir, [self.scenario])
        open_path = open_dir / f"{self.frame_id}.txt"
        self.frame_id += 1

        try:
            with open(open_path, 'w') as f:
                # Line 1: Nodes ((lon lat type) | ...)
                node_strs = [f"{node[0][0]:f} {node[0][1]:f} {node[1]:d}" for node in self._frame_nodes]
                f.write(" | ".join(node_strs))
                f.write("\n")

                # Line 2: Edges ((u v type) | ...)
                edge_strs = [f"{edge[0][0]:d} {edge[0][1]:d} {edge[1]:d}" for edge in self._frame_edges]
                f.write(" | ".join(edge_strs))
                f.write("\n")

                # Line 3: Nodes 3D ((x y z) | ...)
                node_3d_strs = [f"{node[0]:f} {node[1]:f} {node[2]:f}" for node in self._frame_nodes_3d]
                f.write(" | ".join(node_3d_strs))
                f.write("\n")

        except IOError as e:
            print(f"Error writing frame file {open_path}: {e}", file=sys.stderr)