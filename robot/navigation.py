from tinyk import (
    ClimbCommand,
    InitializeCommand,
    MoveForwardCommand,
    MoveToPositionCommand,
    RobotPosition,
    RotateClockwiseCommand,
    RotateCounterClockwiseCommand,
    ShutdownCommand,
    TinyK,
    MoveLeftCommand,
    MoveRightCommand,
    MoveBackwardCommand,
)
from tinyk import ResponseType, CommandError
import logging
from typing import List
from speaker import Speaker
import time


class NavigationResult:
    """Represents the outcome of a navigation action.
    Abstracts away the details of the communication with the TinyK.
    """
    def __init__(self, success: bool, error: CommandError, error_value: int = 0) -> None:
        """Creates a new instance.

        Args:
            success (bool): True if the navigation action was successful.
            error (CommandError): the error if something failed.
            error_value (int, optional): Additional information for the error. Defaults to 0.
        """
        self.success = success
        self.error = error
        # Distance to obstacle if obstacle is detected!
        self.error_value = error_value


class Navigation:
    """Represents a class used for navigating/moving the robot physically.
    """
    def __init__(self, tinyK: TinyK, speaker: Speaker) -> None:
        """Creates a new instance.

        Args:
            tinyK (TinyK): the TinyK interface that executes the actual movements.
            speaker (Speaker): the speaker used to announce state changes.
        """
        self.tinyK = tinyK
        self.speaker = speaker

    def initialize(self) -> NavigationResult:
        """Initializes the TinyK.

        Returns:
            NavigationResult: the result.
        """
        self.speaker.announce_init_master()
        logging.debug("Navigation - initialize")
        self.tinyK.execute(InitializeCommand())
        resp = self.tinyK.wait_for_response()
        if resp.type == ResponseType.ack:
            resp = self.tinyK.wait_for_response()
            if resp.type == ResponseType.completed:
                return NavigationResult(True, None)

        logging.error(
            f"Navigation - initialize - not completed | reason {resp.type}, error {CommandError(resp.payload).name}"
        )
        return NavigationResult(False, CommandError(resp.payload))

    def move_forward(self, movement_in_cm: int) -> NavigationResult:
        """Moves forward the given amount of centimetres.

        Args:
            movement_in_cm (int): the movement in cm.

        Returns:
            NavigationResult: the result.
        """
        self.speaker.announce_move_forward()
        logging.debug(f"Navigation - move_forward {movement_in_cm}cm")
        self.tinyK.execute(MoveForwardCommand(movement_in_cm))
        resp = self.tinyK.wait_for_response()
        if resp.type == ResponseType.ack:
            resp = self.tinyK.wait_for_response()
            if resp.type == ResponseType.completed:
                return NavigationResult(True, None)

        logging.error(
            f"Navigation - move_forward {movement_in_cm}cm - not completed | reason {resp.type}, error {CommandError(resp.payload).name}"
        )
        return NavigationResult(False, CommandError(resp.payload))

    def move_forward_until_obstacle(self, movement_in_cm: int) -> NavigationResult:
        """Moves forward the given amount of centimetres and announces success if an obstacle was detected.
        Useful for moving forward until we've reached the stairs.

        Args:
            movement_in_cm (int): the movement in cm.

        Returns:
            NavigationResult: the result.
        """
        self.speaker.announce_move_forward_until_obstacle()
        logging.debug(f"Navigation - move_forward_until_obstacle {movement_in_cm}cm")
        self.tinyK.execute(MoveForwardCommand(movement_in_cm))
        resp = self.tinyK.wait_for_response()
        if resp.type == ResponseType.ack:
            resp = self.tinyK.wait_for_response()
            if (
                resp.type == ResponseType.failed
                and resp.payload == CommandError.obstacle_detected_front
            ):
                logging.info("Navigation - obstacle front detected, giving back success")
                return NavigationResult(True, None)

        logging.error(
            f"Navigation - move_forward_until_obstacle {movement_in_cm}cm - not completed | reason haven't reached obstacle yet"
        )
        return NavigationResult(False, None)

    def rotate_sideways(self, degrees: int) -> None:
        """
        Rotates the robot sideways.
        Positive values are rotations counter-clockwise. Negative values clockwise.
        """
        logging.debug(f"Navigation - rotate_sideways {degrees} degrees")
        if degrees == 0:
            return
        rotate_counter_clockwise: bool = degrees > 0
        if rotate_counter_clockwise:
            self.speaker.announce_rotate_counter_clockwise()
        else:
            self.speaker.announce_rotate_clockwise()
        pending_rotations: int = abs(degrees)
        # We only have 255 degrees available per command that's why we have to send the commands piecewise.
        while pending_rotations > 0:
            rotation_batch: int = 0
            if pending_rotations <= 255:
                rotation_batch = pending_rotations
                pending_rotations = 0
            else:
                rotation_batch = 255
                pending_rotations -= 255
            if rotate_counter_clockwise:
                self.tinyK.execute(RotateCounterClockwiseCommand(rotation_batch))
            else:
                self.tinyK.execute(RotateClockwiseCommand(rotation_batch))
            resp = self.tinyK.wait_for_response()
            if resp.type == ResponseType.ack:
                resp = self.tinyK.wait_for_response()
                if resp.type != ResponseType.completed:
                    return NavigationResult(False, resp.payload)
            else:
                return NavigationResult(False, resp.payload)
        return NavigationResult(True, None)

    def move_sideways_left(self, movement_in_cm: int) -> NavigationResult:
        """
        Moves the robot sideways to the left.
        """
        logging.debug(f"Navigation - move_sideways_left {movement_in_cm}cm")
        self.speaker.announce_sideways_left(movement_in_cm)
        if movement_in_cm > 0:
            self.tinyK.execute(MoveLeftCommand(movement_in_cm))

        else:
            raise Exception(f"Illegal movement_in_cm {movement_in_cm}")

        resp = self.tinyK.wait_for_response()
        if resp.type == ResponseType.ack:
            resp = self.tinyK.wait_for_response()

            if resp.type == ResponseType.completed:
                return NavigationResult(True, None)

        logging.error(
            f"Navigation - move_sideways_left {movement_in_cm}cm - not completed | reason {resp.type}, error {CommandError(resp.payload).name}, error_value {resp.error_value}"
        )

        return NavigationResult(False, CommandError(resp.payload), resp.error_value)

    def move_sideways_right(self, movement_in_cm: int) -> NavigationResult:
        """
        Moves the robot sideways to the right.
        """
        self.speaker.announce_sideways_right(movement_in_cm)
        logging.debug(f"Navigation - move_sideways_right {movement_in_cm}cm")

        if movement_in_cm > 0:
            self.tinyK.execute(MoveRightCommand(movement_in_cm))

        else:
            raise Exception(f"Illegal movement_in_cm {movement_in_cm}")

        resp = self.tinyK.wait_for_response()
        if resp.type == ResponseType.ack:
            resp = self.tinyK.wait_for_response()

            if resp.type == ResponseType.completed:
                return NavigationResult(True, None)

        logging.error(
            f"Navigation - move_sideways_right {movement_in_cm}cm - not completed | reason {resp.type}, error {CommandError(resp.payload).name}, error_value {resp.error_value}"
        )

        return NavigationResult(False, CommandError(resp.payload), resp.error_value)

    def move_backwards(self, movement_in_cm: int) -> NavigationResult:
        """
        Moves the robot backwards.
        """
        self.speaker.announce_move_backward()
        logging.debug(f"Navigation - move_backwards {movement_in_cm}cm")

        if movement_in_cm > 0:
            self.tinyK.execute(MoveBackwardCommand(movement_in_cm))

        else:
            raise Exception(f"Illegal movement_in_cm {movement_in_cm}")

        resp = self.tinyK.wait_for_response()
        if resp.type == ResponseType.ack:
            resp = self.tinyK.wait_for_response()

            if resp.type == ResponseType.completed:
                return NavigationResult(True, None)

        logging.error(
            f"Navigation - move_backwards {movement_in_cm}cm - not completed | reason {resp.type}, error {CommandError(resp.payload).name}, error_value {resp.error_value}"
        )

        return NavigationResult(False, CommandError(resp.payload))

    def climb(self, speed: int = 5) -> NavigationResult:
        """
        Climbs a step.
        """
        self.speaker.announce_climb()
        logging.debug(f"Navigation - climb {speed}")

        if speed > 0:
            self.tinyK.execute(ClimbCommand(speed))

        else:
            raise Exception(f"Illegal speed {speed}")

        resp = self.tinyK.wait_for_response()
        if resp.type == ResponseType.ack:
            resp = self.tinyK.wait_for_response()

            if resp.type == ResponseType.completed:
                return NavigationResult(True, None)

        logging.error(
            f"Navigation - move_backwards {speed} - not completed | reason {resp.type}, error {CommandError(resp.payload).name}, error_value {resp.error_value}"
        )

        return NavigationResult(False, CommandError(resp.payload), resp.error_value)

    def shutdown(self) -> None:
        """
        Shuts down the TinyK/navigation.
        """
        self.speaker.announce_shutdown_master()
        logging.warn("Shutting down TinyK/navigation.")
        # We try to shut the tinyK down. If it doesn't work we can't do anything anyway.
        try:
            self.tinyK.execute(ShutdownCommand())
            _ = self.tinyK.wait_for_response()
        except Exception as e:
            logging.exception(f"Error when shutting down: {e}")
            pass

    def move_to_position(self, position: RobotPosition) -> NavigationResult:
        """
        Moves the robot to a certain position.
        """
        self.speaker.announce_change_robot_position(position)

        logging.debug(f"Navigation - move_to_position {position.name}")

        self.tinyK.execute(MoveToPositionCommand(position))

        resp = self.tinyK.wait_for_response()
        if resp.type == ResponseType.ack:
            resp = self.tinyK.wait_for_response()

            if resp.type == ResponseType.completed:
                return NavigationResult(True, None)

        logging.error(
            f"Navigation - move_to_position {position.name} - not completed | reason {resp.type}, error {resp.payload}"
        )

        return NavigationResult(False, CommandError(resp.payload))


class FakeNavigation(Navigation):
    """Represents a pseudo-navigation used for testing purposes.

    Args:
        Navigation ([type]): the superclass.
    """
    def __init__(self, fake_results: List[NavigationResult]) -> None:
        self.fake_results = fake_results
        self.result_number = 0

    def initialize(self) -> NavigationResult:
        logging.debug("FakeNavigation - initialize")
        return self.__get_next_result()

    def move_forward(self, movement_in_cm: int) -> NavigationResult:
        logging.debug(f"FakeNavigation - movement_in_cm {movement_in_cm}cm")
        return self.__get_next_result()

    def move_forward_until_obstacle(self, movement_in_cm: int) -> NavigationResult:
        logging.debug(f"FakeNavigation - movement_in_cm {movement_in_cm}cm")
        return self.__get_next_result()

    def rotate_sideways(self, degrees: int) -> None:
        logging.debug(f"FakeNavigation - degrees {degrees}")
        return self.__get_next_result()

    def move_sideways_left(self, movement_in_cm: int) -> NavigationResult:
        logging.debug(f"FakeNavigation - movement_in_cm {movement_in_cm}cm")
        return self.__get_next_result()

    def move_sideways_right(self, movement_in_cm: int) -> NavigationResult:
        logging.debug(f"FakeNavigation - movement_in_cm {movement_in_cm}cm")
        return self.__get_next_result()

    def move_backwards(self, movement_in_cm: int) -> NavigationResult:
        logging.debug(f"FakeNavigation - movement_in_cm {movement_in_cm}cm")
        return self.__get_next_result()

    def climb(self, speed: int = 5) -> NavigationResult:
        logging.debug(f"FakeNavigation - speed {speed}")
        return self.__get_next_result()

    def move_to_position(self, position: RobotPosition) -> NavigationResult:
        logging.debug(f"FakeNavigation - position {position} - always works")
        return NavigationResult(True, None)

    def __get_next_result(self) -> NavigationResult:
        next_result = self.fake_results[self.result_number]
        self.result_number += 1
        return next_result
