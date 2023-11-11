import cv2
import os, sys, inspect, glob

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from pytorch_object_detection import PyTorchObjectDetection
from detected_object import DetectedObject
from bounding_box import BoundingBox


def extract_steps(images_folder: str, output_folder: str, prefix: str) -> None:
    od = PyTorchObjectDetection("../models/yolov5-4.0", "../models/weights.pt")
    images = glob.glob(f"{images_folder}/*.jpg")
    counter = 0
    for image in images:
        img = cv2.imread(image)
        result = od.detect(img, confidence=0.7)
        steps_box = next(
            iter(
                [obj for obj in result if obj.detected_object == DetectedObject.steps]
            ),
            None,
        )
        if steps_box is not None:
            steps = steps_box.extract(img)
            try:
                cv2.imwrite(f"{output_folder}/{prefix}{counter}.jpg", steps)
                counter = counter + 1
            except:
                print("FAILED" + image)


extract_steps(
    images_folder="C:/Temp/annotate_this",
    output_folder="C:/Temp/steps_only",
    prefix="steps-only-",
)
