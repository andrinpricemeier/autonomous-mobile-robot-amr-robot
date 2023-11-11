from tinyk import RobotPosition
from typing import Any
from robot import Robot
from state import State
from run_completed_state import RunCompletedState
import time
import Jetson.GPIO as GPIO

class PresentationState(State):
    def __init__(self, robot: Robot) -> None:
        self.robot = robot
        self.navigation = self.robot.navigation
        self.speaker = self.robot.speaker
        self.camera = self.robot.camera
        self.object_detection = self.robot.object_detection
        self.start_button = self.robot.start_stop_button

    def enter(self) -> None:
        self.navigation.move_forward(10)
        self.navigation.rotate_sideways(90)
        self.navigation.move_sideways_right(10)
        self.navigation.move_forward(10)
        self.navigation.move_sideways_left(10)     
        self.speaker.announce_audience_detected()
        self.speaker.announce_introduction()

        self.start_button.wait_for_edge(GPIO.FALLING)

        self.speaker.announce_farewell()

        # Wait a bit to make it easier to cut the final video
        time.sleep(3)
        self.robot.transition(RunCompletedState(self.robot))
