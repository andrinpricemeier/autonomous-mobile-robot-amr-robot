import numpy as np


class Line:
    def __init__(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def get_angle(self) -> float:
        return np.arctan2(self.y2 - self.y1, self.x2 - self.x1) * 180.0 / np.pi
