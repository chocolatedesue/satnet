# from simulation_package.stats import StatisticsCollector
import sys
from simulation_package.simulation import Simulation
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
    level="DEBUG", # Log INFO level messages and above
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

def test_delay_calc():
    # Create a simulation object
    sim = Simulation(config_file_name="configs/full.json", node_class_name="DijkstraNode")

    sim.calc_delay_by_node()