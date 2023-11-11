from line import Line
import cv2
from typing import Any, List
import image_logging
import logging
import numpy as np
import img_utils


class LineDetection:
    def detect_lines(
        self,
        img: Any,
        min_angle: float,
        max_angle: float,
        min_line_length: float,
        max_line_gap: float,
    ) -> List[Line]:
        pass


class CannyHoughLineDetection(LineDetection):
    def __init__(
        self,
        low_threshold: float = 50,
        high_threshold: float = 150,
        min_votes: float = 10,
    ) -> None:
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.min_votes = min_votes

    def detect_lines(
        self,
        img: Any,
        min_angle: float,
        max_angle: float,
        min_line_length: float,
        max_line_gap: float,
    ) -> List[Line]:
        # Histogram Ausgleich
        gray = self.convert_to_gray_scale(img)
        equalized = cv2.equalizeHist(gray)

        # Median Filter instead
        # blur_gray = self.apply_gaussian(equalized)

        # Maybe use Sobel Operator
        edges = self.apply_auto_canny(equalized)
        lines = self.apply_hough_lines(
            edges, min_line_length=min_line_length, max_line_gap=max_line_gap
        )
        detected_lines = self.filter_lines(lines, min_angle, max_angle)

        image_logging.log(
            "all_detected_lines.jpg",
            img_utils.render_lines(
                cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR), detected_lines
            ),
        )

        return detected_lines

    def apply_gaussian(self, img: Any) -> Any:
        kernel_size = 3
        blur_gray = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

        image_logging.log("line_detection_gaussian.jpg", blur_gray)
        return blur_gray

    def apply_median(self, img: Any) -> Any:
        kernel_size = 1
        blur_gray = cv2.medianBlur(img, kernel_size)

        image_logging.log("line_detection_median.jpg", blur_gray)
        return blur_gray

    def apply_canny(self, img: Any) -> Any:
        edges = cv2.Canny(
            img, self.low_threshold, self.high_threshold, 3, L2gradient=True
        )
        image_logging.log("line_detection_canny.jpg", edges)
        return edges

    def apply_auto_canny(self, img: Any, sigma: float = 0.33) -> Any:
        # compute the median of the single channel pixel intensities
        v = np.median(img)
        # apply automatic Canny edge detection using the computed median
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))
        edges = cv2.Canny(img, lower, upper, 3, L2gradient=True)
        # return the edged image
        return edges

    def apply_hough_lines(
        self, img: Any, min_line_length: float, max_line_gap: float
    ) -> Any:
        rho = 1  # distance resolution in pixels of the Hough grid
        theta = np.pi / 180  # angular resolution in radians of the Hough grid
        # Run Hough on edge detected image
        # Output "lines" is an array containing endpoints of detected line segments
        lines = cv2.HoughLinesP(
            img, rho, theta, self.min_votes, np.array([]), min_line_length, max_line_gap
        )
        return lines

    def convert_to_gray_scale(self, img: Any) -> Any:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def filter_lines(self, lines: Any, min_angle: float, max_angle: float) -> Any:
        detected_lines = []
        angles = []

        for line in lines:
            for x1, y1, x2, y2 in line:
                angle = np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi
                if (angle >= min_angle) and (angle <= max_angle):
                    detected_lines.append(Line(x1=x1, y1=y1, x2=x2, y2=y2))
                    angles.append(angle)

        logging.debug("Average angle: {}".format((sum(angles) / len(angles))))
        return detected_lines
