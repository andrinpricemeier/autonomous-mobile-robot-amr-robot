from stairs_area import StairsArea
from state import State
from finding_target_pictogram_state import FindingTargetPictogramState
from robot import Robot
import logging


class ClimbingStairsState(State):
    """Represents the state wherein the robot climbs the stairs.

    Args:
        State ([type]): the superclass.
    """
    def __init__(self, robot: Robot) -> None:
        """Creates a new instance.

        Args:
            robot (Robot): a reference to the robot.
        """
        self.robot = robot
        self.stairs_area: StairsArea = self.robot.competition_area.stairs_area

    def enter(self) -> None:
        """Starts the state.
        """
        logging.info("ClimbingStairsState - formulate_plan")
        self.stairs_area.formulate_plan()

        logging.info("ClimbingStairsState - climb")
        self.stairs_area.climb()
        logging.info("ClimbingStairsState - climbing finished")

        self.robot.transition(FindingTargetPictogramState(self.robot))
