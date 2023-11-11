from fake_speaker import FakeSpeaker
from guidance.a_star_center_bias_path_finder import AStarCenterBiasPathFinder
from guidance.a_star_path_finder import AStarPathFinder
from path_climbing_plan import PathClimbingPlan
from sensor_climbing_plan import SensorClimbingPlan
from path import Path
import logging.config
from movement import Movement
from tinyk_serial import DummyUART
from navigation import FakeNavigation, Navigation, NavigationResult
from tinyk import CommandError, FakeTinyK
from guidance.stairs_map import StairsMap
from guidance.a_star_center_bias_path_finder import AStarCenterBiasPathFinder
import pytest

import os
import sys
import inspect
import img_utils

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import image_logging
from stairs_area import StairsArea, StairsInformation


def stairs_map_empty() -> StairsMap:
    cell_width_in_cm = 5
    map_width = 135 // 5
    map_height = 5 + 2
    map = StairsMap(
        width=map_width, height=map_height, cell_width_in_cm=cell_width_in_cm, robot_width_in_cm=40
    )
    map.initialize()
    map.set_start(0.5)
    map.set_goal(0.5)
    return map


def stairs_map_2() -> StairsMap:
    cell_width_in_cm = 5
    map_width = 135 // 5
    map_height = 5 + 2
    map: StairsMap = StairsMap(
        width=map_width, height=map_height, cell_width_in_cm=cell_width_in_cm, robot_width_in_cm=40
    )
    map.initialize()
    map.set_start(0.5)
    map.set_goal(0.5)
    map.set_obstacle(12, 2)
    map.set_obstacle(13, 2)
    map.set_obstacle(14, 2)
    map.set_obstacle(15, 2)
    map.set_obstacle(8, 4)
    map.set_obstacle(9, 4)
    map.set_obstacle(10, 4)
    map.set_obstacle(11, 4)
    map.set_obstacle(12, 4)
    map.set_obstacle(13, 4)
    map.set_obstacle(14, 4)
    map.set_obstacle(15, 4)
    return map


def standard_stairs_information() -> StairsInformation:
    return StairsInformation(135, 20, 5)


def path_only_climb() -> Path:
    return Path(
        [
            Movement.climb,
            Movement.climb,
            Movement.climb,
            Movement.climb,
            Movement.climb,
            Movement.climb,
        ], 5
    )


def path_1_with_obstacles() -> Path:
    return Path(
        [
            Movement.climb,
            Movement.left,
            Movement.left,
            Movement.climb,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.climb,
            Movement.right,
            Movement.climb,
            Movement.left,
            Movement.left,
            Movement.climb,
            Movement.left,
            Movement.climb,
        ], 5
    )


def path_2_with_obstacles() -> Path:
    return Path(
        [
            Movement.climb,
            Movement.left,
            Movement.left,
            Movement.climb,
            Movement.climb,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.climb,
            Movement.climb,
            Movement.left,
            Movement.left,
            Movement.left,
            Movement.left,
            Movement.climb,
        ], 5
    )


def initialize_stairs_area_1() -> StairsArea:
    image_logging.configure("robot.conf")
    logging.config.fileConfig(fname="logger.conf")

    navigation = Navigation(FakeTinyK(DummyUART()), FakeSpeaker())
    stairs_area: StairsArea = StairsArea(
        navigation, standard_stairs_information(), FakeSpeaker()
    )

    return stairs_area


def test_formulate_plan_path():
    stairs_area: StairsArea = initialize_stairs_area_1()
    stairs_map: StairsMap = stairs_map_empty()
    path: Path = path_only_climb()
    stairs_area.stairs_map = stairs_map
    stairs_area.path = path
    stairs_area.formulate_plan()
    assert stairs_area.plan == PathClimbingPlan(
        path, stairs_map, stairs_area.navigation, FakeSpeaker()
    )


def test_formulate_plan_sensor():
    stairs_area: StairsArea = initialize_stairs_area_1()
    stairs_map: StairsMap = stairs_map_empty()
    stairs_area.stairs_map = stairs_map
    stairs_area.formulate_plan()
    assert stairs_area.plan == SensorClimbingPlan(
        stairs_map, stairs_area.navigation, AStarCenterBiasPathFinder(), stairs_area.speaker
    )


def test_working_climbing_plan(mocker):
    stairs_area: StairsArea = initialize_stairs_area_1()
    stairs_map: StairsMap = stairs_map_empty()
    path: Path = path_only_climb()
    stairs_area.stairs_map = stairs_map
    stairs_area.path = path

    spy_navigation_climb = mocker.spy(stairs_area.navigation, "climb")
    spy_stairs_area_move_position_up = mocker.spy(stairs_area.stairs_map, "move_position_up")
    spy_stairs_area_move_position_left = mocker.spy(
        stairs_area.stairs_map, "move_position_left_in_distance"
    )
    spy_stairs_area_move_position_right = mocker.spy(
        stairs_area.stairs_map, "move_position_right_in_distance"
    )

    stairs_area.formulate_plan()
    stairs_area.climb()

    spy_navigation_climb.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ]
    )

    spy_stairs_area_move_position_up.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ]
    )

    spy_stairs_area_move_position_left.assert_has_calls([])
    spy_stairs_area_move_position_right.assert_has_calls([])

    assert stairs_area.plan == PathClimbingPlan(
        path, stairs_map, stairs_area.navigation, FakeSpeaker()
    )
    assert stairs_area.stairs_map.position == stairs_area.stairs_map.goal


def test_working_difficult_climbing_plan(mocker):
    stairs_area: StairsArea = initialize_stairs_area_1()
    # This is used, since creating a stairs map manually is very complicated
    stairs_map: StairsArea = stairs_map_empty()
    path: Path = path_1_with_obstacles()
    stairs_area.stairs_map = stairs_map
    stairs_area.path = path

    spy_navigation_climb = mocker.spy(stairs_area.navigation, "climb")
    spy_navigation_move_sideways_left = mocker.spy(
        stairs_area.navigation, "move_sideways_left"
    )
    spy_navigation_move_sideways_right = mocker.spy(
        stairs_area.navigation, "move_sideways_right"
    )

    spy_stairs_area_move_position_up = mocker.spy(stairs_area.stairs_map, "move_position_up")
    spy_stairs_area_move_position_left = mocker.spy(
        stairs_area.stairs_map, "move_position_left_in_distance"
    )
    spy_stairs_area_move_position_right = mocker.spy(
        stairs_area.stairs_map, "move_position_right_in_distance"
    )

    stairs_area.formulate_plan()
    stairs_area.plan.path_finder = AStarPathFinder()
    stairs_area.climb()

    spy_navigation_climb.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ]
    )

    spy_navigation_move_sideways_left.assert_has_calls(
        [mocker.call(10), mocker.call(10), mocker.call(5)]
    )

    spy_navigation_move_sideways_right.assert_has_calls(
        [mocker.call(20), mocker.call(5)]
    )

    spy_stairs_area_move_position_up.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ]
    )

    spy_stairs_area_move_position_left.assert_has_calls(
        [mocker.call(10), mocker.call(10), mocker.call(5)]
    )
    spy_stairs_area_move_position_right.assert_has_calls(
        [mocker.call(20), mocker.call(5)]
    )

    assert stairs_area.plan == PathClimbingPlan(
        path, stairs_map, stairs_area.navigation, FakeSpeaker()
    )
    assert stairs_area.stairs_map.position == stairs_area.stairs_map.goal


def test_successfully_recalculating_climbing_plan_obstacle_right(mocker):
    stairs_area: StairsArea = initialize_stairs_area_1()
    stairs_map: StairsArea = stairs_map_2()

    # Detect obstacle right at 5th movement -> Movement.right
    stairs_area.navigation = FakeNavigation(
        [
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(False, CommandError.obstacle_detected_right, 4),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
        ]
    )

    path: Path = path_2_with_obstacles()
    stairs_area.stairs_map = stairs_map
    stairs_area.path = path

    image_logging.log("new_plan.jpg", img_utils.render_map_with_path(stairs_map, path))

    spy_navigation_climb = mocker.spy(stairs_area.navigation, "climb")
    spy_navigation_move_sideways_left = mocker.spy(
        stairs_area.navigation, "move_sideways_left"
    )
    spy_navigation_move_sideways_right = mocker.spy(
        stairs_area.navigation, "move_sideways_right"
    )

    spy_stairs_area_move_position_up = mocker.spy(stairs_area.stairs_map, "move_position_up")
    spy_stairs_area_move_position_left = mocker.spy(
        stairs_area.stairs_map, "move_position_left_in_distance"
    )
    spy_stairs_area_move_position_right = mocker.spy(
        stairs_area.stairs_map, "move_position_right_in_distance"
    )

    stairs_area.formulate_plan()
    stairs_area.plan.path_finder = AStarPathFinder()

    stairs_area.climb()

    spy_navigation_climb.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ]
    )

    spy_navigation_move_sideways_left.assert_has_calls(
        [
            mocker.call(10),
            mocker.call(20),
        ]
    )

    spy_navigation_move_sideways_right.assert_has_calls(
        [
            mocker.call(25),mocker.call(30)
        ]
    )

    spy_stairs_area_move_position_up.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ]
    )

    spy_stairs_area_move_position_left.assert_has_calls(
        [
            mocker.call(10),
            mocker.call(20),
        ]
    )
    spy_stairs_area_move_position_right.assert_has_calls(
        [
            mocker.call(30),
        ]
    )

    recalculated_path = Path(
        [
            Movement.left,
            Movement.left,
            Movement.left,
            Movement.left,
            Movement.climb,
            Movement.climb,
            Movement.climb,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.right,
        ],5
    )
    assert stairs_area.stairs_map.position == stairs_area.stairs_map.goal
    assert stairs_area.stairs_map.get_position(12, 4).is_obstacle == True

    assert stairs_area.plan.path == recalculated_path


def test_successfully_recalculating_climbing_plan_obstacle_front(mocker):
    stairs_area: StairsArea = initialize_stairs_area_1()
    stairs_map: StairsArea = stairs_map_2()

    # Detect obstacle front at 4th movement -> Movement.climb
    stairs_area.navigation = FakeNavigation(
        [
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(False, CommandError.obstacle_detected_front),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
        ]
    )

    path: Path = path_2_with_obstacles()
    stairs_area.stairs_map = stairs_map
    stairs_area.path = path

    image_logging.log("plan.jpg", img_utils.render_map_with_path(stairs_map, path))

    spy_navigation_climb = mocker.spy(stairs_area.navigation, "climb")
    spy_navigation_move_sideways_left = mocker.spy(
        stairs_area.navigation, "move_sideways_left"
    )
    spy_navigation_move_sideways_right = mocker.spy(
        stairs_area.navigation, "move_sideways_right"
    )

    spy_stairs_area_move_position_up = mocker.spy(stairs_area.stairs_map, "move_position_up")
    spy_stairs_area_move_position_left = mocker.spy(
        stairs_area.stairs_map, "move_position_left_in_distance"
    )
    spy_stairs_area_move_position_right = mocker.spy(
        stairs_area.stairs_map, "move_position_right_in_distance"
    )

    stairs_area.formulate_plan()
    stairs_area.plan.path_finder = AStarPathFinder()
    stairs_area.climb()

    spy_navigation_climb.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ]
    )

    spy_navigation_move_sideways_left.assert_has_calls(
        [mocker.call(10),mocker.call(5), mocker.call(15)]
    )

    spy_navigation_move_sideways_right.assert_has_calls(
        [mocker.call(30)]
    )

    spy_stairs_area_move_position_up.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ]
    )

    spy_stairs_area_move_position_left.assert_has_calls(
        [mocker.call(10), mocker.call(5), mocker.call(15)]
    )
    spy_stairs_area_move_position_right.assert_has_calls(
        [mocker.call(30)]
    )

    recalculated_path = Path(
        [
            Movement.left,
            Movement.climb,
            Movement.left,
            Movement.left,
            Movement.left,
            Movement.climb,
            Movement.climb,
            Movement.climb,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.right
        ],5
    )
    assert stairs_area.stairs_map.position == stairs_area.stairs_map.goal
    assert stairs_area.stairs_map.get_position(11, 3).is_obstacle == True
    logging.info(f"stairs_area.plan.path {stairs_area.plan.path}")
    logging.info(f"recalculated_path {recalculated_path}")

    assert stairs_area.plan.path == recalculated_path


def test_successfully_recalculating_climbing_plan_obstacle_left(mocker):
    stairs_area: StairsArea = initialize_stairs_area_1()
    stairs_map: StairsArea = stairs_map_2()

    # Detect obstacle left at 3th movement -> Movement.left
    stairs_area.navigation = FakeNavigation(
        [
            NavigationResult(True, None),
            NavigationResult(False, CommandError.obstacle_detected_left, 8),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
        ]
    )

    path: Path = path_2_with_obstacles()
    stairs_area.stairs_map = stairs_map
    stairs_area.path = path

    image_logging.log("plan.jpg", img_utils.render_map_with_path(stairs_map, path))

    spy_navigation_climb = mocker.spy(stairs_area.navigation, "climb")
    spy_navigation_move_sideways_left = mocker.spy(
        stairs_area.navigation, "move_sideways_left"
    )
    spy_navigation_move_sideways_right = mocker.spy(
        stairs_area.navigation, "move_sideways_right"
    )

    spy_stairs_area_move_position_up = mocker.spy(stairs_area.stairs_map, "move_position_up")
    spy_stairs_area_move_position_left = mocker.spy(
        stairs_area.stairs_map, "move_position_left_in_distance"
    )
    spy_stairs_area_move_position_right = mocker.spy(
        stairs_area.stairs_map, "move_position_right_in_distance"
    )

    stairs_area.formulate_plan()
    stairs_area.plan.path_finder = AStarPathFinder()
    stairs_area.climb()

    spy_navigation_climb.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ]
    )

    spy_navigation_move_sideways_left.assert_has_calls(
        [mocker.call(10), mocker.call(15)]
    )

    spy_navigation_move_sideways_right.assert_has_calls(
        [mocker.call(15)]
    )

    spy_stairs_area_move_position_up.assert_has_calls(
        [mocker.call(), mocker.call(), mocker.call(), mocker.call(), mocker.call()]
    )

    spy_stairs_area_move_position_left.assert_has_calls(
        [mocker.call(15)]
    )
    spy_stairs_area_move_position_right.assert_has_calls(
        [mocker.call(15)]
    )

    recalculated_path = Path(
        [
            Movement.right,
            Movement.right,
            Movement.right,
            Movement.climb,
            Movement.climb,
            Movement.climb,
            Movement.climb,
            Movement.climb,
            Movement.left,
            Movement.left,
            Movement.left,
        ], 5
    )
    assert stairs_area.stairs_map.position == stairs_area.stairs_map.goal
    assert stairs_area.stairs_map.get_position(11, 1).is_obstacle == True
    assert stairs_area.plan.path == recalculated_path


def test_successfully_recalculating_climbing_plan_obstacle_twice(mocker):
    stairs_area: StairsArea = initialize_stairs_area_1()
    stairs_map: StairsArea = stairs_map_2()

    # Detect obstacle left at 3th movement -> Movement.left and at the 9.th movement -> Movement.climb
    stairs_area.navigation = FakeNavigation(
        [
            NavigationResult(True, None),
            NavigationResult(False, CommandError.obstacle_detected_left, 4),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(False, CommandError.obstacle_detected_front),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
        ]
    )

    path: Path = path_2_with_obstacles()
    stairs_area.stairs_map = stairs_map
    stairs_area.path = path

    image_logging.log("plan.jpg", img_utils.render_map_with_path(stairs_map, path))

    spy_navigation_climb = mocker.spy(stairs_area.navigation, "climb")
    spy_navigation_move_sideways_left = mocker.spy(
        stairs_area.navigation, "move_sideways_left"
    )
    spy_navigation_move_sideways_right = mocker.spy(
        stairs_area.navigation, "move_sideways_right"
    )

    spy_stairs_area_move_position_up = mocker.spy(stairs_area.stairs_map, "move_position_up")
    spy_stairs_area_move_position_left = mocker.spy(
        stairs_area.stairs_map, "move_position_left_in_distance"
    )
    spy_stairs_area_move_position_right = mocker.spy(
        stairs_area.stairs_map, "move_position_right_in_distance"
    )

    stairs_area.formulate_plan()
    stairs_area.plan.path_finder = AStarPathFinder()
    stairs_area.climb()

    spy_navigation_climb.assert_has_calls(
        [
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
            mocker.call(),
        ]
    )

    spy_navigation_move_sideways_left.assert_has_calls(
        [mocker.call(10), mocker.call(20)]
    )

    spy_navigation_move_sideways_right.assert_has_calls(
        [mocker.call(15), mocker.call(5)]
    )

    spy_stairs_area_move_position_up.assert_has_calls(
        [mocker.call(), mocker.call(), mocker.call(), mocker.call(), mocker.call()]
    )

    spy_stairs_area_move_position_left.assert_has_calls(
        [mocker.call(20)]
    )
    spy_stairs_area_move_position_right.assert_has_calls(
        [mocker.call(15), mocker.call(5)]
    )

    recalculated_path = Path(
        [
            Movement.right,
            Movement.climb,
            Movement.climb,
            Movement.climb,
            Movement.left,
            Movement.left,
            Movement.left,
            Movement.left,
        ], 5
    )
    assert stairs_area.stairs_map.position == stairs_area.stairs_map.goal
    assert stairs_area.stairs_map.get_position(12, 1).is_obstacle == True
    assert stairs_area.stairs_map.get_position(16, 4).is_obstacle == True
    assert stairs_area.plan.path == recalculated_path

def test_failed_recalculating_climbing_plan_obstacle(mocker):
    stairs_area: StairsArea = initialize_stairs_area_1()
    stairs_map: StairsArea = stairs_map_2()

    # Sackgasse
    # Detect obstacle left at 2nd movement -> Movement.left and obstacle right at the 7.th movement -> Movement.right
    stairs_area.navigation = FakeNavigation(
        [
            NavigationResult(True, None),
            NavigationResult(False, CommandError.obstacle_detected_left, 4),
            NavigationResult(False, CommandError.obstacle_detected_right, 8),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
            NavigationResult(True, None),
        ]
    )

    path: Path = path_2_with_obstacles()
    stairs_area.stairs_map = stairs_map
    stairs_area.path = path

    image_logging.log("plan.jpg", img_utils.render_map_with_path(stairs_map, path))

    stairs_area.formulate_plan()
    stairs_area.plan.path_finder = AStarPathFinder()
    stairs_area.climb()

    # Did obstacles get removed? The sensor based plan assumes nothing about its environment.
    assert stairs_area.stairs_map.get_position(12, 1).is_obstacle == False
    assert stairs_area.stairs_map.get_position(15, 1).is_obstacle == False
    assert isinstance(stairs_area.plan, SensorClimbingPlan)
