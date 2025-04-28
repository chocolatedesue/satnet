# -*- coding: utf-8 -*-
"""
Processes algorithm performance report files from specified directories
(optionally recursively) to generate a summary CSV and latency distribution data.
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
# If RECURSIVE_SEARCH is True, this should typically contain ONE base directory.
# If RECURSIVE_SEARCH is False, reports will be searched in each listed directory (non-recursively).
REPORT_SOURCES: List[Path] = [
    Path("output"),
    # Path("output/startlink-v2-group5-Jan"), # Example: Add more directories if RECURSIVE_SEARCH = False
    # Path("archive/old_reports")             # Example
]
RECURSIVE_SEARCH: bool = True # Set to True to search recursively within the directories listed above

# --- Output Directories and Files ---
# Base directory for all generated output files
BASE_OUTPUT_DIRECTORY = Path("processed_results")
OUTPUT_PLOT_DIRECTORY = BASE_OUTPUT_DIRECTORY / "plot_data"
REPORT_FILE_SUFFIX = ".txt"
REPORT_FILE_PREFIX = "report"
# Ensure summary report goes into the base output directory
SUMMARY_REPORT_FILENAME_TEMPLATE = BASE_OUTPUT_DIRECTORY / "summary [{target_name}].csv"
# CDF filename template (will be placed inside OUTPUT_PLOT_DIRECTORY)
LATENCY_CDF_FILENAME_TEMPLATE = "{safe_algo_name}_latency_cdf.csv"

# --- Target Scenarios ---
# List of scenario names to process (matches 'name' field in report files)
TARGET_LIST = ["startlink-v2-group5-Apr", "startlink-v2-group5-Jan", "startlink-v2-group4-Jan", "startlink-v2-group4-April"]

# --- Algorithm Identification and Mapping ---
# (Keep ALGORITHM_ID_MAP, DEFAULT_SORT_ID, ALGORITHM_DISPLAY_MAPPING as before)
ALGORITHM_ID_MAP: Dict[str, int] = {
    "Oracle": 0, "Base": 1000, "DijkstraBase": 1001, "CoinFlipBase": 2001,
    "CoinFlipPred": 2003, "DijkstraPred": 3003, "MinHopCount": 5001,
    "MinHopCountPred": 5003, "DomainHeuristic": 5100, "DisCoRouteBase": 9000,
    "LBP": 9001, "DiffDomainBridge_10_3": 9100, "DiffDomainBridge_10_1": 9101,
    "DiffDomainBridge_8_3": 9102, "LocalDomainBridge_10_3": 9200,
    "LocalDomainBridge_10_1": 9201,
}
DEFAULT_SORT_ID = float('inf')

ALGORITHM_DISPLAY_MAPPING: Dict[str, str] = {
    "DijkstraPred": "GSPR", "MinHopCount": "MinHopCount", "MinHopCountPred": "MHR",
    "DisCoRouteBase": "DisCoRoute", "LBP": "LBP", "DiffDomainBridge_10_3": "DomainBridge",
    "DiffDomainBridge_10_1": "DomainBridge_1", "DiffDomainBridge_8_3": "DomainBridge(8_3)",
    "LocalDomainBridge_10_3": "LocalDM", "LocalDomainBridge_10_1": "LocalDM_1",
    "DomainHeuristic": "DomainHeuristic", "CoinFlipPred": "CoinFlipPred",
    "DijkstraBase": "DijkstraBase", "Base": "Base", "Oracle": "Oracle",
}

# --- Reporting and Analysis Parameters ---
# (Keep ALGORITHM_OUTPUT_ORDER, BENCHMARK_ALGORITHM, etc. as before)
ALGORITHM_OUTPUT_ORDER: List[str] = [
    "DijkstraPred", "MinHopCount", "MinHopCountPred", "DisCoRouteBase", "LBP",
    "DiffDomainBridge_10_3", "DiffDomainBridge_10_1", "DiffDomainBridge_8_3",
    "LocalDomainBridge_10_3", "LocalDomainBridge_10_1", "DomainHeuristic",
    "CoinFlipPred", "DijkstraBase", "Base", "Oracle",
]
BENCHMARK_ALGORITHM: str = "DijkstraPred"
LATENCY_CDF_NUM_BINS: int = 200
LATENCY_CDF_MIN_UPPER_BOUND: float = 300.0
LATENCY_CDF_UPPER_BOUND_FACTOR: float = 1.2
GENERATE_LATENCY_CDF_FILES: bool = True

# =============================================================================
# Core Logic Functions
# =============================================================================

# Keep read_report_file as it was in the provided good version
# It correctly parses a single file.
def read_report_file(file_path: Path, target_name: str) -> Optional[Dict[str, Any]]:
    """
    Reads and parses a single report file, handling flexible metadata keys
    and the specific path data format.

    Args:
        file_path: Path object for the report file.
        target_name: The target scenario name to match against the 'name' field.

    Returns:
        A dictionary containing the parsed report data, or None if the file
        doesn't match the target name, is unreadable, or has format errors.
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
                    print(f"Warning: Unexpected end of file in {file_path} before finding 'number of observers' or path data.")
                    return None

                stripped_line = line.strip()

                if stripped_line == "---" or stripped_line.startswith("route path"):
                    if "number of observers" not in found_keys:
                        print(f"Warning: Reached separator/path data in {file_path} at line {line_num} before finding 'number of observers'.")
                        return None
                    else:
                        if stripped_line.startswith("route path"):
                            current_line_for_path = line
                        else:
                            current_line_for_path = None # Discard "---" or empty line
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
                elif not stripped_line:
                    continue # Allow empty lines
                elif "number of observers" in found_keys:
                     # Found non-empty line without ':' after num_observers - assume separator/path start
                    current_line_for_path = line
                    break # Exit metadata reading loop
                # else: # Line without ':' before finding num_observers - ignore or warn? Let's ignore for now.
                #     print(f"Warning: Skipping line {line_num} without colon in metadata: '{stripped_line}' in {file_path}")


            # --- Phase 2: Post-Metadata Validation ---
            if num_observers == -1:
                print(f"Warning: 'number of observers' key not found or processed in {file_path}.")
                return None

            missing_keys = required_keys - found_keys
            if missing_keys:
                print(f"Warning: Missing required metadata keys in {file_path}: {missing_keys}")
                # Allow processing even with missing non-essential keys? For now, let's require them.
                return None

            if report_data.get("name") != target_name:
                # print(f"Debug: Skipping {file_path.name}, name '{report_data.get('name')}' != target '{target_name}'")
                return None # Silently skip non-matching targets

            # --- Phase 3: Read Path Data ---
            route_paths: List[List[str]] = []
            observers_read = 0
            current_line = current_line_for_path if current_line_for_path is not None else f.readline()

            while observers_read < num_observers:
                # Find start of next path block
                path_name = None
                while current_line:
                    stripped_line = current_line.strip()
                    if stripped_line.startswith("route path"):
                        path_name = stripped_line
                        break
                    elif not stripped_line or stripped_line == "---":
                        current_line = f.readline() # Skip empty/separator lines
                        continue
                    else:
                        print(f"Warning: Unexpected non-empty line before 'route path' for observer {observers_read + 1} in {file_path}: '{stripped_line}'")
                        # Option: skip line or abort? Let's skip the line and keep searching.
                        current_line = f.readline()
                        # return None # Stricter: abort if unexpected content found
                else: # current_line is empty (EOF)
                    if observers_read < num_observers:
                         print(f"Warning: Unexpected end of file in {file_path} while looking for 'route path' for observer {observers_read + 1} (expected {num_observers}). Found {observers_read}.")
                    # Return None if data is incomplete
                    return None

                # Found "route path...", read latency and failure
                latency_line = f.readline()
                if not latency_line:
                    print(f"Warning: Unexpected EOF after reading '{path_name}' in {file_path}. Missing latency/failure.")
                    return None

                failure_line = f.readline()
                if not failure_line:
                    print(f"Warning: Unexpected EOF after reading latency line for '{path_name}' in {file_path}. Missing failure rate.")
                    return None

                # Parse latency and failure rate
                try:
                    if ':' not in latency_line or ':' not in failure_line:
                         raise ValueError("Missing colon in latency/failure line")
                    latency_str = latency_line.split(":", 1)[1].strip()
                    failure_str = failure_line.split(":", 1)[1].strip()
                    # Basic validation (will be converted to float later)
                    float(latency_str)
                    float(failure_str)
                except (IndexError, ValueError) as e:
                    print(f"Warning: Error parsing latency/failure value for '{path_name}' in {file_path}. Error: {e}. Lines: '{latency_line.strip()}', '{failure_line.strip()}'")
                    return None

                route_paths.append([path_name, latency_str, failure_str])
                observers_read += 1

                # Read next line for the next loop iteration
                current_line = f.readline()

            # --- Final Check ---
            if len(route_paths) != num_observers:
                print(f"Warning: Mismatch between expected observers ({num_observers}) and successfully read paths ({len(route_paths)}) in {file_path}.")
                return None # Data integrity issue

            report_data["path info"] = route_paths
            # print(f"Debug: Successfully parsed {file_path.name} for target '{target_name}'")
            return report_data

    except FileNotFoundError:
        print(f"Error: Report file not found: {file_path}")
        return None
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading {file_path}: {e}")
        # import traceback
        # traceback.print_exc() # Uncomment for detailed debug trace
        return None

# --- MODIFIED get_records function ---
def get_records_from_location(directory: Path, target_name: str, recursive: bool) -> List[Dict[str, Any]]:
    """
    Scans a directory (optionally recursively) for report files
    matching the target scenario name and parses them.

    Args:
        directory: The Path object for the directory to scan.
        target_name: The target scenario name to match.
        recursive: If True, search recursively in subdirectories.

    Returns:
        A list of dictionaries, where each dictionary represents a parsed report.
    """
    records = []
    if not directory.is_dir():
        print(f"Warning: Source directory '{directory}' not found or is not a directory. Skipping.")
        return []

    search_mode = "recursively" if recursive else "non-recursively"
    print(f"Scanning directory '{directory}' {search_mode} for reports matching scenario '{target_name}'...")

    # Define the pattern for report files
    pattern = f"{REPORT_FILE_PREFIX}*{REPORT_FILE_SUFFIX}"

    # Choose the appropriate glob method
    if recursive:
        # Use rglob for recursive search
        files_to_check = directory.rglob(pattern)
    else:
        # Use glob for non-recursive search in the current directory
        files_to_check = directory.glob(pattern)

    # Sort files for consistent processing order (optional, but good practice)
    # Convert generator to list for sorting. Can consume memory for very large sets.
    sorted_files = sorted([f for f in files_to_check if f.is_file()])

    processed_files_count = 0
    matched_files_count = 0

    for file_path in sorted_files:
        processed_files_count += 1
        # print(f"Debug: Checking file: {file_path}") # Uncomment for verbose debugging
        report_data = read_report_file(file_path, target_name) # Use the robust reader
        if report_data:
            # Check for duplicates based on algorithm name within the same target?
            # For now, assume each file per target is unique or overwriting is intended later.
            records.append(report_data)
            matched_files_count += 1
        # read_report_file already prints warnings for parsing errors or non-matching target names

    print(f"Scan of '{directory}' complete. Processed {processed_files_count} potential report files, "
          f"successfully parsed {matched_files_count} matching reports for scenario '{target_name}'.")
    return records


# Keep calculate_statistics, create_summary_report, sanitize_filename,
# generate_latency_distribution, and sort_records functions as they were.
# Their logic depends on the structure of the parsed record (dict) and config,
# which remain compatible. Make sure calculate_statistics returns Optional[StatsTuple].

StatsTuple = Tuple[str, float, float, float, float, float, float, float]

def calculate_statistics(record: Dict[str, Any]) -> Optional[StatsTuple]:
    """Calculates performance statistics from a single parsed report record."""
    try:
        algorithm_name = record["algorithm"] # Keep original name for internal use
        compute_time = float(record["compute time"])
        update_entry = float(record["update entry"])
        paths = record["path info"] # This structure is maintained by the new reader
        num_observers = int(record["number of observers"]) # Already validated in read_report_file

        if num_observers <= 0:
            print(f"Warning: Algorithm '{algorithm_name}' record has {num_observers} observers. Cannot calculate statistics.")
            return None

        latencies = []
        total_failure_rate = 0.0

        for i, path_data in enumerate(paths):
            try:
                # path_data[0] is the "route path [...]" string, not used here
                latency = float(path_data[1])
                failure_rate = float(path_data[2])
                if not (np.isfinite(latency) and np.isfinite(failure_rate)):
                    raise ValueError("Non-finite value detected")
                latencies.append(latency)
                total_failure_rate += failure_rate
            except (IndexError, ValueError) as e:
                print(f"Warning: Invalid path data for algorithm '{algorithm_name}', path '{path_data[0]}'. Data: {path_data}. Error: {e}. Skipping record.")
                return None # Skip entire record if any path data is bad

        if not latencies: # Should not happen if num_observers > 0 and no errors above
            print(f"Warning: No valid latency data found for algorithm '{algorithm_name}'.")
            return None

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
        print(f"Error calculating statistics for '{algo}': {e}. Check required keys exist in report data.")
        return None
    except Exception as e:
        algo = record.get('algorithm', 'Unknown Algorithm')
        print(f"An unexpected error occurred during statistics calculation for '{algo}': {e}")
        return None


def create_summary_report(
    target_name: str, records: List[Dict[str, Any]],
    algorithm_display_mapping: Dict[str, str], benchmark_algorithm: str, output_filename: Path
) -> None:
    """Calculates statistics for all records, compares against a benchmark, and writes a summary CSV file."""
    print(f"\nCreating summary report for scenario '{target_name}' -> {output_filename}")

    # Ensure the output directory exists
    output_filename.parent.mkdir(parents=True, exist_ok=True)

    all_stats: Dict[str, StatsTuple] = {}
    valid_algo_names_in_order: List[str] = [] # To preserve sort order later

    # Use a set to track algorithms already processed for this target to handle potential duplicates across files/dirs
    processed_algos = set()

    for record in records: # Assumes records are already sorted if desired
        algo_name = record.get("algorithm")
        if not algo_name: continue # Should have been caught earlier

        if algo_name in processed_algos:
             # This might happen if the same report (algo+target) exists in multiple scanned locations.
             # Decide on strategy: use first, use last, error out, or try to merge?
             # Using the first one encountered (based on sorted_records order).
             print(f"Warning: Duplicate record found for algorithm '{algo_name}' in scenario '{target_name}'. Using the first instance found.")
             continue

        stats = calculate_statistics(record)
        if stats:
            all_stats[algo_name] = stats
            valid_algo_names_in_order.append(algo_name)
            processed_algos.add(algo_name)
        else:
            print(f"Warning: Skipping algorithm '{algo_name}' in summary for '{target_name}' due to errors in statistics calculation.")

    if not all_stats:
        print(f"Error: No valid statistics could be calculated for scenario '{target_name}'. Summary report cannot be generated.")
        return

    base_stats_tuple = all_stats.get(benchmark_algorithm)
    if not base_stats_tuple:
        print(f"Warning: Benchmark algorithm '{benchmark_algorithm}' not found or had errors for scenario '{target_name}'. Relative values cannot be calculated.")
        # Define defaults or handle absence of relative values
        base_update, base_latency, base_p50, base_p90, base_p99 = 1.0, 1.0, 1.0, 1.0, 1.0
        has_benchmark = False
    else:
        # Indices in StatsTuple: 2=update, 4=avg_lat, 5=p50, 6=p90, 7=p99
        base_update = base_stats_tuple[2] if base_stats_tuple[2] != 0 else 1.0
        base_latency = base_stats_tuple[4] if base_stats_tuple[4] != 0 else 1.0
        base_p50 = base_stats_tuple[5] if base_stats_tuple[5] != 0 else 1.0
        base_p90 = base_stats_tuple[6] if base_stats_tuple[6] != 0 else 1.0
        base_p99 = base_stats_tuple[7] if base_stats_tuple[7] != 0 else 1.0
        print(f"Using benchmark '{benchmark_algorithm}' for '{target_name}': Update={base_stats_tuple[2]:.2f}, Avg Latency={base_stats_tuple[4]:.2f}ms")
        has_benchmark = True

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

            # Iterate using the order established by sort_records (passed via valid_algo_names_in_order)
            for algorithm_name in valid_algo_names_in_order:
                stats = all_stats[algorithm_name]
                (algo_name_internal, compute_time, update_entry, avg_failure_rate,
                 avg_latency, p50, p90, p99) = stats
                display_name = algorithm_display_mapping.get(algo_name_internal, algo_name_internal)

                # Calculate relative values only if benchmark data is valid
                if has_benchmark:
                    # Avoid division by zero if base stat was 0; relative change becomes infinite/undefined. Show N/A.
                    rel_update = (update_entry - base_stats_tuple[2]) / base_update if base_update != 0 else float('nan')
                    rel_latency = (avg_latency - base_stats_tuple[4]) / base_latency if base_latency != 0 else float('nan')
                    rel_p50 = (p50 - base_stats_tuple[5]) / base_p50 if base_p50 != 0 else float('nan')
                    rel_p90 = (p90 - base_stats_tuple[6]) / base_p90 if base_p90 != 0 else float('nan')
                    rel_p99 = (p99 - base_stats_tuple[7]) / base_p99 if base_p99 != 0 else float('nan')

                    rel_update_str = f"{rel_update:+.2%}" if not np.isnan(rel_update) else "N/A"
                    rel_latency_str = f"{rel_latency:+.2%}" if not np.isnan(rel_latency) else "N/A"
                    rel_p50_str = f"{rel_p50:+.2%}" if not np.isnan(rel_p50) else "N/A"
                    rel_p90_str = f"{rel_p90:+.2%}" if not np.isnan(rel_p90) else "N/A"
                    rel_p99_str = f"{rel_p99:+.2%}" if not np.isnan(rel_p99) else "N/A"
                else:
                    rel_update_str = rel_latency_str = rel_p50_str = rel_p90_str = rel_p99_str = "N/A"


                line_data = [
                    f'"{display_name}"', f"{compute_time:.2f}", f"{update_entry:.2f}",
                    rel_update_str, f"{avg_failure_rate:.4%}",
                    f"{avg_latency:.2f}", rel_latency_str,
                    f"{p50:.2f}", rel_p50_str,
                    f"{p90:.2f}", rel_p90_str,
                    f"{p99:.2f}", rel_p99_str,
                ]
                f.write(",".join(line_data) + "\n")
        print(f"Successfully written summary report: {output_filename}")
    except IOError as e:
        print(f"Error writing summary file {output_filename}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while creating summary report for '{target_name}': {e}")


def sanitize_filename(name: str) -> str:
    """Removes or replaces characters unsuitable for filenames."""
    # Keep original implementation
    sanitized = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in name)
    # Replace multiple consecutive underscores with a single one
    sanitized = '_'.join(filter(None, sanitized.split('_')))
    # Remove leading/trailing underscores/spaces
    return sanitized.strip('_ ')


def generate_latency_distribution(
    record: Dict[str, Any], algorithm_name: str, output_dir: Path,
    num_bins: int, min_upper_bound: float, upper_bound_factor: float, filename_template: str
) -> None:
    """Generates a CSV file containing data points for a latency CDF plot."""
    # Keep original implementation, but ensure output_dir exists
    try:
        paths = record.get("path info", [])
        if not paths:
            print(f"Info: No path data found for algorithm '{algorithm_name}' to generate CDF.")
            return

        latency_data = []
        for i, path in enumerate(paths):
            try:
                latency = float(path[1])
                # Include only valid, non-negative latencies
                if np.isfinite(latency) and latency >= 0:
                    latency_data.append(latency)
                # else: # Optional: Warn about invalid/negative values being excluded from CDF
                #    print(f"Debug: Excluding invalid latency value {path[1]} for {algorithm_name} from CDF.")
            except (IndexError, ValueError):
                 # Ignore parsing errors here, should have been caught earlier if critical
                 continue

        if not latency_data:
             print(f"Info: No valid latency data available for algorithm '{algorithm_name}' to generate CDF.")
             return

        latency_array = np.array(latency_data)

        # Determine a realistic upper bound for the CDF histogram
        if len(latency_array) > 10: # Need enough points for percentiles to be meaningful
            # Use a high percentile to avoid outliers overly stretching the x-axis
            p99_9 = np.percentile(latency_array, 99.9)
            # Ensure the upper bound is at least min_upper_bound
            realistic_upper_bound = max(min_upper_bound, p99_9 * upper_bound_factor)
        elif latency_array.size > 0: # Handle cases with few data points
             realistic_upper_bound = max(min_upper_bound, np.max(latency_array) * upper_bound_factor)
        else: # Should be caught by 'if not latency_data', but belt-and-suspenders
             realistic_upper_bound = min_upper_bound


        # Calculate cumulative frequency histogram
        cumfreq_result = stats.cumfreq(latency_array, numbins=num_bins, defaultreallimits=(0, realistic_upper_bound))
        # Calculate x coordinates (bin upper bounds)
        x_coords = cumfreq_result.lowerlimit + np.linspace(0, cumfreq_result.binsize * cumfreq_result.cumcount.size, cumfreq_result.cumcount.size + 1)[1:]
        # Calculate y coordinates (cumulative fraction)
        y_coords = cumfreq_result.cumcount / len(latency_array)

        # Ensure the output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare filename
        safe_algo_name = sanitize_filename(algorithm_name)
        output_filename = filename_template.format(safe_algo_name=safe_algo_name)
        output_path = output_dir / output_filename

        with output_path.open("w", encoding='utf-8', newline='') as pf:
            pf.write("Latency (ms),Cumulative Fraction\n")
            # Add (0,0) point if data starts above 0
            if cumfreq_result.lowerlimit >= 0 and (len(x_coords) == 0 or x_coords[0] > 1e-9): # Check if first bin starts significantly after 0
                pf.write("0.000000,0.000000\n")

            last_y = 0.0
            for x, y in zip(x_coords, y_coords):
                 # Ensure coordinates are valid and cumulative fraction is non-decreasing
                if np.isfinite(x) and np.isfinite(y) and y >= last_y:
                    pf.write(f"{x:.6f},{y:.6f}\n")
                    last_y = y
            # Optional: Add a final point at the upper limit with y=1.0?
            # if last_y < 1.0 and np.isfinite(realistic_upper_bound):
            #    pf.write(f"{realistic_upper_bound:.6f},1.000000\n")

        # print(f"Debug: Generated CDF data for '{algorithm_name}' at {output_path}")

    except Exception as e:
        print(f"An unexpected error occurred during latency CDF generation for '{algorithm_name}': {e}")
        # import traceback
        # traceback.print_exc() # For detailed debug


def sort_records(records: List[Dict[str, Any]], algorithm_id_map: Dict[str, int], output_order: List[str]) -> List[Dict[str, Any]]:
    """Sorts the records based on the predefined output order and ID fallback."""
    # Keep original implementation
    order_dict = {name: index for index, name in enumerate(output_order)}
    fallback_order_index = len(output_order) # For algos not in output_order

    def sort_key(record):
        algo_name = record.get("algorithm", "")
        # Primary key: Position in ALGORITHM_OUTPUT_ORDER (lower is earlier)
        primary_key = order_dict.get(algo_name, fallback_order_index)
        # Secondary key: ID from ALGORITHM_ID_MAP (lower is earlier) for tie-breaking or unlisted algos
        secondary_key = algorithm_id_map.get(algo_name, DEFAULT_SORT_ID)
        return (primary_key, secondary_key)

    try:
        sorted_records = sorted(records, key=sort_key)
        print("\nRecords sorted based on ALGORITHM_OUTPUT_ORDER and ALGORITHM_ID_MAP.")
        # Optional: Print the final sorted order for verification
        # print("Final processing order of algorithms for this target:")
        # for i, rec in enumerate(sorted_records):
        #     algo_name = rec.get('algorithm', 'UNKNOWN')
        #     display_name = ALGORITHM_DISPLAY_MAPPING.get(algo_name, algo_name)
        #     print(f"  {i+1}. {algo_name} (Display: {display_name})")
        return sorted_records
    except Exception as e:
        print(f"Error during record sorting: {e}. Returning records in the order they were found.")
        return records


# =============================================================================
# Main Execution
# =============================================================================
def main():
    """Main function to orchestrate the report processing."""
    print("=" * 60)
    print("Starting Report Processing Script")
    print(f"Report Source(s): {[str(p) for p in REPORT_SOURCES]}")
    print(f"Recursive Search: {RECURSIVE_SEARCH}")
    print(f"Base Output Directory: {BASE_OUTPUT_DIRECTORY.resolve()}")
    print(f"Output Plot Data Directory: {OUTPUT_PLOT_DIRECTORY.resolve()}")
    print(f"Benchmark Algorithm: {BENCHMARK_ALGORITHM}")
    print("=" * 60)
    print("\n--- Configuration Summary ---")
    print(f"Target Scenarios: {TARGET_LIST}")
    print(f"Algorithm Output Order: {ALGORITHM_OUTPUT_ORDER}") # Shows desired final order in summary
    print(f"Generate Latency CDFs: {GENERATE_LATENCY_CDF_FILES}")
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
        return # Cannot proceed without output directory

    # --- Process Each Target Scenario ---
    for target_name in TARGET_LIST:
        print(f"\n===== Processing Scenario: {target_name} =====")

        all_records_for_target: List[Dict[str, Any]] = []

        # --- Gather Records based on Search Mode ---
        if RECURSIVE_SEARCH:
            if len(REPORT_SOURCES) > 1:
                print("Warning: Recursive search enabled, but multiple source directories provided. "
                      f"Searching recursively starting from the first source: '{REPORT_SOURCES[0]}'")
            if not REPORT_SOURCES:
                 print("Error: Recursive search enabled, but no report source directory specified.")
                 continue # Skip to next target
            base_dir = REPORT_SOURCES[0]
            all_records_for_target = get_records_from_location(base_dir, target_name, recursive=True)
        else:
            # Non-recursive: iterate through all specified source directories
            if not REPORT_SOURCES:
                 print("Error: No report source directories specified.")
                 break # Stop processing if no sources are listed
            for report_dir in REPORT_SOURCES:
                records_from_dir = get_records_from_location(report_dir, target_name, recursive=False)
                # Simple append. Consider merging/deduplication if needed based on file path or content hash?
                # Current create_summary_report handles deduplication by algorithm name *after* collection.
                all_records_for_target.extend(records_from_dir)

        # --- Process Collected Records for the Target ---
        if not all_records_for_target:
            print(f"No matching reports found or parsed for scenario '{target_name}' in the specified locations. Skipping.")
            continue

        print(f"Found a total of {len(all_records_for_target)} report records for scenario '{target_name}'.")

        # Sort the collected records according to the desired output order
        sorted_records = sort_records(all_records_for_target, ALGORITHM_ID_MAP, ALGORITHM_OUTPUT_ORDER)

        # Define the specific output filename for this target's summary
        # SUMMARY_REPORT_FILENAME_TEMPLATE is now a Path object including the base dir
        summary_filename = Path(str(SUMMARY_REPORT_FILENAME_TEMPLATE).format(target_name=target_name))

        # Create the summary report (function now handles directory creation)
        create_summary_report(target_name, sorted_records, ALGORITHM_DISPLAY_MAPPING, BENCHMARK_ALGORITHM, summary_filename)

        # Generate CDF files if enabled
        if GENERATE_LATENCY_CDF_FILES:
            print(f"\nGenerating latency distribution CDF files for '{target_name}'...")
            cdf_count = 0
            # Use a set to track algorithms for which CDF has been generated for this target
            # Handles cases where the same algo might appear in sorted_records (if deduplication before sort failed)
            generated_cdf_for_algo = set()
            for record in sorted_records:
                algo_name = record.get("algorithm")
                if algo_name and algo_name not in generated_cdf_for_algo:
                     generate_latency_distribution(
                        record, algo_name, OUTPUT_PLOT_DIRECTORY, LATENCY_CDF_NUM_BINS,
                        LATENCY_CDF_MIN_UPPER_BOUND, LATENCY_CDF_UPPER_BOUND_FACTOR, LATENCY_CDF_FILENAME_TEMPLATE
                    )
                     cdf_count += 1
                     generated_cdf_for_algo.add(algo_name)
                elif algo_name in generated_cdf_for_algo:
                    # This shouldn't happen if create_summary_report deduplicates correctly before sorting,
                    # but good to be safe.
                    # print(f"Debug: Skipping duplicate CDF generation for {algo_name}")
                    pass


            print(f"Generated {cdf_count} CDF data files for '{target_name}' in '{OUTPUT_PLOT_DIRECTORY}'.")

        print(f"===== Finished Processing Scenario: {target_name} =====")

    print("\n" + "=" * 60)
    print("Report Processing Script Finished")
    print("=" * 60)


if __name__ == "__main__":
    main()