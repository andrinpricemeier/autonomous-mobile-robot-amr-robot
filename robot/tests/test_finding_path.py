from warming_up_state import WarmingUpState
import logging.config
import image_logging
from tests.preparation import get_triton_object_detection_from_config, __read_config
from movement import Movement
from fake_camera import FakeCamera
import cv2
from tinyk_serial import DummyUART
from navigation import Navigation
from robot import Robot
from finding_path_state import FindingPathState
from tinyk import FakeTinyK
import pytest
from fake_speaker import FakeSpeaker
import os
import sys
import inspect
from detected_object import DetectedObject

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


@pytest.fixture()
def object_detection():
    image_logging.configure("robot.conf")
    logging.config.fileConfig(fname="logger.conf")
    yield get_triton_object_detection_from_config("robot.conf")


def initialize_new_fake_robot(object_detection) -> Robot:
    robot = Robot()
    warming_up_state = WarmingUpState(robot)
    robot.object_detection = object_detection
    tinyK = FakeTinyK(DummyUART())
    robot.navigation = Navigation(tinyK, FakeSpeaker())
    robot.camera = FakeCamera()
    robot.speaker = FakeSpeaker()
    robot.width_in_cm = 38
    robot.movements_in_cm = 5
    robot.competition_area = warming_up_state.init_competition_area(
        __read_config("robot.conf"), tinyK
    )
    robot.competition_area.target_area.target_pictogram = DetectedObject.bucket
    return robot


def test_path_treppe_mitte_6_backsteine_5_stufen_sackgasse(object_detection):
    robot: Robot = initialize_new_fake_robot(object_detection)
    robot.camera.add_image(
        cv2.imread(
            "tests/camera_images/path/Test_Treppe_Mitte_6_Backsteine_5_Stufen_Sackgasse.jpg"
        )
    )

    state = FindingPathState(robot)

    state.enter()

    assert robot.competition_area.stairs_area.path is not None, "unable to find path"


def test_path_treppe_aussen_7_ziegelsteine(object_detection):
    robot: Robot = initialize_new_fake_robot(object_detection)
    robot.camera.add_image(
        cv2.imread("tests/camera_images/path/Test_Treppe_Aussen_7_Ziegelsteine.jpg")
    )

    state = FindingPathState(robot)

    state.enter()

    assert robot.competition_area.stairs_area.path is not None, "unable to find path"


def test_path_treppe_aussen_7_ziegelsteine_2(object_detection):
    robot: Robot = initialize_new_fake_robot(object_detection)
    robot.camera.add_image(
        cv2.imread("tests/camera_images/path/Test_Treppe_Aussen_7_Ziegelsteine_2.jpg")
    )

    state = FindingPathState(robot)

    state.enter()

    assert robot.competition_area.stairs_area.path is not None, "unable to find path"


def test_path_jetson_2021_07_05_testlauf_00691(object_detection):
    robot: Robot = initialize_new_fake_robot(object_detection)
    robot.camera.add_image(
        cv2.imread("tests/camera_images/path/Test_jetson-2021-07-05-testlauf-00691.jpg")
    )
    robot.camera.add_image(
        cv2.imread("tests/camera_images/path/Test_jetson-2021-07-05-testlauf-00721.jpg")
    )
    robot.camera.add_image(
        cv2.imread("tests/camera_images/path/Test_jetson-2021-07-05-testlauf-00736.jpg")
    )

    state = FindingPathState(robot)

    state.enter()

    assert robot.competition_area.stairs_area.path is not None, "unable to find path"
