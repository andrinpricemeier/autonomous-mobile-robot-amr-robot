from tinyk import CommandError, RobotPosition
from bounding_box import BoundingBox
from detected_object import DetectedObject
from typing import List, Tuple
from pictogram_detection import PictogramDetection
from navigation import Navigation, NavigationResult
from camera import Camera
from speaker import Speaker
import logging
from enum import Enum
import image_logging
import img_utils
import math
import time

class TargetDirection(Enum):
    left = 0
    forward = 1
    right = 2
    reached = 3


class TargetArea:
    def __init__(
        self,
        navigation: Navigation,
        camera: Camera,
        speaker: Speaker,
        pictogram_detection: PictogramDetection,
        pictogram_order: List[DetectedObject],
        distance_to_flag_in_cm: int,
        pictogram_width_in_cm,
        distance_between_pictograms_in_cm
    ) -> None:
        self.navigation = navigation
        self.camera = camera
        self.speaker = speaker
        self.pictogram_detection = pictogram_detection
        self.pictogram_order: List[DetectedObject] = pictogram_order
        self.distance_to_flag_in_cm = distance_to_flag_in_cm
        self.pictogram_width_in_cm = pictogram_width_in_cm
        self.distance_between_pictograms_in_cm = distance_between_pictograms_in_cm
        self.target_pictogram: DetectedObject = None
        self.target_pictogram_position: int = -1
        self.total_forward_distance_in_cm = 0
        self.forward_driving_distance_in_cm = math.ceil(
            self.distance_to_flag_in_cm / 3.0
        )

    def move_to_target_flag(self) -> bool:
        if self.target_pictogram is None:
            self.speaker.announce_no_target_pictogram()
            raise Exception("No target Pictogram set.")
        
        # Gradually switch to stand up position, otherwise we risk falling down the stairs.
        self.navigation.move_to_position(RobotPosition.drive_around)
        self.navigation.move_to_position(RobotPosition.stand_up)

        self.__set_target_pictogram_position()

        logging.debug(f"TargetArea - move_to_target_flag: {self.target_pictogram}")

        while not self.__has_reached_target():
            self.__next_movement()
            logging.info(
                f"TargetArea total distance forward {self.total_forward_distance_in_cm}"
            )

        logging.info(
            f"TargetArea reached target - total distance: {self.total_forward_distance_in_cm}"
        )
        self.__signal_target_reached()
        return True

    def __set_target_pictogram_position(self) -> None:
        try:
            self.target_pictogram_position = self.pictogram_order.index(
                self.target_pictogram
            )
        except KeyboardInterrupt:
            raise
        except Exception:
            logging.exception(
                f"Target Pictogram : {self.target_pictogram} not in pictograms {self.pictogram_order}"
            )
            raise Exception(
                f"Target Pictogram : {self.target_pictogram} not in pictograms {self.pictogram_order}"
            )

    def __next_movement(self) -> None:
        
        logging.info("TargetArea - has not nearly reached target - detect next central pictogram")
        central_pictogram = self.get_central_pictogram()
        direction, distance = self.get_target_direction(central_pictogram)

        if direction is None:
            logging.error("TargetArea - Unable to calculate movement, retry!")
            return
    
        moved = self.__move(direction, distance)

        if not moved.success:
            logging.error("TargetArea - Unable to move - recalculate move")
            new_direction, new_distance = self.__recalculate_movement(direction, distance, moved)
            logging.info(f"TargetArea - Recalculated move - move to direction {new_direction} {new_distance} cm")
            moved = self.__move(new_direction, new_distance)

        if moved.success and (direction == TargetDirection.forward):
            self.total_forward_distance_in_cm += distance
            logging.debug(f"Target Area - total_forward_distance_in_cm: {self.total_forward_distance_in_cm}")


    def get_central_pictogram(self) -> BoundingBox:
        central_pictogram = None
        logging.debug("TargetArea - get central pictogram")
        while central_pictogram is None:
            self.navigation.move_to_position(RobotPosition.stand_up)
            time.sleep(0.25)
            image = self.camera.take_picture()
            # Fix camera angle
            image = img_utils.rotate_center_counter_clockwise(image, -3)

            image_logging.log(
                image_logging.RAW_IMAGE + "target_area_get_central_pictogram.jpg", image
            )
            central_pictogram = self.pictogram_detection.find_central(image)
            # TODO: Move a little to the right?
            if central_pictogram is None:
                logging.error("TargetArea - no central pictogram detected")
                self.navigation.move_forward(1)

        logging.info(
            f"TargetArea - get_central_pictogram : central_pictogram: {central_pictogram}"
        )

        image_logging.log(
            "central_pictogram.jpg", img_utils.render_boxes(image, [central_pictogram])
        )
        return central_pictogram

    def __move(self, direction: TargetDirection, movement_in_cm: int) -> NavigationResult:
        self.navigation.move_to_position(RobotPosition.drive_around)
        if direction == TargetDirection.forward:
            if self.__has_nearly_reached_target():
                logging.info("TargetArea - has_nearly_reached_target")
                return self.__hit_target_flag()
            
            return self.navigation.move_forward(movement_in_cm)

        elif direction == TargetDirection.left:
            return self.navigation.move_sideways_left(movement_in_cm)

        elif direction == TargetDirection.right:
            return self.navigation.move_sideways_right(movement_in_cm)

        return False

    def get_target_direction(
        self, central_pictogram: BoundingBox
    ) -> Tuple[TargetDirection, int]:
        if central_pictogram.detected_object == self.target_pictogram:
            return self.__calculate_direction_target_central(central_pictogram)

        try:
            central_pictogram_position = self.pictogram_order.index(
                central_pictogram.detected_object
            )

        except KeyboardInterrupt:
            raise
        except Exception:
            logging.exception(
                f"Central Pictogram : {central_pictogram} not in pictograms {self.pictogram_order}"
            )
            return None, None

        position_difference = (
            self.target_pictogram_position - central_pictogram_position
        )

        movement_in_cm = self.distance_between_pictograms_in_cm * abs(position_difference)

        logging.debug(
            f"TargetArea - get_target_direction : target_pictogram_position {self.target_pictogram_position} central_pictogram_position {central_pictogram_position}"
        )

        if position_difference > 0:
            return TargetDirection.right, movement_in_cm

        else:
            return TargetDirection.left, movement_in_cm

    def __has_reached_target(self) -> bool:
        return self.total_forward_distance_in_cm >= self.distance_to_flag_in_cm

    def __calculate_direction_target_central(
        self, central_pictogram: BoundingBox
    ) -> Tuple[TargetDirection, int]:
        logging.info(
            f"TargetArea - calculate_direction_target_central - center normalized {central_pictogram.center_normalized()}"
        )

        epsilon = 0.015
        if central_pictogram.is_in_center_x(epsilon):
            logging.info(
                "TargetArea - calculate_direction_target_central - is in center"
            )
            return TargetDirection.forward, self.forward_driving_distance_in_cm

        logging.info(
            f"TargetArea - calculate_direction_target_central - distance to center {central_pictogram.distance_to_center()}"
        )

        movement_in_cm = self.__calculate_sideways_movement_in_cm(central_pictogram)

        logging.info(
            f"TargetArea - calculate_direction_target_central - movement_in_cm {movement_in_cm}"
        )

        if central_pictogram.is_to_the_left(epsilon):
            logging.info("TargetArea - calculate_direction_target_central - is left")
            return TargetDirection.left, movement_in_cm

        if central_pictogram.is_to_the_right(epsilon):
            logging.info("TargetArea - calculate_direction_target_central - is right")
            return TargetDirection.right, movement_in_cm

    def __calculate_sideways_movement_in_cm(self, pictogram: BoundingBox) -> int:
        return int(
            pictogram.abs_distance_to_center()
            / (pictogram.width_normalized() / self.pictogram_width_in_cm)
        )

    def __signal_target_reached(self) -> None:
        self.speaker.announce_target(self.target_pictogram)

    def __recalculate_movement(self, direction: TargetDirection, distance: int , result: NavigationResult) -> Tuple[TargetDirection, int]:
        """
        Recalculates the movement if an error occurs. Tries to move in same direction, but less far or into the opposite direction.
        """
        margin_of_safety_in_cm = 3

        # If the obstacle is less than 3cm away, don't move in this direction
        if result.error_value < margin_of_safety_in_cm:
            if direction is TargetDirection.left:
                return TargetDirection.right, margin_of_safety_in_cm
            
            elif direction is TargetDirection.right:
                return TargetDirection.left, margin_of_safety_in_cm


        elif (result.error is CommandError.obstacle_detected_left) and (direction is TargetDirection.left):
            return direction, result.error_value - margin_of_safety_in_cm

        elif (result.error is CommandError.obstacle_detected_right) and (direction is TargetDirection.right):
            return direction, result.error_value - margin_of_safety_in_cm

        logging.debug(f"TargetArea - can not handle: direction {direction}, distance {distance}, result: {result}")

        return TargetDirection.forward, margin_of_safety_in_cm

    def __hit_target_flag(self) -> NavigationResult:
        logging.info("TargetArea - Hit target flag")
        self.navigation.move_to_position(RobotPosition.drive_around)
        self.navigation.move_sideways_right(3)
        self.navigation.move_to_position(RobotPosition.hit_target_pictogram)
        # Move to target flag
        distance_to_drive = self.distance_to_flag_in_cm - self.total_forward_distance_in_cm + 15
        self.total_forward_distance_in_cm += distance_to_drive
        return self.navigation.move_forward(distance_to_drive)

    def __has_nearly_reached_target(self) -> bool:
        return self.total_forward_distance_in_cm > 0
            
