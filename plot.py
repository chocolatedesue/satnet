# Final code to generate the plot based on user's requirements and further modifications

# Importing required libraries
import pandas as pd
import re
import matplotlib.pyplot as plt
import time

# Function to extract the value from the string
def extract_value(s):
    match = re.search(r'(.*)\(([-+]?[\d.]+)%\)', s)
    return float(match.group(1)) if match else 0

# Function to extract the percentage value from the string
def extract_percentage(s):
    match = re.search(r'\(([-+]?[\d.]+)%\)', s)
    return float(match.group(1)) if match else 0

# Function to get prefix from the name
def get_prefix(name):
    sp = re.split('_', name)
    if len(sp) > 1:
        sp = sp[:-1]
    return ''.join(sp).replace("Pred", "").replace("Ng", "")

# Function to check if a name ends with a specific suffix
def ends_with_suffix(name, suffixes):
    return any(name.endswith(suffix) for suffix in suffixes)

# Function to check if a name starts with a specific prefix
def starts_with_prefix(name, prefixes):
    return any(name.startswith(prefix) for prefix in prefixes)


# Load the data from the uploaded CSV file
file_path = 'summary [GW-A59-3 (24 hour) - Jan].csv'

df = pd.read_csv(file_path)

# Clean up column names by stripping leading and trailing whitespaces
df.columns = df.columns.str.strip()

# Extract percentages for 'avg_latency' and 'update_entry'
df['avg_latency_percentage'] = df['avg_latency'].apply(extract_value)
df['update_entry_percentage'] = df['update_entry'].apply(extract_value)

# Suffixes and prefixes to be removed
remove_suffixes = ['Probe', 'Base']
remove_prefixes = ['CoinFlip', 'Oracle', 'DagShortNorm', 'Domain', 'NgDomainBridge_1_1', 'DisCoRoute', 'LBP']

# Filter out rows based on the given suffixes and prefixes
filtered_df = df[~df['name'].apply(lambda x: ends_with_suffix(x, remove_suffixes) or starts_with_prefix(x, remove_prefixes))]


# Get unique prefixes for color mapping based on the filtered data
filtered_unique_prefixes = []
for name in filtered_df['name']:
    name_pfx = get_prefix(name)
    if name_pfx not in filtered_unique_prefixes:
        filtered_unique_prefixes.append(name_pfx)
filtered_color_map = {prefix: plt.cm.jet(i/len(filtered_unique_prefixes)) for i, prefix in enumerate(filtered_unique_prefixes)}

# Plotting
plt.figure(figsize=(10, 6))

# Plot each point with the color based on its prefix in the filtered data
rows = [row for _, row in filtered_df.iterrows()]
rows.reverse()
for row in rows:
    prefix = get_prefix(row['name'])
    color = filtered_color_map[prefix]
    plt.scatter(row['avg_latency_percentage'], row['update_entry_percentage'], marker='o', color=color)

# Add labels and title
plt.xlabel('Avg Latency (ms)')
plt.ylabel('Update Entry')
plt.title('Avg Latency vs Update Entry (Filtered)')

# Add guide lines without adding them to the legend
# plt.axvline(x=10, color='r', linestyle='--', linewidth=0.8)
# plt.axhline(y=-10, color='g', linestyle='--', linewidth=0.8)

# Add legend for prefixes only (based on the filtered data)
legend_labels_prefixes = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=filtered_color_map[prefix], markersize=10) for prefix in filtered_unique_prefixes]
plt.legend(legend_labels_prefixes, filtered_unique_prefixes, loc='upper right')

plt.grid(True)

plot_filename = "plot_figs/plot " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ".png"

plt.savefig(plot_filename)