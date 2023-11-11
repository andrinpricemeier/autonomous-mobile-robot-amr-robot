from object_detection import ObjectDetection
from detected_object import DetectedObject
from typing import Any, List
from best_of_k_object_detection import (
    MaxObjectsCountObjectDetectionEvaluator,
)

from bounding_box import (
    BoundingBox,
    get_bounding_boxes_of_object,
    where_confidence_is_higher_than
)

import image_logging
import img_utils
import logging

import numpy as np

class PathObjectDetectionResult:
    def __init__(self, boxes: List[List[BoundingBox]], image: Any):
        self.detected_boxes = boxes
        self.image = image

    def get_steps(self) -> BoundingBox:

        all_steps = get_bounding_boxes_of_object(MaxObjectsCountObjectDetectionEvaluator([DetectedObject.steps]).get_best_detections(where_confidence_is_higher_than(self.detected_boxes, 0.3)), DetectedObject.steps)
        
        if len(all_steps) == 0:
            return None

        return all_steps[0]

    def get_bricks(self) -> List[BoundingBox]:
        all_bricks = get_bounding_boxes_of_object(MaxObjectsCountObjectDetectionEvaluator([DetectedObject.brick]).get_best_detections(where_confidence_is_higher_than(self.detected_boxes, 0.35)), DetectedObject.brick)
        return self.remove_outliers(all_bricks)

    def get_edges(self, min_width_normalized: float = 0.5) -> List[BoundingBox]:
        all_edges = get_bounding_boxes_of_object(MaxObjectsCountObjectDetectionEvaluator([DetectedObject.edge]).get_best_detections(where_confidence_is_higher_than(self.detected_boxes, 0.1)), DetectedObject.edge)
        return self.__filter_edges(all_edges, min_width_normalized)

    def remove_outliers(self, boxes: List[BoundingBox]) -> List[BoundingBox]:
        return boxes

    def __filter_edges(self, edges: List[BoundingBox], min_width_normalized: float) -> List[BoundingBox]:
        # NMS can be pretty small, since edges should not intersect!
        return [edge for edge in edges if edge.width_normalized() > min_width_normalized]

    def __nms(
        self, boxes: List[BoundingBox], nms_threshold: float = 0.05
    ) -> List[BoundingBox]:
        x1_coord = np.array([box.x1 for box in boxes]).astype(int)
        x2_coord = np.array([box.x2 for box in boxes]).astype(int)
        y1_coord = np.array([box.y1 for box in boxes]).astype(int)
        y2_coord = np.array([box.y2 for box in boxes]).astype(int)

        areas = np.array([box.area_absolute() for box in boxes]).astype(int)
        ordered = np.array([box.confidence for box in boxes]).argsort()[::-1]
        keep = list()

        while ordered.size > 0:

            i = ordered[0]
            keep.append(i)

            xx1 = np.maximum(x1_coord[i], x1_coord[ordered[1:]])
            yy1 = np.maximum(y1_coord[i], y1_coord[ordered[1:]])
            xx2 = np.minimum(x2_coord[i], x2_coord[ordered[1:]])
            yy2 = np.minimum(y2_coord[i], y2_coord[ordered[1:]])
            width1 = np.maximum(0.0, xx2 - xx1 + 1)
            height1 = np.maximum(0.0, yy2 - yy1 + 1)

            intersection = width1 * height1
            union = areas[i] + areas[ordered[1:]] - intersection
            iou = intersection / union
            iou = np.nan_to_num(iou)

            indexes = np.where(iou <= nms_threshold)[0]
            ordered = ordered[indexes + 1]

        keep = np.array(keep).astype(int)
        return np.array(boxes)[keep].tolist()

class PathObjectDetection:
    def __init__(self, object_detection: ObjectDetection, k: int = 3) -> None:
        self.object_detection = object_detection
        self.k = k

    def detect(self, image: Any, confidence: float = 0.1) -> PathObjectDetectionResult:
        boxes = []
        boxes.append(self.object_detection.detect(image, confidence=confidence))
        image_logging.log(f"path_object_detection_detected.jpg", img_utils.render_boxes(image, boxes[0]))

        return PathObjectDetectionResult(boxes, image)

