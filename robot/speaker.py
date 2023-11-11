from detected_object import DetectedObject
from tinyk import RobotPosition

class Announcement():
    """Represents an announcement spoken through the speakers.
    """
    def output_filename(self) -> str:
        """The mp3 filename to play.

        Returns:
            str: the mp3 filepath.
        """
        pass

    def is_debug_only(self) -> bool:
        """True if this announcement should only be played in debug mode.

        Returns:
            bool: True if this announcement should only be played in debug mode.
        """
        return False

class Speaker:
    """Represents the physical speakers connected to the Jetson Nano.
    """
    def announce_start(self, pictogram: DetectedObject) -> None:
        """Announces that we found the start pictogram.

        Args:
            pictogram (DetectedObject): the pictogram that was found.
        """
        pass

    def announce_target(self, pictogram: DetectedObject) -> None:
        """Announces that the target pictogram was found.

        Args:
            pictogram (DetectedObject): the pictogram that was found.
        """
        pass

    def announce_path_found(self) -> None:
        """Announces that a path has been found.
        """
        pass

    def announce_path_not_found(self) -> None:
        """Announces that no path could be found.
        """
        pass

    def announce_run_started(self) -> None:
        """Announces that the run has started.
        """
        pass

    def announce_run_completed(self) -> None:
        """Announces that the run has been completed.
        """
        pass

    def announce_run_stopped(self) -> None:
        """Announces that the run has been stopped, usually due to some kind of error.
        """
        pass

    def announce_state_transition(self, state_class_name: str) -> None:
        """Announces a state transition of the robot (e.g. from initialized to detecting the start pictogram).

        Args:
            state_class_name (str): the name of the state class, exactly as it's specified in the Python file.
        """
        pass

    def announce_sideways_left(self, movement_in_cm: int) -> None:
        """Announces that we're moving a certain amount to the left.

        Args:
            movement_in_cm (int): the amount we're moving.
        """
        pass

    def announce_sideways_right(self, movement_in_cm: int) -> None:        
        """Announces that we're moving a certain amount to the right.

        Args:
            movement_in_cm (int): the amount we're moving.
        """
        pass

    def announce_bricks(self, bricks_count: int) -> None:
        """Announces the amount of bricks we found.

        Args:
            bricks_count (int): the number of bricks detected.
        """
        pass

    def announce_no_target_pictogram(self) -> None:
        """Announces the scenario where no start pictogram was found ergo no target pictogram has been set.
        """
        pass

    def announce_start_pictogram_found_area(self) -> None:
        """Announces that the area filter matched for finding the start pictogram.
        """
        pass

    def announce_start_pictogram_found_height(self) -> None:
        """Announces that the height filter matched for finding the start pictogram.
        """
        pass

    def announce_stairs_area_execute_climbing_plan(self) -> None:
        """Announces that we're executing a climbing plan.
        """
        pass

    def announce_stairs_area_using_path_climbing_plan(self) -> None:
        """Announces that we're executing the path climbing plan.
        """
        pass

    def announce_stairs_area_using_sensor_climbing_plan(self) -> None:
        """Announces that we're executing the sensor climbing plan.
        """
        pass

    def announce_stairs_area_climbing_plan_failed_has_backupplan(self) -> None:
        """Announces that the climbing plan failed but we have a backup plan.
        """
        pass

    def announce_stairs_area_climbing_plan_failed_no_backupplan(self) -> None:
        """Announces that the climbing plan failed and we don't have any backup.
        """
        pass

    def announce_path_climbing_plan_error_found(self) -> None:
        """Announces that some sort of error occurred during climbing.
        """
        pass

    def announce_path_climbing_plan_completed(self) -> None:
        """Announces the completion of the climbing plan.
        """
        pass

    def announce_path_climbing_plan_obstacle_found(self) -> None:
        """Announces that an unforeseen obstacle was found.
        """
        pass

    def announce_move_forward(self) -> None:
        """Announces that we're moving forward.
        """
        pass

    def announce_move_forward_until_obstacle(self) -> None:
        """Announces that we're moving forward until there's an obstacle.
        """
        pass

    def announce_rotate_clockwise(self) -> None:
        """Announces that we're rotating clockwise.
        """
        pass

    def announce_rotate_counter_clockwise(self) -> None:
        """Announces that we're moving counter clockwise.
        """
        pass

    def announce_move_backward(self) -> None:
        """Announces that we're moving backwards.
        """
        pass

    def announce_climb(self) -> None:
        """Announces that we're climbing.
        """
        pass

    def announce_init_master(self) -> None:
        """Announces that we're initializing the MasterTinyK.
        """
        pass

    def announce_shutdown_master(self) -> None:
        """Announces that we're shutting down the MasterTinyK.
        """
        pass

    def announce_change_robot_position(self, position: RobotPosition) -> None:
        """Announces that we're changing the robot's position.

        Args:
            position (RobotPosition): the new position.
        """
        pass

    def announce_press_start_button(self) -> None:
        """Announces that we're ready to start the run and the start button can be pressed.
        """
        pass

    def announce_start_pictogram_not_found(self) -> None:
        """Announces that no start pictogram was found.
        """
        pass

    def announce_indiana_jones(self) -> None:
        """Plays the team's song.
        """
        pass    

    def announce_audience_detected(self) -> None:
        pass    

    def announce_introduction(self) -> None:
        pass
    
    def announce_farewell(self) -> None:
        pass
