import os, sys, inspect


current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from bounding_box import BoundingBox, get_bounding_boxes_of_object
from detected_object import DetectedObject
import numpy as np
from sklearn.linear_model import LinearRegression
import img_utils
from pytorch_object_detection import PyTorchObjectDetection
import cv2
from matplotlib.pyplot import plot

od = PyTorchObjectDetection("../models/yolov5-4.0", "../models/weights.pt")
img = cv2.imread("images/jetson-pfad-00001.jpg")
result = od.detect(img, confidence=0.6)
steps_box = next(
    iter([obj for obj in result if obj.detected_object == DetectedObject.steps]), None
)
steps = steps_box.extract(img)
steps_boxes = od.detect(steps, confidence=0.4)

for box in steps_boxes:
    print(box.detected_object)

bricks = get_bounding_boxes_of_object(steps_boxes, DetectedObject.brick)
# edges = get_bounding_boxes_of_object(steps_boxes, DetectedObject.edge)

annotated_steps = img_utils.render_boxes(steps, steps_boxes)
cv2.imwrite("images/steps_annotated.jpg", annotated_steps)

# TODO: https://stackabuse.com/linear-regression-in-python-with-scikit-learn/

edges = [
    BoundingBox(
        DetectedObject.edge, 0.8, 26, 735, 340, 335, steps.shape[1], steps.shape[0]
    ),
    BoundingBox(
        DetectedObject.edge, 0.9, 68, 660, 235, 233, steps.shape[1], steps.shape[0]
    ),
    BoundingBox(
        DetectedObject.edge, 0.9, 95, 637, 153, 160, steps.shape[1], steps.shape[0]
    ),
    # BoundingBox(DetectedObject.edge, 0.9, 120, 591, 93, 103, steps.shape[1], steps.shape[0]),
    BoundingBox(
        DetectedObject.edge, 0.9, 139, 567, 47, 49, steps.shape[1], steps.shape[0]
    ),
    BoundingBox(
        DetectedObject.edge, 0.9, 158, 544, 9, 10, steps.shape[1], steps.shape[0]
    ),
]

missing_box = BoundingBox(
    DetectedObject.edge, 0.9, 120, 591, 93, 103, steps.shape[1], steps.shape[0]
)
print(
    "missing_box center_v_normalized {0} width {1}".format(
        missing_box.center_v_normalized(), missing_box.width()
    )
)

X = np.zeros([len(edges), 1])
y = np.zeros(len(edges))

for i in range(len(edges)):
    X[i, 0] = edges[i].center_v_normalized()
    y[i] = edges[i].width()

reg = LinearRegression().fit(X, y)
print(reg.score(X, y))

print(reg.predict(np.array([missing_box.center_v_normalized()]).reshape(1, -1)))
