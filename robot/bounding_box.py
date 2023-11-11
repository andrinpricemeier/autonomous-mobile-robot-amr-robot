from typing import Any, List, Tuple
from detected_object import DetectedObject


class BoundingBox:
    """Represents the bounding box a detected object.
    """
    def __init__(
        self,
        detected_object: DetectedObject,
        confidence: float,
        x1: int,
        x2: int,
        y1: int,
        y2: int,
        image_width: int,
        image_height: int,
    ) -> None:
        self.detected_object = detected_object
        self.confidence = confidence
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.u1 = x1 / image_width
        self.u2 = x2 / image_width
        self.v1 = y1 / image_height
        self.v2 = y2 / image_height
        self.image_width = image_width
        self.image_height = image_height

    def box(self) -> Tuple[int, int, int, int]:
        """The coordinates of the bounding box.

        Returns:
            Tuple[int, int, int, int]: The x1, y1, x2 and y2 coordinates.
        """
        return (self.x1, self.y1, self.x2, self.y2)

    def width(self) -> int:
        """The absolute width of the bounding box.

        Returns:
            int: the width in pixels.
        """
        return self.x2 - self.x1

    def width_normalized(self) -> float:
        """The normalized width of the bounding box.
        E.g. if the entire image width is 100 and the bounding box's width
        is 10, the normalized width would be 0.10 (10%).

        Returns:
            float: the normalized width.
        """
        return self.u2 - self.u1

    def height(self) -> int:
        """The absolute height of the bounding box.

        Returns:
            int: the height in pixels.
        """
        return self.y2 - self.y1

    def height_normalized(self) -> float:
        """The normalized height of the bounding box.
        E.g. if the height of the image is 100 pixels and the bounding box is 10 pixels tall,
        the normalized height would be 0.10 (10%).

        Returns:
            float: the normalized height.
        """
        return self.v2 - self.v1

    def center_absolute(self) -> Tuple[float, float]:
        """The center of the bounding box.

        Returns:
            Tuple[float, float]: the center x and center y of the bounding box.
        """
        return (self.center_x(), self.center_y())

    def center_x(self) -> float:
        """The x coordinates of the center of the bounding box.

        Returns:
            float: the x coordinates of the center.
        """
        return 0.5 * (self.x1 + self.x2)

    def center_y(self) -> float:
        """The y coordinates of the center of the bounding box.

        Returns:
            float: the y coordinates of the center.
        """
        return 0.5 * (self.y1 + self.y2)

    def center_u_normalized(self) -> float:
        """The normalized x coordinates of the center of the bounding box.

        Returns:
            float: The normalized x coordinates of the center.
        """
        return 0.5 * (self.u1 + self.u2)

    def center_v_normalized(self) -> float:
        """The normalized y coordinates of the center of the bounding box.

        Returns:
            float: The normalized y coordinates of the center.
        """
        return 0.5 * (self.v1 + self.v2)

    def center_normalized(self) -> Tuple[float, float]:
        """The normalized center of the bounding box.

        Returns:
            Tuple[float, float]: The x and y coordinates of the center.
        """
        return (self.center_u_normalized(), self.center_v_normalized())

    def size_absolute(self) -> Tuple[int, int]:
        """The absolute width and height of the bounding box.

        Returns:
            Tuple[int, int]: The absolute width and height of the bounding box.
        """
        return (self.x2 - self.x1, self.y2 - self.y1)

    def size_normalized(self) -> Tuple[float, float]:
        """The normalized width and height of the bounding box.

        Returns:
            Tuple[float, float]: the width and height, normalized.
        """
        return (self.u2 - self.u1, self.v2 - self.v1)

    def area_absolute(self) -> float:
        """The area of the bounding box in pixels.

        Returns:
            float: the area.
        """
        return self.width() * self.height()

    def area_normalized(self) -> float:
        """The normalized area of the bounding box.

        Returns:
            float: the normalized area.
        """
        return (self.width() * self.height()) / (self.image_width * self.image_height)

    def is_to_the_right(self, epsilon: float = 0.05) -> bool:
        """Whether the bounding box is more to the right in the image.

        Args:
            epsilon (float, optional): The error margin for what it means to be in the center. Defaults to 0.05.

        Returns:
            bool: True if the object is more to the right.
        """
        (center_x, _) = self.center_normalized()
        return center_x > 0.5 and not self.is_in_center_x(epsilon)

    def is_to_the_left(self, epsilon: float = 0.05) -> bool:
        """Whether the bounding box is more to the left in the image.

        Args:
            epsilon (float, optional): The error margin for what it means to be in the center. Defaults to 0.05.

        Returns:
            bool: True if the object is more to the left.
        """
        (center_x, _) = self.center_normalized()
        return center_x < 0.5 and not self.is_in_center_x(epsilon)

    def is_in_center_x(self, epsilon: float = 0.05) -> bool:
        """Whether the object is in the center.

        Args:
            epsilon (float, optional): The error margin for what it means to be in the center. Defaults to 0.05.

        Returns:
            bool: True if the object is in the center.
        """
        (center_x, _) = self.center_normalized()
        return center_x <= 0.5 + epsilon and center_x >= 0.5 - epsilon

    def distance_to_center(self) -> float:
        """The normalized distance to the center.

        Returns:
            float: the distance to the center.
        """
        (center_x, _) = self.center_normalized()
        return center_x - 0.5

    def abs_distance_to_center(self) -> float:
        """The absolute distance to the center.

        Returns:
            float: the distance to the center.
        """
        return abs(self.distance_to_center())

    def extract(self, image: Any) -> Any:
        """Extract the bounding box from the original image into its own image.

        Args:
            image (Any): the original image on which the bounding box was detected.

        Returns:
            Any: The extracted image of the object only.
        """
        until_y = int(self.y1 + self.height())
        until_x = int(self.x1 + self.width())
        return image[int(self.y1) : until_y, int(self.x1) : until_x].copy()

    def unpad(self, original_width: float, original_height: float) -> Any:
        """Resizes the bounding box in such a way that its coordinates are correct in respect to the original
        image used for object detection.
        This is necessary because the object detection uses differently sized images internally since that's
        what the ML model was trained with. The user of the object detection should not know that though.

        Args:
            original_width (float): the width of the original image.
            original_height (float): the height of the original image.

        Returns:
            Any: the corrected bounding box.
        """
        # Assume we have been center padded by imgaug
        new_x1 = 0
        new_x2 = 0
        new_y1 = 0
        new_y2 = 0
        if original_width > original_height:
            padding = (original_width - original_height) / 2
            width_ratio = self.image_width / original_width
            new_x1 = self.x1 / width_ratio
            new_x2 = self.x2 / width_ratio
            new_y1 = (self.y1 / width_ratio) - padding
            new_y2 = (self.y2 / width_ratio) - padding
        else:
            padding = (original_height - original_width) / 2
            height_ratio = self.image_height / original_height
            new_x1 = (self.x1 / height_ratio) - padding
            new_x2 = (self.x2 / height_ratio) - padding
            new_y1 = self.y1 / height_ratio
            new_y2 = self.y2 / height_ratio
        return BoundingBox(
            self.detected_object,
            self.confidence,
            new_x1,
            new_x2,
            new_y1,
            new_y2,
            original_width,
            original_height,
        )

    def __str__(self) -> str:
        """The string representation of this bounding box.

        Returns:
            str: the string representation.
        """
        return "[{0}] x1: {1}, x2: {2}, y1: {3}, y2: {4} confidence: {5}".format(
            self.detected_object, self.x1, self.x2, self.y1, self.y2, self.confidence
        )


def get_bounding_boxes_of_object(
    boxes: List[BoundingBox], object: DetectedObject
) -> List[BoundingBox]:
    """Retrieves all bounding boxes of a certain type.

    Args:
        boxes (List[BoundingBox]): the boxes to filter
        object (DetectedObject): the type of object to match.

    Returns:
        List[BoundingBox]: all boxes that match the filter.
    """
    return [box for box in boxes if box.detected_object == object]


def get_bounding_box_of_highest_confidence(boxes: List[BoundingBox]) -> BoundingBox:
    """Gets the bounding box with the highest confidence.

    Args:
        boxes (List[BoundingBox]): all boxes.

    Returns:
        BoundingBox: the box with the highest confidence.
    """
    max_confidence = 0
    max_box = None

    for box in boxes:
        if box.confidence > max_confidence:
            max_confidence = box.confidence
            max_box = box

    return max_box

def where_confidence_is_higher_than(detection_list: List[List[BoundingBox]], min_confidence: float) -> List[List[BoundingBox]]:
    """Gets all bounding boxes with a confidence higher than specified.

    Args:
        detection_list (List[List[BoundingBox]]): all boxes.
        min_confidence (float): the minimum confidence, inclusive.

    Returns:
        List[List[BoundingBox]]: The filtered bounding boxes.
    """
    return [[box for box in boxes if box.confidence >= min_confidence] for boxes in detection_list]
