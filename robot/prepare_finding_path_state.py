from finding_path_state import FindingPathState
from robot import Robot
from state import State


class PrepareFindingPathState(State):
    """Represents the state for preparing the path finding.
    Basically we simply move to an optimal position.

    Args:
        State ([type]): the superclass.
    """
    def __init__(self, robot: Robot) -> None:
        """Creates a new instance.

        Args:
            robot (Robot): the robot.
        """
        self.robot = robot
        self.start_area = robot.competition_area.start_area
        self.stairs_area = robot.competition_area.stairs_area
        self.target_area = robot.competition_area.target_area

    def enter(self) -> None:
        """Prepares the robot for finding the path.
        """
        self.start_area.move_to_optimal_path_finding_position()
        self.robot.transition(FindingPathState(self.robot))
