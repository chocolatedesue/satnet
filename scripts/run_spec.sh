#!/bin/bash
# filepath: /home/cnic/work/satnet/scripts/run_spec.sh
#
# Run a range of spec configurations for the satnet simulator
# 
# Usage: ./scripts/run_spec.sh [options]
#
# Options:
#   -c, --config CONFIG    Configuration file path (default: configs/ng-full-starlink_group5-April.json)
#   -s, --start START      Starting spec number (default: 5100)
#   -e, --end END          Ending spec number (default: 5300)
#   -h, --help             Display this help message

# Default values
CONFIG="configs/ng-full-starlink_group5-April.json"
START_SPEC=200
END_SPEC=300

# Process command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -c|--config)
      CONFIG="$2"
      shift 2
      ;;
    -s|--start)
      START_SPEC="$2"
      shift 2
      ;;
    -e|--end)
      END_SPEC="$2"
      shift 2
      ;;
    -h|--help)
      echo "Run a range of spec configurations for the satnet simulator"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  -c, --config CONFIG    Configuration file path (default: configs/ng-full-starlink_group5-April.json)"
      echo "  -s, --start START      Starting spec number (default: 5100)"
      echo "  -e, --end END          Ending spec number (default: 5300)"
      echo "  -h, --help             Display this help message"
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
echo "Running specs $START_SPEC to $END_SPEC with config: $CONFIG"
echo "-----------------------------------------------------------"
echo "building the project..."

xmake || { echo "Build failed"; exit 1; }

# if fails, exit


# Run the specs
for i in $(seq $START_SPEC $END_SPEC); do
  echo "Running spec $i"
  xmake run -w . satnet "$CONFIG" $i
  
  # Add a small delay to avoid potential race conditions
#   sleep 0.5
done

echo "Completed all spec runs"