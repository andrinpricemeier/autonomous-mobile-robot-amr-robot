import logging.config
from typing import Any

from callee.operators import LessThan
from fake_speaker import FakeSpeaker
from stairs_detection import StairsDetection
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
from stairs_positioner import (
    FinetuneStairsPositionerStrategy,
    RoughStairsPositionerStrategy,
)
from callee import GreaterThan

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


@pytest.fixture()
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


def test_fine_stairs_positioner_stairs_left_2(object_detection):
    fake_camera = FakeCamera()
    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_left_2.jpg")
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


def test_fine_stairs_positioner_stairs_right_1(object_detection):
    fake_camera = FakeCamera()
    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_right_1.jpg")
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
    assert position > 0
    assert fine_positioner_strategy.is_right(position)


def test_fine_stairs_positioner_stairs_right_2(object_detection):
    fake_camera = FakeCamera()
    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_right_2.jpg")
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
    assert position > 0
    assert fine_positioner_strategy.is_right(position)


def test_rough_stairs_positioner_3_movements(mocker, object_detection):
    max_movements = 3

    fake_camera = FakeCamera()
    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_left_1.jpg")
        )
    )

    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_left_2.jpg")
        )
    )

    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_right_1.jpg")
        )
    )

    rough_positioner_strategy = RoughStairsPositionerStrategy(
        StairsDetection(object_detection),
        PictogramDetection(object_detection),
        fake_camera,
        Navigation(FakeTinyK(DummyUART()), FakeSpeaker()),
        0.15,
        150
    )

    spy_navigation_move_left = mocker.spy(
        rough_positioner_strategy.navigation, "move_sideways_left"
    )
    spy_navigation_move_right = mocker.spy(
        rough_positioner_strategy.navigation, "move_sideways_right"
    )
    spy_navigation_move_backwards = mocker.spy(
        rough_positioner_strategy.navigation, "move_backwards"
    )

    rough_positioner_strategy.move_to_center(max_movements)

    spy_navigation_move_backwards.assert_has_calls([])
    spy_navigation_move_left.assert_called_with(GreaterThan(10), GreaterThan(10))
    spy_navigation_move_right.assert_called_with(GreaterThan(5))


def test_fine_tune_stairs_positioner_3_movements(mocker, object_detection):
    max_movements = 3

    fake_camera = FakeCamera()
    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_left_1.jpg")
        )
    )

    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_left_2.jpg")
        )
    )

    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_right_1.jpg")
        )
    )

    fine_positioner_strategy = FinetuneStairsPositionerStrategy(
        EdgeDetection(object_detection),
        fake_camera,
        Navigation(FakeTinyK(DummyUART()), FakeSpeaker()),
        135
    )

    spy_navigation_move_left = mocker.spy(
        fine_positioner_strategy.navigation, "move_sideways_left"
    )
    spy_navigation_move_right = mocker.spy(
        fine_positioner_strategy.navigation, "move_sideways_right"
    )
    spy_navigation_move_backwards = mocker.spy(
        fine_positioner_strategy.navigation, "move_backwards"
    )

    fine_positioner_strategy.move_to_center(max_movements)

    assert spy_navigation_move_left.call_count == 2
    assert spy_navigation_move_right.call_count == 1
    assert spy_navigation_move_backwards.call_count == 0


def test_fine_stairs_positioner_move_sideways_tilted_right(mocker, object_detection):
    fake_camera = FakeCamera()
    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/stairs_positioner/stairs_right_2.jpg")
        )
    )

    fine_positioner_strategy = FinetuneStairsPositionerStrategy(
        EdgeDetection(object_detection),
        fake_camera,
        Navigation(FakeTinyK(DummyUART()), FakeSpeaker()),
        135
    )
    image: Any = fake_camera.take_picture()

    spy_navigation_rotate_sideways = mocker.spy(
        fine_positioner_strategy.navigation, "rotate_sideways"
    )

    fine_positioner_strategy.rotate_sideways(
        fine_positioner_strategy.get_average_edge_angle(
            fine_positioner_strategy.edge_detection.detect_edges(image, 0.1), image
        )
    )

    spy_navigation_rotate_sideways.assert_called_with(GreaterThan(0))
