from line import Line
from line_detection import CannyHoughLineDetection, LineDetection
import img_utils
import image_logging
from typing import Any, List
from enum import Enum


class BoundarySide(Enum):
    left = 1
    right = 2

class Boundary:
    def __init__(self, side: BoundarySide, x1: int, y1: int, x2: int, y2: int) -> None:
        self.side = side
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.calculate_x_at = self.create_function()

    def create_function(self) -> Any:
        m = (self.x2 - self.x1) / (self.y2 - self.y1)
        c = self.x1 - m * self.y1

        return lambda y: y * m + c

    def to_line(self) -> Line:
        return Line(self.x1, self.y1, self.x2, self.y2)

    @staticmethod
    def from_line(side: BoundarySide, line: Line) -> Any:
        return Boundary(side, x1=line.x1, y1=line.y1, x2=line.x2, y2=line.y2)


class Boundaries:
    def __init__(self, left: Boundary, right: Boundary, x_min: int, x_max: int) -> None:
        self.left = left
        self.right = right
        self.x_min = x_min
        self.x_max = x_max

    def get_x1_within_boundaries(self, y: int) -> int:
        return max(self.left.calculate_x_at(y), self.x_min)

    def get_x2_within_boundaries(self, y: int) -> int:
        return min(self.right.calculate_x_at(y), self.x_max)


class BoundaryDetection:
    def __init__(self) -> None:
        self.line_detection: LineDetection = CannyHoughLineDetection(
            low_threshold=5, high_threshold=240, min_votes=5
        )

    def detect_boundaries(self, img: Any) -> Boundaries:
        img_height = img.shape[0]
        img_width = img.shape[1]

        possible_lines_left = self.line_detection.detect_lines(
            img,
            min_angle=-65,
            max_angle=-50,
            min_line_length=0.5 * img_height,
            max_line_gap=0.2 * img_height,
        )
        possible_lines_right = self.line_detection.detect_lines(
            img,
            min_angle=50,
            max_angle=65,
            min_line_length=0.5 * img_height,
            max_line_gap=0.2 * img_height,
        )

        image_logging.log(
            "possible_lines_left.jpg", img_utils.render_lines(img, possible_lines_left)
        )

        image_logging.log(
            "possible_lines_right.jpg",
            img_utils.render_lines(img, possible_lines_right),
        )

        boundary_left = self.get_boundary_left(possible_lines_left)
        boundary_right = self.get_boundary_right(possible_lines_right)

        image_logging.log(
            "boundaries.jpg",
            img_utils.render_lines(
                img, [boundary_left.to_line(), boundary_right.to_line()]
            ),
        )

        return Boundaries(
            left=boundary_left, right=boundary_right, x_min=0, x_max=img_width
        )

    def get_boundary_left(self, left_lines: List[Line]) -> Boundary:
        leftest = left_lines[0]
        for line in left_lines:
            if (line.x1 + line.x2) < (leftest.x1 + leftest.x2):
                leftest = line

        return Boundary.from_line(BoundarySide.left, leftest)

    def get_boundary_right(self, right_lines: List[Line]) -> Boundary:
        rightest = right_lines[0]
        for line in right_lines:
            if (line.x1 + line.x2) > (rightest.x1 + rightest.x2):
                rightest = line

        return Boundary.from_line(BoundarySide.right, rightest)
