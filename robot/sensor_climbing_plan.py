from guidance.stairs_map import StairsMap
from movement import Movement, MovementInCm
from navigation import Navigation, NavigationResult
from climbing_plan import ClimbingPlan
from guidance.path_finder import PathFinder
import logging
import image_logging
import img_utils
from path import Path
from tinyk import CommandError, RobotPosition
from speaker import Speaker

class SensorClimbingPlan(ClimbingPlan):
    """Represents a climbing plan that only works by using the sensors.

    Args:
        ClimbingPlan ([type]): the superclass.
    """
    def __init__(
        self, stairs_map: StairsMap, navigation: Navigation, path_finder: PathFinder, speaker: Speaker
    ) -> None:
        self.path: Path = None
        self.stairs_map: StairsMap = stairs_map
        self.navigation: Navigation = navigation
        self.movement_in_cm = stairs_map.cell_width_in_cm
        self.path_finder = path_finder
        self.target_area_reached = False
        self.speaker = speaker

    def execute(self) -> None:
        """Executes the plan.
        """
        # Object detection with path finding failed, that's why we assume nothing about our environment.
        self.stairs_map.clear_obstacles()
        self.__recalculate_path()
        logging.info("SensorClimbingPlan - Execution started")
        movement: MovementInCm = self.path.get_next_movement()
        while movement is not None:
            logging.debug(f"SensorClimbingPlan - execute_movement {movement}")
            result: NavigationResult = self.__execute_movement(movement)
            if not result.success:
                logging.error(
                    f"SensorClimbingPlan - Executing plan has error {result.error}"
                )
                self.__handle_error(result, movement)
            else:
                logging.debug(f"SensorClimbingPlan - update map with {movement}")
                self.__update_map__position(movement)
                if movement.movement == Movement.climb:
                    logging.debug(f"SensorClimbingPlan - move to correct position and drive forward")
                    self.navigation.move_forward(3)
                    self.navigation.move_to_position(RobotPosition.hit_stairs)
                    self.navigation.move_forward(2)    
                    self.navigation.move_backwards(1)                
                    if self.stairs_map.is_in_target_area() and not self.target_area_reached:
                        self.navigation.move_forward(13)
                        self.target_area_reached = True

            movement: MovementInCm = self.path.get_next_movement()
            image_logging.log(
                "sensorplan_stairs_map_with_obstacles.jpg",
                img_utils.render_map_with_path(self.stairs_map, self.path),
            )
        logging.info("SensorClimbingPlan - Execution finished")

    def __execute_movement(self, movement_in_cm: MovementInCm) -> NavigationResult:
        """
        Executes the movement.
        """
        if movement_in_cm.movement == Movement.climb:
            self.navigation.move_to_position(RobotPosition.drive_on_stairs)
            return self.navigation.climb()

        elif movement_in_cm.movement == Movement.left:
            self.navigation.move_to_position(RobotPosition.go_home)
            return self.navigation.move_sideways_left(movement_in_cm.distance_in_cm)

        elif movement_in_cm.movement == Movement.right:
            self.navigation.move_to_position(RobotPosition.go_home)
            return self.navigation.move_sideways_right(movement_in_cm.distance_in_cm)

        logging.error(f"Unknown Movement: {movement_in_cm.movement}")
        raise Exception(f"Unknown Movement: {movement_in_cm}")

    def __update_map__position(self, movement_in_cm: MovementInCm) -> None:
        """
        Updates the position in the Map depending on the movement!
        """
        if movement_in_cm.movement == Movement.climb:
            return self.stairs_map.move_position_up()

        elif movement_in_cm.movement == Movement.left:
            return self.stairs_map.move_position_left_in_distance(movement_in_cm.distance_in_cm)

        elif movement_in_cm.movement == Movement.right:
            return self.stairs_map.move_position_right_in_distance(movement_in_cm.distance_in_cm)

        logging.error(f"Unknown Movement: {movement_in_cm}")
        raise Exception(f"Unknown Movement: {movement_in_cm}")

    def __handle_error(self, result: NavigationResult, movement_in_cm: MovementInCm) -> None:
        """
        Handles the error, if a movement fails.
        Raises an exception, if it can not handle the error.
        """
        logging.info(
            f"SensorClimbingPlan - __handle_error - handle error {result.error} with value: {result.error_value} from movement {movement_in_cm}"
        )

        if result.error == CommandError.obstacle_detected_left and movement_in_cm.movement == Movement.left:
            self.speaker.announce_path_climbing_plan_obstacle_found()
            logging.info(f"SensorClimbingPlan - __handle_error - detected obstacle in {result.error_value} cm, set obstacle left")
            self.stairs_map.set_obstacle_left_in_distance(result.error_value)

        elif (
            result.error == CommandError.obstacle_detected_right and movement_in_cm.movement == Movement.right
        ):
            self.speaker.announce_path_climbing_plan_obstacle_found()
            logging.info(f"SensorClimbingPlan - __handle_error - detected obstacle in {result.error_value} cm, set obstacle right")
            self.stairs_map.set_obstacle_right_in_distance(result.error_value)

        elif (
            result.error == CommandError.obstacle_detected_front and movement_in_cm.movement == Movement.climb
        ):
            self.speaker.announce_path_climbing_plan_obstacle_found()
            logging.info("SensorClimbingPlan - __handle_error - set obstacle front")
            self.stairs_map.set_obstacle_front()

        else:
            image_logging.log(
                "stairs_map_with_obstacles.jpg",
                img_utils.render_map_with_path(self.stairs_map, self.path),
            )
            logging.error(
                f"SensorClimbingPlan - Plan failed - __handle_error failed - can not handle error {result.error} from movement {movement_in_cm.movement}"
            )
            raise Exception(
                f"SensorClimbingPlan - Plan failed - __handle_error failed - can not handle error {result.error} from movement {movement_in_cm.movement}"
            )

        logging.info("SensorClimbingPlan - recalculate path")
        self.__recalculate_path()
        
    def __recalculate_path(self) -> None:
        self.stairs_map.set_start_cell(self.stairs_map.position)
        self.path = self.path_finder.find_path(
            self.stairs_map, self.stairs_map.position, self.stairs_map.goal
        )
        if self.path is None:
            image_logging.log(
                "stairs_map_with_obstacles.jpg", img_utils.render_map(self.stairs_map)
            )
            if self.stairs_map.is_in_target_area():
                logging.warn("SensorClimbingPlan - Plan failed - we're in the target area though that's why we give control to the finding target state.")
                # Create an empty path that will lead the main loop of the plan to stop and give
                # control to the finding target pictogram state.
                self.path = Path([], self.stairs_map.cell_width_in_cm)
            else:
                logging.error(
                    "SensorClimbingPlan - Plan failed - __recalculate_path failed"
                )
                raise Exception(
                    "SensorClimbingPlan - Plan failed - __recalculate_path failed"
                )

    def __eq__(self, o: object) -> bool:
        return (
            self.path == o.path
            and self.stairs_map == o.stairs_map
            and self.navigation == o.navigation
        )
