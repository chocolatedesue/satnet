from typing import Tuple

def move(node_id: int, direction: int, P: int, Q: int, F: int) -> int:
    """Calculates the neighbor ID based on current ID and direction."""
    x = node_id // Q
    y = node_id % Q

    if direction == 1:   # West (-y)
        y = (y - 1 + Q) % Q
    elif direction == 2: # North (+x, with wrap & phase shift)
        if x == P - 1:
            x = 0 # Wrap around
        else:
            x = x + 1
        y = (y + F) % Q # Apply phase shift F
    elif direction == 3: # East (+y)
        y = (y + 1) % Q
    elif direction == 4: # South (-x, with wrap & phase shift)
        if x == 0:
            x = P - 1 # Wrap around
        else:
            x = x - 1
        y = (y - F + Q) % Q # Apply phase shift -F
    # else: direction == 0 or invalid: do nothing, return original id

    return x * Q + y

def get_port(u: int, v: int, P: int, Q: int, F: int) -> Tuple[int, int]:
    """Finds the port u uses to reach v, and the port v uses to reach u."""
    u_port = 0
    v_port = 0
    for i in range(1, 5): # Check directions 1, 2, 3, 4
        if move(u, i, P, Q, F) == v:
            u_port = i
        if move(v, i, P, Q, F) == u:
            v_port = i
    # Returns (0, 0) if not direct neighbors via ports 1-4
    return u_port, v_port