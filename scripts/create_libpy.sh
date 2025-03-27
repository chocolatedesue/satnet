#!/bin/bash

# Define the base project directory name
PROJECT_DIR="."

# Create the base directory
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit # Move into the project dir, exit if failed

# Create the main package directory and subdirectories
mkdir -p "simulation_package/nodes"

# Create empty __init__.py files to mark directories as packages
touch "simulation_package/__init__.py"
touch "simulation_package/nodes/__init__.py"

# Create placeholder Python files (optional, but helpful)
touch main.py
touch simulation_package/simulation.py
touch simulation_package/config.py
touch simulation_package/world.py
touch simulation_package/topology.py
touch simulation_package/physics.py
touch simulation_package/data_manager.py
touch simulation_package/failure.py
touch simulation_package/routing.py
touch simulation_package/stats.py
touch simulation_package/visualizer.py
touch simulation_package/reporter.py
touch simulation_package/utils.py
touch simulation_package/nodes/base_node.py
touch simulation_package/nodes/dummy_node.py # Placeholder

# Create common data/output directories (adjust names as needed)
mkdir -p data/isl_state
mkdir -p data/sat_position
mkdir -p data/sat_lla
mkdir -p data/sat_velocity
mkdir -p reports
mkdir -p frames
mkdir -p rib

echo "Directory structure created successfully in '$PROJECT_DIR'"
ls -R # List the created structure (optional)