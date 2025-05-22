# -*- coding: utf-8 -*-
"""
Processes specified algorithm performance report files from specified directories
(optionally recursively) to generate a filtered summary CSV and latency distribution data
with 'result-' prefixed filenames.
"""

import os
from pathlib import Path # Use pathlib for better path handling
from typing import Dict, List, Tuple, Any, Optional # Optional is cleaner than | None for hints
import numpy as np
from scipy import stats
import re # Import re for potentially more robust parsing if needed

# =============================================================================
# Configuration Section
# =============================================================================
# --- Input Sources and Search Mode ---
# List of directories to search for report files.
REPORT_SOURCES: List[Path] = [
    Path("output"),
    # Add other source directories if needed and RECURSIVE_SEARCH = False
]
RECURSIVE_SEARCH: bool = True # Set to True to search recursively within the first directory listed above

# --- Output Directories and Files ---
# Base directory for all generated output files
BASE_OUTPUT_DIRECTORY = Path("processed_results")
OUTPUT_PLOT_DIRECTORY = BASE_OUTPUT_DIRECTORY / "plot_data"
REPORT_FILE_SUFFIX = ".txt"
REPORT_FILE_PREFIX = "report"

# --- MODIFIED: Added "result-" prefix ---
# Ensure summary report goes into the base output directory
SUMMARY_REPORT_FILENAME_TEMPLATE = BASE_OUTPUT_DIRECTORY / "result-summary [{target_name}].csv"
# --- MODIFIED: Added "result-" prefix ---
# CDF filename template (will be placed inside OUTPUT_PLOT_DIRECTORY)
LATENCY_CDF_FILENAME_TEMPLATE = "result-{safe_algo_name}_latency_cdf.csv"

# --- Target Scenarios ---
# List of scenario names to process (matches 'name' field in report files)
TARGET_LIST = ["startlink-v2-group5-Apr", "startlink-v2-group5-Jan", "startlink-v2-group4-Jan", "startlink-v2-group4-April"]

# --- MODIFIED: Specify ONLY the algorithms to output and their order ---
# Use the original algorithm names found in the report files.
# GSPR -> DijkstraPred
# MHR  -> MinHopCountPred
ALGORITHMS_TO_OUTPUT: List[str] = [
    "DijkstraPred",         # Corresponds to GSPR
    "MinHopCountPred",      # Corresponds to MHR
    "DomainHeuristic_2_3",
    "DomainHeuristic_7_10", 
    "DomainHeuristic_14_60",
]

# --- MODIFIED: Simplify display mapping to only include required algorithms ---
# Map original names to desired display names in the output CSV.
# If an algorithm isn't listed here, its original name will be used.
ALGORITHM_DISPLAY_MAPPING: Dict[str, str] = {
    "DijkstraPred": "GSPR",
    "MinHopCountPred": "MHR",
    # DomainHeuristic variants will use their original names as they are not mapped here
}

# --- Algorithm Identification (Optional - Used for secondary sorting if needed) ---
# Kept for potential tie-breaking within the specified list, though less critical now.
ALGORITHM_ID_MAP: Dict[str, int] = {
    "Oracle": 0, "Base": 1000, "DijkstraBase": 1001, "CoinFlipBase": 2001,
    "CoinFlipPred": 2003, "DijkstraPred": 3003, "MinHopCount": 5001,
    "MinHopCountPred": 5003, "DomainHeuristic": 5100, # Base ID might be used if specific ones aren't listed
    "DomainHeuristic_2_2": 5101, # Assign arbitrary unique IDs if needed
    "DomainHeuristic_7_20": 5102,
    "DomainHeuristic_14_60": 5103,
    "DisCoRouteBase": 9000, "LBP": 9001, "DiffDomainBridge_10_3": 9100,
    "DiffDomainBridge_10_1": 9101, "DiffDomainBridge_8_3": 9102,
    "LocalDomainBridge_10_3": 9200, "LocalDomainBridge_10_1": 9201,
}
DEFAULT_SORT_ID = float('inf')

# --- Reporting and Analysis Parameters ---
# Benchmark algorithm should be one of the ALGORITHMS_TO_OUTPUT
# GSPR (DijkstraPred) is in the list, so this is fine.
BENCHMARK_ALGORITHM: str = "DijkstraPred"
LATENCY_CDF_NUM_BINS: int = 200
LATENCY_CDF_MIN_UPPER_BOUND: float = 300.0
LATENCY_CDF_UPPER_BOUND_FACTOR: float = 1.2
GENERATE_LATENCY_CDF_FILES: bool = True # Set to False if you don't need CDF files

# =============================================================================
# Core Logic Functions (Keeping essential ones, assuming they are correct)
# =============================================================================

# Keep read_report_file as it was in the provided good version
def read_report_file(file_path: Path, target_name: str) -> Optional[Dict[str, Any]]:
    """
    Reads and parses a single report file. (Implementation from original code)
    Returns a dictionary or None if file doesn't match target or has errors.
    """
    report_data: Dict[str, Any] = {}
    num_observers = -1
    required_keys = {"name", "algorithm", "compute time", "update entry", "number of observers"}
    found_keys = set()

    try:
        with file_path.open('r', encoding='utf-8') as f:
            # --- Phase 1: Read Metadata Block ---
            line_num = 0
            current_line_for_path: Optional[str] = None # Initialize
            while True:
                line = f.readline()
                line_num += 1
                if not line:
                    # Reached EOF before finding separator or path data
                    if "number of observers" not in found_keys:
                         print(f"Warning: Unexpected end of file in {file_path} before finding 'number of observers'.")
                    # If num_observers was found but no path data, it might be okay if num_observers is 0
                    # but the original check expects path data if num_observers > 0 later.
                    # Let's treat EOF here as an issue if we expected paths.
                    if num_observers > 0:
                         print(f"Warning: Unexpected end of file in {file_path} before finding path data for {num_observers} observers.")
                    return None # Treat premature EOF generally as an error

                stripped_line = line.strip()

                # Check for separator or start of path data
                if stripped_line == "---" or stripped_line.startswith("route path"):
                    if "number of observers" not in found_keys:
                        print(f"Warning: Reached separator/path data in {file_path} at line {line_num} before finding 'number of observers'.")
                        return None
                    else:
                        # Store the line if it's the start of path data, discard "---"
                        current_line_for_path = line if stripped_line.startswith("route path") else None
                        break # Exit metadata reading loop

                if ':' in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    report_data[key] = value
                    found_keys.add(key)

                    if key == "number of observers":
                        try:
                            num_observers = int(value)
                            if num_observers < 0:
                                raise ValueError("Number of observers cannot be negative")
                            # Found it, continue reading metadata
                        except ValueError:
                            print(f"Warning: Invalid 'number of observers' value '{value}' in {file_path} at line {line_num}.")
                            return None
                # Allow empty lines within metadata
                elif not stripped_line:
                    continue
                # If we found num_observers and encounter a non-empty line without ':', assume start of next section
                elif "number of observers" in found_keys:
                     current_line_for_path = line # Treat this unexpected line as potential start of path
                     break # Exit metadata reading loop

            # --- Phase 2: Post-Metadata Validation ---
            if num_observers == -1: # Check if it was actually found and parsed
                print(f"Warning: 'number of observers' key not found or processed correctly in {file_path}.")
                return None

            missing_keys = required_keys - found_keys
            if missing_keys:
                print(f"Warning: Missing required metadata keys in {file_path}: {missing_keys}")
                return None # Require all essential keys

            if report_data.get("name") != target_name:
                return None # Silently skip non-matching targets

            # --- Phase 3: Read Path Data ---
            route_paths: List[List[str]] = []
            observers_read = 0
            # Start reading from the line after metadata (or the stored 'route path' line)
            current_line = current_line_for_path if current_line_for_path is not None else f.readline()

            # Loop until we have read data for the expected number of observers
            while observers_read < num_observers:
                # Find the start of the next path block ("route path...")
                path_name = None
                while current_line:
                    stripped_line = current_line.strip()
                    if stripped_line.startswith("route path"):
                        path_name = stripped_line
                        break # Found the start of a path block
                    elif not stripped_line or stripped_line == "---":
                        current_line = f.readline() # Skip empty/separator lines
                        continue
                    else:
                        # Unexpected content before the next 'route path'
                        print(f"Warning: Unexpected non-empty line before 'route path' for observer {observers_read + 1} in {file_path}: '{stripped_line}'")
                        current_line = f.readline() # Skip this line and continue search
                        # If strict parsing is needed, uncomment the next line:
                        # return None

                if not path_name: # Reached EOF while searching for the next path block
                     if observers_read < num_observers:
                         print(f"Warning: Unexpected end of file in {file_path} while looking for 'route path' for observer {observers_read + 1} (expected {num_observers}). Found {observers_read}.")
                     # If num_observers was 0, this is okay. Otherwise, it's an error.
                     if num_observers > 0:
                         return None # Incomplete path data
                     else:
                         break # Correctly handled 0 observers

                # Found "route path...", now read the next two lines for latency and failure rate
                latency_line = f.readline()
                failure_line = f.readline()

                if not latency_line or not failure_line:
                    print(f"Warning: Unexpected EOF after reading '{path_name}' in {file_path}. Missing latency or failure rate.")
                    return None

                # Parse latency and failure rate
                try:
                    if ':' not in latency_line or ':' not in failure_line:
                        raise ValueError("Missing colon in latency/failure line")
                    latency_str = latency_line.split(":", 1)[1].strip()
                    failure_str = failure_line.split(":", 1)[1].strip()
                    # Basic validation: ensure they can be converted to float
                    float(latency_str)
                    float(failure_str)
                except (IndexError, ValueError) as e:
                    print(f"Warning: Error parsing latency/failure value for '{path_name}' in {file_path}. Error: {e}. Lines: '{latency_line.strip()}', '{failure_line.strip()}'")
                    return None

                route_paths.append([path_name, latency_str, failure_str])
                observers_read += 1

                # Read the next line to continue the outer loop (searching for next 'route path')
                current_line = f.readline()

            # --- Final Check ---
            # This check should be precise: did we read exactly the expected number?
            if len(route_paths) != num_observers:
                print(f"Warning: Mismatch between expected observers ({num_observers}) and successfully read paths ({len(route_paths)}) in {file_path}.")
                return None # Data integrity issue

            report_data["path info"] = route_paths
            return report_data

    except FileNotFoundError:
        print(f"Error: Report file not found: {file_path}")
        return None
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected error during parsing
        print(f"An unexpected error occurred while reading {file_path}: {e}")
        # import traceback
        # traceback.print_exc() # Uncomment for detailed debug trace if needed
        return None


# Keep get_records_from_location as it was
def get_records_from_location(directory: Path, target_name: str, recursive: bool) -> List[Dict[str, Any]]:
    """
    Scans a directory (optionally recursively) for report files
    matching the target scenario name and parses them.
    """
    records = []
    if not directory.is_dir():
        print(f"Warning: Source directory '{directory}' not found or is not a directory. Skipping.")
        return []

    search_mode = "recursively" if recursive else "non-recursively"
    print(f"Scanning directory '{directory}' {search_mode} for reports matching scenario '{target_name}'...")

    pattern = f"{REPORT_FILE_PREFIX}*{REPORT_FILE_SUFFIX}"
    files_to_check = directory.rglob(pattern) if recursive else directory.glob(pattern)

    # Sort files for potentially consistent processing order, especially if duplicates might exist
    sorted_files = sorted([f for f in files_to_check if f.is_file()])

    processed_files_count = 0
    matched_files_count = 0
    added_algos = set() # Track algorithms added for this target to warn about duplicates

    for file_path in sorted_files:
        processed_files_count += 1
        report_data = read_report_file(file_path, target_name)
        if report_data:
            algo_name = report_data.get("algorithm")
            # Handle potential duplicates if the same algo report exists in multiple places
            if algo_name:
                 if algo_name in added_algos:
                     print(f"Warning: Duplicate report found for algorithm '{algo_name}' for target '{target_name}' (e.g., in file {file_path.name}). Using the first one encountered.")
                 else:
                     records.append(report_data)
                     added_algos.add(algo_name)
                     matched_files_count += 1
            else:
                 print(f"Warning: Report file {file_path.name} parsed but missing 'algorithm' key.")


    print(f"Scan of '{directory}' complete. Processed {processed_files_count} potential report files, "
          f"successfully parsed {matched_files_count} unique matching reports for scenario '{target_name}'.")
    return records


# Keep calculate_statistics as it was
StatsTuple = Tuple[str, float, float, float, float, float, float, float]
def calculate_statistics(record: Dict[str, Any]) -> Optional[StatsTuple]:
    """Calculates performance statistics from a single parsed report record."""
    try:
        algorithm_name = record["algorithm"] # Keep original name for internal use
        compute_time = float(record["compute time"])
        update_entry = float(record["update entry"])
        paths = record["path info"]
        num_observers = int(record["number of observers"])

        if num_observers <= 0:
            # If 0 observers, return stats with 0/NaN for path-related metrics
            if num_observers == 0:
                 print(f"Info: Algorithm '{algorithm_name}' has 0 observers. Path statistics will be NaN/0.")
                 return (algorithm_name, compute_time, update_entry, 0.0, # Avg Failure Rate
                         float('nan'), float('nan'), float('nan'), float('nan')) # Latency stats
            else: # Should have been caught earlier if negative
                 print(f"Warning: Algorithm '{algorithm_name}' record has invalid observer count {num_observers}.")
                 return None


        latencies = []
        total_failure_rate = 0.0

        for i, path_data in enumerate(paths):
            try:
                latency = float(path_data[1])
                failure_rate = float(path_data[2])
                if not (np.isfinite(latency) and np.isfinite(failure_rate) and latency >= 0):
                     # Treat non-finite or negative latency as an error for calculation purposes
                    raise ValueError(f"Invalid latency ({latency}) or failure ({failure_rate}) value")
                latencies.append(latency)
                total_failure_rate += failure_rate
            except (IndexError, ValueError) as e:
                print(f"Warning: Invalid path data for algorithm '{algorithm_name}', path index {i} ('{path_data[0]}'). Data: {path_data[1:]}. Error: {e}. Skipping record.")
                return None # Skip entire record if any path data is bad

        if not latencies: # Should only happen if num_observers > 0 but somehow all paths failed parsing (unlikely with check above)
             print(f"Warning: No valid latency data found for algorithm '{algorithm_name}' despite {num_observers} observers reported.")
             return None


        # Calculate stats only if we have valid latency data
        avg_failure_rate = total_failure_rate / num_observers
        avg_latency = np.mean(latencies)
        percentile_50 = np.percentile(latencies, 50)
        percentile_90 = np.percentile(latencies, 90)
        percentile_99 = np.percentile(latencies, 99)

        return (
            algorithm_name, compute_time, update_entry, avg_failure_rate,
            avg_latency, percentile_50, percentile_90, percentile_99
        )
    except (KeyError, ValueError, TypeError) as e:
        algo = record.get('algorithm', 'Unknown Algorithm')
        print(f"Error calculating statistics for '{algo}': {e}. Check required keys and data types in report.")
        return None
    except Exception as e:
        algo = record.get('algorithm', 'Unknown Algorithm')
        print(f"An unexpected error occurred during statistics calculation for '{algo}': {e}")
        return None


# --- MODIFIED: Filters and Sorts records based on ALGORITHMS_TO_OUTPUT ---
def filter_and_sort_records(
    records: List[Dict[str, Any]],
    algorithms_to_output: List[str],
    algorithm_id_map: Dict[str, int],
    default_sort_id: float
) -> List[Dict[str, Any]]:
    """
    Filters records to include only those listed in algorithms_to_output,
    then sorts them according to the order in that list.
    """
    # Filter records first
    filtered_records = [
        record for record in records
        if record.get("algorithm") in algorithms_to_output
    ]

    if not filtered_records:
        print("Warning: No records matched the specified algorithms_to_output list.")
        return []

    # Create the order dictionary based ONLY on the desired output list
    order_dict = {name: index for index, name in enumerate(algorithms_to_output)}

    def sort_key(record):
        algo_name = record.get("algorithm", "")
        # Primary key: Position in algorithms_to_output (lower is earlier)
        primary_key = order_dict.get(algo_name, float('inf')) # Should always be found due to filtering
        # Secondary key: ID from ALGORITHM_ID_MAP (lower is earlier) for tie-breaking
        secondary_key = algorithm_id_map.get(algo_name, default_sort_id)
        return (primary_key, secondary_key)

    try:
        sorted_filtered_records = sorted(filtered_records, key=sort_key)
        print(f"\nFiltered and sorted {len(sorted_filtered_records)} records based on ALGORITHMS_TO_OUTPUT:")
        # Optional: Print the final order for verification
        # for i, rec in enumerate(sorted_filtered_records):
        #     algo_name = rec.get('algorithm', 'UNKNOWN')
        #     print(f"  {i+1}. {algo_name}")
        return sorted_filtered_records
    except Exception as e:
        print(f"Error during filtered record sorting: {e}. Returning filtered records unsorted.")
        return filtered_records


# Keep create_summary_report as it was (it iterates over the list passed to it)
def create_summary_report(
    target_name: str,
    # --- MODIFIED: Expects already filtered and sorted records ---
    sorted_filtered_records: List[Dict[str, Any]],
    algorithm_display_mapping: Dict[str, str],
    benchmark_algorithm: str,
    output_filename: Path
) -> None:
    """Calculates statistics for the provided records, compares against a benchmark, and writes a summary CSV."""
    print(f"\nCreating summary report for scenario '{target_name}' -> {output_filename}")

    # Ensure the output directory exists
    output_filename.parent.mkdir(parents=True, exist_ok=True)

    all_stats: Dict[str, StatsTuple] = {}

    # --- MODIFIED: Input list is already filtered and sorted ---
    # Calculate stats for the records we have
    for record in sorted_filtered_records:
        algo_name = record.get("algorithm")
        if not algo_name: continue # Should not happen if record structure is good

        # Since the list is already filtered, we just calculate stats
        # Duplicate handling was done during record gathering or should be handled by filter/sort logic
        if algo_name not in all_stats:
             stats = calculate_statistics(record)
             if stats:
                 all_stats[algo_name] = stats
             else:
                 print(f"Warning: Skipping algorithm '{algo_name}' in summary for '{target_name}' due to errors in statistics calculation.")
        # else: # This case shouldn't happen if input list is correctly prepared
            # print(f"Debug: Algo {algo_name} already has stats.")


    if not all_stats:
        print(f"Error: No valid statistics could be calculated for the filtered algorithms in scenario '{target_name}'. Summary report cannot be generated.")
        return

    # Find benchmark stats among the calculated stats
    base_stats_tuple = all_stats.get(benchmark_algorithm)
    has_benchmark = False
    if base_stats_tuple:
         # Indices in StatsTuple: 2=update, 4=avg_lat, 5=p50, 6=p90, 7=p99
         try:
             # Check if benchmark values are usable (not NaN, not zero for divisors)
             base_update_val = base_stats_tuple[2]
             base_latency_val = base_stats_tuple[4]
             base_p50_val = base_stats_tuple[5]
             base_p90_val = base_stats_tuple[6]
             base_p99_val = base_stats_tuple[7]

             # Check for NaN before division check
             if not np.isnan(base_update_val) and \
                not np.isnan(base_latency_val) and \
                not np.isnan(base_p50_val) and \
                not np.isnan(base_p90_val) and \
                not np.isnan(base_p99_val):

                 # Use 1.0 as base if actual value is 0 to avoid division by zero, relative % will be huge/inf
                 base_update_divisor = base_update_val if base_update_val != 0 else 1.0
                 base_latency_divisor = base_latency_val if base_latency_val != 0 else 1.0
                 base_p50_divisor = base_p50_val if base_p50_val != 0 else 1.0
                 base_p90_divisor = base_p90_val if base_p90_val != 0 else 1.0
                 base_p99_divisor = base_p99_val if base_p99_val != 0 else 1.0
                 has_benchmark = True
                 print(f"Using benchmark '{benchmark_algorithm}' for '{target_name}': Update={base_update_val:.2f}, Avg Latency={base_latency_val:.2f}ms")
             else:
                 print(f"Warning: Benchmark algorithm '{benchmark_algorithm}' for scenario '{target_name}' has NaN statistics. Relative values cannot be calculated.")

         except IndexError:
              print(f"Warning: Benchmark statistics tuple for '{benchmark_algorithm}' seems incomplete. Relative values cannot be calculated.")

    if not has_benchmark:
         # Ensure benchmark divisors are defined even if not used, to avoid errors later
         base_update_divisor, base_latency_divisor, base_p50_divisor, base_p90_divisor, base_p99_divisor = 1.0, 1.0, 1.0, 1.0, 1.0
         if benchmark_algorithm in all_stats:
              # Already warned about NaN above if that was the case
              pass
         else:
              print(f"Warning: Benchmark algorithm '{benchmark_algorithm}' not found among processed algorithms for scenario '{target_name}'. Relative values cannot be calculated.")


    try:
        with output_filename.open('w', encoding='utf-8', newline='') as f:
            header = [
                "Algorithm Name", "Compute Time (s)", "Update Entry (#)",
                "Update Entry (Relative %)", "Failure Rate (%)", "Avg Latency (ms)",
                "Avg Latency (Relative %)", "P50 Latency (ms)", "P50 Latency (Relative %)",
                "P90 Latency (ms)", "P90 Latency (Relative %)", "P99 Latency (ms)",
                "P99 Latency (Relative %)"
            ]
            f.write(",".join(header) + "\n")

            # Iterate through the sorted list of records again to maintain order
            for record in sorted_filtered_records:
                algorithm_name = record.get("algorithm")
                if not algorithm_name or algorithm_name not in all_stats:
                    continue # Skip if algo name is missing or stats failed

                stats = all_stats[algorithm_name]
                (algo_name_internal, compute_time, update_entry, avg_failure_rate,
                 avg_latency, p50, p90, p99) = stats

                # Use display mapping, fallback to original name
                display_name = algorithm_display_mapping.get(algo_name_internal, algo_name_internal)

                # Calculate relative values only if benchmark data is valid and usable
                if has_benchmark and base_stats_tuple: # base_stats_tuple must exist if has_benchmark is True
                    # Check for NaN in current algorithm's stats before calculating relative
                    if any(np.isnan(v) for v in [update_entry, avg_latency, p50, p90, p99]):
                         rel_update_str = rel_latency_str = rel_p50_str = rel_p90_str = rel_p99_str = "NaN Input"
                    else:
                        # Avoid division by zero using the divisors calculated earlier
                        # Calculate difference relative to the benchmark value
                        rel_update = (update_entry - base_stats_tuple[2]) / base_update_divisor if base_update_divisor != 0 else float('inf')
                        rel_latency = (avg_latency - base_stats_tuple[4]) / base_latency_divisor if base_latency_divisor != 0 else float('inf')
                        rel_p50 = (p50 - base_stats_tuple[5]) / base_p50_divisor if base_p50_divisor != 0 else float('inf')
                        rel_p90 = (p90 - base_stats_tuple[6]) / base_p90_divisor if base_p90_divisor != 0 else float('inf')
                        rel_p99 = (p99 - base_stats_tuple[7]) / base_p99_divisor if base_p99_divisor != 0 else float('inf')

                        # Format relative values, handling potential infinity
                        rel_update_str = f"{rel_update:+.2%}" if np.isfinite(rel_update) else ("+inf%" if rel_update > 0 else "-inf%")
                        rel_latency_str = f"{rel_latency:+.2%}" if np.isfinite(rel_latency) else ("+inf%" if rel_latency > 0 else "-inf%")
                        rel_p50_str = f"{rel_p50:+.2%}" if np.isfinite(rel_p50) else ("+inf%" if rel_p50 > 0 else "-inf%")
                        rel_p90_str = f"{rel_p90:+.2%}" if np.isfinite(rel_p90) else ("+inf%" if rel_p90 > 0 else "-inf%")
                        rel_p99_str = f"{rel_p99:+.2%}" if np.isfinite(rel_p99) else ("+inf%" if rel_p99 > 0 else "-inf%")
                else: # No valid benchmark
                    rel_update_str = rel_latency_str = rel_p50_str = rel_p90_str = rel_p99_str = "N/A"


                # Format absolute values, handling potential NaN from calculation (e.g., for 0 observers)
                compute_time_str = f"{compute_time:.2f}" if np.isfinite(compute_time) else "N/A"
                update_entry_str = f"{update_entry:.2f}" if np.isfinite(update_entry) else "N/A"
                avg_failure_rate_str = f"{avg_failure_rate:.4%}" if np.isfinite(avg_failure_rate) else "N/A"
                avg_latency_str = f"{avg_latency:.2f}" if np.isfinite(avg_latency) else "N/A"
                p50_str = f"{p50:.2f}" if np.isfinite(p50) else "N/A"
                p90_str = f"{p90:.2f}" if np.isfinite(p90) else "N/A"
                p99_str = f"{p99:.2f}" if np.isfinite(p99) else "N/A"


                line_data = [
                    f'"{display_name}"', compute_time_str, update_entry_str,
                    rel_update_str, avg_failure_rate_str,
                    avg_latency_str, rel_latency_str,
                    p50_str, rel_p50_str,
                    p90_str, rel_p90_str,
                    p99_str, rel_p99_str,
                ]
                f.write(",".join(line_data) + "\n")
        print(f"Successfully written summary report: {output_filename}")
    except IOError as e:
        print(f"Error writing summary file {output_filename}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while creating summary report for '{target_name}': {e}")


# Keep sanitize_filename as it was
def sanitize_filename(name: str) -> str:
    """Removes or replaces characters unsuitable for filenames."""
    # Allow alphanumeric, underscore, hyphen, parenthesis, comma
    sanitized = "".join(c if c.isalnum() or c in ['_', '-', '(', ')', ','] else '_' for c in name)
    # Replace multiple consecutive underscores with a single one
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores/spaces/hyphens
    sanitized = sanitized.strip('_ -')
    # Handle potential empty string after sanitization
    return sanitized if sanitized else "invalid_name"


# Keep generate_latency_distribution (it operates on a single record)
# --- Filename generation uses the MODIFIED template ---
def generate_latency_distribution(
    record: Dict[str, Any], algorithm_name: str, output_dir: Path,
    num_bins: int, min_upper_bound: float, upper_bound_factor: float,
    # --- MODIFIED: Takes the modified filename template ---
    filename_template: str
) -> None:
    """Generates a CSV file containing data points for a latency CDF plot."""
    try:
        paths = record.get("path info", [])
        num_observers = int(record.get("number of observers", 0))

        if num_observers == 0:
             print(f"Info: Skipping CDF for algorithm '{algorithm_name}' as it has 0 observers.")
             return
        if not paths:
             # This might happen if num_observers > 0 but path info is missing/empty
             print(f"Warning: No path data found for algorithm '{algorithm_name}' (expected {num_observers} observers). Cannot generate CDF.")
             return


        latency_data = []
        invalid_count = 0
        for i, path in enumerate(paths):
            try:
                latency = float(path[1])
                # Include only valid, non-negative, finite latencies
                if np.isfinite(latency) and latency >= 0:
                    latency_data.append(latency)
                else:
                     invalid_count += 1
            except (IndexError, ValueError):
                 invalid_count += 1 # Count parsing errors as invalid too

        if invalid_count > 0:
             print(f"Debug: Excluded {invalid_count} invalid/non-finite/negative latency values for {algorithm_name} from CDF.")


        if not latency_data:
              print(f"Info: No valid, finite, non-negative latency data available for algorithm '{algorithm_name}' after filtering. Cannot generate CDF.")
              return

        latency_array = np.array(latency_data)

        # Determine a realistic upper bound for the CDF histogram
        # Use max value unless it's extreme, then use percentile + factor
        max_latency = np.max(latency_array)
        realistic_upper_bound = max_latency * upper_bound_factor

        # If max seems reasonable (e.g., not excessively large compared to median/mean if available), use it directly?
        # Let's stick to percentile for robustness against single outliers if data is sufficient
        if len(latency_array) > 10: # Use percentile if enough data points
             p99_9 = np.percentile(latency_array, 99.9)
             # Choose the smaller of p99.9*factor or max*factor, but ensure it's at least min_upper_bound
             realistic_upper_bound = max(min_upper_bound, min(p99_9 * upper_bound_factor, max_latency * upper_bound_factor) )
        else: # Not enough data for reliable percentile, use max * factor
             realistic_upper_bound = max(min_upper_bound, max_latency * upper_bound_factor)

        # Ensure lower bound is 0 for latency CDF
        lower_bound = 0.0

        # Calculate cumulative frequency histogram
        # Ensure the range [lower_bound, realistic_upper_bound] is valid
        if realistic_upper_bound <= lower_bound:
             realistic_upper_bound = lower_bound + 1.0 # Ensure a minimal positive range if all data is at 0


        cumfreq_result = stats.cumfreq(latency_array, numbins=num_bins, defaultreallimits=(lower_bound, realistic_upper_bound))

        # Handle potential issues with cumfreq result (e.g., if all data points are identical)
        if cumfreq_result.cumcount.size == 0:
            print(f"Warning: Could not generate CDF bins for {algorithm_name}. Data might be constant or have issues.")
            return

        # Calculate x coordinates (bin upper bounds)
        x_coords = cumfreq_result.lowerlimit + np.linspace(0, cumfreq_result.binsize * cumfreq_result.cumcount.size, cumfreq_result.cumcount.size + 1)[1:]
        # Calculate y coordinates (cumulative fraction)
        y_coords = cumfreq_result.cumcount / len(latency_array)

        # Ensure the output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare filename using the template and sanitized name
        safe_algo_name = sanitize_filename(algorithm_name)
        output_filename = filename_template.format(safe_algo_name=safe_algo_name)
        output_path = output_dir / output_filename

        with output_path.open("w", encoding='utf-8', newline='') as pf:
            pf.write("Latency (ms),Cumulative Fraction\n")
            # Add (0,0) point if the first bin starts significantly after 0
            if cumfreq_result.lowerlimit >= 0 and (len(x_coords) == 0 or x_coords[0] > 1e-9):
                pf.write("0.000000,0.000000\n")

            last_y = 0.0
            # Write the calculated CDF points
            for x, y in zip(x_coords, y_coords):
                 # Ensure coordinates are valid and cumulative fraction is non-decreasing
                 # Clamp y slightly below 1.0 if needed, though cumcount/N should handle this.
                 y_val = min(y, 1.0)
                 if np.isfinite(x) and np.isfinite(y_val) and y_val >= last_y:
                     pf.write(f"{x:.6f},{y_val:.6f}\n")
                     last_y = y_val
                 # else: # Optional: Log skipped points
                     # print(f"Debug: Skipping CDF point ({x}, {y}) for {algorithm_name}")


            # Ensure the CDF reaches 1.0 if it hasn't already
            # Check if the last written point's y-value is less than 1.0
            # And if the realistic upper bound is finite.
            if last_y < (1.0 - 1e-9) and np.isfinite(realistic_upper_bound):
                 # Option 1: Add a point at the calculated upper bound with y=1.0
                 # pf.write(f"{realistic_upper_bound:.6f},1.000000\n")
                 # Option 2: Add a point slightly after the last x with y=1.0 (if last x wasn't the upper bound)
                 last_x = x_coords[-1] if len(x_coords)>0 else realistic_upper_bound
                 if np.isfinite(last_x) and last_x < realistic_upper_bound:
                      pf.write(f"{realistic_upper_bound:.6f},1.000000\n") # Use upper bound for final point
                 elif np.isfinite(last_x): # If last_x was already the upper bound, just ensure Y is 1
                      # This case might be tricky if the last bin exactly hit 1.0 already.
                      # Let's assume the loop handled the last point correctly if its x was the upper bound.
                      # If last_y was still < 1, we add the point at the upper bound.
                      pf.write(f"{realistic_upper_bound:.6f},1.000000\n")



        # print(f"Debug: Generated CDF data for '{algorithm_name}' at {output_path}")

    except Exception as e:
        print(f"An unexpected error occurred during latency CDF generation for '{algorithm_name}': {e}")
        # import traceback
        # traceback.print_exc() # For detailed debug


# =============================================================================
# Main Execution
# =============================================================================
def main():
    """Main function to orchestrate the report processing."""
    print("=" * 60)
    print("Starting Filtered Report Processing Script")
    print(f"Report Source(s): {[str(p) for p in REPORT_SOURCES]}")
    print(f"Recursive Search: {RECURSIVE_SEARCH}")
    print(f"Base Output Directory: {BASE_OUTPUT_DIRECTORY.resolve()}")
    print(f"Output Plot Data Directory: {OUTPUT_PLOT_DIRECTORY.resolve()}")
    print(f"Benchmark Algorithm: {BENCHMARK_ALGORITHM}")
    print("=" * 60)
    print("\n--- Configuration Summary ---")
    print(f"Target Scenarios: {TARGET_LIST}")
    # --- MODIFIED: Show the list of algorithms that WILL be processed ---
    print(f"Algorithms to Process and Output: {ALGORITHMS_TO_OUTPUT}")
    print(f"Generate Latency CDFs: {GENERATE_LATENCY_CDF_FILES}")
    print(f"Summary Filename Template: {SUMMARY_REPORT_FILENAME_TEMPLATE.name}")
    print(f"CDF Filename Template: {LATENCY_CDF_FILENAME_TEMPLATE}")
    print("-" * 30)

    # --- Create Base Output Directory ---
    try:
        BASE_OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
        print(f"Ensured base output directory exists: {BASE_OUTPUT_DIRECTORY}")
        if GENERATE_LATENCY_CDF_FILES:
            OUTPUT_PLOT_DIRECTORY.mkdir(parents=True, exist_ok=True)
            print(f"Ensured plot data directory exists: {OUTPUT_PLOT_DIRECTORY}")
    except OSError as e:
        print(f"Error: Could not create output directory: {e}")
        return # Cannot proceed

    # --- Process Each Target Scenario ---
    for target_name in TARGET_LIST:
        print(f"\n===== Processing Scenario: {target_name} =====")

        all_raw_records_for_target: List[Dict[str, Any]] = []

        # --- Gather Records based on Search Mode ---
        if not REPORT_SOURCES:
             print("Error: No report source directories specified.")
             break # Stop processing if no sources are listed

        if RECURSIVE_SEARCH:
            if len(REPORT_SOURCES) > 1:
                print(f"Warning: Recursive search enabled, using only the first source: '{REPORT_SOURCES[0]}'")
            base_dir = REPORT_SOURCES[0]
            all_raw_records_for_target = get_records_from_location(base_dir, target_name, recursive=True)
        else:
            for report_dir in REPORT_SOURCES:
                records_from_dir = get_records_from_location(report_dir, target_name, recursive=False)
                # Extend list, duplicate algorithm names will be handled by get_records or later processing
                all_raw_records_for_target.extend(records_from_dir)

        # --- Filter and Sort Collected Records ---
        if not all_raw_records_for_target:
            print(f"No raw report records found for scenario '{target_name}' in the specified locations. Skipping.")
            continue

        print(f"Found a total of {len(all_raw_records_for_target)} raw report records for scenario '{target_name}'.")

        # --- MODIFIED: Use the filter and sort function ---
        processed_records = filter_and_sort_records(
            all_raw_records_for_target,
            ALGORITHMS_TO_OUTPUT,
            ALGORITHM_ID_MAP,
            DEFAULT_SORT_ID
        )

        if not processed_records:
            print(f"No records matched the specified algorithms for scenario '{target_name}'. Skipping summary/CDF generation.")
            continue

        # --- Create Summary Report for Filtered/Sorted Records ---
        # Define the specific output filename using the MODIFIED template
        try:
             # Sanitize target_name for the filename formatting just in case
             safe_target_name = sanitize_filename(target_name)
             summary_filename = Path(str(SUMMARY_REPORT_FILENAME_TEMPLATE).format(target_name=safe_target_name))
        except Exception as e:
             print(f"Error formatting summary filename for target '{target_name}': {e}")
             summary_filename = BASE_OUTPUT_DIRECTORY / f"result-summary_{sanitize_filename(target_name)}_fallback.csv"
             print(f"Using fallback filename: {summary_filename}")


        create_summary_report(
            target_name,
            processed_records, # Pass the filtered and sorted list
            ALGORITHM_DISPLAY_MAPPING,
            BENCHMARK_ALGORITHM,
            summary_filename
        )

        # --- Generate CDF files for Filtered/Sorted Records if enabled ---
        if GENERATE_LATENCY_CDF_FILES:
            print(f"\nGenerating latency distribution CDF files for '{target_name}'...")
            cdf_count = 0
            # --- SIMPLIFIED: Iterate directly over the filtered/sorted list ---
            for record in processed_records:
                algo_name = record.get("algorithm")
                if algo_name: # Should always have algo_name here
                    generate_latency_distribution(
                        record,
                        algo_name,
                        OUTPUT_PLOT_DIRECTORY,
                        LATENCY_CDF_NUM_BINS,
                        LATENCY_CDF_MIN_UPPER_BOUND,
                        LATENCY_CDF_UPPER_BOUND_FACTOR,
                        # Pass the MODIFIED CDF filename template
                        LATENCY_CDF_FILENAME_TEMPLATE
                    )
                    cdf_count += 1
                # No need for duplicate check here, list is already filtered and unique by algo

            print(f"Generated {cdf_count} CDF data files for '{target_name}' in '{OUTPUT_PLOT_DIRECTORY}'.")

        print(f"===== Finished Processing Scenario: {target_name} =====")

    print("\n" + "=" * 60)
    print("Filtered Report Processing Script Finished")
    print("=" * 60)


if __name__ == "__main__":
    main()