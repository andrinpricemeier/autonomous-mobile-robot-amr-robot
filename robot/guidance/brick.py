import os, sys, inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from bounding_box import BoundingBox


class Brick:
    def __init__(self, box: BoundingBox) -> None:
        self.box = box
