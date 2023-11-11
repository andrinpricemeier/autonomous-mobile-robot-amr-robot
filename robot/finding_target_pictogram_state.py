import logging
from run_completed_state import RunCompletedState
from robot import Robot
from state import State
from target_area import TargetArea


class FindingTargetPictogramState(State):
    """Represents the state in which the robot finds the target pictogram and ends the run.

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
        self.target_area: TargetArea = self.robot.competition_area.target_area

    def enter(self) -> None:
        """Starts the process of finding the target pictogram.
        """
        logging.info(f"Finding target pictogram {self.target_area.target_pictogram}.")

        try:
            self.target_area.move_to_target_flag()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logging.exception("Moving to the target flag failed. Completing run.", e)
            pass

        self.robot.transition(RunCompletedState(self.robot))
