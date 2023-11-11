from tinyk_serial import FakeUART, SerialConnection
from tinyk import (
    CommandError,
    CommandType,
    InitializeCommand,
    MoveForwardCommand,
    MoveToPositionCommand,
    ResponseType,
    RobotPosition,
    RotateClockwiseCommand,
    RotateCounterClockwiseCommand,
    TinyK,
    TinyKResponse,
)
import pytest
import logging.config


@pytest.fixture(scope="session", autouse=True)
def do_something(request):
    logging.config.fileConfig(fname="logger.conf")


def test_tiny_k_send_forward_5(mocker):
    send_responses: bytes = b""
    uart: SerialConnection = FakeUART(send_responses)
    tinyK = TinyK(uart)

    spy_uart_send = mocker.spy(uart, "send")

    tinyK.execute(MoveForwardCommand(5))

    expected_byte_data: bytes = b"\x00\x08\x00\x05\x00\x01\xFF"
    spy_uart_send.assert_has_calls([mocker.call(expected_byte_data)])

def test_tiny_k_send_rotate_counter_clockwise_16(mocker):
    send_responses: bytes = b""
    uart: SerialConnection = FakeUART(send_responses)
    tinyK = TinyK(uart)

    spy_uart_send = mocker.spy(uart, "send")

    tinyK.execute(RotateCounterClockwiseCommand(16))

    expected_byte_data: bytes = b"\x00\x05\x00\x10\x00\x01\xFF"
    spy_uart_send.assert_has_calls([mocker.call(expected_byte_data)])

def test_tiny_k_send_rotate_clockwise_3(mocker):
    send_responses: bytes = b""
    uart: SerialConnection = FakeUART(send_responses)
    tinyK = TinyK(uart)

    spy_uart_send = mocker.spy(uart, "send")

    tinyK.execute(RotateClockwiseCommand(3))

    expected_byte_data: bytes = b"\x00\x04\x00\x03\x00\x01\xFF"
    spy_uart_send.assert_has_calls([mocker.call(expected_byte_data)])

def test_tiny_k_send_initialized(mocker):
    send_responses: bytes = b""
    uart: SerialConnection = FakeUART(send_responses)
    tinyK = TinyK(uart)

    spy_uart_send = mocker.spy(uart, "send")

    tinyK.execute(InitializeCommand())

    expected_byte_data: bytes = b"\x00\x01\x00\x00\x00\x01\xFF"
    spy_uart_send.assert_has_calls([mocker.call(expected_byte_data)])


def test_tiny_k_wait_for_response_forward_5_ack():
    send_responses: bytes = b"\x00\x01\x00\x08\x00\x00\xFF"
    uart: FakeUART = FakeUART(send_responses)
    tinyK = TinyK(uart)

    response: TinyKResponse = tinyK.wait_for_response()

    assert response.type == ResponseType.ack
    assert CommandType(response.payload) == CommandType.move_forward


def test_tiny_k_wait_for_response_climb_full():
    send_responses: bytes = b"\x00\x01\x00\x0A\x00\x00\xFF\x00\x03\x00\x0A\x00\x00\xFF"
    uart: FakeUART = FakeUART(send_responses)
    tinyK = TinyK(uart)

    response: TinyKResponse = tinyK.wait_for_response()

    assert response.type == ResponseType.ack
    assert CommandType(response.payload) == CommandType.climb

    response: TinyKResponse = tinyK.wait_for_response()

    assert response.type == ResponseType.completed
    assert CommandType(response.payload) == CommandType.climb


def test_tiny_k_wait_for_response_move_right_failed_due_to_obstacle_right():
    send_responses: bytes = b"\x00\x02\x00\x03\x00\x05\xFF"
    uart: FakeUART = FakeUART(send_responses)
    tinyK = TinyK(uart)

    response: TinyKResponse = tinyK.wait_for_response()

    assert response.type == ResponseType.failed
    assert response.error_value == 5
    assert CommandError(response.payload) == CommandError.obstacle_detected_right


def test_tiny_k_wait_for_response_initialize_full():
    send_responses: bytes = b"\x00\x01\x00\x01\x00\x00\xFF\x00\x03\x00\x01\x00\x00\xFF"
    uart: FakeUART = FakeUART(send_responses)
    tinyK = TinyK(uart)

    response: TinyKResponse = tinyK.wait_for_response()

    assert response.type == ResponseType.ack
    assert CommandType(response.payload) == CommandType.initialize

    response: TinyKResponse = tinyK.wait_for_response()

    assert response.type == ResponseType.completed
    assert CommandType(response.payload) == CommandType.initialize


def test_tiny_k_send_move_to_position_drive_around(mocker):
    uart: SerialConnection = FakeUART(b"")
    tinyK = TinyK(uart)

    spy_uart_send = mocker.spy(uart, "send")

    tinyK.execute(MoveToPositionCommand(RobotPosition.drive_around))

    expected_byte_data: bytes = b"\x00\x0C\x00\x01\x00\x01\xFF"
    spy_uart_send.assert_has_calls([mocker.call(expected_byte_data)])


def test_tiny_k_send_move_to_position_stand_up(mocker):
    uart: SerialConnection = FakeUART(b"")
    tinyK = TinyK(uart)

    spy_uart_send = mocker.spy(uart, "send")

    tinyK.execute(MoveToPositionCommand(RobotPosition.stand_up))

    expected_byte_data: bytes = b"\x00\x0C\x00\x02\x00\x01\xFF"
    spy_uart_send.assert_has_calls([mocker.call(expected_byte_data)])


def test_tiny_k_send_move_to_position_drive_on_stairs(mocker):
    uart: SerialConnection = FakeUART(b"")
    tinyK = TinyK(uart)

    spy_uart_send = mocker.spy(uart, "send")

    tinyK.execute(MoveToPositionCommand(RobotPosition.drive_on_stairs))

    expected_byte_data: bytes = b"\x00\x0C\x00\x03\x00\x01\xFF"
    spy_uart_send.assert_has_calls([mocker.call(expected_byte_data)])


def test_tiny_k_send_move_to_position_hit_target_pictogram(mocker):
    uart: SerialConnection = FakeUART(b"")
    tinyK = TinyK(uart)

    spy_uart_send = mocker.spy(uart, "send")

    tinyK.execute(MoveToPositionCommand(RobotPosition.hit_target_pictogram))

    expected_byte_data: bytes = b"\x00\x0C\x00\x04\x00\x01\xFF"
    spy_uart_send.assert_has_calls([mocker.call(expected_byte_data)])


def test_tiny_k_send_move_to_position_go_home(mocker):
    uart: SerialConnection = FakeUART(b"")
    tinyK = TinyK(uart)

    spy_uart_send = mocker.spy(uart, "send")

    tinyK.execute(MoveToPositionCommand(RobotPosition.go_home))

    expected_byte_data: bytes = b"\x00\x0C\x00\x05\x00\x01\xFF"
    spy_uart_send.assert_has_calls([mocker.call(expected_byte_data)])

def test_tiny_k_send_move_to_position_hit_stairs(mocker):
    uart: SerialConnection = FakeUART(b"")
    tinyK = TinyK(uart)

    spy_uart_send = mocker.spy(uart, "send")

    tinyK.execute(MoveToPositionCommand(RobotPosition.hit_stairs))

    expected_byte_data: bytes = b"\x00\x0C\x00\x06\x00\x01\xFF"
    spy_uart_send.assert_has_calls([mocker.call(expected_byte_data)])