import numpy as np
from pathlib import Path
import sys

class Average:
    """Calculates a running average, handling -1 as a special case."""
    def __init__(self):
        self._sum = 0.0
        self._cnt = 0
        self._mx = 0.0

    def add(self, val: float):
        if val == -1:
            val_to_add = 2 * self._mx if self._mx > 0 else 0 # Avoid adding 0 if no max seen
        else:
            val_to_add = val
            self._mx = max(self._mx, val)

        self._sum += val_to_add
        self._cnt += 1

    def get_result(self) -> float:
        return self._sum / self._cnt if self._cnt > 0 else 0.0

    def get_count(self) -> int:
        return self._cnt

    def get_sum(self) -> float:
        return self._sum

def create_dir_recursive(dir_path: Path):
    """Creates a directory including parent directories if they don't exist."""
    dir_path.mkdir(parents=True, exist_ok=True)

def go_and_create(base_dir: Path, dir_levels: list[str]) -> Path:
    """Constructs path from levels relative to base_dir and creates directories."""
    cur_path = base_dir
    for level in dir_levels:
        cur_path = cur_path / level
    create_dir_recursive(cur_path)
    return cur_path

def _load_data_from_file(file_path: Path, target_array: np.ndarray):
    """Helper to load space-separated data into a numpy array."""
    if not file_path.exists():
        print(f"Error: Data file not found: {file_path}", file=sys.stderr)
        # Decide how to handle missing files: exit, warning, default values?
        # For now, let's exit as the original code likely assumes file existence.
        sys.exit(1)
    try:
        # Use numpy.loadtxt which is efficient for numerical data
        loaded_data = np.loadtxt(file_path)
        # Check if shape matches, handle potential single line/column cases
        if loaded_data.shape == target_array.shape:
            target_array[:] = loaded_data
        elif loaded_data.ndim == 0 and target_array.size == 1: # Single value file
             target_array.flat[0] = loaded_data
        elif loaded_data.ndim == 1 and target_array.ndim == 2 and target_array.shape[0] == 1: # Single row target
             if loaded_data.shape[0] == target_array.shape[1]:
                  target_array[0,:] = loaded_data
             else: raise ValueError("Shape mismatch")
        elif loaded_data.ndim == 1 and target_array.ndim == 1 : # 1D array target
             if loaded_data.shape == target_array.shape:
                  target_array[:] = loaded_data
             else: raise ValueError("Shape mismatch")
        else:
             # Attempt reshape or raise error
             if loaded_data.size == target_array.size:
                  target_array[:] = loaded_data.reshape(target_array.shape)
             else:
                  raise ValueError(f"Shape mismatch: loaded {loaded_data.shape}, expected {target_array.shape}")

    except Exception as e: # Catch loadtxt errors (parsing, shape)
        print(f"Error loading data from {file_path}: {e}", file=sys.stderr)
        sys.exit(1)