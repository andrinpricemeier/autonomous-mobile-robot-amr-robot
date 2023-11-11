import cv2
import numpy as np
import image_logging
from bounding_box import BoundingBox
from detected_object import DetectedObject
from typing import List, Tuple
import img_utils
from object_detection import ObjectDetection


class ClassicEdgeDetection(ObjectDetection):
    def detect(self, image, confidence=0.8, nms=0.5) -> List[BoundingBox]:
        return self.detect_edges(image)

    def create_function(self, coordinates):
        for x1, y1, x2, y2 in coordinates:
            m = (x2 - x1) / (y2 - y1)
            c = x1 - m * y1

        return lambda y: y * m + c

    def cut_steps(self, leftest, rightest, steps, img):
        left_point = self.create_function(leftest)
        right_point = self.create_function(rightest)

        left_max = 0
        right_max = img.shape[1]

        steps_cut = []

        for step in steps:
            for x1, y1, x2, y2 in step:
                new_x1 = int(max(left_point((y2 + y1) // 2), left_max))
                new_x2 = int(min(right_point((y2 + y1) // 2), right_max))
                steps_cut.append([[new_x1, y1, new_x2, y2]])

        return steps_cut

    def combine_edges(self, edges: List[BoundingBox]) -> List[BoundingBox]:
        combined_edges = edges.copy()
        print("combine_edges")
        for index, edge in enumerate(edges):
            edge_center_norm = np.array([edge.center_normalized()[1]])
            if edge in combined_edges:
                for other_index, other_edge in enumerate(edges, start=index):
                    if other_edge in combined_edges and edge != other_edge:
                        other_edge_center_norm = np.array(
                            [other_edge.center_normalized()[1]]
                        )
                        dist = np.linalg.norm(edge_center_norm - other_edge_center_norm)
                        # TODO: Make this distance dependent on position y!
                        if dist < (0.05 + other_edge.center_normalized()[0] / 6):
                            # Drop the shorter edge
                            if edge.width() < other_edge.width():
                                combined_edges.remove(edge)
                                # TODO: Merge them? -> Take average?
                                # This edge was removed, so it doesn't have to get checked
                                break
                            else:
                                combined_edges.remove(other_edge)

        return combined_edges

    def detect_steps_borders(self, img) -> Tuple:
        img_height = img.shape[0]
        print(img.shape)

        # TODO: Take the leftest
        step_ends_left = []

        # TODO: Take the rightest
        step_ends_right = []

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kernel_size = 3
        blur_gray = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)

        image_logging.log("border_edge_detection_blur.jpg", blur_gray)

        low_threshold = 40
        high_threshold = 200
        edges = cv2.Canny(blur_gray, low_threshold, high_threshold)
        image_logging.log("border_edge_detection_canny.jpg", edges)

        rho = 1  # distance resolution in pixels of the Hough grid
        theta = np.pi / 180  # angular resolution in radians of the Hough grid
        threshold = 5  # minimum number of votes (intersections in Hough grid cell)

        min_line_length = 0.6 * img_height  # minimum number of pixels making up a line
        max_line_gap = (
            0.5 * min_line_length
        )  # maximum gap in pixels between connectable line segments
        line_image = np.copy(img) * 0  # creating a blank to draw lines on

        # Run Hough on edge detected image
        # Output "lines" is an array containing endpoints of detected line segments
        lines = cv2.HoughLinesP(
            edges, rho, theta, threshold, np.array([]), min_line_length, max_line_gap
        )

        for line in lines:
            for x1, y1, x2, y2 in line:
                # TODO: filter non horizontal lines
                angle = np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi
                # detect them differently!
                if (angle > -80) and (angle < -50):
                    step_ends_left.append(line)

                elif (angle > 50) and (angle < 70):
                    step_ends_right.append(line)

        for line in step_ends_left:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 0), 5)

        for line in step_ends_right:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image, (x1, y1), (x2, y2), (0, 0, 255), 5)

        # TODO: What to do if no borders are detected?
        leftest = step_ends_left[0]
        for left_end in step_ends_left:
            for x1, y1, x2, y2 in left_end:
                if x1 < leftest[0, 0]:
                    leftest = left_end

        print(f"leftest {leftest}")

        rightest = step_ends_right[0]
        for right_end in step_ends_right:
            for x1, y1, x2, y2 in right_end:
                if x2 > rightest[0, 2]:
                    rightest = right_end

        print(f"rightest {rightest}")

        lines_edges = cv2.addWeighted(img, 0.8, line_image, 1, 0)
        image_logging.log("border_edge_detection_lines.jpg", lines_edges)

        return leftest, rightest

    def detect_edges(self, img) -> List[BoundingBox]:
        img_width = img.shape[1]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kernel_size = 3
        blur_gray = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)

        image_logging.log("edge_detection_blur.jpg", blur_gray)

        low_threshold = 50
        high_threshold = 150
        edges = cv2.Canny(blur_gray, low_threshold, high_threshold)
        image_logging.log("edge_detection_canny.jpg", edges)

        rho = 1  # distance resolution in pixels of the Hough grid
        theta = np.pi / 180  # angular resolution in radians of the Hough grid
        threshold = 12  # minimum number of votes (intersections in Hough grid cell)

        # TODO: Decrease to detect left and right end!
        # TODO: Make this relative!
        min_line_length = img_width * 0.65  # minimum number of pixels making up a line
        max_line_gap = (
            0.2 * min_line_length
        )  # maximum gap in pixels between connectable line segments
        line_image = np.copy(img) * 0  # creating a blank to draw lines on

        # Run Hough on edge detected image
        # Output "lines" is an array containing endpoints of detected line segments
        lines = cv2.HoughLinesP(
            edges, rho, theta, threshold, np.array([]), min_line_length, max_line_gap
        )

        steps = []

        for line in lines:
            for x1, y1, x2, y2 in line:
                # TODO: filter non horizontal lines
                angle = np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi
                if (angle > -5) and (angle < 5):
                    steps.append(line)

        for line in steps:
            for x1, y1, x2, y2 in line:
                cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 5)

        lines_edges = cv2.addWeighted(img, 0.8, line_image, 1, 0)
        image_logging.log("edge_detection_lines.jpg", lines_edges)

        leftest, rightest = self.detect_steps_borders(img)
        correct_line_image = np.copy(img) * 0  # creating a blank to draw lines on
        for x1, y1, x2, y2 in leftest:
            cv2.line(correct_line_image, (x1, y1), (x2, y2), (255, 0, 0), 5)

        for x1, y1, x2, y2 in rightest:
            cv2.line(correct_line_image, (x1, y1), (x2, y2), (255, 0, 0), 5)

        borders_image = cv2.addWeighted(img, 0.8, correct_line_image, 1, 0)
        image_logging.log("bordered_edge_detection_lines.jpg", borders_image)

        raw_edges_as_bounding_boxes = [
            BoundingBox(
                DetectedObject.edge, 0.5, x1, x2, y1, y2, img.shape[1], img.shape[0]
            )
            for step in steps
            for x1, y1, x2, y2 in step
        ]
        image_logging.log(
            "bounding_boxes_raw.jpg",
            img_utils.render_boxes(img.copy(), raw_edges_as_bounding_boxes),
        )

        cutted_steps = self.cut_steps(leftest, rightest, steps, img.copy())

        edges_as_bounding_boxes = [
            BoundingBox(
                DetectedObject.edge, 0.5, x1, x2, y1, y2, img.shape[1], img.shape[0]
            )
            for step in cutted_steps
            for x1, y1, x2, y2 in step
        ]
        image_logging.log(
            "bounding_boxes_cutted.jpg",
            img_utils.render_boxes(img.copy(), edges_as_bounding_boxes),
        )

        combined_edges = self.combine_edges(edges_as_bounding_boxes)
        image_logging.log(
            "bounding_boxes_combined.jpg",
            img_utils.render_boxes(img.copy(), combined_edges),
        )
        return combined_edges


detection: ObjectDetection = ClassicEdgeDetection()

img = cv2.imread("examples/images/steps.jpg")

image_logging.configure("robot.conf")

boxes = detection.detect(img)

image_logging.log(
    "bounding_boxes_combined.jpg", img_utils.render_boxes(img.copy(), boxes)
)
