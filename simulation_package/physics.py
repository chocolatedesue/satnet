from loguru import logger
import numpy as np
import math

def calculate_distance_m(pos_a_km: np.ndarray, pos_b_km: np.ndarray) -> float:
    """
    Calculates Euclidean distance between two satellite positions.
    Assumes input positions are in km, returns distance in meters.
    """
    diff_km = pos_a_km - pos_b_km
    # distance_km = np.linalg.norm(diff_km)
    distance_km_sq = np.sum(diff_km * diff_km) # Slightly faster
    return np.sqrt(distance_km_sq) * 1000.0 # Convert km to m

def calculate_delay_ms(pos_a_km: np.ndarray, pos_b_km: np.ndarray,
                       proc_delay_ms: float, prop_coef: float, prop_speed_m_s: float) -> float:
    """
    Calculates one-hop latency (processing + propagation) in milliseconds.
    Assumes positions in km, prop_speed in km/s.
    """
    dist_m = calculate_distance_m(pos_a_km, pos_b_km)

    # logger.debug(f"dist_m: {dist_m:.3f} m")

    # C++ version: proc_delay + prop_delay_coef * getDist(a, b) / prop_speed * 1000
    # Units: ms + coef * (m) / (km/s) * 1000
    # Units: ms + coef * (m) / (1000 m/s) * 1000 = ms + coef * s * 1000 = ms + coef * ms
    # So, calculation is coef * dist_m / (prop_speed_km_s * 1000) for seconds, then * 1000 for ms
    # Simplified: coef * dist_m / prop_speed_km_s
    prop_delay_ms = prop_coef * dist_m * 1000 / prop_speed_m_s 

    return proc_delay_ms + prop_delay_ms