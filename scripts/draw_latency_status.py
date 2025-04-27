import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import argparse # <-- MODIFICATION: Import argparse for command-line arguments
import os       # <-- MODIFICATION: Import os for path operations

# --- Constants ---
# FILE_PATH is now obtained from command-line arguments
TIME_COLUMN = 'time'            # Name of the time column
LATENCY_COLUMN = 'latency'      # Name of the latency column
SRC_COLUMN = 'src'              # Name of the source address column
DST_COLUMN = 'dst'              # Name of the destination address column

PLOT_TITLE_BASE = 'Network Latency Over Time (First 5 Pairs, Outliers Removed)' # Base title for the plot
X_AXIS_LABEL = 'Time'           # X-axis label
Y_AXIS_LABEL = 'Latency (ms)'   # Y-axis label
FIGURE_SIZE = (12, 6)           # Figure size (width, height) in inches

# --- Outlier Removal Settings ---
# Choose one method and comment out the other
# Method 1: Using Quantile Filter
ENABLE_QUANTILE_FILTER = True   # Set to True to enable this method
QUANTILE_THRESHOLD = 0.95       # Keep latency values below the 95th percentile (adjustable: 0.95, 0.99, etc.)

# Method 2: Using Fixed Threshold Filter (ignored if quantile filter is enabled)
ENABLE_FIXED_THRESHOLD_FILTER = False # Set to True to enable this method (ensure Quantile Filter is False)
MAX_LATENCY_THRESHOLD = 1000    # Set a maximum latency threshold (e.g., 1000ms, adjust based on your data)

# --- Main Script ---
def main(file_path):
    """
    Reads network latency data from a CSV file, removes outliers,
    and plots latency over time for the first 5 source-destination pairs.

    Args:
        file_path (str): The path to the input CSV file.
    """
    try:
        # 1. Read Data
        print(f"Attempting to read data from: {file_path}")
        df = pd.read_csv(file_path)

        # 2. Data Check
        if df.empty:
            print(f"Error: The file '{file_path}' is empty or could not be parsed.")
            return # Exit the function if file is empty
        required_columns = [TIME_COLUMN, LATENCY_COLUMN, SRC_COLUMN, DST_COLUMN]
        if not all(col in df.columns for col in required_columns):
            print(f"Error: Missing one or more required columns in '{file_path}'. ")
            print(f"Required: {required_columns}, Found: {list(df.columns)}")
            return # Exit the function if columns are missing

        # Ensure latency is numeric, drop rows where conversion fails
        df[LATENCY_COLUMN] = pd.to_numeric(df[LATENCY_COLUMN], errors='coerce')
        df.dropna(subset=[LATENCY_COLUMN], inplace=True)

        print(f"Original data points: {len(df)}")

        # --- 3. Remove Outliers ---
        df_filtered = df.copy() # Create a copy for filtering

        if ENABLE_QUANTILE_FILTER:
            latency_limit = df_filtered[LATENCY_COLUMN].quantile(QUANTILE_THRESHOLD)
            original_count = len(df_filtered)
            df_filtered = df_filtered[df_filtered[LATENCY_COLUMN] <= latency_limit]
            removed_count = original_count - len(df_filtered)
            print(f"Using Quantile Filter ({QUANTILE_THRESHOLD * 100:.0f}%):")
            print(f" - Latency threshold: {latency_limit:.2f} ms")
            print(f" - Removed {removed_count} outlier(s).")
        elif ENABLE_FIXED_THRESHOLD_FILTER:
            original_count = len(df_filtered)
            df_filtered = df_filtered[df_filtered[LATENCY_COLUMN] <= MAX_LATENCY_THRESHOLD]
            removed_count = original_count - len(df_filtered)
            print(f"Using Fixed Threshold Filter:")
            print(f" - Max latency threshold: {MAX_LATENCY_THRESHOLD} ms")
            print(f" - Removed {removed_count} outlier(s).")
        else:
            print("No outlier filtering applied.")

        print(f"Data points after filtering: {len(df_filtered)}")

        # --- 4. Plotting (using filtered data df_filtered) ---
        if df_filtered.empty:
            print("No data left after filtering. Cannot plot.")
            return # Exit the function if no data to plot

        fig, ax = plt.subplots(figsize=FIGURE_SIZE)

        # Create a 'pair' column for grouping
        df_filtered['pair'] = df_filtered[SRC_COLUMN].astype(str) + ' -> ' + df_filtered[DST_COLUMN].astype(str)

        # Group by pair and plot only the first 5 pairs encountered
        plot_count = 0
        grouped_pairs = df_filtered.groupby('pair')

        for pair_name, group_data in grouped_pairs:
            if plot_count >= 5:
                print(f"Stopped plotting after {plot_count} pairs.")
                break

            # Sort data within each group by time before plotting
            group_data_sorted = group_data.sort_values(by=TIME_COLUMN)
            ax.plot(group_data_sorted[TIME_COLUMN], group_data_sorted[LATENCY_COLUMN],
                    marker='o', linestyle='-', label=pair_name)

            plot_count += 1

        # Add legend to distinguish lines
        ax.legend(title='Source -> Destination (First 5)', bbox_to_anchor=(1.05, 1), loc='upper left')

        # Extract filename without extension for plot title and saving
        base_name = os.path.basename(file_path) # Get filename with extension
        file_name_no_ext = os.path.splitext(base_name)[0] # Get filename without extension

        # 5. Customize Plot
        ax.set_title(f"{PLOT_TITLE_BASE}\nFile: {base_name}") # Use base_name for clarity
        ax.set_xlabel(X_AXIS_LABEL)
        ax.set_ylabel(Y_AXIS_LABEL)
        ax.grid(True, linestyle='--', alpha=0.6)

        # Format time axis (ensure it's numeric before setting integer locator)
        if pd.api.types.is_numeric_dtype(df_filtered[TIME_COLUMN]):
             ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=10)) # Adjust nbins as needed

        # Adjust layout to prevent legend overlap
        plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust right boundary

        # Save the plot
        output_filename = f"./{file_name_no_ext}_latency_plot_first_5.png"
        plt.savefig(output_filename, dpi=300, bbox_inches='tight') # Use bbox_inches='tight' for better fit
        print(f"Plot saved to {output_filename}")
        # plt.show() # Uncomment to display the plot interactively

    except FileNotFoundError:
        print(f"Error: File not found at '{file_path}'. Please check the path.")
    except pd.errors.EmptyDataError:
         print(f"Error: No data found in '{file_path}'. The file might be empty or incorrectly formatted.")
    except KeyError as e:
        print(f"Error: Missing expected column in the CSV: {e}. Please check the column names.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc() # Print detailed traceback for debugging

if __name__ == "__main__":
    # --- MODIFICATION: Set up argument parser ---
    parser = argparse.ArgumentParser(description="Plot network latency from a CSV file.")
    parser.add_argument("file_path", # Make it a required positional argument
                        help="Path to the input CSV file containing latency data.")
    # --- MODIFICATION END ---

    # Parse arguments
    args = parser.parse_args()

    # Call the main function with the provided file path
    main(args.file_path)
