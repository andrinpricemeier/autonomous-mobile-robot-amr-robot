from climbing_stairs_state import ClimbingStairsState
from state import State
from robot import Robot
from start_area import StartArea


class MoveToStairsState(State):
    """Represents the state wherein the robot moves to the stairs so that we can start climbing.

    Args:
        State ([type]): the superclass.
    """
    def __init__(self, robot: Robot) -> None:
        """Creates a new instance.

        Args:
            robot (Robot): the robot.
        """
        self.robot = robot
        self.start_area: StartArea = robot.competition_area.start_area

    def enter(self) -> None:
        """Starts moving to the stairs.
        """
        self.start_area.move_to_climbing_start_position()
        self.robot.transition(ClimbingStairsState(self.robot))
