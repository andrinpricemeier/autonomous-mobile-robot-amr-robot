import logging.config
from fake_speaker import FakeSpeaker
from pictogram_detection import PictogramDetection
from edge_detection import EdgeDetection

import image_logging
from tests.preparation import get_filename, get_triton_object_detection_from_config
from movement import Movement
from fake_camera import FakeCamera
import cv2
from tinyk_serial import DummyUART
from navigation import Navigation
from tinyk import FakeTinyK
import pytest
import os
import sys
import inspect
from stairs_positioner import FinetuneStairsPositionerStrategy

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


def object_detection():
    image_logging.configure("robot.conf")
    logging.config.fileConfig(fname="logger.conf")
    yield get_triton_object_detection_from_config("robot.conf")


def test_fine_stairs_positioner_stairs_left_1(object_detection):
    fake_camera = FakeCamera()
    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_left_1.jpg")
        )
    )

    fine_positioner_strategy = FinetuneStairsPositionerStrategy(
        EdgeDetection(object_detection),
        fake_camera,
        Navigation(FakeTinyK(DummyUART()), FakeSpeaker()),
        135
    )

    position = fine_positioner_strategy.get_position(
        fine_positioner_strategy.edge_detection.detect_edges(
            fake_camera.take_picture(), 0.1
        )
    )
    assert position < 0
    assert fine_positioner_strategy.is_left(position)


test_fine_stairs_positioner_stairs_left_1(object_detection())
