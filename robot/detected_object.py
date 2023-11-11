from enum import Enum


class DetectedObject(Enum):
    """Represents an object that was detected with the object detection.
    These are all the objects we know about in the physical world.

    Args:
        Enum ([type]): the superclass.
    """
    brick = 0
    stairs = 1
    steps = 2
    hammer = 3
    taco = 4
    ruler = 5
    bucket = 6
    pencil = 7
    wrench = 8
    edge = 9
