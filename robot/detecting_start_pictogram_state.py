from robot import Robot
from state import State
from prepare_finding_path_state import PrepareFindingPathState
from run_completed_state import RunCompletedState
import logging

class DetectingStartPictogramState(State):
    """Represents the state in the start area when we're looking for the start pictogram.

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
        self.stairs_area = robot.competition_area.stairs_area
        self.target_area = robot.competition_area.target_area
        self.speaker = robot.speaker
        self.camera = robot.camera
        self.object_detection = robot.object_detection

    def enter(self) -> None:
        """Starts the state actions.
        """
        self.target_area.target_pictogram = self.start_area.find_pictogram_180_then_360()
        if self.target_area.target_pictogram is None:
            logging.error("Failed to find start pictogram. Stopping run.")
            self.speaker.announce_start_pictogram_not_found()     
            self.robot.transition(RunCompletedState(self.robot))
        else:
            logging.info(
                f"DetectingStartPictogramState: found pictogram {self.target_area.target_pictogram}"
            )
            self.speaker.announce_start(self.target_area.target_pictogram)
            self.robot.transition(PrepareFindingPathState(self.robot))
