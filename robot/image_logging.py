import socket
from typing import Any
import cv2
import datetime
import configparser
import logging

RAW_IMAGE = "raw_image_"

global image_socket
global image_saving
global path
image_saving = False
image_logging = False
image_path = ""


def read_config(fname: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(fname)
    return config


def configure(fname: str) -> None:
    global image_socket
    global image_path
    global image_saving
    global image_logging
    try:
        config = read_config(fname)

        image_saving = config["Debugging"]["ImageSaving"] == "yes"
        image_logging = config["Debugging"]["ImageLogging"] == "yes"
        image_logging_port = int(config["Debugging"]["ImageLoggingPort"])
        image_path = config["Debugging"]["ImagePath"]

        logging.info(
            "Configure image logger image_saving: {}, image_path{}, image_logging:{}, image_logging_port:{}".format(
                image_saving, image_path, image_logging, image_logging_port
            )
        )

        if image_logging and image_saving:
            image_socket = ImageSocket()
            image_socket.connect("localhost", image_logging_port)
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        print(ex)
        logging.exception("ERROR Image Logging failed {}".format(ex))


def log(image_name: str, image: Any) -> None:
    if image_saving:
        image_name = generate_image_name(image_name)
        save_image(image_name, image)
        if image_logging:
            global image_socket
            try:
                image_socket.send(image_name)
            except KeyboardInterrupt:
                raise
            except Exception:
                logging.exception("Socket connection broken")


def save_image(image_name: str, image: Any) -> None:
    full_image_path = image_path + image_name
    print(full_image_path)
    logging.debug(f"Saving {full_image_path}")
    cv2.imwrite(full_image_path, image)


def generate_image_name(image_name: str) -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc).strftime("%m_%d_%Y_%H_%M_%S_%f")
        + "-"
        + image_name
    )


class ImageSocket:
    def __init__(self, sock: socket = None) -> None:
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host: str, port: int) -> None:
        logging.info("connect host:{0}, port: {1}".format(host, port))
        self.sock.connect((host, port))

    def send(self, msg: str) -> None:
        logging.debug("send image {0}".format(msg))
        sent = self.sock.send(msg.encode())
        if sent == 0:
            raise RuntimeError("socket connection broken")
