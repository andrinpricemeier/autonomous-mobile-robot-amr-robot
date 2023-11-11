from typing import Any
from state import State
from robot import Robot

import socket
import configparser
import logging
import json
from tinyk import (
    ResponseType,
    CommandType,
    RobotPosition,
    TinyKCommand,
    tinyk_command_from_command_type,
    TinyK,
)


class DebuggerDrivingSocket:
    def __init__(self, sock: socket = None) -> None:
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host: str, port: int) -> None:
        logging.info("connect host:{0}, port: {1}".format(host, port))
        self.sock.connect((host, port))

    def send(self, msg: str) -> None:
        logging.debug("send command {0}".format(msg))
        sent = self.sock.send(msg.encode())
        if sent == 0:
            raise RuntimeError("socket connection broken")

    def receive(self) -> str:
        logging.debug("receive command ")
        return self.sock.recv(1024)


class DebuggerClient:
    def __init__(self, fname: str) -> None:
        config = self.read_config(fname)
        self.enabled = config["Debugging"]["ManualDriving"] == "yes"
        self.port = int(config["Debugging"]["ManualDrivingPort"])
        self.debugging_socket = DebuggerDrivingSocket()
        try:
            self.debugging_socket.connect("localhost", self.port)
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            logging.info(ex)
            logging.error("ERROR Image Logging failed {}".format(ex))

    def read_config(self, fname: str) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read(fname)
        return config

    def send_response(self, response_id: str, response_payload: str) -> None:
        self.debugging_socket.send(
            json.dumps(
                {
                    "type": "jetson_response",
                    "responseID": response_id,
                    "responsePayload": response_payload,
                }
            )
        )

    def get_next_command(self) -> Any:
        data = self.debugging_socket.receive()
        print(data)
        return json.loads(data)


class ManualDrivingState(State):
    def __init__(self, robot: Robot) -> None:
        self.robot = robot
        self.tinyK: TinyK = self.robot.navigation.tinyK
        self.client: DebuggerClient = DebuggerClient("robot.conf")

    def enter(self) -> None:
        while True:
            data = self.client.get_next_command()
            logging.info(f"ManualDrivingState received  {data}")

            try:
                command = self.create_tinyK_command(data)
                logging.info(f"ManualDrivingState - command: {command}")
                self.tinyK.execute(command)
                response = self.tinyK.wait_for_response()
                self.client.send_response(response.type.name, str(response.payload))

                if response.type == ResponseType.ack:
                    response = self.tinyK.wait_for_response()
                    self.client.send_response(response.type.name, str(response.payload))
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.error(e)
                self.client.send_response(ResponseType.failed.name, "Failed")

    def create_tinyK_command(self, data: Any) -> TinyKCommand:
        commandId = data["commandID"]
        payload = data["commandPayload"]
        logging.info(
            f"ManualDrivingState - create_tinyK_command commandId  {commandId}, payload {payload}"
        )

        commandType: CommandType = CommandType[commandId]

        if commandType == CommandType.move_to_position:
            payload: RobotPosition = RobotPosition[payload]

        command = tinyk_command_from_command_type(commandType, payload)

        return command
