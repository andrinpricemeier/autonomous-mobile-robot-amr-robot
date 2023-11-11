from robot import Robot
from warming_up_state import WarmingUpState

# This class pulls everything together and actually executes the run.
robot = Robot()
robot.transition(WarmingUpState(robot))
robot.run()
