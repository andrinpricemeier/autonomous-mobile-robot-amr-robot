from guidance.a_star_path_finder_obstacle_avoider import AStarPathFinderObstacleAvoider
import path_object_detection
from tinyk import RobotPosition
from move_to_stairs_state import MoveToStairsState
import logging
from camera import Camera
from bounding_box import BoundingBox
from guidance.stairs_map_creator import StairsMapCreator, AdvancedStairsMapCreator
from guidance.stairs_map import StairsMap
from guidance.path_finder import PathFinder
from guidance.a_star_path_finder import AStarPathFinder
from guidance.a_star_space_optimized_path_finder import AStarSpaceOptimizedPathFinder
import img_utils

from typing import Any, List
from robot import Robot
from state import State
import image_logging
from path import Path


class FindingPathState(State):
    """Represents the state for finding a path.

    Args:
        State ([type]): the superclass.
    """
    def __init__(self, robot: Robot) -> None:
        """Creates a new instance.

        Args:
            robot (Robot): a reference to the robot.
        """
        self.robot = robot
        self.start_area = robot.competition_area.start_area
        self.camera: Camera = self.robot.camera
        self.stairs_map_creator: StairsMapCreator = AdvancedStairsMapCreator(
            self.robot.width_in_cm,
            self.robot.movements_in_cm,
            self.robot.competition_area.stairs_area.stairs_information,
        )
        self.path_finder: PathFinder = AStarPathFinderObstacleAvoider()
        self.speaker = robot.speaker
        self.navigation = robot.navigation
        self.pictogram_order = robot.competition_area.target_area.pictogram_order
        self.target_pictogram = robot.competition_area.target_area.target_pictogram

    def enter(self) -> None:
        """Starts the state actions.
        """
        retries: int = 3
        path: Path = None

        self.navigation.move_to_position(RobotPosition.drive_around)

        for retry in range(retries):
            logging.info(f"Find path retry: {retry}")

            path_object_detection_result: path_object_detection.PathObjectDetectionResult = self.start_area.find_path_objects()
            steps = path_object_detection_result.get_steps()
            image = path_object_detection_result.image
            steps_image: Any = steps.extract(image)

            # detect bricks on complete image since it works better there
            bricks = self.__cut_boxes_to_steps_size(
                steps, path_object_detection_result.get_bricks()
            )
            self.speaker.announce_bricks(len(bricks))
            image_logging.log(
                "finding_path_found_bricks.jpg",
                img_utils.render_boxes(steps_image, bricks),
            )

            # detect edges on complete image since it works better there
            edges = self.__cut_boxes_to_steps_size(
                steps,
                path_object_detection_result.get_edges(min_width_normalized=0.2)
            )
            image_logging.log(
                "finding_path_found_edges.jpg",
                img_utils.render_boxes(steps_image, edges),
            )

            path = self.__find_path(steps_image, bricks=bricks, edges=edges, robot_width_in_cm=self.robot.width_in_cm)

            if path is not None:
                self.speaker.announce_path_found()
                logging.info(f"found path : {path}")
                break

            self.navigation.move_forward(1)

        if path is None:
            self.speaker.announce_path_not_found()

        self.robot.competition_area.stairs_area.path = path

        self.robot.transition(MoveToStairsState(self.robot))

    # currently center in the middle
    def __determine_start(self) -> float:
        return 0.5

    def __determine_goal(self) -> float:
        """Determines the normalized x-position of the target area to move to.
        The returned x-position is right in the middle of the target pictogram.
        The target pictograms won't be placed exactly evenly spaced that's why the returned
        position is only a rough estimate. It should however give us a nice speed up.

        We assume every target pictogram takes up the same amount of space
        (e.g. with 5 target pictograms it would be 0.16 per pictogram). We then determine the
        goal by placing it in the middle of its width. E.g. if we'd have target pictogram number 2
        we'd place the goal at 0.32 + 0.1 = 0.42 (first target pictogram = 0.1 - 0.26, second is 0.26 - 0.42).

        Returns:
            float: the normalized x-position of the goal of the path finding algorithm.
        """
        target_pictogram_index = self.pictogram_order.index(self.target_pictogram)
        number_of_pictograms = len(self.pictogram_order)
        normalized_width_per_pictogram = (1 - 0.2) / number_of_pictograms
        normalized_middle_of_target_pictogram = (
            0.1 + target_pictogram_index * normalized_width_per_pictogram
            + (normalized_width_per_pictogram / 2)
        )
        return normalized_middle_of_target_pictogram

    def __find_path(
        self, steps_image: Any, bricks: List[BoundingBox], edges: List[BoundingBox],
        robot_width_in_cm
    ) -> Path:
        stairs_map_creator: StairsMapCreator = AdvancedStairsMapCreator(
                    robot_width_in_cm,
                    self.robot.movements_in_cm,
                    self.robot.competition_area.stairs_area.stairs_information,
                )
        stairs_map: StairsMap = stairs_map_creator.convert_to_stairs_map(
            image_of_steps=steps_image, bricks=bricks, edges=edges
        )

        if stairs_map is None:
            logging.info("FindingPathState - No stairs_map created - create empty map")
            self.robot.competition_area.stairs_area.stairs_map = self.__create_empty_stairs_map()
            return None

        self.robot.competition_area.stairs_area.stairs_map = stairs_map

        stairs_map.set_start(self.__determine_start())
        stairs_map.set_goal(self.__determine_goal())

        path: Path = self.path_finder.find_path(
            stairs_map, stairs_map.start, stairs_map.goal
        )

        if path is None:
            logging.info("FindingPathState - No path found")

        return path

    def __cut_boxes_to_steps_size(
        self,
        steps: BoundingBox,
        boxes: List[BoundingBox],
        remove_outliers: bool = False,
    ) -> List[BoundingBox]:
        """
        Cuts the boxes to an image of the position and size of the steps BoundingBox.
        :param remove_outliers This will drop all boxes intersecting with the steps since this should not happen.
        """

        logging.debug(f"__cut_boxes_to_steps_size remove_outliers: {remove_outliers}")

        if remove_outliers:
            logging.debug("remove_outliers")
            boxes = self.__filter_boxes_intersecting_steps(steps, boxes)

        return [self.__cut_box_to_steps_size(steps, box) for box in boxes]

    def __cut_box_to_steps_size(
        self, steps: BoundingBox, box: BoundingBox
    ) -> BoundingBox:
        """
        Cuts the box to an image of the position and size of the steps BoundingBox.
        """
        return BoundingBox(
            box.detected_object,
            box.confidence,
            max(0, box.x1 - steps.x1),
            steps.width() - max(0, steps.x2 - box.x2),
            max(0, box.y1 - steps.y1),
            steps.height() - max(0, steps.y2 - box.y2),
            steps.width(),
            steps.height(),
        )

    def __filter_boxes_intersecting_steps(
        self, steps: BoundingBox, boxes: List[BoundingBox]
    ) -> List[BoundingBox]:
        """
        This will remove all the boxes intersecting with the borders of the steps.
        """
        logging.debug("Remove outliers!")
        return [
            box
            for box in boxes
            if (box.x1 >= steps.x1)
            and (box.x2 <= steps.x2)
            and (box.y1 >= steps.y1)
            and (box.y2 <= steps.y2)
        ]

    def __create_empty_stairs_map(self) -> StairsMap:
        stairs_map_width = (
            self.robot.competition_area.stairs_area.stairs_information.step_width_in_cm // self.robot.movements_in_cm
        )
        stairs_map_height = self.robot.competition_area.stairs_area.stairs_information.step_count + 2

        stairs_map1 = StairsMap(stairs_map_width, stairs_map_height, self.robot.movements_in_cm, self.robot.width_in_cm)

        stairs_map1.initialize()

        stairs_map1.set_start(self.__determine_start())
        stairs_map1.set_goal(self.__determine_goal())

        return stairs_map1
