# -*- coding: utf-8 -*-
"""
Processes algorithm performance report files to generate a summary CSV
and latency distribution data for plotting.
"""

import os
from pathlib import Path # Use pathlib for better path handling
from typing import Dict, List, Tuple, Any, Optional # Optional is cleaner than | None for hints
import numpy as np
from scipy import stats
import re # Import re for potentially more robust parsing if needed, though split might suffice

# =============================================================================
# Configuration Section
# (Keep the configuration section as defined in the previous good version)
# =============================================================================
# --- Input/Output Directories and Files ---
REPORT_DIRECTORY = Path("output")
OUTPUT_PLOT_DIRECTORY = REPORT_DIRECTORY / "plot_data"
REPORT_FILE_SUFFIX = ".txt"
REPORT_FILE_PREFIX = "report"
SUMMARY_REPORT_FILENAME_TEMPLATE = "summary [{target_name}].csv"
LATENCY_CDF_FILENAME_TEMPLATE = "{safe_algo_name}_latency_cdf.csv"

# --- Target Scenarios ---
TARGET_LIST = ["startlink-v2-group5-Apr"]

# --- Algorithm Identification and Mapping ---
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
    "DijkstraPred": "DT-DVTR", "MinHopCount": "MinHopCount", "MinHopCountPred": "FSA-LA",
    "DisCoRouteBase": "DisCoRoute", "LBP": "LBP", "DiffDomainBridge_10_3": "DomainBridge",
    "DiffDomainBridge_10_1": "DomainBridge_1", "DiffDomainBridge_8_3": "DomainBridge(8_3)",
    "LocalDomainBridge_10_3": "LocalDM", "LocalDomainBridge_10_1": "LocalDM_1",
    "DomainHeuristic": "DomainHeuristic", "CoinFlipPred": "CoinFlipPred",
    "DijkstraBase": "DijkstraBase", "Base": "Base", "Oracle": "Oracle",
}

# --- Reporting and Analysis Parameters ---
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
            # Read lines until we find 'number of observers' or hit the path section/EOF
            line_num = 0
            while True:
                line = f.readline()
                line_num += 1
                if not line:  # End of file before finding observer count or path data
                    print(f"Warning: Unexpected end of file in {file_path} before finding 'number of observers' or path data.")
                    return None
                
                stripped_line = line.strip()

                # Stop metadata reading if we hit common separators or path start indicator
                if stripped_line == "---" or stripped_line.startswith("route path"):
                    # We hit the separator/path data before finding num_observers? Problem.
                    if "number of observers" not in found_keys:
                         print(f"Warning: Reached separator/path data in {file_path} at line {line_num} before finding 'number of observers'.")
                         return None
                    else:
                        # Found num_observers, now process the line we just read
                        # If it was "route path...", put it back conceptually for Phase 2
                        # If it was "---" or empty, discard and move to Phase 2
                        if stripped_line.startswith("route path"):
                             current_line_for_path = line # Keep this line for Phase 2
                        else:
                             current_line_for_path = None
                        break # Exit metadata reading loop

                if ':' in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    report_data[key] = value  # Store all metadata keys found
                    found_keys.add(key)

                    if key == "number of observers":
                        try:
                            num_observers = int(value)
                            if num_observers < 0:
                                raise ValueError("Number of observers cannot be negative")
                            # Found it, keep reading metadata until separator/path/EOF
                        except ValueError:
                            print(f"Warning: Invalid 'number of observers' value '{value}' in {file_path} at line {line_num}.")
                            return None
                # Allow empty lines within the metadata section
                elif not stripped_line:
                     continue
                # Found a line without ':' after potentially finding num_observers
                # This might be the separator or start of path data
                elif "number of observers" in found_keys:
                     current_line_for_path = line # Keep this line for Phase 2
                     break # Exit metadata reading loop


            # --- Phase 2: Post-Metadata Validation ---
            if num_observers == -1: # Should be caught earlier, but double-check
                print(f"Warning: 'number of observers' key not found or processed in {file_path}.")
                return None

            # Check if all *required* keys were found
            missing_keys = required_keys - found_keys
            if missing_keys:
                print(f"Warning: Missing required metadata keys in {file_path}: {missing_keys}")
                return None

            # Check if the scenario name matches *after* reading metadata
            if report_data.get("name") != target_name:
                # print(f"Debug: Skipping {file_path.name}, name '{report_data.get('name')}' != target '{target_name}'")
                return None # Not the target scenario, skip silently

            # --- Phase 3: Read Path Data ---
            route_paths: List[List[str]] = []
            observers_read = 0

            # Use the line potentially read at the end of Phase 1, or read a new one
            current_line = current_line_for_path if current_line_for_path is not None else f.readline()

            while observers_read < num_observers:
                 # Find the start of the next path block ("route path [...]")
                 while current_line:
                     stripped_line = current_line.strip()
                     if stripped_line.startswith("route path"):
                         path_name = stripped_line # Use the whole line as identifier
                         break # Found the start of the block
                     # Skip empty lines or unexpected separators between path blocks
                     elif not stripped_line or stripped_line == "---":
                         current_line = f.readline()
                         continue
                     else:
                         print(f"Warning: Unexpected non-empty line before 'route path' for observer {observers_read + 1} in {file_path}: '{stripped_line}'")
                         # Decide how to handle: skip line or abort? Let's try skipping.
                         # return None # Stricter: abort
                         current_line = f.readline() # Skip and continue searching
                 else: # current_line became empty (EOF) while searching for "route path"
                      if observers_read < num_observers:
                           print(f"Warning: Unexpected end of file in {file_path} while looking for 'route path' for observer {observers_read + 1} (expected {num_observers}). Found {observers_read}.")
                      # Allow partial data? For now, require all observers.
                      return None # Or return report_data if partial results are OK


                 # Read the latency line (usually indented)
                 latency_line = f.readline()
                 if not latency_line: # EOF after path_name
                      print(f"Warning: Unexpected EOF after reading '{path_name}' in {file_path}. Missing latency/failure.")
                      return None

                 # Read the failure rate line (usually indented)
                 failure_line = f.readline()
                 if not failure_line: # EOF after latency
                      print(f"Warning: Unexpected EOF after reading latency line for '{path_name}' in {file_path}. Missing failure rate.")
                      return None

                 # Parse latency and failure rate
                 try:
                     # Use regex or split to handle potential variations? Split is simpler for now.
                     if ':' not in latency_line or ':' not in failure_line:
                         raise ValueError("Missing colon in latency/failure line")

                     latency_str = latency_line.split(":", 1)[1].strip()
                     failure_str = failure_line.split(":", 1)[1].strip()

                     # Validate they are numbers
                     float(latency_str)
                     float(failure_str)
                 except (IndexError, ValueError) as e:
                     print(f"Warning: Error parsing latency/failure value for '{path_name}' in {file_path}. Error: {e}. Lines: '{latency_line.strip()}', '{failure_line.strip()}'")
                     return None # Treat as critical format error

                 route_paths.append([path_name, latency_str, failure_str])
                 observers_read += 1

                 # Read the next line to prepare for the next iteration's search for "route path"
                 # This might be an empty line separator or the next "route path" directly
                 current_line = f.readline()


            # --- Final Check ---
            if len(route_paths) != num_observers:
                print(f"Warning: Mismatch between expected observers ({num_observers}) and successfully read paths ({len(route_paths)}) in {file_path}.")
                # This case might indicate an issue in the loop logic or file format
                return None

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
        # traceback.print_exc() # Uncomment for detailed debugging if needed
        return None


# =============================================================================
# Other Functions (get_records, calculate_statistics, create_summary_report, etc.)
# Keep the implementations from the previous good refactoring, as they depend
# on the output structure of read_report_file (which remains the same: a dict
# with 'path info' list etc.), and the configuration variables.
# =============================================================================

# Define a type alias for the statistics tuple for clarity
StatsTuple = Tuple[str, float, float, float, float, float, float, float]

def get_records(directory: Path, target_name: str) -> List[Dict[str, Any]]:
    """Scans a directory for report files matching the target scenario name."""
    # (Implementation from previous version is likely fine)
    records = []
    if not directory.is_dir():
        print(f"Error: Report directory '{directory}' not found or is not a directory.")
        return []

    print(f"Scanning directory '{directory}' for reports matching scenario '{target_name}'...")
    file_count = 0
    matched_count = 0
    for file_path in sorted(directory.iterdir()): # Iterate over Path objects
        if (file_path.is_file() and
            file_path.name.startswith(REPORT_FILE_PREFIX) and
            file_path.name.endswith(REPORT_FILE_SUFFIX)):
            file_count += 1
            report_data = read_report_file(file_path, target_name) # Use the NEW function here
            if report_data:
                records.append(report_data)
                matched_count +=1

    print(f"Scan complete. Found {file_count} potential report files, successfully parsed {matched_count} matching reports for scenario '{target_name}'.")
    return records


def calculate_statistics(record: Dict[str, Any]) -> Optional[StatsTuple]:
    """Calculates performance statistics from a single parsed report record."""
    # (Implementation from previous version is likely fine, relies on keys being present)
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

        if not latencies:
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
    # (Implementation from previous version is likely fine)
    print(f"\nCreating summary report for scenario '{target_name}' -> {output_filename}")

    all_stats: Dict[str, StatsTuple] = {}
    valid_records_in_order: List[str] = []
    for record in records:
        algo_name = record.get("algorithm")
        if not algo_name: continue # Should have been caught earlier
        stats = calculate_statistics(record)
        if stats:
            all_stats[algo_name] = stats
            valid_records_in_order.append(algo_name)
        else:
            print(f"Warning: Skipping algorithm '{algo_name}' in summary due to errors in statistics calculation.")

    if not all_stats:
        print("Error: No valid statistics could be calculated. Summary report cannot be generated.")
        return

    base_stats = all_stats.get(benchmark_algorithm)
    if not base_stats:
        print(f"Warning: Benchmark algorithm '{benchmark_algorithm}' not found or had errors. Relative values cannot be calculated.")
        base_update, base_latency, base_p50, base_p90, base_p99 = 1.0, 1.0, 1.0, 1.0, 1.0
    else:
        base_update = base_stats[2] if base_stats[2] != 0 else 1.0
        base_latency = base_stats[4] if base_stats[4] != 0 else 1.0
        base_p50 = base_stats[5] if base_stats[5] != 0 else 1.0
        base_p90 = base_stats[6] if base_stats[6] != 0 else 1.0
        base_p99 = base_stats[7] if base_stats[7] != 0 else 1.0
        print(f"Using benchmark '{benchmark_algorithm}': Update={base_stats[2]:.2f}, Avg Latency={base_stats[4]:.2f}ms")

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

            for algorithm_name in valid_records_in_order:
                 stats = all_stats[algorithm_name]
                 (algo_name_internal, compute_time, update_entry, avg_failure_rate,
                  avg_latency, p50, p90, p99) = stats
                 display_name = algorithm_display_mapping.get(algo_name_internal, algo_name_internal)

                 rel_update = (update_entry - base_stats[2]) / base_update if base_stats else 0.0
                 rel_latency = (avg_latency - base_stats[4]) / base_latency if base_stats else 0.0
                 rel_p50 = (p50 - base_stats[5]) / base_p50 if base_stats else 0.0
                 rel_p90 = (p90 - base_stats[6]) / base_p90 if base_stats else 0.0
                 rel_p99 = (p99 - base_stats[7]) / base_p99 if base_stats else 0.0

                 line_data = [
                     f'"{display_name}"', f"{compute_time:.2f}", f"{update_entry:.2f}",
                     f"{rel_update:+.2%}" if base_stats else "N/A", f"{avg_failure_rate:.4%}",
                     f"{avg_latency:.2f}", f"{rel_latency:+.2%}" if base_stats else "N/A",
                     f"{p50:.2f}", f"{rel_p50:+.2%}" if base_stats else "N/A",
                     f"{p90:.2f}", f"{rel_p90:+.2%}" if base_stats else "N/A",
                     f"{p99:.2f}", f"{rel_p99:+.2%}" if base_stats else "N/A",
                 ]
                 f.write(",".join(line_data) + "\n")
        print(f"Successfully written summary report: {output_filename}")
    except IOError as e:
        print(f"Error writing summary file {output_filename}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while creating summary report: {e}")

def sanitize_filename(name: str) -> str:
    """Removes or replaces characters unsuitable for filenames."""
    # (Implementation from previous version is likely fine)
    sanitized = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in name)
    sanitized = '_'.join(filter(None, sanitized.split('_')))
    return sanitized.strip('_ ')


def generate_latency_distribution(
    record: Dict[str, Any], algorithm_name: str, output_dir: Path,
    num_bins: int, min_upper_bound: float, upper_bound_factor: float, filename_template: str
) -> None:
    """Generates a CSV file containing data points for a latency CDF plot."""
    # (Implementation from previous version is likely fine)
    try:
        paths = record.get("path info", [])
        if not paths: return

        latency_data = []
        for i, path in enumerate(paths):
            try:
                latency = float(path[1])
                if np.isfinite(latency) and latency >= 0:
                    latency_data.append(latency)
                # else: # Optional: Warn about invalid values
            except (IndexError, ValueError): continue # Ignore parsing errors here, handled in calculate_stats

        if not latency_data: return
        latency_array = np.array(latency_data)

        if len(latency_array) > 10:
             p99_9 = np.percentile(latency_array, 99.9)
             realistic_upper_bound = max(min_upper_bound, p99_9 * upper_bound_factor)
        else:
             realistic_upper_bound = max(min_upper_bound, np.max(latency_array) * upper_bound_factor if latency_array.size > 0 else min_upper_bound)

        cumfreq_result = stats.cumfreq(latency_array, numbins=num_bins, defaultreallimits=(0, realistic_upper_bound))
        x_coords = cumfreq_result.lowerlimit + np.linspace(cumfreq_result.binsize, cumfreq_result.binsize * cumfreq_result.cumcount.size, cumfreq_result.cumcount.size)
        y_coords = cumfreq_result.cumcount / len(latency_array)

        output_dir.mkdir(parents=True, exist_ok=True)
        safe_algo_name = sanitize_filename(algorithm_name)
        output_filename = filename_template.format(safe_algo_name=safe_algo_name)
        output_path = output_dir / output_filename

        with output_path.open("w", encoding='utf-8', newline='') as pf:
            pf.write("Latency (ms),Cumulative Fraction\n")
            if cumfreq_result.lowerlimit >= 0 and (len(x_coords) == 0 or x_coords[0] > 0):
                 pf.write("0.000000,0.000000\n")
            last_y = 0.0
            for x, y in zip(x_coords, y_coords):
                if np.isfinite(x) and np.isfinite(y) and y >= last_y:
                    pf.write(f"{x:.6f},{y:.6f}\n")
                    last_y = y
    except Exception as e:
        print(f"An unexpected error occurred during latency CDF generation for '{algorithm_name}': {e}")


def sort_records(records: List[Dict[str, Any]], algorithm_id_map: Dict[str, int], output_order: List[str]) -> List[Dict[str, Any]]:
    """Sorts the records based on the predefined output order and ID fallback."""
    # (Implementation from previous version is likely fine)
    order_dict = {name: index for index, name in enumerate(output_order)}
    fallback_order_index = len(output_order)

    def sort_key(record):
        algo_name = record.get("algorithm", "")
        primary_key = order_dict.get(algo_name, fallback_order_index)
        secondary_key = algorithm_id_map.get(algo_name, DEFAULT_SORT_ID)
        return (primary_key, secondary_key)

    try:
        sorted_records = sorted(records, key=sort_key)
        print("\nRecords sorted according to predefined output order (with ID fallback).")
        print("Final processing order of algorithms:")
        for i, rec in enumerate(sorted_records):
            algo_name = rec.get('algorithm', 'UNKNOWN')
            display_name = ALGORITHM_DISPLAY_MAPPING.get(algo_name, algo_name)
            print(f"  {i+1}. {algo_name} (Display: {display_name})")
        return sorted_records
    except Exception as e:
        print(f"Error during record sorting: {e}. Returning unsorted records.")
        return records


# =============================================================================
# Main Execution
# =============================================================================
def main():
    """Main function to orchestrate the report processing."""
    # (Implementation from previous version is likely fine)
    print("=" * 60)
    print("Starting Report Processing Script")
    print(f"Report Directory: {REPORT_DIRECTORY.resolve()}")
    print(f"Output Plot Data Directory: {OUTPUT_PLOT_DIRECTORY.resolve()}")
    print(f"Benchmark Algorithm: {BENCHMARK_ALGORITHM}")
    print("=" * 60)
    print("\n--- Configuration Summary ---")
    print(f"Target Scenarios: {TARGET_LIST}")
    print(f"Algorithm Output Order: {ALGORITHM_OUTPUT_ORDER}")
    print(f"Generate Latency CDFs: {GENERATE_LATENCY_CDF_FILES}")
    print("-" * 30)

    for target_name in TARGET_LIST:
        print(f"\n===== Processing Scenario: {target_name} =====")
        records = get_records(REPORT_DIRECTORY, target_name) # Uses new read_report_file
        if not records:
            print(f"No matching reports found or parsed for scenario '{target_name}'. Skipping.")
            continue

        sorted_records = sort_records(records, ALGORITHM_ID_MAP, ALGORITHM_OUTPUT_ORDER)

        summary_filename = Path(SUMMARY_REPORT_FILENAME_TEMPLATE.format(target_name=target_name))
        create_summary_report(target_name, sorted_records, ALGORITHM_DISPLAY_MAPPING, BENCHMARK_ALGORITHM, summary_filename)

        if GENERATE_LATENCY_CDF_FILES:
            print("\nGenerating latency distribution CDF files...")
            cdf_count = 0
            for record in sorted_records:
                algo_name = record.get("algorithm")
                if algo_name:
                    generate_latency_distribution(
                        record, algo_name, OUTPUT_PLOT_DIRECTORY, LATENCY_CDF_NUM_BINS,
                        LATENCY_CDF_MIN_UPPER_BOUND, LATENCY_CDF_UPPER_BOUND_FACTOR, LATENCY_CDF_FILENAME_TEMPLATE
                    )
                    cdf_count += 1
            print(f"Generated {cdf_count} CDF data files in '{OUTPUT_PLOT_DIRECTORY}'.")

        print(f"===== Finished Processing Scenario: {target_name} =====")

    print("\n" + "=" * 60)
    print("Report Processing Script Finished")
    print("=" * 60)


if __name__ == "__main__":
    main()