from detected_object import DetectedObject
from typing import List
from bounding_box import BoundingBox
from object_detection import ObjectDetection
import torch
import img_utils


class PyTorchObjectDetection(ObjectDetection):
    """Implements the ObjectDetection interface using a PyTorch implementation.
    Useful for testing the object detection on the laptop.

    Args:
        ObjectDetection ([type]): the superclass.
    """
    def __init__(self, model_path, weights_path):
        self.model_path = model_path
        self.weights_path = weights_path

    def detect(self, image, confidence=0.8, nms=0.5) -> List[BoundingBox]:
        model = torch.hub.load(
            self.model_path, "custom", path_or_model=self.weights_path, source="local"
        )
        model.eval()
        height, width, _ = image.shape
        resized_image = img_utils.resize(image, 640, 640)
        results = model(resized_image, size=640)
        resized_boundingboxes = [
            BoundingBox(
                DetectedObject(obj[5].item()),
                obj[4].item(),
                obj[0].item(),
                obj[2].item(),
                obj[1].item(),
                obj[3].item(),
                640,
                640,
            )
            for obj in results.pred[0]
            if obj[4].item() >= confidence
        ]
        return [obj.unpad(width, height) for obj in resized_boundingboxes]