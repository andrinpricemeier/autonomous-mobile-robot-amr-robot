from tinyk_serial import SerialConnection
from enum import Enum
from typing import Any
import queue
import time
import logging

END_OF_MESSAGE: Any = b"\xFF"
DATA_SIZE_IN_BYTES: int = 2
BYTE_ORDER: str = "big"


class TinyKMessage:
    """Represents the unit of information passed between the Jetson Nano and MasterTinyK.
    """
    pass


class TinyKCommand(TinyKMessage):
    """Represents a command from the Jetson Nano to the MasterTinyK for executing something, e.g. a movement.

    Args:
        TinyKMessage ([type]): the superclass.
    """
    def __init__(self) -> None:
        """Creates a new instance.
        """
        self.ttl = 3
    
    def consume_ttl(self) -> None:
        """Used for resending a command in case of failures, similarly to how IP packets work.
        """
        if self.ttl > 0:
            self.ttl -= 1

class ResponseType(Enum):
    """The type of response returned by the MasterTinyK.

    Args:
        Enum ([type]): the superclass.
    """
    ack = 1
    failed = 2
    completed = 3


class TinyKResponse:
    """The response sent by the MasterTinyK.
    """
    def __init__(self, type: ResponseType, payload: int, error_value: int = 0) -> None:
        """Creates a new instance.

        Args:
            type (ResponseType): the type of response.
            payload (int): additional data.
            error_value (int, optional): additional information regarding the error. Defaults to 0.
        """
        self.type = type
        self.payload = payload
        self.error_value = error_value

    def __str__(self) -> str:
        return f"TinyKResponse type: {self.type}, payload: {self.payload}"

    def __repr__(self) -> str:
        return f"TinyKResponse type: {self.type}, payload: {self.payload}"


class CommandType(Enum):
    """The type of command to send from the Jetson Nano to the MasterTinyK.

    Args:
        Enum ([type]): the superclass.

    Returns:
        [type]: the type.
    """
    initialize = 1
    rotate_upwards = 2
    rotate_downwards = 3
    rotate_clockwise = 4
    rotate_counter_clockwise = 5
    move_left = 6
    move_right = 7
    move_forward = 8
    move_backward = 9
    climb = 10
    shutdown = 11
    move_to_position = 12

    def to_bytes(self) -> bytes:
        return self.value.to_bytes(DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER)


class CommandError(Enum):
    """The type of error returned for the command from the MasterTinyK.

    Args:
        Enum ([type]): the superclass.
    """
    unknown_command = 1
    obstacle_detected_left = 2
    obstacle_detected_right = 3
    obstacle_detected_front = 4
    invalid_command = 5


class RobotPosition(Enum):
    """The possible driving positions for the robot.

    Args:
        Enum ([type]): the superclass.
    """
    drive_around = 1
    stand_up = 2
    drive_on_stairs = 3
    hit_target_pictogram = 4
    go_home = 5
    hit_stairs = 6


class InitializeCommand(TinyKCommand):
    """
    Command to initialize TinyK22.
    """

    def __init__(self) -> None:
        super().__init__()
        self.type = CommandType.initialize.to_bytes()
        self.argument = b"\x00\x00"


class RotateUpwardsCommand(TinyKCommand):
    """
    Command to move rotate camera up.
    """

    def __init__(self, degrees: int) -> None:
        super().__init__()
        self.type = CommandType.rotate_upwards.to_bytes()
        self.argument = degrees.to_bytes(DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER)


class RotateDownwardsCommand(TinyKCommand):
    """
    Command to move rotate camera down.
    """

    def __init__(self, degrees: int) -> None:
        super().__init__()
        self.type = CommandType.rotate_downwards.to_bytes()
        self.argument = degrees.to_bytes(DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER)


class RotateClockwiseCommand(TinyKCommand):
    """
    Command to rotate the robot clockwise.
    """

    def __init__(self, degrees: int) -> None:
        super().__init__()
        self.type = CommandType.rotate_clockwise.to_bytes()
        self.argument = degrees.to_bytes(DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER)


class RotateCounterClockwiseCommand(TinyKCommand):
    """
    Command to rotate the robot counterclockwise.
    """

    def __init__(self, degrees: int) -> None:
        super().__init__()
        self.type = CommandType.rotate_counter_clockwise.to_bytes()
        self.argument = degrees.to_bytes(DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER)


class MoveLeftCommand(TinyKCommand):
    """
    Command to move the robot to the left.
    """

    def __init__(self, movement_in_cm: int) -> None:
        super().__init__()
        self.type = CommandType.move_left.to_bytes()
        self.argument = movement_in_cm.to_bytes(
            DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER
        )


class MoveRightCommand(TinyKCommand):
    """
    Command to move the robot to the right.
    """

    def __init__(self, movement_in_cm: int) -> None:
        super().__init__()
        self.type = CommandType.move_right.to_bytes()
        self.argument = movement_in_cm.to_bytes(
            DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER
        )


class MoveForwardCommand(TinyKCommand):
    """
    Command to move the robot forward.
    """

    def __init__(self, movement_in_cm: int) -> None:
        super().__init__()
        self.type = CommandType.move_forward.to_bytes()
        self.argument = movement_in_cm.to_bytes(
            DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER
        )


class MoveBackwardCommand(TinyKCommand):
    """
    Command to move the robot backward.
    """

    def __init__(self, movement_in_cm: int) -> None:
        super().__init__()
        self.type = CommandType.move_backward.to_bytes()
        self.argument = movement_in_cm.to_bytes(
            DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER
        )


class ClimbCommand(TinyKCommand):
    """
    Command to climb a step.
    """

    def __init__(self, speed: int) -> None:
        super().__init__()
        self.type = CommandType.climb.to_bytes()
        self.argument = speed.to_bytes(DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER)


class ShutdownCommand(TinyKCommand):
    """
    Command to shutdown the robot.
    """

    def __init__(self) -> None:
        super().__init__()
        self.type = CommandType.shutdown.to_bytes()
        self.argument = b"\x00\x00"


class MoveToPositionCommand(TinyKCommand):
    """
    Move the Robot to a certain position.
    """

    def __init__(self, position: RobotPosition) -> None:
        super().__init__()
        self.type = CommandType.move_to_position.to_bytes()
        self.argument = position.value.to_bytes(
            DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER
        )


def tinyk_command_from_command_type(
    command_type: CommandType, payload: Any
) -> TinyKCommand:
    """
    Returns the TinyKCommand associated with the command_type.
    """
    if command_type == CommandType.initialize:
        return InitializeCommand(int(payload))

    if command_type == CommandType.rotate_upwards:
        return RotateUpwardsCommand(int(payload))

    if command_type == CommandType.rotate_downwards:
        return RotateDownwardsCommand(int(payload))

    if command_type == CommandType.rotate_clockwise:
        return RotateClockwiseCommand(int(payload))

    if command_type == CommandType.rotate_counter_clockwise:
        return RotateCounterClockwiseCommand(int(payload))

    if command_type == CommandType.move_left:
        return MoveLeftCommand(int(payload))

    if command_type == CommandType.move_right:
        return MoveRightCommand(int(payload))

    if command_type == CommandType.move_forward:
        return MoveForwardCommand(int(payload))

    if command_type == CommandType.move_backward:
        return MoveBackwardCommand(int(payload))

    if command_type == CommandType.climb:
        return ClimbCommand(int(payload))

    if command_type == CommandType.shutdown:
        return ShutdownCommand()

    if command_type == CommandType.move_to_position:
        return MoveToPositionCommand(payload)

    raise Exception(f"Unknown command {command_type}")


class TinyK:
    """Represents the entry point into communicating with the MasterTinyK.
    """
    def __init__(self, serial: SerialConnection) -> None:
        """Creates a new instance.

        Args:
            serial (SerialConnection): the serial connection to use.
        """
        self.serial: SerialConnection = serial
        self.current_seq_number = 1
        self.previous_seq_number = -1
        self.last_command: TinyKCommand = None
        
    def execute(self, command: TinyKCommand) -> None:
        """Executes the command.

        Args:
            command (TinyKCommand): the command.
        """
        self.__execute(command, self.current_seq_number)
        self.previous_seq_number = self.current_seq_number
        self.current_seq_number += 1

    def __execute(self, command: TinyKCommand, seq_number: int) -> None:
        data: bytes = command.type + command.argument + seq_number.to_bytes(DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER) + END_OF_MESSAGE
        logging.debug(f"TinyK send data: {data}")
        self.serial.send(data=data)
        self.last_command = command
        command.consume_ttl()

    def has_response_arrived(self) -> bool:
        """True if a response has been sent by the MasterTinyK.

        Returns:
            bool: True if a response has been sent by the MasterTinyK.
        """
        return self.serial.has_data_to_be_read()

    def __resend_last_command(self) -> TinyKResponse:
        if self.last_command is None:
            raise Exception("TinyK - No command sent previously. Can't resend command.")
        if self.previous_seq_number == -1:
            raise Exception("TinyK - Previous seq number hasn't been set. Can't resend command.")
        if self.last_command.ttl == 0:
            raise Exception("TinyK - TTL exceeded of command.")
        logging.info("TinyK - resending last command.")
        self.serial.reconnect()
        self.__execute(self.last_command, self.previous_seq_number)
        resp = self.wait_for_response()
        if resp.type != ResponseType.ack:
            raise Exception("TinyK - Resending command failed. The command didn't get acknowledged.")
        return self.wait_for_response()

    def wait_for_response(self) -> TinyKResponse:
        """Blocks until a response has been sent by the MasterTinyK.

        Returns:
            TinyKResponse: the response.
        """
        data = self.serial.read(7)
        logging.debug(f"TinyK: Received data: {data}")
        if len(data) != 7:
            logging.error(
                f"TinyK: Received only {len(data)} bytes, expected 7. Returning failure."
            )
            return self.__resend_last_command()           
        type = int.from_bytes(data[0:2], byteorder=BYTE_ORDER)
        payload = int.from_bytes(data[2:4], byteorder=BYTE_ORDER)
        error_value = int.from_bytes(data[4:6], byteorder=BYTE_ORDER)
        eol = data[6]

        logging.info(f"wait_for_response type: {type}, payload: {payload}, error_value: {error_value}, eol: {eol}")
        if eol == END_OF_MESSAGE[0]:
            try:
                return self.create_response(type, payload, error_value)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.exception("TinyK - Creating response failed")
                return self.__resend_last_command()
        else:
            logging.error("TinyK - Last byte wasn't EOL.")
            return self.__resend_last_command()

    def create_response(self, type: int, payload: int, error_value: int) -> TinyKResponse:
        response_type: ResponseType = ResponseType(type)
        logging.info(f"create_response: response_type: {response_type}")

        if response_type == ResponseType.ack:
            logging.info("create_response: ack")
            return TinyKResponse(response_type, CommandType(payload))

        elif response_type == ResponseType.failed:
            logging.info("create_response: failed")
            return TinyKResponse(response_type, CommandError(payload), error_value)

        elif response_type == ResponseType.completed:
            logging.info("create_response: completed")
            return TinyKResponse(response_type, CommandType(payload))

        raise Exception(f"Can not handle ResponseType {response_type.name}")


class FakeTinyK(TinyK):
    """Represents a pseudo-TinyK for testing purposes.

    Args:
        TinyK ([type]): [description]
    """
    def __init__(self, serial: SerialConnection) -> None:
        super().__init__(serial)
        self.serial = serial
        self.queue = queue.Queue()

    def execute(self, command: TinyKCommand) -> None:
        logging.debug(f"FakeTinyK - execute - {command}")
        self.queue.put(
            ResponseType.ack.value.to_bytes(DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER)
        )
        self.queue.put(command.type)
        error: int = 0
        self.queue.put(error.to_bytes(
                DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER
            ))
        self.queue.put(END_OF_MESSAGE)
        self.queue.put(
            ResponseType.completed.value.to_bytes(
                DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER
            )
        )
        self.queue.put(command.type)
        self.queue.put(error.to_bytes(
                DATA_SIZE_IN_BYTES, byteorder=BYTE_ORDER
            ))
        self.queue.put(END_OF_MESSAGE)

    def has_response_arrived(self) -> bool:
        return self.serial.has_data_to_be_read()

    def wait_for_response(self) -> TinyKResponse:
        logging.debug("FakeTinyK - wait_for_response")
        type = int.from_bytes(self.queue.get(), byteorder=BYTE_ORDER)
        payload = int.from_bytes(self.queue.get(), byteorder=BYTE_ORDER)
        error_value = int.from_bytes(self.queue.get(), byteorder=BYTE_ORDER)
        eol = self.queue.get()

        logging.debug("FakeTinyK - wait_for_response - sleep")
        # sleep a little
        time.sleep(0.5)
        if eol == END_OF_MESSAGE:
            response: TinyKResponse = super().create_response(type, payload, error_value)
            logging.debug(
                f"FakeTinyK - wait_for_response - received response : {response}"
            )
            return response
        else:
            raise Exception(
                f"Expected end of line received type: {type}, payload: {payload}, eol: {eol}"
            )
