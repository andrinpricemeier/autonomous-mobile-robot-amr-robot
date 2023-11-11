from object_detection import ObjectDetection
from detected_object import DetectedObject
from bounding_box import BoundingBox
from typing import Any, List
import image_logging
import img_utils

class PictogramDetection:
    """The object detection specialized for detecting pictograms.
    """
    def __init__(self, object_detection: ObjectDetection) -> None:
        """Creates a new instance.

        Args:
            object_detection (ObjectDetection): the underlying object detection to use.
        """
        self.pictograms = [
            DetectedObject.hammer,
            DetectedObject.taco,
            DetectedObject.ruler,
            DetectedObject.bucket,
            DetectedObject.pencil,
            DetectedObject.wrench,
        ]
        self.object_detection = object_detection

    def are_target_pictograms_visible(self, image: Any) -> bool:
        """Checks whether the target pictograms are visible.

        Args:
            image (Any): the current camera image.

        Returns:
            bool: True if the target pictograms are visible.
        """
        pictograms = self.__find_pictograms(image, 0.2)
        image_logging.log(
            "detected_target_from_start_area_pictograms.jpg", img_utils.render_boxes(image, pictograms)
        )
        return len(pictograms) >= 2

    def find_closest_in_distance(self, image: Any) -> BoundingBox:
        """Returns the pictogram closest in distance.
        This is necessary to figure out whether a pictogram is in the start or target area.

        Args:
            image (Any): the camera image.

        Returns:
            BoundingBox: the pictogram closest in distance.
        """
        pictograms = self.__find_pictograms(image)
        closest: BoundingBox = None
        for pictogram in pictograms:
            if closest is None or pictogram.area_absolute() > closest.area_absolute():
                closest = pictogram
        return closest

    def find_central(self, image: Any) -> BoundingBox:
        """Finds the pictogram in the center of the camera.

        Args:
            image (Any): the camera image.

        Returns:
            BoundingBox: the pictogram in the center.
        """
        pictograms: List[BoundingBox] = self.__find_pictograms(image)

        relative_pictogram_widths: List[float] = [pictogram.center_u_normalized() for pictogram in pictograms]

        if len(relative_pictogram_widths) < 1:
            return None
            
        # It can be a half an average pictogram shifted and will still be detected as a center pictogram
        abs_distance_to_center: float = 0.5 * (sum(relative_pictogram_widths) / len(relative_pictogram_widths))
        central: BoundingBox = None
        for pictogram in pictograms:
            if (
                pictogram.abs_distance_to_center() < abs_distance_to_center
                and pictogram.area_normalized() > 0.01
            ):
                central = pictogram
                abs_distance_to_center = pictogram.abs_distance_to_center()
        return central

    def __find_pictograms(self, image: Any, confidence=0.6) -> List[BoundingBox]:
        boxes = self.object_detection.detect(image, confidence=confidence)
        return [obj for obj in boxes if self.__is_pictogram(obj)]

    def __is_pictogram(self, box: BoundingBox) -> bool:
        return box.detected_object in self.pictograms
