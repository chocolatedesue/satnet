import numpy as np
from pathlib import Path
import sys # Keep sys only if needed elsewhere, not for stderr print
from typing import List

# Import loguru logger
from loguru import logger

# Assuming these are in the same package or accessible
try:
    from .config import Config
    from .topology import get_port
    from .utils import _load_data_from_file
except ImportError as e:
    # Log critical import errors if they happen at import time
    logger.critical(f"Failed to import DataManager dependencies: {e}")
    sys.exit(1) # Can't proceed without these

class DataManager:
    """Loads and manages dynamic simulation state from files."""

    def __init__(self, config: Config):
        self.config = config
        self.N = config.N
        self.P = config.P
        self.Q = config.Q
        self.F = config.F
        logger.debug("Initializing DataManager...")

        # Initialize state arrays
        self.cur_banned: np.ndarray = np.zeros((self.N, 5), dtype=int)
        self.futr_banned: np.ndarray = np.zeros((self.N, 5), dtype=int)
        self.sat_pos: np.ndarray = np.zeros((self.N, 3), dtype=float)
        self.sat_lla: np.ndarray = np.zeros((self.N, 3), dtype=float)
        self.sat_vel: np.ndarray = np.zeros(self.N, dtype=float) # Should this be (N, 1) or (N,)? Assuming scalar velocity per sat for now
        logger.debug("State arrays initialized.")

        # Check directory existence early
        if not self.config.isl_state_dir.is_dir():
            # Use logger.warning for non-fatal configuration issues
            logger.warning(f"ISL state directory not found: {self.config.isl_state_dir}")
        # Add similar checks for other essential directories if needed
        if not self.config.sat_pos_dir.is_dir():
             logger.warning(f"Satellite position directory not found: {self.config.sat_pos_dir}")
        if not self.config.sat_lla_dir.is_dir():
             logger.warning(f"Satellite LLA directory not found: {self.config.sat_lla_dir}")
        if not self.config.sat_vel_dir.is_dir():
             logger.warning(f"Satellite velocity directory not found: {self.config.sat_vel_dir}")


    def _read_isl_state_file(self, time: int, banned_array: np.ndarray):
        """Reads banned ISLs from file and updates the specified banned_array."""
        isl_state_filename = self.config.isl_state_dir / f"{time}.txt"
        logger.debug(f"Attempting to read ISL state file: {isl_state_filename}")

        if not isl_state_filename.exists():
            # Use DEBUG level for expected 'file not found' if it's not an error
            logger.debug(f"ISL state file not found: {isl_state_filename} (assuming no links down for this time step)")
            return # No file means no links are banned from this source

        try:
            with open(isl_state_filename, 'r') as f:
                processed_count = 0
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line: # Skip empty lines
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            u, v = int(parts[0]), int(parts[1])
                            if 0 <= u < self.N and 0 <= v < self.N:
                                u_port, v_port = get_port(u, v, self.P, self.Q, self.F)
                                # Original code checked for != 0, assuming 0 is invalid/unused port
                                if u_port is not None and u_port != 0 and v_port is not None and v_port != 0:
                                    # Assuming port indices are 1-based in the file/logic?
                                    # Adjust index if banned_array is 0-based for ports
                                    banned_array[u, u_port] = 1
                                    banned_array[v, v_port] = 1
                                    processed_count += 1
                                else:
                                     # Warning for potential data/topology inconsistency
                                     logger.warning(f"Could not find valid ports between nodes {u} and {v} (line {i+1} in {isl_state_filename})")
                            else:
                                logger.warning(f"Node index out of range ({u} or {v}, N={self.N}) on line {i+1} in {isl_state_filename}")

                        except ValueError:
                            logger.warning(f"Invalid integer format on line {i+1} in {isl_state_filename}: '{line}'")
                    else:
                        logger.warning(f"Insufficient parts on line {i+1} in {isl_state_filename}: '{line}'")
            logger.debug(f"Processed {processed_count} banned link entries from {isl_state_filename}")

        except IOError as e:
             # Warning for file read errors, include exception details
             logger.warning(f"Could not read ISL state file {isl_state_filename}: {e}")
        except Exception as e:
             # Catch unexpected errors during processing
             logger.exception(f"An unexpected error occurred while processing {isl_state_filename}")


    def load_state_for_time(self, time: int):
        """Loads all dynamic state for the given simulation time."""
        # Use INFO for major actions within the component
        logger.info(f"Loading state for time {time}")

        # Positions
        pos_file = self.config.sat_pos_dir / f"{time}.csv"
        logger.debug(f"Loading positions from {pos_file}")
        _load_data_from_file(pos_file, self.sat_pos) # Assume _load_data adds its own logging if needed

        # LLA
        lla_file = self.config.sat_lla_dir / f"{time}.csv"
        logger.debug(f"Loading LLA from {lla_file}")
        _load_data_from_file(lla_file, self.sat_lla)

        # Velocity
        vel_file = self.config.sat_vel_dir / f"{time}.csv"
        logger.debug(f"Loading velocity from {vel_file}")
        _load_data_from_file(vel_file, self.sat_vel) # Ensure dtype/shape match

        # Current Banned Links
        logger.debug("Clearing and loading current banned links...")
        self.cur_banned.fill(0) # Clear previous state
        self._read_isl_state_file(time, self.cur_banned)
        logger.info(f"Finished loading state for time {time}")


    def load_future_banned(self, current_time: int):
        """Loads banned links for the upcoming update period."""
        logger.info(f"Loading future banned links (interval: {self.config.step}s, period: {self.config.update_period}s)")
        self.futr_banned.fill(0) # Clear previous state

        start_futr_time = current_time + self.config.step
        # Calculate end time correctly based on simulation end or update period end
        sim_end_time = self.config.start_time + self.config.duration
        period_end_time = current_time + self.config.update_period
        end_load_time = min(period_end_time, sim_end_time)

        logger.debug(f"Future banned load range: {start_futr_time} up to (exclusive) {end_load_time}")

        futr_time = start_futr_time
        files_processed = 0
        while futr_time < end_load_time:
            self._read_isl_state_file(futr_time, self.futr_banned)
            files_processed += 1
            futr_time += self.config.step

        logger.info(f"Finished loading future banned links (processed {files_processed} time steps).")

    # --- Getters for other components to access state ---
    # (No logging needed in simple getters)
    def get_positions(self) -> np.ndarray: return self.sat_pos
    def get_lla(self) -> np.ndarray: return self.sat_lla
    def get_velocities(self) -> np.ndarray: return self.sat_vel
    def get_current_banned(self) -> np.ndarray: return self.cur_banned
    def get_future_banned(self) -> np.ndarray: return self.futr_banned