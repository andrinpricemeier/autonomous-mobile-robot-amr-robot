from detected_object import DetectedObject
import cv2
from bounding_box import BoundingBox
from typing import List, Any
from triton_client import TritonClient
import numpy as np
from object_detection import ObjectDetection
import img_utils
import time
import logging

class TensorRTObjectDetection(ObjectDetection):
    """Reponsible for detecting objects using a TensorRT engine and the Triton server.

    Args:
        ObjectDetection ([type]): the superclass.
    """
    def __init__(self, client: TritonClient, warmup_image_path: str) -> None:
        """Creates a new instance.

        Args:
            client (TritonClient): the client to use for communicating with the Triton server.
            warmup_image_path (str): the image to use for warming up the object detection since at first it's always a bit slow.
        """
        self.client = client
        self.warmup_image_path = warmup_image_path
        warmup_image = cv2.imread(self.warmup_image_path)
        self.__check_server(warmup_image)
        self.__warmup(5, warmup_image)

    def __warmup(self, count: int, warmup_image: Any) -> None:
        logging.debug("Warming up Triton server.")
        for i in range(count):
            logging.debug(f"Warmup {i}.")
            self.detect(warmup_image)
        logging.debug("Warming up completed.")

    def __check_server(self, warmup_image: Any) -> None:   
        logging.debug("Checking if the Triton server is up and running.")
        wait_in_seconds = 5
        number_of_tries = 20
        while number_of_tries > 0:
            try:
                self.detect(warmup_image)
                logging.debug("Object detection is ready.")
                # No error means we're ready.
                break
            except KeyboardInterrupt:
                raise
            except Exception:
                time.sleep(wait_in_seconds)
                number_of_tries -= 1
        if number_of_tries == 0:
            logging.error("Triton server isn't ready. Object detection won't work.")

    def detect(
        self, image: Any, confidence: float = 0.8, nms: float = 0.5
    ) -> List[BoundingBox]:     
        np.random.seed(0)
        cv2.setRNGSeed(0)
        logging.debug("TensorRTObjectDetection starting detection.")
        height, width, _ = image.shape
        resized_image = img_utils.resize(image, 640, 640)
        preprocessed_image = self.__preprocess(resized_image)
        input_image_buffer = np.expand_dims(preprocessed_image, axis=0)
        result = self.client.infer(input_image_buffer, 640, 640)
        resized_bounding_boxes = self.__postprocess(result, 640, 640, confidence, nms)
        logging.debug("TensorRTObjectDetection detection finished.")
        return [obj.unpad(width, height) for obj in resized_bounding_boxes]

    def __preprocess(self, image: Any) -> Any:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = np.transpose(np.array(image, dtype=np.float32, order="C"), (2, 0, 1))
        image /= 255.0
        return image

    def __xywh2xyxy(self, x):
        """
        description:    Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
        param:
            x:          A boxes tensor, each row is a box [center_x, center_y, w, h]
        return:
            y:          A boxes tensor, each row is a box [x1, y1, x2, y2]
        """
        y = np.zeros_like(x)
        y[:, 0] = x[:, 0] - x[:, 2] / 2
        y[:, 2] = x[:, 0] + x[:, 2] / 2
        y[:, 1] = x[:, 1] - x[:, 3] / 2
        y[:, 3] = x[:, 1] + x[:, 3] / 2
        return y
    
    def __nms_boxes(self, boxes, box_confidences, nms_threshold):
        x_coord = boxes[:, 0]
        y_coord = boxes[:, 1]
        width = boxes[:, 2]
        height = boxes[:, 3]

        areas = width * height
        ordered = box_confidences.argsort()[::-1]

        keep = list()
        while ordered.size > 0:
            # Index of the current element:
            i = ordered[0]
            keep.append(i)
            xx1 = np.maximum(x_coord[i], x_coord[ordered[1:]])
            yy1 = np.maximum(y_coord[i], y_coord[ordered[1:]])
            xx2 = np.minimum(x_coord[i] + width[i], x_coord[ordered[1:]] + width[ordered[1:]])
            yy2 = np.minimum(y_coord[i] + height[i], y_coord[ordered[1:]] + height[ordered[1:]])

            width1 = np.maximum(0.0, xx2 - xx1 + 1)
            height1 = np.maximum(0.0, yy2 - yy1 + 1)
            intersection = width1 * height1
            union = (areas[i] + areas[ordered[1:]] - intersection)
            iou = intersection / union
            indexes = np.where(iou <= nms_threshold)[0]
            ordered = ordered[indexes + 1]

        keep = np.array(keep)
        return keep

    def __postprocess(
        self,
        buffer: Any,
        image_width: float,
        image_height: float,
        conf_threshold: float = 0.5,
        nms_threshold: float = 0.5,
    ) -> List[BoundingBox]:
        output2 = buffer[0]
        output = output2[0:6001]
        # Get the num of boxes detected
        num = int(output[0])
        # Reshape to a two dimensional ndarray
        pred = np.reshape(output[1:], (-1, 6))[:num, :]
        # Get the boxes
        boxes = pred[:, :4]
        # Get the scores
        scores = pred[:, 4]
        # Get the classes
        classid = pred[:, 5]
        # Choose those boxes that score > CONF_THRESH
        si = scores > conf_threshold
        boxes = boxes[si, :]
        scores = scores[si]
        classid = classid[si]
        nms_boxes = np.zeros((0, 4), dtype=boxes.dtype)
        nms_scores = np.zeros(0, dtype=scores.dtype)
        nms_classid = np.zeros(0, dtype=classid.dtype)
        for class_id in set(classid):
            idxs = np.where(classid == class_id)
            clsboxes = boxes[idxs]
            clsscores = scores[idxs]
            clsclassid = classid[idxs]
            keep = self.__nms_boxes(clsboxes, clsscores, nms_threshold)
            nms_boxes = np.concatenate([nms_boxes, clsboxes[keep]], axis=0)
            nms_scores = np.concatenate([nms_scores, clsscores[keep]], axis=0)
            nms_classid = np.concatenate([nms_classid, clsclassid[keep]], axis=0)
        realboxes = self.__xywh2xyxy(nms_boxes)
        detected_objects = []
        for box, score, label in zip(realboxes, nms_scores, nms_classid):
            detected_objects.append(BoundingBox(DetectedObject(label), score, box[0], box[2], box[1], box[3], image_height, image_width))
        return detected_objects