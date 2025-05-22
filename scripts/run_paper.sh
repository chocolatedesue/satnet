#!/bin/bash
# filepath: /home/cnic/work/satnet/scripts/run_spec_ids.sh
#
# Run specific algorithm configurations (by ID) for the satnet simulator
#
# Usage: ./scripts/run_spec_ids.sh [options]
#
# Options:
#   -c, --config CONFIG    Configuration file path (default: configs/ng-full-starlink_group5-April.json)
#   -h, --help             Display this help message

# --- List of Algorithm IDs to run ---
# Based on the C++ enum AlgorithmId and user request:
# 101: DijkstraPredNode (GSPR)
# 152: MinHopCountPredNode (MHR)
# 205: DomainHeuristicNode<2, 2>
# 202: DomainHeuristicNode<7, 20>
# 206: DomainHeuristicNode<14, 60>
ALGORITHM_IDS_TO_RUN=(
    # 101
    # 152
    205
    202
    206
)

# Default values
CONFIG="configs/ng-full-starlink_group5-April.json"

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -c|--config)
      CONFIG="$2"
      shift 2
      ;;
    -h|--help)
      echo "Run specific algorithm configurations (by ID) for the satnet simulator"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  -c, --config CONFIG    Configuration file path (default: configs/ng-full-starlink_group5-April.json)"
      echo "  -h, --help             Display this help message"
      echo ""
      echo "This script will run the following algorithm IDs:"
      # Print the list of algorithm IDs for clarity in help
      for algo_id in "${ALGORITHM_IDS_TO_RUN[@]}"; do
        # Optional: Add a lookup here to show names if you want, but IDs are primary
        echo "  - $algo_id"
      done
      echo "(Check C++ source or script comments for name mapping)"
      exit 0
      ;;
    *)
      echo "Error: Unknown option $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Validate config file exists
if [ ! -f "$CONFIG" ]; then
  echo "Error: Config file not found: $CONFIG"
  exit 1
fi

# Display run information
echo "Running specific algorithm IDs with config: $CONFIG"
echo "Algorithm IDs to run:"
for algo_id in "${ALGORITHM_IDS_TO_RUN[@]}"; do
  echo "  - $algo_id"
done
echo "-----------------------------------------------------------"
echo "Building the project..."

xmake || { echo "Build failed"; exit 1; }

# Run the specified algorithms using their IDs
# Loop through the array of algorithm IDs
for ALGO_ID in "${ALGORITHM_IDS_TO_RUN[@]}"; do
  echo "Running algorithm ID: $ALGO_ID"
  # Pass the config file and the integer algorithm ID to 'satnet'
  xmake run -w . satnet "$CONFIG" "$ALGO_ID"

  # Check exit status of the run command (optional but recommended)
  if [[ $? -ne 0 ]]; then
      echo "Error running algorithm ID: $ALGO_ID"
      # Decide whether to continue or exit
      # exit 1 # Uncomment to stop script on first error
  fi

  # Add a small delay if needed (optional)
  # sleep 0.5
done

echo "Completed all specified algorithm ID runs"