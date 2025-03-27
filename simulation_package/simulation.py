from typing import Type
import numpy as np
import time
import sys
import importlib
# Import loguru logger - Ensure this is imported where the logger is configured
# (likely higher up in your application's entry point, e.g., main.py)
from loguru import logger

# Assuming these imports are relative to where Simulation is defined
try:
    from .config import Config, ConfigError
    from .world import World
    from .data_manager import DataManager
    from .failure import FailureManager
    from .routing import RoutingManager
    from .stats import StatisticsCollector
    from .visualizer import Visualizer
    from .reporter import Reporter
    from .nodes.base_node import BaseNode # For type hint
except ImportError as e:
    # Use logger for critical import errors if they happen even before Simulation init
    logger.critical(f"Failed to import core Simulation component: {e}")
    # Provide guidance if possible
    logger.critical("Ensure the simulation package structure is correct and accessible.")
    sys.exit(1)


class Simulation:
    """Orchestrates the satellite network simulation."""

    def __init__(self, config_file_name: str, node_class_name: str):
        """
        Initializes the simulation environment.

        Args:
            config_file_name: Path to the main JSON configuration file.
            node_class_name: The name of the node class to use (e.g., 'DummyNode', 'DijkstraNode').
                              Must match a class in a file within the 'nodes' subpackage.
        """
        logger.info("Initializing Simulation environment...")
        try:
            self.config = Config(config_file_name)
            logger.info(f"Loaded configuration '{self.config.name}' from '{config_file_name}'")
        except ConfigError as e:
            # Use logger.exception for errors during init, includes traceback
            logger.exception(f"Configuration Error loading '{config_file_name}'")
            sys.exit(1)
        except FileNotFoundError:
             # More specific exception for missing file
             logger.exception(f"Configuration file not found: '{config_file_name}'")
             sys.exit(1)

        # Load the specified node algorithm class dynamically
        self.node_class: Type[BaseNode] | None = None # Initialize to None
        try:
            # Construct module path (assuming standard naming convention)
            # Example: "DiscoRouteNode" -> "simulation_package.nodes.discoroute_node"
            base_name = node_class_name
            if base_name.endswith("Node"):
                 base_name = base_name[:-4] # Remove "Node" suffix for filename
            module_name = f"simulation_package.nodes.{base_name.lower()}_node"

            logger.debug(f"Attempting to import module: '{module_name}'")
            node_module = importlib.import_module(module_name, package='simulation_package')
            logger.debug(f"Successfully imported module: '{module_name}'")

            logger.debug(f"Attempting to get class '{node_class_name}' from module '{module_name}'")
            self.node_class = getattr(node_module, node_class_name)
            logger.info(f"Successfully loaded Node Algorithm Class: '{node_class_name}'")

        except (ImportError, AttributeError, ModuleNotFoundError) as e:
            # Log the exception with traceback
            logger.exception(f"Failed to load node class '{node_class_name}'")
            # Provide helpful guidance
            logger.error(f"Ensure a file like '{base_name.lower()}_node.py' exists in 'simulation_package/nodes/'")
            logger.error(f"and contains the class '{node_class_name}'. Check for typos or missing files.")
            sys.exit(1)
        # Catch other potential issues during init
        except Exception as e:
             logger.exception("An unexpected error occurred during Node Class loading")
             sys.exit(1)


        # --- Component Initialization ---
        # Use DEBUG level for potentially verbose init steps if needed, INFO is also fine
        logger.debug("Initializing simulation components...")
        try:
            self.current_time: int = self.config.start_time
            self.end_time: int = self.config.start_time + self.config.duration
            self.step: int = self.config.step

            # Random Number Generator
            self.random_engine = np.random.default_rng(self.config.seed)
            logger.debug(f"Initialized RNG with seed: {self.config.seed}")

            # Initialize components, injecting dependencies
            self.data_manager = DataManager(self.config)
            self.world = World(
                self.data_manager.get_current_banned(),
                self.data_manager.get_future_banned(),
                self.data_manager.get_positions(),
                self.data_manager.get_lla(),
                self.data_manager.get_velocities()
            )
            self.failure_manager = FailureManager(self.config, self.random_engine)
            # Ensure node_class was loaded successfully before passing
            if self.node_class is None:
                 # This should technically be caught above, but belt-and-suspenders
                 logger.critical("Node class was not loaded successfully, cannot initialize RoutingManager.")
                 sys.exit(1)
            self.routing_manager = RoutingManager(self.config, self.world, self.node_class)
            self.stats_collector = StatisticsCollector(self.config)
            self.visualizer = Visualizer(self.config)
            self.reporter = Reporter(self.config, self.routing_manager.get_algorithm_name(), node_class_name)

            self._run_start_wall_time: float = 0.0
            logger.info("Simulation components initialized successfully.")

        # Catch errors during component setup
        except Exception as e:
            logger.exception("An unexpected error occurred during simulation component initialization")
            sys.exit(1)


    def run(self):
        """Executes the main simulation loop."""
        # Use f-string and let logger handle formatting/newlines
        logger.info(f"--- Starting Simulation: {self.config.name} ---")
        logger.info(f"Time Range: {self.current_time} to {self.end_time - self.step} (Step: {self.step})")
        logger.info(f"Update Period: {self.config.update_period}, Refresh Period: {self.config.refresh_period}")

        self._run_start_wall_time = time.time()

        try: # Wrap the main loop in try/except for runtime errors
            while self.current_time < self.end_time:
                step_start_time = time.time()
                # Use info for major step marker, consider debug if too noisy
                logger.info(f"--- Sim Time: {self.current_time} ---")

                # 1. Load state for current time
                logger.debug("Loading state data...")
                self.data_manager.load_state_for_time(self.current_time)

                # 2. Routing Update?
                if self.current_time % self.config.update_period == 0:
                    logger.info("Routing update triggered.")
                    logger.debug("Loading future banned states...")
                    self.data_manager.load_future_banned(self.current_time)

                    logger.debug("Applying random failures...")
                    self.failure_manager.apply_random_failures(self.data_manager.get_current_banned())

                    logger.debug("Computing and updating routes...")
                    compute_time_ms, update_count = self.routing_manager.compute_and_update_routes(self.current_time)
                    logger.info(f"Route computation/update took {compute_time_ms:.2f} ms for {update_count} nodes.")

                    # Log computation statistics
                    self.stats_collector.log_compute_update_metrics(compute_time_ms * self.config.N, # Total time
                                                                   update_count * self.config.N,    # Total updates
                                                                   self.current_time)
                else:
                    logger.debug("Skipping routing update this step.")

                # 3. Collect Observer Statistics for this step
                logger.debug("Collecting observer statistics...")
                self.stats_collector.compute_observer_metrics(
                    self.routing_manager.get_routing_tables(),
                    self.data_manager # Pass DataManager to access state inside stats
                )

                # 4. Reporting Period?
                if self.current_time != self.config.start_time and \
                   self.current_time % self.config.refresh_period == 0:
                    logger.info(f"Generating report for time {self.current_time}...")
                    elapsed_wall = time.time() - self._run_start_wall_time
                    self.reporter.generate_report(
                        self.current_time,
                        self.stats_collector.get_results(),
                        elapsed_wall
                    )

                # 5. Visualization Output?
                # Use debug as visualization might happen every step and be verbose
                logger.debug("Checking for visualization output...")
                self.visualizer.generate_and_save_frame(
                    self.current_time,
                    self.data_manager,
                    self.routing_manager.get_routing_tables()
                )

                # 6. Advance Simulation Time
                self.current_time += self.step
                step_duration = time.time() - step_start_time
                # Use debug for step timing unless high-level performance monitoring is needed
                logger.debug(f"Step wall time: {step_duration:.3f} s")

        # Catch errors occurring during the simulation run
        except Exception as e:
            logger.exception(f"An unexpected error occurred during simulation run at time {self.current_time}")
            # Optionally try to generate a partial/error report
            try:
                error_elapsed_wall = time.time() - self._run_start_wall_time
                logger.warning("Attempting to generate final report despite error...")
                self.reporter.generate_report(
                    self.current_time, # Report at the time of failure
                    self.stats_collector.get_results(), # Use potentially incomplete stats
                    error_elapsed_wall,
                    is_error_report=True # Add flag if Reporter supports it
                )
            except Exception as report_err:
                logger.error(f"Failed to generate error report: {report_err}")
            sys.exit(1) # Exit after runtime error

        # --- Simulation Finished Normally ---
        final_elapsed_wall = time.time() - self._run_start_wall_time
        # Use SUCCESS level for clear indication of normal completion
        logger.success("--- Simulation Finished Successfully ---")
        logger.info("Generating final report...")
        self.reporter.generate_report(
            self.current_time - self.step, # Report time is the last completed step
            self.stats_collector.get_results(),
            final_elapsed_wall
        )
        logger.info(f"Total Wall Time: {final_elapsed_wall:.2f} s")