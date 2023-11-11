from tinyk import RobotPosition
from typing import Any
from robot import Robot
from state import State
from detecting_start_pictogram_state import DetectingStartPictogramState
from presentation_state import PresentationState
import logging
import Jetson.GPIO as GPIO


class InitializedState(State):
    """Represents the state wherin the robot is fully warmed up and waiting for
    someone to press the start button.

    Args:
        State ([type]): the superclass.
    """
    def __init__(self, robot: Robot) -> None:
        """Creates a new instance.

        Args:
            robot (Robot): the robot.
        """
        self.robot = robot
        self.navigation = self.robot.navigation
        self.start_button = self.robot.start_stop_button
        self.speaker = self.robot.speaker
        self.camera = self.robot.camera
        self.object_detection = self.robot.object_detection

    def enter(self) -> None:
        """Initializes and waits for the start button to be pressed.
        """
        # Save time by moving to the correct position before the run starts.
        self.navigation.move_to_position(RobotPosition.go_home)
        self.navigation.move_to_position(RobotPosition.drive_around)
        self.speaker.announce_press_start_button()
        self.start_button.wait_for_edge(GPIO.FALLING)
        logging.info(f"Start button pressed. Starting competition run.")
        self.speaker.announce_run_started()
        self.robot.emergency_stop_watchdog.activate()
        self.robot.transition(DetectingStartPictogramState(self.robot))
        # Tobias: Uncomment this line to activate the presentation / entrance mode
        # The entrances themselves are in the presentation state.
        # self.robot.transition(PresentationState(self.robot))
