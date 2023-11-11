from enum import Enum
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
import heapq
from graphviz import Digraph
import os, sys, inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from detected_object import DetectedObject
from bounding_box import get_bounding_boxes_of_object
import img_utils
import logging.config
import logging
import image_logging
from tests.preparation import get_triton_object_detection_from_config
image_logging.configure(fname="../robot.conf")
logging.config.fileConfig(fname="../logger.conf")

img = cv2.imread("../tests/camera_images/path/path_2.jpg")
triton_single = get_triton_object_detection_from_config("../robot.conf")
result = triton_single.detect(img, confidence=0.4)
cv2.imwrite("output.jpg", img_utils.render_boxes(img, result))
