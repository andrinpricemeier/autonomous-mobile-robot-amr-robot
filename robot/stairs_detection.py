from object_detection import ObjectDetection
from detected_object import DetectedObject
from typing import Any, List
from bounding_box import (
    BoundingBox,
    get_bounding_boxes_of_object,
    get_bounding_box_of_highest_confidence,
)


class StairsDetection:
    """Object detection specialized for detecting stairs.
    """
    def __init__(self, object_detection: ObjectDetection) -> None:
        """Creates a new instance.

        Args:
            object_detection (ObjectDetection): the underlying object detection to use.
        """
        self.object_detection = object_detection

    def detect_stairs(self, image: Any) -> BoundingBox:
        """Detects the stairs.

        Args:
            image (Any): the camera image.

        Returns:
            BoundingBox: the detected stairs.
        """
        boxes = self.object_detection.detect(image, confidence=0.3)
        return self.__get_stairs(boxes)

    def __get_stairs(self, boxes: List[BoundingBox]) -> BoundingBox:
        possible_steps: List[BoundingBox] = get_bounding_boxes_of_object(
            boxes, DetectedObject.stairs
        )
        return get_bounding_box_of_highest_confidence(possible_steps)
