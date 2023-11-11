from detected_object import DetectedObject
from typing import Any, List
from bounding_box import BoundingBox
import logging


class ObjectDetectionEvaluator:
    """Evaluates the results of an object detection process based on certain criteria.
    """
    def get_best_detections(
        self, detections: List[List[BoundingBox]]
    ) -> List[BoundingBox]:
        pass

class MaxObjectsCountObjectDetectionEvaluator(ObjectDetectionEvaluator):
    """
    This evaluator chooses the detections with the heighest count of these objects.
    """

    def __init__(self, objects: List[DetectedObject]) -> None:
        self.objects = objects
        logging.debug(
            "MaxObjectCountObjectDetectionEvaluator with objects: {}".format(
                self.objects
            )
        )

    def get_best_detections(
        self, detections: List[List[BoundingBox]]
    ) -> List[BoundingBox]:
        count_of_objects = [
            len([box for box in boxes if box.detected_object in self.objects])
            for boxes in detections
        ]
        logging.info("MaxObjectsCountObjectDetectionEvaluator - count_of_objects {}".format(count_of_objects))
        return detections[count_of_objects.index(max(count_of_objects))]