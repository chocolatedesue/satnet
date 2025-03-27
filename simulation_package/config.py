import json
from pathlib import Path
import sys
from typing import Dict, Any, List, Optional

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Loads and provides access to simulation configuration."""

    def __init__(self, config_file_name: str):
        self.file_path = Path(config_file_name)
        if not self.file_path.is_file():
            raise ConfigError(f"Configuration file not found: {self.file_path}")

        try:
            with open(self.file_path, 'r') as f:
                self._raw_config: Dict[str, Any] = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Error decoding JSON configuration file {self.file_path}: {e}")

        # --- Extract and validate parameters ---
        self.name: str = self._get_required("name")

        # Constellation
        const_cfg = self._get_required("constellation")
        self.P: int = self._get_required("num_of_orbit_planes", parent=const_cfg, parent_name="constellation")
        self.Q: int = self._get_required("num_of_satellites_per_plane", parent=const_cfg, parent_name="constellation")
        self.F: int = self._get_required("relative_spacing", parent=const_cfg, parent_name="constellation")
        self.N: int = self.P * self.Q

        # ISL Latency
        isl_cfg = self._get_required("ISL_latency")
        self.proc_delay: float = self._get_required("processing_delay", parent=isl_cfg, parent_name="ISL_latency")
        self.prop_delay_coef: float = self._get_required("propagation_delay_coef", parent=isl_cfg, parent_name="ISL_latency")
        self.prop_speed: float = self._get_required("propagation_speed", parent=isl_cfg, parent_name="ISL_latency")

        # Timing
        self.step: int = self._get_required("step_length")
        self.duration: int = self._get_required("duration")
        self.start_time: int = self._get_optional("start_time", 0)
        self.update_period: int = self._get_optional("update_period", self.duration)
        self.refresh_period: int = self._get_optional("refresh_period", self.update_period)

        # Directories
        self.isl_state_dir: Path = Path(self._get_required("isl_state_dir"))
        self.sat_pos_dir: Path = Path(self._get_required("sat_position_dir"))
        self.sat_lla_dir: Path = Path(self._get_required("sat_lla_dir"))
        self.sat_vel_dir: Path = Path(self._get_required("sat_velocity_dir"))
        self.report_dir: Path = Path(self._get_required("report_dir"))
        self.dawn_dust_dir: Optional[Path] = Path(d) if (d := self._get_optional("dawn_dusk_dir")) else None
        self.dawn_dusk_icrs_dir: Optional[Path] = Path(d) if (d := self._get_optional("dawn_dusk_icrs_dir")) else None

        # Visualization
        self.visualization_enabled: bool = "visualization" in self._raw_config
        self.vis_config: Dict[str, Any] = self._get_optional("visualization", {})
        self.vis_src: int = self.vis_config.get("source", -1)
        self.vis_dst: int = self.vis_config.get("destination", -1)
        self.vis_frames_dir: Path = Path(self.vis_config.get("frames_dir", "frames")) # Default dir
        self.vis_scenario: str = self.vis_config.get("scenario", self.name) # Default scenario
        self.vis_show_diff_table: int = self.vis_config.get("diff_table", 0)

        # Failure Model
        self.failure_model_config: Dict[str, Any] = self._get_optional("failure_model", {})
        self.link_failure_probability: float = self.failure_model_config.get("link_probability", 0.0)
        self.node_failure_probability: float = self.failure_model_config.get("node_probability", 0.0)

        # Observers
        observer_path_str = self._get_required("observer_config_path")
        self.observer_config_path: Path = Path(observer_path_str)
        if not self.observer_config_path.is_file():
             raise ConfigError(f"Observer config file not found: {self.observer_config_path}")

        # RIB Dump
        self.dump_rib_nodes: List[int] = self._get_optional("dump_rib_nodes", [])

        # Seed
        self.seed: int = self._get_optional("seed", 42)

        # --- Basic Validation ---
        if self.step <= 0: raise ConfigError("step_length must be positive")
        if self.duration <= 0: raise ConfigError("duration must be positive")
        if self.update_period <= 0: raise ConfigError("update_period must be positive")
        if self.refresh_period <= 0: raise ConfigError("refresh_period must be positive")


    def _get_required(self, key: str, parent: Optional[Dict] = None, parent_name: Optional[str] = None) -> Any:
        """Gets a required key from the config, raising an error if missing."""
        source = parent if parent is not None else self._raw_config
        source_name = f" in '{parent_name}'" if parent_name else ""
        if key not in source:
            raise ConfigError(f"Missing required configuration key: '{key}'{source_name}")
        return source[key]

    def _get_optional(self, key: str, default: Any = None, parent: Optional[Dict] = None) -> Any:
        """Gets an optional key from the config, returning default if missing."""
        source = parent if parent is not None else self._raw_config
        return source.get(key, default)