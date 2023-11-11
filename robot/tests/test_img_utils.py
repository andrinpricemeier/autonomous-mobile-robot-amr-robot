from bounding_box import BoundingBox
from detected_object import DetectedObject
import img_utils
import cv2
import numpy as np
import os
import sys
import inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


def test_enable_img_utils():
    img_utils.set_rendering_enabled(True)
    image = cv2.imread(
        "tests/camera_images/path/Test_Treppe_Mitte_6_Backsteine_5_Stufen_Sackgasse.jpg"
    )
    assert img_utils.render_boxes(
        image, [BoundingBox(DetectedObject.brick, 0.5, 12, 14, 12, 14, 120, 230)]
    ) is not np.zeros((1, 1))


def test_disable_img_utils():
    img_utils.set_rendering_enabled(False)
    image = cv2.imread(
        "tests/camera_images/path/Test_Treppe_Mitte_6_Backsteine_5_Stufen_Sackgasse.jpg"
    )
    assert img_utils.render_boxes(
        image, [BoundingBox(DetectedObject.brick, 0.5, 12, 14, 12, 14, 120, 230)]
    ) == np.zeros((1, 1))
