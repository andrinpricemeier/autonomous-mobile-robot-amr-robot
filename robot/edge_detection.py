from object_detection import ObjectDetection
from detected_object import DetectedObject
from typing import Any, List

from classic_edge_detection import ClassicEdgeDetection

from bounding_box import (
    BoundingBox,
    get_bounding_boxes_of_object,
)

import image_logging
import img_utils
import numpy as np


class EdgeDetection:
    def __init__(self, object_detection: ObjectDetection) -> None:
        self.object_detection = object_detection
        self.classic_detection: ClassicEdgeDetection = ClassicEdgeDetection()

    def detect_edges(
        self, image: Any, min_width_normalized: float = 0.5, confidence: float = 0.2
    ) -> List[BoundingBox]:
        edges_od = self.get_edges(
            self.object_detection.detect(image, confidence=confidence),
            min_width_normalized,
        )

        image_logging.log("edges_od.jpg", img_utils.render_boxes(image, edges_od))
        return edges_od

    def get_edges(
        self, boxes: List[BoundingBox], min_width_normalized: float
    ) -> List[BoundingBox]:
        edges = get_bounding_boxes_of_object(boxes, DetectedObject.edge)

        return [edge for edge in edges if edge.width_normalized() > min_width_normalized]