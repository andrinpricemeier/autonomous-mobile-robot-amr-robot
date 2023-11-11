from detected_object import DetectedObject
import os, sys, inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from bounding_box import BoundingBox
from typing import List, Any
import cv2
import logging

from guidance.brick import Brick
from guidance.stairs_map import StairsMap
from guidance.step import Step
from guidance.missing_edge_calculator import (
    BricksBasedMissingEdgeCalculator,
    GapBasedMissingEdgeCalculator,
)

import img_utils
from stairs_area import StairsInformation
import image_logging


class StairsMapCreator:
    def __init__(
        self,
        robot_width_in_cm: int,
        movements_in_cm: int,
        stairs_information: StairsInformation,
    ) -> None:
        self.robot_width_in_cm = robot_width_in_cm
        self.movements_in_cm = movements_in_cm
        self.stairs_information = stairs_information
        self.number_of_expected_edges: int = self.stairs_information.step_count + 1

        logging.info(
            "robot_width_in_cm: {0}, movements_in_cm {1}, step_width_in_cm: {2}, step_height_in_cm: {3},".format(
                self.robot_width_in_cm,
                self.movements_in_cm,
                self.stairs_information.step_width_in_cm,
                self.stairs_information.step_height_in_cm,
            )
        )

    def convert_to_stairs_map(
        self, image_of_steps, bricks: List[Brick], edges: List[BoundingBox] = []
    ) -> StairsMap:
        """
        Creates a stairs map with the information of the bricks and the edges.
        """
        pass


# TODO: Improve name
class AdvancedStairsMapCreator(StairsMapCreator):
    def convert_to_stairs_map(
        self, image_of_steps: Any, bricks: List[Brick], edges: List[BoundingBox] = []
    ) -> StairsMap:

        logging.info(
            "AdvancedStairsMapCreator - convert_to_stairs_map- bricks: {0}, edges: {1}".format(
                len(bricks), len(edges)
            )
        )
        height, self.width, _ = image_of_steps.shape
        self.current_image_of_steps = image_of_steps

        image_logging.log(
            "filtered_edges.jpg",
            img_utils.render_boxes(self.current_image_of_steps, bricks + edges),
        )

        # with 5 steps, at min 2 edges are required, e.g. 4 can be missing
        if len(edges) < (self.number_of_expected_edges - 4):
            logging.error(
                "Impossible to convert to stairs_map, not enough edges detected"
            )
            return None

        self.__sort_edges_from_lowest_to_highest(edges)

        # calculate edges which are not detected
        fixed_edges = BricksBasedMissingEdgeCalculator(
            self.number_of_expected_edges
        ).calculate_missing_edges(edges, bricks)

        image_logging.log(
            "calculated_steps_annotated_brick_based.jpg",
            img_utils.render_boxes(self.current_image_of_steps, bricks + fixed_edges),
        )

        self.__sort_edges_from_lowest_to_highest(fixed_edges)

        if len(fixed_edges) < self.number_of_expected_edges:
            logging.info(
                f"Still {self.number_of_expected_edges - len(fixed_edges)} edges missing, use GapBasedMissingEdgeCalculator..."
            )
            # calculate edges which are not detected
            fixed_edges = GapBasedMissingEdgeCalculator(
                self.number_of_expected_edges
            ).calculate_missing_edges(fixed_edges, bricks)

            image_logging.log(
                "calculated_steps_annotated_brick_based_and_basic.jpg",
                img_utils.render_boxes(
                    self.current_image_of_steps, bricks + fixed_edges
                ),
            )
            self.__sort_edges_from_lowest_to_highest(fixed_edges)

        if len(fixed_edges) != self.number_of_expected_edges:
            logging.error("Error while calculating missing edges")
            return None

        steps = self.convert_to_steps(bricks, fixed_edges)

        # floor and top
        stairs_map_height = self.stairs_information.step_count + 2
        stairs_map_width = (
            self.stairs_information.step_width_in_cm // self.movements_in_cm
        )
        stairs_map = self.create_stairs_map(steps, stairs_map_width, stairs_map_height)
        image_logging.log(
            "stairs_map_with_obstacles.jpg", img_utils.render_map(stairs_map)
        )

        return stairs_map

    def create_stairs_map(
        self, steps: List[Step], stairs_map_width: int, stairs_map_height: int
    ) -> StairsMap:
        stairs_map = StairsMap(
            stairs_map_width,
            stairs_map_height,
            self.movements_in_cm,
            self.robot_width_in_cm
        )
        stairs_map.initialize()

        # TODO: Improve quadratic complexity -> Maybe reduce n
        for step in steps:
            for cell in stairs_map.cells:
                if cell.step_number == step.step_number:
                    for brick in step.bricks:
                        # these u values are relative to the current_step
                        brick_u1, brick_u2 = self.get_brick_u_relative_to_step(
                            brick, step
                        )
                        brick_u1 = brick_u1 * stairs_map.width
                        brick_u2 = brick_u2 * stairs_map.width
                        if (
                            cell.cell_number >= brick_u1
                            and cell.cell_number <= brick_u2
                        ):
                            cell.is_obstacle = True

        return stairs_map

    def convert_to_steps(
        self, bricks: List[BoundingBox], edges: List[BoundingBox]
    ) -> List[Step]:
        steps = []
        for step_number, edge in enumerate(edges, start=1):
            next_edge = edges[step_number]

            current_step: Step = Step(step_number, edge.x1, edge.x2, edge.center_y())
            step_height_in_pxl = edge.center_y() - next_edge.center_y()

            # TODO: Fix, the brick is more on the current edge then on the next edge...
            one_cm_in_pxl = (
                edge.width() * 0.75 + next_edge.width() * 0.25
            ) / self.stairs_information.step_width_in_cm
            robot_width_in_pxl = self.robot_width_in_cm * one_cm_in_pxl

            bricks_on_current_step = self.find_bricks_for_step(
                current_step.y, bricks, step_height_in_pxl
            )

            for brick in bricks_on_current_step:
                current_step.bricks.append(
                    self.create_buffered_brick(
                        brick=brick, buffer=robot_width_in_pxl / 2
                    )
                )

            steps.append(current_step)

            cv2.line(
                self.current_image_of_steps,
                (int(current_step.x1), int(current_step.y)),
                (int(current_step.x2), int(current_step.y)),
                (0, 0, 255),
                2,
            )

            image_logging.log("steps_marked.jpg", self.current_image_of_steps)

            logging.info(
                f"Step {current_step.step_number}: Bricks: {len(current_step.bricks)}"
            )

            if self.stairs_information.step_count == step_number:
                break

        annotated = img_utils.render_boxes(
            self.current_image_of_steps,
            [brick for cur_step in steps for brick in cur_step.bricks],
        )
        image_logging.log("bricks_buffered.jpg", annotated)

        return steps

    def create_buffered_brick(self, brick: BoundingBox, buffer: Any) -> BoundingBox:
        buff_x1 = max(0, brick.x1 - buffer)
        buff_x2 = min(self.width, brick.x2 + buffer)
        return BoundingBox(
            brick.detected_object,
            brick.confidence,
            buff_x1,
            buff_x2,
            brick.y1,
            brick.y2,
            brick.image_width,
            brick.image_height,
        )

    def get_brick_u_relative_to_step(
        self, brick: BoundingBox, step: Step
    ) -> BoundingBox:
        return (
            max(brick.x1 - step.x1, 0.0) / float(step.width),
            min(brick.x2 - step.x1, step.width) / float(step.width),
        )

    # the one with the highest y -> is actually the lowest, since (0,0) is in the upper left corner
    def __sort_edges_from_lowest_to_highest(self, edges: List[BoundingBox]):
        edges.sort(reverse=True, key=lambda e: e.center_y())

    def find_bricks_for_step(
        self, step_y: float, bricks: List[BoundingBox], step_height: float
    ) -> List[BoundingBox]:
        found = []

        for brick in bricks:
            # if center is in step_height
            if (step_y - brick.center_y()) < step_height and (
                step_y - brick.center_y()
            ) > 0:
                found.append(brick)
        return found

    def calculate_missing_edges(self, edges: List[BoundingBox]) -> List[BoundingBox]:
        """
        Calculates the edges which could not be detected with the object detection model.
        Return: Edges with the len == step_count + 1
        """


class BasicStairsMapCreator(StairsMapCreator):
    def convert_to_stairs_map(
        self, image_of_steps: Any, bricks: List[Brick], edges: List[BoundingBox] = []
    ) -> StairsMap:

        logging.info(
            "BasicStairsMapCreator - convert_to_stairs_map- bricks: {0}".format(
                len(bricks)
            )
        )
        height, width, _ = image_of_steps.shape

        ONE_CM_IN_PIXEL = width / self.stairs_information.step_width_in_cm
        STEP_HEIGHT_IN_PIXELS = (
            ONE_CM_IN_PIXEL * self.stairs_information.step_height_in_cm
        )
        ROBOT_WIDTH_IN_PIXELS = ONE_CM_IN_PIXEL * self.robot_width_in_cm

        step_number = 1

        number_of_steps = self.stairs_information.step_count
        current_y = 1
        steps = []

        while step_number <= number_of_steps:
            bricks_on_current_step = self.find_bricks_for_step(
                current_y, bricks, STEP_HEIGHT_IN_PIXELS / 2
            )
            s1 = Step(step_number, 0, width, current_y)
            for b in bricks_on_current_step:
                buff_x1 = max(0, b.x1 - (ROBOT_WIDTH_IN_PIXELS / 2))
                buff_x2 = min(width, b.x2 + (ROBOT_WIDTH_IN_PIXELS / 2))
                buffered_brick = BoundingBox(
                    b.detected_object,
                    b.confidence,
                    buff_x1,
                    buff_x2,
                    b.y1,
                    b.y2,
                    b.image_width,
                    b.image_height,
                )
                s1.bricks.append(buffered_brick)
            steps.append(s1)
            cv_y = height - current_y
            cv2.line(
                image_of_steps, (0, int(cv_y)), (int(width), int(cv_y)), (0, 0, 255), 2
            )
            step_number = step_number + 1
            current_y = current_y + STEP_HEIGHT_IN_PIXELS
        image_logging.log("steps_marked.jpg", image_of_steps)

        for sz in steps:
            print(f"{sz.step_number}: {len(sz.bricks)}")
            for b in sz.bricks:
                annotated = img_utils.render_box(
                    image_of_steps, (b.x1, b.y1, b.x2, b.y2), b.confidence
                )

        image_logging.log("bricks_buffered.jpg", image_of_steps)

        stairs_map_width = (
            self.stairs_information.step_width_in_cm // self.movements_in_cm
        )
        stairs_map_height = self.stairs_information.step_count + 2

        stairs_map1 = StairsMap(stairs_map_width, stairs_map_height, self.movements_in_cm, self.robot_width_in_cm)

        stairs_map1.initialize()

        # TODO: Improve quadratic complexity -> Maybe reduce n
        for sz in steps:
            for c in stairs_map1.cells:
                if c.step_number == sz.step_number:
                    for b in sz.bricks:
                        b_x1 = b.u1 * stairs_map1.width
                        b_x2 = b.u2 * stairs_map1.width
                        if c.cell_number >= b_x1 and c.cell_number <= b_x2:
                            c.is_obstacle = True
                        elif c.cell_number >= b_x2 and c.cell_number <= b_x2:
                            c.is_obstacle = True

        image_logging.log(
            "stairs_map_with_obstacles.jpg", img_utils.render_map(stairs_map1)
        )
        return stairs_map1

    def find_bricks_for_step(
        self, step_y: float, bricks: List[BoundingBox], epsilon: float
    ) -> List[BoundingBox]:
        found = []
        for brick in bricks:
            brick_y2 = brick.image_height - brick.y2
            if abs(step_y - brick_y2) < epsilon:
                found.append(brick)
        return found
