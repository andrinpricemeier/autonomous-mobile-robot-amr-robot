import numpy as np
import image_logging
from bounding_box import BoundingBox
from detected_object import DetectedObject
from typing import Any, List
import img_utils
from object_detection import ObjectDetection
from line import Line
from line_detection import CannyHoughLineDetection
from boundary_detection import Boundaries, BoundaryDetection
import logging


class ClassicEdgeDetection(ObjectDetection):
    default_boundary_detection = BoundaryDetection()

    def __init__(
        self, boundary_detection: BoundaryDetection = default_boundary_detection
    ) -> None:
        self.boundary_detection = boundary_detection
        self.line_detection = CannyHoughLineDetection(
            low_threshold=5, high_threshold=240, min_votes=80
        )

    def detect(
        self, image: Any, confidence: float = 0.8, nms: float = 0.5
    ) -> List[BoundingBox]:
        return self.detect_edges(image)

    def cut_edges_to_boundaries(
        self, edges: List[BoundingBox], boundaries: Boundaries
    ) -> List[BoundingBox]:
        cutted_edges: List[BoundingBox] = []

        for edge in edges:
            y = (edge.y2 + edge.y1) // 2
            x1 = boundaries.get_x1_within_boundaries(y)
            x2 = boundaries.get_x2_within_boundaries(y)
            cutted_edges.append(
                BoundingBox(
                    edge.detected_object,
                    confidence=edge.confidence,
                    x1=x1,
                    x2=x2,
                    y1=edge.y1,
                    y2=edge.y2,
                    image_width=edge.image_width,
                    image_height=edge.image_height,
                )
            )

        return cutted_edges

    def combine_edges(self, edges: List[BoundingBox]) -> List[BoundingBox]:
        combined_edges = edges.copy()
        for index, edge in enumerate(edges):
            edge_center_norm = np.array([edge.center_normalized()[1]])
            if edge in combined_edges:
                for _other_index, other_edge in enumerate(edges, start=index):
                    if other_edge in combined_edges and edge != other_edge:
                        other_edge_center_norm = np.array(
                            [other_edge.center_normalized()[1]]
                        )
                        dist = np.linalg.norm(edge_center_norm - other_edge_center_norm)
                        # TODO: Make this distance dependent on position y!
                        if dist < (0.01 + other_edge.center_normalized()[0] / 6):
                            # Drop the higher edge -> y lower
                            if edge.center_y() < other_edge.center_y():
                                combined_edges.remove(edge)
                                # TODO: Merge them? -> Take average?
                                # This edge was removed, so it doesn't have to get checked
                                break
                            else:
                                combined_edges.remove(other_edge)

        return combined_edges

    def detect_edges(self, img: Any) -> List[BoundingBox]:
        img_width = img.shape[1]

        lines: List[Line] = self.line_detection.detect_lines(
            img,
            min_angle=-3,
            max_angle=3,
            min_line_length=0.65 * img_width,
            max_line_gap=0.08 * img_width,
        )

        image_logging.log("lines_raw.jpg", img_utils.render_lines(img.copy(), lines))

        edges: List[BoundingBox] = self.lines_to_bounding_boxes(img, lines)
        image_logging.log(
            "bounding_boxes_raw.jpg", img_utils.render_boxes(img.copy(), edges)
        )

        combined_edges = self.combine_edges(edges)
        logging.info("combined edges {}".format(combined_edges))
        image_logging.log(
            "bounding_boxes_combined.jpg",
            img_utils.render_boxes(img.copy(), combined_edges),
        )

        boundaries: Boundaries = self.boundary_detection.detect_boundaries(img)
        edges: List[BoundingBox] = self.cut_edges_to_boundaries(
            combined_edges, boundaries
        )
        image_logging.log(
            "bounding_boxes_cutted.jpg", img_utils.render_boxes(img.copy(), edges)
        )

        padded_edges = self.pad_edges(edges)

        image_logging.log(
            "padded_edges.jpg", img_utils.render_boxes(img.copy(), padded_edges)
        )

        return padded_edges

    def lines_to_bounding_boxes(self, img: Any, lines: List[Line]) -> List[BoundingBox]:
        return [
            BoundingBox(
                DetectedObject.edge,
                0.5,
                line.x1,
                line.x2,
                min(line.y1, line.y2),
                max(line.y1, line.y2) + 1,
                img.shape[1],
                img.shape[0],
            )
            for line in lines
        ]

    def pad_edges(self, boxes: List[BoundingBox]) -> List[BoundingBox]:
        expected_width_to_height_ratio = 25
        for box in boxes:
            logging.info(f"Box: {box}")
            width_to_height_ratio = box.width() / box.height()
            logging.info(f"width_to_height_ratio: {width_to_height_ratio}")

            if width_to_height_ratio > expected_width_to_height_ratio:
                padding = (
                    (width_to_height_ratio / float(expected_width_to_height_ratio))
                    * box.height()
                    / 2
                )
                logging.info(f"padding: {padding}")

                box.y1 = max(box.y1 - padding, 0)
                box.y2 = min(box.y2 + padding, box.image_width)
                logging.info(f"box: {box}")

        return boxes
