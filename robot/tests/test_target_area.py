import os, sys, inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from pictogram_detection import PictogramDetection
from tinyk_serial import DummyUART
from tinyk import FakeTinyK, RobotPosition
from navigation import Navigation
import cv2
import pytest
from fake_camera import FakeCamera
from target_area import TargetArea, TargetDirection
from bounding_box import BoundingBox
from tests.preparation import get_triton_object_detection_from_config, get_filename
from fake_speaker import FakeSpeaker
from detected_object import DetectedObject
import logging.config
import image_logging


@pytest.fixture()
def target_pictogram_detection():
    image_logging.configure("robot.conf")
    logging.config.fileConfig(fname="logger.conf")
    object_detection = get_triton_object_detection_from_config(
        fname=get_filename("robot.conf")
    )
    yield PictogramDetection(object_detection)


def target_area_1(target_pictogram_detection) -> TargetArea:
    pictogram_order = [
        DetectedObject.hammer,
        DetectedObject.ruler,
        DetectedObject.bucket,
        DetectedObject.taco,
        DetectedObject.wrench,
    ]
    return TargetArea(
        Navigation(FakeTinyK(DummyUART()), FakeSpeaker()),
        FakeCamera(),
        FakeSpeaker(),
        target_pictogram_detection,
        pictogram_order,
        40,
        10,
        15
    )


def test_central_pictogram_1(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_1.png"))
    )
    pictogram = target_area.get_central_pictogram()
    assert pictogram.detected_object == DetectedObject.ruler


def test_central_pictogram_2(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_2.png"))
    )
    pictogram = target_area.get_central_pictogram()
    assert pictogram.detected_object == DetectedObject.bucket


def test_central_pictogram_3(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_3.png"))
    )
    pictogram = target_area.get_central_pictogram()
    assert pictogram.detected_object == DetectedObject.bucket


def test_central_pictogram_4(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_4.png"))
    )
    pictogram = target_area.get_central_pictogram()
    assert pictogram.detected_object == DetectedObject.bucket


def test_central_pictogram_5(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_5.png"))
    )
    pictogram = target_area.get_central_pictogram()
    assert pictogram.detected_object == DetectedObject.bucket


def test_get_target_direction_1_target_bucket(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.bucket
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_1.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.right
    assert movement_in_cm == 15


def test_get_target_direction_1_target_hammer(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.hammer
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_1.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.left
    assert movement_in_cm == 15


def test_get_target_direction_1_target_ruler(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.hammer
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_1.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.left
    # TODO: Check distance


def test_get_target_direction_1_target_taco(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.taco
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_1.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.right
    assert movement_in_cm == 30


def test_get_target_direction_1_target_wrench(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.wrench
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_1.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.right
    assert movement_in_cm == 45


def test_get_target_direction_2_target_bucket(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.bucket
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_2.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.right
    # TODO: Check distance


def test_get_target_direction_2_target_hammer(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.hammer
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )

    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_2.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.left
    assert movement_in_cm == 30


def test_get_target_direction_2_target_ruler(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.ruler
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_2.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.left
    assert movement_in_cm == 15


def test_get_target_direction_2_target_taco(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.taco
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_2.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.right
    assert movement_in_cm == 15


def test_get_target_direction_2_target_wrench(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.wrench
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_2.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.right
    assert movement_in_cm == 30


def test_get_target_direction_3_target_bucket(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.bucket
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_3.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.right
    # TODO: Check distance


def test_get_target_direction_4_target_bucket(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.bucket
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_4.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.forward
    # TODO: Check distance


def test_get_target_direction_5_target_bucket(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.bucket
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_5.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.right
    # TODO: Check distance


def test_get_target_direction_6_target_bucket(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.bucket
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_6.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.forward
    # TODO: Check distance


def test_get_target_direction_7_target_bucket(target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.bucket
    target_area.target_pictogram_position = target_area.pictogram_order.index(
        target_area.target_pictogram
    )
    target_area.camera.add_image(
        cv2.imread(get_filename("tests/camera_images/target_area/target_area_1_7.png"))
    )
    pictogram = target_area.get_central_pictogram()
    direction, movement_in_cm = target_area.get_target_direction(pictogram)
    assert direction == TargetDirection.forward
    # TODO: Check distance


def test_target_area_1(mocker, target_pictogram_detection):
    target_area = target_area_1(target_pictogram_detection)
    target_area.target_pictogram = DetectedObject.bucket

    for i in range(1, 8):
        target_area.camera.add_image(
            cv2.imread(
                get_filename(f"tests/camera_images/target_area/target_area_1_{i}.png")
            )
        )

    spy_navigation_move_right = mocker.spy(
        target_area.navigation, "move_sideways_right"
    )
    spy_navigation_move_left = mocker.spy(target_area.navigation, "move_sideways_left")
    spy_navigation_move_forward = mocker.spy(target_area.navigation, "move_forward")
    spy_navigation_move_to_position = mocker.spy(
        target_area.navigation, "move_to_position"
    )

    spy_speaker = mocker.spy(target_area.speaker, "announce_target")

    target_area.move_to_target_flag()

    spy_navigation_move_left.assert_has_calls([])
    spy_navigation_move_forward.assert_has_calls(
        [mocker.call(14), mocker.call(41)]
    )

    spy_navigation_move_to_position.assert_has_calls(
        [
            mocker.call(RobotPosition.stand_up),
            mocker.call(RobotPosition.hit_target_pictogram),
        ]
    )
    spy_speaker.assert_called_once_with(DetectedObject.bucket)
    # Just check if if was called 4 times, since the actual distance is non deterministic because of the object detection
    assert spy_navigation_move_right.call_count == 4
