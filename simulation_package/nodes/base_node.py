from abc import ABC, abstractmethod
import numpy as np

# Forward reference for type hinting
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..config import Config
    from ..world import World

class BaseNode(ABC):
    """Abstract Base Class for satellite node routing algorithms."""

    def __init__(self, config: 'Config', node_id: int, world: 'World'):
        """
        Args:
            config: Simulation configuration object.
            node_id: The unique ID (0 to N-1) of this node.
            world: Reference to the shared simulation state.
        """
        self.config = config
        self.node_id = node_id
        self.world = world
        self.N = config.N
        self._route_table = np.zeros(self.N, dtype=int) # Internal storage for computed routes

    @abstractmethod
    def compute(self) -> None:
        """
        Perform the routing computation for this node based on the current
        state available in self.world. Update internal state.
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this routing algorithm."""
        pass

    def get_route_table(self) -> np.ndarray:
        """
        Return the computed routing table for this node as a 1D NumPy array.
        Index `j` of the array should contain the next hop *port* (1-4)
        to reach destination node `j`, or 0 if no route.
        """
        return self._route_table