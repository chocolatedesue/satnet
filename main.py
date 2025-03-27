# main.py

import sys
import argparse
import importlib
# import traceback # No longer needed with logger.exception()
from pathlib import Path
from typing import Type

# Import loguru logger
from loguru import logger

# --- Logger Configuration ---
# Remove the default handler to prevent potential duplicate outputs
logger.remove()
# Add a standard handler to stderr
# You can customize the format, level (e.g., "DEBUG", "INFO", "WARNING")
# and add file sinks here if needed.
logger.add(
    sys.stderr,
    level="INFO", # Log INFO level messages and above
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
# Example file logging (uncomment if needed):
# logger.add("simulation_{time}.log", level="DEBUG", rotation="10 MB")
# --------------------------


# Assuming your simulation package is structured like 'simulation_package'
# It's good practice to handle potential ImportErrors during simulation setup
try:
    from simulation_package.simulation import Simulation
    from simulation_package.nodes.base_node import BaseNode # For type hinting
except ImportError as e:
    logger.critical(f"Failed to import core simulation components: {e}")
    logger.critical("Please ensure 'simulation_package' is installed and accessible.")
    sys.exit(1)


# Mapping from Algorithm ID (int) to Node Class Name (str)
# (Keep the ALGORITHM_MAP as it is)
ALGORITHM_MAP = {
    # --- Basic ---
    # 1000: "BaseNode", # BaseNode is abstract, can't be instantiated directly

    # --- DisCoRoute Variants ---
    1001: "DiscoRouteNode",        # Assumes disco_route_node.py exists
    1002: "DiscoRouteProbeNode",   # Assumes disco_route_probe_node.py exists
    1003: "DiscoRoutePredNode",    # Assumes disco_route_pred_node.py exists

    # --- CoinFlip Variants ---
    2001: "CoinFlipNode",
    2002: "CoinFlipProbeNode",
    2003: "CoinFlipPredNode",

    # --- Dijkstra Variants ---
    3001: "DijkstraNode", # Assumes dijkstra_node.py exists
    3002: "DijkstraProbeNode",
    3003: "DijkstraPredNode",

    # --- DagShort Variants ---
    4001: "DagShortNode",
    4002: "DagShortProbeNode",
    4003: "DagShortPredNode",
    # DagShortNormNode<N> might need special handling.
    # Option 1: Create separate classes in Python (DagShortNormNode1, DagShortNormNode2, ...)
    # Option 2: Create one DagShortNormNode class that takes N as an __init__ parameter
    #           (requires modification of how Simulation passes config/params)
    # Option 3: Use a factory function (shown below)
    # Let's use placeholder names for now, assuming separate classes or factory needed
    4011: "DagShortNormNode_1",
    4012: "DagShortNormNode_2",
    4013: "DagShortNormNode_3",
    4014: "DagShortNormNode_4",
    4015: "DagShortNormNode_5",
    4016: "DagShortNormNode_6",
    4017: "DagShortNormNode_7",
    4018: "DagShortNormNode_8",

    # --- Misc ---
    5001: "MinHopCountNode",
    5002: "LbpNode",

    # --- Domain Routing --- (Similar template issue as DagShortNormNode)
    # Using placeholder names. You'll need to implement these classes/factories.
    6001: "DomainRoutingNode_1",
    6002: "DomainRoutingNode_3",
    6003: "DomainRoutingNode_4",
    6004: "DomainRoutingNode_6",
    6005: "DomainRoutingNode_12",
    6006: "DomainRoutingNode_20",
    6007: "DomainRoutingNode_30",
    6008: "DomainRoutingNode_60",

    # --- Domain DagShort ---
    7001: "DomainDagShortNode_1",
    7002: "DomainDagShortNode_3",
    7003: "DomainDagShortNode_4",
    7004: "DomainDagShortNode_6",
    7005: "DomainDagShortNode_12",
    7006: "DomainDagShortNode_20",
    7007: "DomainDagShortNode_30",
    7008: "DomainDagShortNode_60",

    # --- Domain Bridge --- (Template with two parameters)
    # These definitely require special handling, likely a factory or modified class init
    9001: "DomainBridgeNode_1_0",
    9002: "DomainBridgeNode_3_0",
    9003: "DomainBridgeNode_4_0",
    # ... and so on for all DomainBridgeNode combinations ...
    9028: "DomainBridgeNode_60_2",

    # --- NgDomainBridge ---
    9100: "NgDomainBridge_1_1",
    9110: "NgDomainBridge_5_1",
    # ... and so on ...
    9314: "NgDomainBridge_15_20",

    # --- DiffDomainBridge ---
    9411: "DiffDomainBridge_1_1",
    # ... and so on ...
    9455: "DiffDomainBridge_20_5",

    # --- LocalDomainBridge ---
    9511: "LocalDomainBridge_1_1",
    # ... and so on ...
    9555: "LocalDomainBridge_20_5",

    # --- Add your translated algorithms here ---
    # Example:
    # 1001: "DiscoRouteNode",
}

# Function remains the same, but errors raised within it will be caught later
def get_node_class(algorithm_id: int) -> str:
    """
    Returns the Node class name string based on the algorithm ID.
    Raises ValueError for invalid IDs.
    """
    if algorithm_id not in ALGORITHM_MAP:
        raise ValueError(f"Invalid or unsupported algorithm ID: {algorithm_id}")
    class_name = ALGORITHM_MAP[algorithm_id]
    logger.debug(f"Mapping Algorithm ID {algorithm_id} to Node Class Name '{class_name}'")
    return class_name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Space Network Simulation")
    parser.add_argument("config_file", help="Path to the simulation JSON configuration file.")
    parser.add_argument("algorithm_id", type=int, help="Integer ID specifying the routing algorithm to use.")

    # Check if enough arguments were provided
    if len(sys.argv) != 3:
         logger.error("Incorrect number of arguments provided. Expected <config_file> and <algorithm_id>.")
         parser.print_help(sys.stderr) # Keep using print_help for standard argparse output
         sys.exit(1)

    args = parser.parse_args()
    logger.info(f"Received arguments: config_file='{args.config_file}', algorithm_id={args.algorithm_id}")

    # Validate algorithm ID before proceeding (more specific logging)
    if args.algorithm_id not in ALGORITHM_MAP:
         # Log the error using logger
         logger.error(f"Invalid or unsupported algorithm ID: {args.algorithm_id}")
         # Log available IDs for user convenience (consider DEBUG level if too verbose)
         logger.info(f"Available Algorithm IDs: {sorted(list(ALGORITHM_MAP.keys()))}")
         sys.exit(1)

    try:
        # 1. Get the Node Class name based on ID
        SelectedNodeClassName = get_node_class(args.algorithm_id)
        logger.info(f"Selected Node Class Name: '{SelectedNodeClassName}' for Algorithm ID: {args.algorithm_id}")

        # 2. Instantiate and run the simulation
        #    Pass the class NAME, Simulation constructor should handle instantiation
        #    (Assuming Simulation is designed to take the class name string)
        logger.info(f"Initializing Simulation with config: '{args.config_file}'...")
        sim = Simulation(config_file_name=args.config_file, node_class_name=SelectedNodeClassName)

        logger.info("Starting simulation run...")
        sim.run()
        logger.success("Simulation run completed successfully.") # Use success level for positive outcome

    except FileNotFoundError as e:
         # Use logger.exception to log the error message AND traceback
         logger.exception(f"Configuration file not found") # The exception 'e' details are added automatically
         sys.exit(1)
    except ValueError as e: # Catches invalid algorithm ID from get_node_class or other config value errors
         logger.exception(f"Configuration or Value Error encountered")
         sys.exit(1)
    # Add more specific exceptions if Simulation or node loading might raise them
    except ImportError as e:
         logger.exception(f"Failed to import required modules for simulation/nodes")
         sys.exit(1)
    except AttributeError as e:
         logger.exception(f"Problem accessing attributes, possibly related to node class loading")
         sys.exit(1)
    except Exception as e: # Catch any other unexpected errors during simulation run
        # logger.exception automatically includes the traceback
        logger.exception("An unexpected error occurred during simulation")
        sys.exit(1)

    # No need for a separate print here, the logger.success above handles it.
    # logger.info("Exiting script.") # Optional: Add a final exit log message
    sys.exit(0) # Explicit successful exit