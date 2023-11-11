from path_object_detection import PathObjectDetection, PathObjectDetectionResult
from speaker import Speaker
from tinyk import RobotPosition
from edge_detection import EdgeDetection
from stairs_positioner import (
    FinetuneStairsPositionerStrategy,
    PathFindingPositioner,
    PositionerStrategy,
    RoughStairsPositionerStrategy,
)
from camera import Camera
from navigation import Navigation
from pictogram_detection import PictogramDetection
from stairs_detection import StairsDetection
from detected_object import DetectedObject
from bounding_box import BoundingBox
import logging
import random
import image_logging
import img_utils
import time


class StartArea:
    def __init__(
        self,
        navigation: Navigation,
        camera: Camera,
        edge_detection: EdgeDetection,
        pictogram_detection: PictogramDetection,
        stairs_detection: StairsDetection,
        path_object_detection: PathObjectDetection,
        speaker: Speaker,
        start_pictogram_min_area: int,
        stairs_optimal_left_offset: int,
        stairs_width_in_cm: int,
        steps_width_in_cm: int
    ) -> None:
        self.navigation: Navigation = navigation
        self.camera: Camera = camera
        self.edge_detection: EdgeDetection = edge_detection
        self.pictogram_detection: PictogramDetection = pictogram_detection
        self.stairs_detection: StairsDetection = stairs_detection
        self.path_object_detection: PathObjectDetection = path_object_detection
        self.fine_tune_stairs_positioner: PositionerStrategy = (
            FinetuneStairsPositionerStrategy(
                self.edge_detection, self.camera, self.navigation, steps_width_in_cm, True
            )
        )
        self.path_finding_positioner: PathFindingPositioner = PathFindingPositioner(
            RoughStairsPositionerStrategy(
                self.stairs_detection,
                self.pictogram_detection,
                self.camera,
                self.navigation,
                stairs_optimal_left_offset,
                stairs_width_in_cm
            )
        )
        self.speaker = speaker
        self.start_pictogram_min_area = start_pictogram_min_area

    def find_path_objects(self) -> PathObjectDetectionResult:
        """
        Finds the objects for path finding and returns the detected Objects and the corresponding camera image.
        """
        retries = 4
        total_movement_left = 0
        total_movement_right = 0
        for i in range(retries):
            logging.debug(f"Finding steps try {i}")
            image = self.camera.take_picture()
            image_logging.log(
                image_logging.RAW_IMAGE + "start_area_find_path_objects.jpg", image
            )
            path_object_detection_result: PathObjectDetectionResult = self.path_object_detection.detect(image)
            if path_object_detection_result.get_steps() is not None:
                self.__move_back_to_origin(total_movement_left, total_movement_right)
                return path_object_detection_result
            else:
                logging.warn(
                    "No steps detected. Moving a little and then trying again."
                )
                movement_in_cm = random.randint(1, 5)
                if i % 2 == 0:
                    self.navigation.move_sideways_left(movement_in_cm)
                    total_movement_left += movement_in_cm
                else:
                    self.navigation.move_sideways_right(movement_in_cm)
                    total_movement_right += movement_in_cm
        self.__move_back_to_origin(total_movement_left, total_movement_right)
        raise Exception("Failed to detect steps. Giving up.")

    def __move_back_to_origin(
        self, total_movement_left: int, total_movement_right: int
    ) -> None:
        distance_from_origin = total_movement_left - total_movement_right
        logging.info(
            f"Moving back to origin: left: {total_movement_left}, right: {total_movement_right}"
        )
        if distance_from_origin > 0:
            self.navigation.move_sideways_right(distance_from_origin)
        elif distance_from_origin < 0:
            self.navigation.move_sideways_left(abs(distance_from_origin))

    def find_pictogram_180_then_360(self) -> DetectedObject:
        self.path_finding_positioner.move_to_optimal_path_finding_position()
        self.navigation.move_forward(15)
        for i in range(3):
            pictogram = self.find_pictogram_90_clockwise()
            if pictogram is not None:
                logging.info("90 degrees clockwise - pictogram found.")
                return pictogram
            logging.warn("90 degrees clockwise - no pictogram found. Trying counter clockwise.")
            pictogram = self.find_pictogram_90_counter_clockwise()
            if pictogram is not None:
                logging.info("90 degrees counter clockwise - pictogram found.")
                return pictogram
            logging.warn("90 degrees counter clockwise - no pictogram found. Trying rest 180 degrees.")
            logging.warn("180 degrees approach failed. Trying rest 180 degrees approach.")
            self.navigation.move_forward(20)
            pictogram = self.find_pictogram_180_rest()
            if pictogram is not None:
                logging.info("Found pictogram. Returning.")
                return pictogram
            self.navigation.move_forward(5)

        logging.warn("Rest 180 degrees approach failed.")
        return None
    
    def find_pictogram_90_clockwise(self) -> DetectedObject:
        amount_rotated_in_degrees = 0
        rotation_per_step = 45
        while True:
            time.sleep(0.5)
            image = self.camera.take_picture()
            image_logging.log(
                image_logging.RAW_IMAGE + "start_area_find_pictograms_90_clockwise.jpg", image
            )
            pictogram = self.pictogram_detection.find_closest_in_distance(image)
            if pictogram is not None and self.is_pictogram_in_start_area(pictogram):
                self.navigation.rotate_sideways(amount_rotated_in_degrees)
                image_logging.log(
                    "start_area_find_pictograms_detected_pictogram_90_clockwise.jpg",
                    img_utils.render_boxes(image, [pictogram]),
                )
                return pictogram.detected_object
            if amount_rotated_in_degrees >= 90:
                # Don't rotate back to 0 but to the correct position for rotating 90 degrees to the other side.
                self.navigation.rotate_sideways(abs(-45 - amount_rotated_in_degrees))
                return None
            self.navigation.rotate_sideways(-1 * rotation_per_step)
            amount_rotated_in_degrees += rotation_per_step

    def find_pictogram_90_counter_clockwise(self) -> DetectedObject:
        # The previous step already rotated us 45 degrees to speed up the process.
        amount_rotated_in_degrees = 45
        rotation_per_step = 45
        while True:
            time.sleep(0.5)
            image = self.camera.take_picture()
            image_logging.log(
                image_logging.RAW_IMAGE + "start_area_find_pictograms_90_counter_clockwise.jpg", image
            )
            pictogram = self.pictogram_detection.find_closest_in_distance(image)
            if pictogram is not None and self.is_pictogram_in_start_area(pictogram):
                self.navigation.rotate_sideways(-1 * amount_rotated_in_degrees)
                image_logging.log(
                    "start_area_find_pictograms_detected_pictogram_90_counter_clockwise.jpg",
                    img_utils.render_boxes(image, [pictogram]),
                )
                return pictogram.detected_object
            if amount_rotated_in_degrees >= 90:
                self.navigation.rotate_sideways(-1 * amount_rotated_in_degrees)
                return None
            self.navigation.rotate_sideways(rotation_per_step)
            amount_rotated_in_degrees += rotation_per_step

    def find_pictogram_180_rest(self) -> DetectedObject:
        rotation_per_step = 45        
        self.navigation.rotate_sideways(135)
        amount_rotated_in_degrees = 135
        while True:
            time.sleep(0.5)
            image = self.camera.take_picture()
            image_logging.log(
                image_logging.RAW_IMAGE + "start_area_find_pictograms_180_rest_clockwise.jpg", image
            )
            pictogram = self.pictogram_detection.find_closest_in_distance(image)
            if pictogram is not None and self.is_pictogram_in_start_area(pictogram):
                self.navigation.rotate_sideways(-1 * amount_rotated_in_degrees)
                image_logging.log(
                    "start_area_find_pictograms_detected_pictogram_180_rest_clockwise.jpg",
                    img_utils.render_boxes(image, [pictogram]),
                )
                return pictogram.detected_object
            if amount_rotated_in_degrees >= 225:
                self.navigation.rotate_sideways(-1 * amount_rotated_in_degrees)
                return None
            self.navigation.rotate_sideways(rotation_per_step)
            amount_rotated_in_degrees += rotation_per_step

    def move_to_optimal_path_finding_position(self) -> None:
        logging.info("StartArea - move_to_optimal_path_finding_position")
        # TODO: uncomment
        # self.navigation.move_to_position(RobotPosition.stand_up)
        self.path_finding_positioner.move_to_optimal_path_finding_position()

    def move_to_climbing_start_position(self) -> None:
        self.navigation.move_to_position(RobotPosition.hit_stairs)
        if not self.navigation.move_forward_until_obstacle(130).success:
            while not self.navigation.move_forward_until_obstacle(15).success:
                pass

        logging.info("StartArea - moving backwards 130cm")

        time.sleep(1)

        self.navigation.move_to_position(RobotPosition.drive_around)

        self.navigation.move_backwards(130)

        self.fine_tune_stairs_positioner.move_to_center(20)

        self.navigation.move_to_position(RobotPosition.hit_stairs)

        if not self.navigation.move_forward_until_obstacle(120).success:
            while not self.navigation.move_forward_until_obstacle(15).success:
                pass

    def is_pictogram_in_start_area(self, pictogram: BoundingBox) -> bool:
        area = pictogram.area_normalized()
        if area >= self.start_pictogram_min_area:
            self.speaker.announce_start_pictogram_found_area()
            return True
        else:
            return False
            # Tobias: The pictograms are so close that they are of a similar y-distance like the target pictograms.
            #self.speaker.announce_start_pictogram_found_height()
            #return pictogram.v2 >= self.start_pictogram_min_y_offset
