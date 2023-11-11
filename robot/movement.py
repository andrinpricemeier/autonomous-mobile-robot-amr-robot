from enum import Enum


class Movement(Enum):
    """Represents a movement the robot should execute.

    Args:
        Enum ([type]): the superclass.
    """
    left = 0
    right = 1
    climb = 2

class MovementInCm():
    """Represents a movement with additional distance in cm.
    """
    def __init__(self, movement: Movement, distance_in_cm: int):
        """Creates a new instance.

        Args:
            movement (Movement): the movement.
            distance_in_cm (int): the distance in cm.
        """
        self.movement = movement
        self.distance_in_cm = distance_in_cm

    def __eq__(self, o: object) -> bool:
        if o is None:
            return False
        if isinstance(o, MovementInCm):
            return (self.movement == o.movement) and (self.distance_in_cm == o.distance_in_cm)

    def __str__(self) -> str:
        return (f"{self.movement.name} { self.distance_in_cm}cm") 

    def __repr__(self) -> str:
        return (f"{self.movement.name} { self.distance_in_cm}cm") 