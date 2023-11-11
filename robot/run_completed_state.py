from state import State
from robot import Robot
from camera import Camera


class RunCompletedState(State):
    """State that completes the run.

    Args:
        State ([type]): the superclass.
    """
    def __init__(self, robot: Robot) -> None:
        """Creates a new instance.

        Args:
            robot (Robot): the superclass.
        """
        self.robot = robot
        self.camera: Camera = robot.camera
        self.speaker = robot.speaker

    def enter(self) -> None:
        """Plays our team's song and ends the run.
        """
        self.speaker.announce_indiana_jones()
        self.camera.destroy()
        self.robot.end_run()
