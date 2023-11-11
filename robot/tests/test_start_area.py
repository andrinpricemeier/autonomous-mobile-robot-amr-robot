from edge_detection import EdgeDetection
from path_object_detection import PathObjectDetection
from tests.preparation import get_triton_object_detection_from_config, get_filename
from fake_speaker import FakeSpeaker
from start_area import StartArea
from fake_camera import FakeCamera
import pytest
import cv2
from navigation import FakeNavigation, Navigation, FakeNavigation, NavigationResult
from tinyk import TinyK
from tinyk_serial import DummyUART
from stairs_detection import StairsDetection
from pictogram_detection import PictogramDetection
import os
import sys
import inspect
import logging
import logging.config
import image_logging

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


@pytest.fixture()
def object_detection():
    logging.config.fileConfig(fname="logger.conf")
    image_logging.configure("robot.conf")
    return get_triton_object_detection_from_config(fname=get_filename("robot.conf"))


def test_is_pictogram_in_start_area_is_not_in_start_area(object_detection):
    pictogram_detection = PictogramDetection(object_detection)
    tinyK = TinyK(DummyUART())
    start_area = StartArea(
        Navigation(tinyK, FakeSpeaker()),
        FakeCamera(),
        EdgeDetection(object_detection),
        pictogram_detection,
        StairsDetection(object_detection),
        PathObjectDetection(object_detection),
        FakeSpeaker(),
        0.005,
        0.15,
        150,
        135
    )
    img = cv2.imread(
        get_filename(f"tests/camera_images/start_area/pictogram_not_in_start_area.jpg")
    )
    pictogram = pictogram_detection.find_closest_in_distance(img)
    assert not start_area.is_pictogram_in_start_area(pictogram)


def test_is_pictogram_in_start_area_is_in_start_area(object_detection):
    pictogram_detection = PictogramDetection(object_detection)
    tinyK = TinyK(DummyUART())
    start_area = StartArea(
        Navigation(tinyK, FakeSpeaker()),
        FakeCamera(),
        EdgeDetection(object_detection),
        pictogram_detection,
        StairsDetection(object_detection),
        PathObjectDetection(object_detection),
        FakeSpeaker(),
        0.005,
        0.15,
        150,
        135
    )
    img = cv2.imread(
        get_filename(f"tests/camera_images/start_area/pictogram_in_start_area.jpg")
    )
    pictogram = pictogram_detection.find_closest_in_distance(img)
    assert start_area.is_pictogram_in_start_area(pictogram)


def test_move_to_climbing_start_position(mocker, object_detection):
    pictogram_detection = PictogramDetection(object_detection)

    fake_camera = FakeCamera()
    fake_camera.add_image(
        cv2.imread(
            get_filename(f"tests/camera_images/start_area/stairs_on_the_right_side.jpg")
        )
    )

    fake_camera.add_image(
        cv2.imread(get_filename(f"tests/camera_images/start_area/stairs_centered.jpg"))
    )

    # detects obstacle after 3rd movement -> Move one time backwards -> Correct once -> Move forward twice! -> Detect obstacle on 2nd Movement
    navigation = FakeNavigation(
        [
            NavigationResult(True, None),
            NavigationResult(False, None),
            NavigationResult(False, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(False, None),
            NavigationResult(True, None),
        ]
    )
    start_area = StartArea(
        navigation,
        fake_camera,
        EdgeDetection(object_detection),
        pictogram_detection,
        StairsDetection(object_detection),
        PathObjectDetection(object_detection),
        FakeSpeaker(),
        0.005,
        0.15,
        150,
        135
    )

    spy_navigation_move_left = mocker.spy(start_area.navigation, "move_sideways_left")
    spy_navigation_move_right = mocker.spy(start_area.navigation, "move_sideways_right")
    spy_navigation_move_backwards = mocker.spy(start_area.navigation, "move_backwards")
    spy_navigation_move_forward_until_obstacle = mocker.spy(
        start_area.navigation, "move_forward_until_obstacle"
    )
    start_area.move_to_climbing_start_position()

    spy_navigation_move_right.call_count = 1
    spy_navigation_move_left.assert_has_calls([])
    spy_navigation_move_forward_until_obstacle.assert_has_calls(
        [mocker.call(130), mocker.call(15), mocker.call(120), mocker.call(15)]
    )
    spy_navigation_move_backwards.assert_has_calls([mocker.call(130)])
