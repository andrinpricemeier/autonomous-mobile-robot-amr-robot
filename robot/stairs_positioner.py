from bounding_box import BoundingBox
from typing import List, Tuple, Any
from pictogram_detection import PictogramDetection
from camera import Camera
from navigation import Navigation
from edge_detection import EdgeDetection
from stairs_detection import StairsDetection
import logging
import numpy as np
from sklearn.linear_model import LinearRegression
import image_logging
import img_utils
from line import Line
from line_detection import LineDetection, CannyHoughLineDetection
import math

class PositionerStrategy:
    def move_to_center(self, max_number_of_movements: int) -> None:
        """
        Moves to center of the stairs with a maximum of movements until it stops.
        """
        pass


class RoughStairsPositionerStrategy(PositionerStrategy):
    def __init__(
        self,
        stairs_detection: StairsDetection,
        pictogram_detection: PictogramDetection,
        camera: Camera,
        navigation: Navigation,
        stairs_optimal_left_offset: int,
        stairs_width_in_cm: int
    ):
        self.stairs_detection: StairsDetection = stairs_detection
        self.pictogram_detection: PictogramDetection = pictogram_detection
        self.navigation: Navigation = navigation
        self.camera: Camera = camera
        self.sideways_moving_distance: int = 15
        self.stairs_optimal_left_offset = stairs_optimal_left_offset
        self.stairs_width_in_cm = stairs_width_in_cm

    def move_to_center(self, max_number_of_movements: int) -> None:
        self.__move_until_whole_steps_visible()
        for _ in range(1, max_number_of_movements + 1):
            image = self.camera.take_picture()
            image_logging.log(
                image_logging.RAW_IMAGE + "rough_stairs_positioner_move_to_center.jpg",
                image,
            )
            stairs = self.stairs_detection.detect_stairs(image)
            if stairs is None:
                logging.warn(
                    "RoughStairsPositionerStrategy - move_to_center - no stairs detected, moving backwards"
                )
                self.navigation.move_backwards(5)
            elif stairs.is_to_the_left():
                distance_to_center_in_cm = int(max(5, stairs.abs_distance_to_center() * self.stairs_width_in_cm))
                logging.warn(
                    f"RoughStairsPositionerStrategy - move_to_center - stairs is to the left, moving to the left {distance_to_center_in_cm}cm."
                )
                self.navigation.move_sideways_left(distance_to_center_in_cm)
            elif stairs.is_to_the_right():
                distance_to_center_in_cm = int(max(5, stairs.abs_distance_to_center() * self.stairs_width_in_cm))
                logging.warn(
                    f"RoughStairsPositionerStrategy - move_to_center - stairs is to the right, moving to the right {distance_to_center_in_cm}cm."
                )
                self.navigation.move_sideways_right(distance_to_center_in_cm)
            elif stairs.is_in_center_x():
                logging.info(
                    "RoughStairsPositionerStrategy - move_to_center - center reached. done."
                )
                break
            else:
                raise Exception("We don't know where we are relative to the stairs.")

    def __move_until_whole_steps_visible(self) -> None:
        backwards_distance = 0
        backwards_movement_per_step_in_cm = 15
        backwards_max_movement_in_cm = 75
        while True:
            image = self.camera.take_picture()
            if self.pictogram_detection.are_target_pictograms_visible(image):
                logging.info("Whole stairs are visible. Stopping.")
                break
            else:
                if backwards_distance >= backwards_max_movement_in_cm:
                    logging.warn(f"Couldn't find whole stairs after {backwards_distance}cm. Stopping backwards movement.")
                    break
                logging.info("Steps not visible. Moving backwards.")
                self.navigation.move_backwards(backwards_movement_per_step_in_cm)
                backwards_distance += backwards_movement_per_step_in_cm


class FinetuneStairsPositionerStrategy(PositionerStrategy):
    def __init__(
        self,
        edge_detection: EdgeDetection,
        camera: Camera,
        navigation: Navigation,
        steps_width_in_cm: int,
        correct_rotation: bool = False,
    ):
        """
        Initializes a positionier, which can position itself relative to the stairs with a high precision.

        Keyword arguments:
        correct_rotation -- determines whether the positioner should correct sideways rotation (default False)
        """
        self.edge_detection: EdgeDetection = edge_detection
        self.line_detection: LineDetection = CannyHoughLineDetection()
        self.navigation: Navigation = navigation
        self.camera: Camera = camera
        self.epsilon: float = 0.01
        self.steps_width_in_cm: int = steps_width_in_cm
        self.correct_rotation: bool = correct_rotation
        self.scale_factor = 0.45
        self.rotate_amount = 0
        self.max_rotations = 2

    def move_to_center(self, max_number_of_movements: int) -> None:
        position: float = -1.0
        for _ in range(1, max_number_of_movements + 1):
            image: Any = self.camera.take_picture()
            image_logging.log(
                image_logging.RAW_IMAGE
                + "fine_tune_stairs_positioner_move_to_center.jpg",
                image,
            )
            edges: List[BoundingBox] = self.edge_detection.detect_edges(
                image, min_width_normalized=0.33
            )

            if len(edges) > 1:
                position = self.get_position(edges, image)

                if position is None:
                    logging.error("FinetuneStairsPositionerStrategy - position is None - unable to calculate position")
                    return None

                logging.info(f"FinetuneStairsPositionerStrategy - position: {position}")

                if self.is_left(position):
                    self.move_left(position)

                elif self.is_right(position):
                    self.move_right(position)

                else:
                    logging.info("FinetuneStairsPositionerStrategy - Reached center")
                    if self.correct_rotation:
                        logging.info("FinetuneStairsPositionerStrategy- correct rotation")
                        self.rotate_sideways(self.__get_rotation_direction(edges))
                        self.rotate_amount += 1
                        if self.rotate_amount >= self.max_rotations:
                            return
                    else:
                        logging.info("FinetuneStairsPositionerStrategy - found center")
                        return
            else:
                logging.error(
                    f"FinetuneStairsPositionerStrategy - too little edges [{len(edges)}], retry"
                )
        logging.info(f"FinetuneStairsPositionerStrategy - haven't found center in {max_number_of_movements} movements")

    def is_right(self, position: float) -> bool:
        """
        Returns whether stairs are right, depending on the position.
        """
        return position > (self.epsilon)

    def is_left(self, position: float) -> bool:
        """
        Returns whether stairs are left, depending on the position.
        """
        return position < (-self.epsilon)

    def is_centered(self, position: float):
        """
        Returns whether stairs are centered, depending on the position.
        """
        return (not self.is_left(position)) and (not self.is_right(position))

    def move_right(self, position: float) -> None:
        """
        Moves the robot right, with a distance depending on the position of the stairs.
        """
        logging.info(f"FinetuneStairsPositionerStrategy - stairs are on the right - move_right - position: {position}")
        self.navigation.move_sideways_right(
            max(int(self.scale_factor * self.steps_width_in_cm * abs(position)), 1)
        )

    def move_left(self, position: float) -> None:
        """
        Moves the robot left, with a distance depending on the position of the stairs.
        """
        logging.info(f"FinetuneStairsPositionerStrategy - stairs are on the left - move_left - position: {position}")
        self.navigation.move_sideways_left(
            max(int(self.scale_factor * self.steps_width_in_cm * abs(position)), 1)
        )

    def rotate_sideways(self, average_angle: float) -> None:
        """
        Rotates the robot sidways, with a distance depending on the position of the stairs.
        """
        logging.info(f"FinetuneStairsPositionerStrategy - average_angle: {average_angle}")
        self.navigation.rotate_sideways(int(round(average_angle)))

    def get_position_slope_only(self, edges: List[BoundingBox]) -> float:
        """
        Returns a negative number, if position is left. Returns a positive number if position is right. Returns zero if its centered.
        """
        logging.info("FinetuneStairsPositionerStrategy - __get_position")

        ml, bl = self.__get_line_left(edges)
        mr, br = self.__get_line_right(edges)

        if ml == 0:
            logging.error("FinetuneStairsPositionerStrategy - ml is zero")
            return None

        if mr == 0:
            logging.error("FinetuneStairsPositionerStrategy - mr is zero")
            return None

        logging.debug(
            f"FinetuneStairsPositionerStrategy - ml: {ml}, mr: {mr}"
        )

        difference = -1 * ( ml + mr)
        
        logging.debug(f"FinetuneStairsPositionerStrategy - difference {difference}")

        return difference

    def get_position(self, edges: List[BoundingBox], image: Any = None) -> float:
        """
        Returns a negative number, if position is left. Returns a positive number if position is right. Returns zero if its centered.
        """
        logging.info("FinetuneStairsPositionerStrategy - __get_position")

        ml, bl = self.__get_line_left(edges)
        mr, br = self.__get_line_right(edges)

        if image is not None:
            image_logging.log(
                "slope_left.jpg",
                self.__render_linear_function(
                    ml, bl, edges[0].image_width, edges[0].image_height, image
                )
            )
            image_logging.log(
                "slope_right.jpg",
                self.__render_linear_function(
                    mr, br, edges[0].image_width, edges[0].image_height, image
                )
            )

        if ml == 0:
            logging.error("FinetuneStairsPositionerStrategy - ml is zero")
            return None

        if mr == 0:
            logging.error("FinetuneStairsPositionerStrategy - mr is zero")
            return None

        height = edges[0].image_height
        width = edges[0].image_width

        space_left_down = (height - bl) / ml
        space_right_down = width - ((height - br) / mr)

        space_left_up = -bl / ml
        space_right_up = width + (br / mr)

        logging.debug(
            f"FinetuneStairsPositionerStrategy - space_left_down: {space_left_down}, space_right_down: {space_right_down}, space_left_up {space_left_up} , space_right_up {space_right_up}"
        )

        space_down =  (space_left_down - space_right_down) / width
        space_up = (space_right_up - space_left_up) / width

        logging.debug(f"FinetuneStairsPositionerStrategy - space_down {space_down}, space_up {space_up}")
        
        return space_down

        if not self.is_centered(space_down):
            logging.debug(f"FinetuneStairsPositionerStrategy - space_down: {space_down} not centered")

        logging.debug(f"FinetuneStairsPositionerStrategy - space_down: {space_down} centered,  return space_up: {space_up}")

        return space_up

    def get_average_edge_angle(self, edges: List[BoundingBox], image: Any) -> float:
        """
        Returns the average angle of the edges. 0 is equal to a horizontal line. The angles have to be interpreted from the left upper corner as (0,0).
        """
        lines: List[Line] = []

        for edge in edges:
            # cut image to the edge
            # detect lines
            # add to list
            lines += self.line_detection.detect_lines(
                edge.extract(image),
                min_angle=-5,
                max_angle=5,
                min_line_length=int(edge.width() * 0.25),
                max_line_gap=int(edge.width() * 0.05),
            )

        angles = [line.get_angle() for line in lines]

        average_angle = sum(angles) / len(angles)
        logging.info(
            f"FinetuneStairsPositionerStrategy - get_average_edge_angle - average_angle: {average_angle}"
        )
        return -average_angle

    def __get_rotation_direction(self, edges: List[BoundingBox]) -> int:
        logging.info("FinetuneStairsPositionerStrategy - __get_rotation_direction")
        ml, bl = self.__get_line_left(edges)
        mr, br = self.__get_line_right(edges)

        if ml == 0:
            logging.error("FinetuneStairsPositionerStrategy - ml is zero")
            return None

        if mr == 0:
            logging.error("FinetuneStairsPositionerStrategy - mr is zero")
            return None

        height = edges[0].image_height
        width = edges[0].image_width

        space_left_down = (height - bl) / ml
        space_right_down = width - ((height - br) / mr)

        space_left_up = -bl / ml
        space_right_up = width + (br / mr)

        logging.debug(
            f"FinetuneStairsPositionerStrategy - space_left_down: {space_left_down}, space_right_down: {space_right_down}, space_left_up {space_left_up} , space_right_up {space_right_up}"
        )

        space_up = (space_right_up - space_left_up) / width

        return int(round(space_up * 60))

    def __get_line_left(self, edges: List[BoundingBox]) -> Tuple[float, float]:
        """
        Returns the slope and the y intercept of the left Boundary. The slope has to be interpreted with 0,0 being the left upper corner.
        """
        X = np.zeros([len(edges), 1])
        y = np.zeros(len(edges))

        for i in range(len(edges)):
            X[i, 0] = edges[i].x1
            y[i] = int((edges[i].y1 + edges[i].y2) // 2)


        reg = LinearRegression().fit(X, y)
        m = reg.coef_[0]
        b = reg.intercept_
        logging.info(f"FinetuneStairsPositionerStrategy - __get_line_left - m {m}, b {b}")

        image_logging.log(
            "slope_left.jpg",
            self.__render_linear_function(
                m, b, edges[0].image_width, edges[0].image_height
            ),
        )

        return m, b

    def __get_line_right(self, edges: List[BoundingBox]) -> Tuple[float, float]:
        """
        Returns the slope and the y intercept of the right Boundary. The slope has to be interpreted with 0,0 being the left upper corner.
        """

        X = np.zeros([len(edges), 1])
        y = np.zeros(len(edges))

        for i in range(len(edges)):
            X[i, 0] = edges[i].x2
            y[i] = int((edges[i].y1 + edges[i].y2) // 2)

        reg = LinearRegression().fit(X, y)
        m = reg.coef_[0]
        b = reg.intercept_

        logging.info(f"FinetuneStairsPositionerStrategy - __get_line_right - m {m}, b {b}")
        image_logging.log(
            "slope_right.jpg",
            self.__render_linear_function(
                m, b, edges[0].image_width, edges[0].image_height
            ),
        )

        return m, b

    def __render_linear_function(self, m: int, b: int, width: int, height: int, img: Any = None) -> Any:
        x1 = 0
        x2 = width
        y1 = m * x1 + b
        y2 = m * x2 + b

        logging.info(
            f"FinetuneStairsPositionerStrategy - __render_linear_function - x1: {x1}, y1: {y1}"
        )
        logging.info(
            f"FinetuneStairsPositionerStrategy - __render_linear_function - x2: {x2}, y2: {y2}"
        )

        if img is None:
            img = np.zeros((height, width, 3), np.uint8)

        img = img_utils.render_line(
            img, (x1, y1, x2, y2)
        )

        img = img_utils.render_text(
            img, f"m: {m}, b: {b}", int(width // 2), int(height // 2)
        )

        return img


class PathFindingPositioner:
    def __init__(self, first_strategy: PositionerStrategy):
        self.first_strategy: PositionerStrategy = first_strategy

    def move_to_optimal_path_finding_position(self) -> None:
        logging.info(
            "FinetuneStairsPositionerStrategy - move_to_optimal_path_finding_position - use rough positioning strategy"
        )
        try:
            self.first_strategy.move_to_center(15)
        except KeyboardInterrupt:
            raise

        except Exception as e:
            logging.exception(
                f"FinetuneStairsPositionerStrategy - move_to_optimal_path_finding_position - failed - {e}"
            )
