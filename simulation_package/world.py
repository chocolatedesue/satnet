import numpy as np

class World:
    """
    Holds references to the shared simulation state arrays, providing access
    for node algorithm objects.
    """
    def __init__(self,
                 cur_banned: np.ndarray,
                 futr_banned: np.ndarray,
                 sat_pos: np.ndarray,
                 sat_lla: np.ndarray,
                 sat_vel: np.ndarray):
        """
        Initializes the World state container.
        Args:
            cur_banned: NumPy array (N, 5) for currently banned links.
            futr_banned: NumPy array (N, 5) for future banned links.
            sat_pos: NumPy array (N, 3) for satellite positions (km).
            sat_lla: NumPy array (N, 3) for satellite LLA (lat,lon,alt).
            sat_vel: NumPy array (N,) for satellite velocities/direction.
        """
        self.cur_banned: np.ndarray = cur_banned
        self.futr_banned: np.ndarray = futr_banned
        self.sat_pos: np.ndarray = sat_pos
        self.sat_lla: np.ndarray = sat_lla
        self.sat_vel: np.ndarray = sat_vel