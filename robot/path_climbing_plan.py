from guidance.a_star_path_finder import AStarPathFinder
from guidance.a_star_path_finder_obstacle_avoider import AStarPathFinderObstacleAvoider
from guidance.a_star_space_optimized_path_finder import AStarSpaceOptimizedPathFinder
from guidance.path_finder import PathFinder
from speaker import Speaker
from tinyk import CommandError, RobotPosition
from movement import Movement, MovementInCm
from climbing_plan import ClimbingPlan
from path import Path
from navigation import Navigation, NavigationResult
from guidance.stairs_map import StairsMap
import logging
import image_logging
import img_utils


class PathClimbingPlan(ClimbingPlan):
    """
    Executes a given plan based on a path.
    """

    def __init__(
        self, path: Path, stairs_map: StairsMap, navigation: Navigation, speaker: Speaker
    ) -> None:
        self.path = path
        self.stairs_map = stairs_map
        self.navigation = navigation
        self.movement_in_cm = stairs_map.cell_width_in_cm
        self.path_finder: PathFinder = AStarPathFinderObstacleAvoider()
        #self.path_finder: PathFinder = AStarSpaceOptimizedPathFinder()
        self.speaker = speaker
        self.target_area_reached = False

    def execute(self) -> None:
        """
        Executes the plan. Throws an exception if plan fails.
        """

        logging.info("PathClimbingPlan - Execution started")

        movement: MovementInCm = self.path.get_next_movement()

        while movement is not None:
            logging.debug(f"PathClimbingPlan - execute_movement {movement}")
            result: NavigationResult = self.__execute_movement(movement)
            if not result.success:
                self.speaker.announce_path_climbing_plan_error_found()
                logging.error(
                    f"PathClimbingPlan - Executing plan has error {result.error}"
                )
                self.__handle_error(result, movement)

            else:
                logging.debug(f"PathClimbingPlan - update stairs_map with {movement}")
                self.__update_stairs_map__position(movement)
                if movement.movement == Movement.climb:
                    logging.debug(f"PathClimbingPlan - move to correct position and drive forward")
                    self.navigation.move_forward(3)
                    self.navigation.move_to_position(RobotPosition.hit_stairs)
                    self.navigation.move_forward(2)
                    self.navigation.move_backwards(1)
                    if self.stairs_map.is_in_target_area() and not self.target_area_reached:
                        self.navigation.move_forward(13)
                        self.target_area_reached = True

            movement: MovementInCm = self.path.get_next_movement()
            image_logging.log(
                "stairs_map_with_obstacles.jpg",
                img_utils.render_map_with_path(self.stairs_map, self.path),
            )
        self.speaker.announce_path_climbing_plan_completed()
        logging.info("PathClimbingPlan - Execution finished")

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

    def __update_stairs_map__position(self, movement_in_cm: MovementInCm) -> None:
        """
        Updates the position in the Map depending on the movement!
        """
        # TODO: Move multiple position if movement is more then 1 grid cell
        if movement_in_cm.movement == Movement.climb:
            return self.stairs_map.move_position_up()

        elif movement_in_cm.movement == Movement.left:
            return self.stairs_map.move_position_left_in_distance(movement_in_cm.distance_in_cm)

        elif movement_in_cm.movement == Movement.right:
            return self.stairs_map.move_position_right_in_distance(movement_in_cm.distance_in_cm)

        logging.error(f"Unknown Movement: {movement_in_cm}")
        raise Exception("Unknown Movement: {movement}")

    def __handle_error(self, result: NavigationResult, movement_in_cm: MovementInCm) -> None:
        """
        Handles the error, if a movement fails.
        Raises an exception, if it can not handle the error.
        """
        logging.info(
            f"PathClimbingPlan - __handle_error - handle error {result.error} with value: {result.error_value} from movement {movement_in_cm}"
        )

        if result.error == CommandError.obstacle_detected_left and movement_in_cm.movement == Movement.left:
            self.speaker.announce_path_climbing_plan_obstacle_found()
            logging.info(f"PathClimbingPlan - __handle_error - detected obstacle in {result.error_value} cm, set obstacle left")
            self.stairs_map.set_obstacle_left_in_distance(result.error_value)

        elif (
            result.error == CommandError.obstacle_detected_right and movement_in_cm.movement == Movement.right
        ):
            self.speaker.announce_path_climbing_plan_obstacle_found()
            logging.info(f"PathClimbingPlan - __handle_error - detected obstacle in {result.error_value} cm, set obstacle right")
            self.stairs_map.set_obstacle_right_in_distance(result.error_value)

        elif (
            result.error == CommandError.obstacle_detected_front and movement_in_cm.movement == Movement.climb
        ):
            self.speaker.announce_path_climbing_plan_obstacle_found()
            logging.info("PathClimbingPlan - __handle_error - set obstacle front")
            self.stairs_map.set_obstacle_front()

        else:
            image_logging.log(
                "stairs_map_with_obstacles.jpg",
                img_utils.render_map_with_path(self.stairs_map, self.path),
            )
            logging.error(
                f"PathClimbingPlan - Plan failed - __handle_error failed - can not handle error {result.error} from movement {movement_in_cm.movement}"
            )
            raise Exception(
                f"PathClimbingPlan - Plan failed - __handle_error failed - can not handle error {result.error} from movement {movement_in_cm.movement}"
            )

        logging.info("PathClimbingPlan - recalculate path")
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
            logging.error("PathClimbingPlan - Plan failed - __recalculate_path failed")
            raise Exception(
                "PathClimbingPlan - Plan failed - __recalculate_path failed"
            )

    def __eq__(self, o: object) -> bool:
        return (
            self.path == o.path
            and self.stairs_map == o.stairs_map
            and self.navigation == o.navigation
        )
