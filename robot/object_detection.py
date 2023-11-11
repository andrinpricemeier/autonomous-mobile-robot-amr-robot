from bounding_box import BoundingBox
from typing import Any, List
import numpy as np


class ObjectDetection:
    """Represents the interface for the object detection.
    """
    np.random.seed(0)
    RAND_COLORS = np.random.randint(50, 255, (64, 3), "int")
    RAND_COLORS[0] = [220, 220, 220]

    def detect(
        self, image: Any, confidence: float = 0.8, nms: float = 0.5
    ) -> List[BoundingBox]:
        """Detects the objects on the given image.

        Args:
            image (Any): the image to detect objects on.
            confidence (float, optional): the confidence below which to filter out objects. Defaults to 0.8.
            nms (float, optional): the non-max suppression threshold. Basically the value for the intersection-over-union over which objects get removed. Defaults to 0.5.

        Returns:
            List[BoundingBox]: the detected objects.
        """
        pass
