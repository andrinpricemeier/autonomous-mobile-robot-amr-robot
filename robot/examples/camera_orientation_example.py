import logging
import logging.config
from csi_camera import CSICamera
import image_logging
import img_utils
import configparser
from rtsp_server import RTSPServer

def __init_logging() -> None:
    logging.config.fileConfig(fname="logger.conf")

def __init_debugging() -> None:
    image_logging.configure(fname="robot.conf")

def __init_img_utils(image_rendering: bool) -> None:
    img_utils.set_rendering_enabled(image_rendering)

def __read_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read("robot.conf")
    return config

config = __read_config()
__init_debugging()
__init_img_utils(True)
__init_logging()

camera = CSICamera(
    RTSPServer(
        config["Video"]["RTSPServerBinary"],
        config["Video"]["RTSPServerPipeline"],
    ),
    config["Video"]["RTSPServerURL"],
    config["Debugging"]["CameraStreaming"] == "yes",
    int(config["Debugging"]["CameraStreamingPort"]),
)

gaps: int = 100

while True:
    user_input = input('Press enter to take photo, press CTRL + C to exit.\n')
    image = camera.take_picture()
    for i in range(1, image.shape[0]//gaps):
        img_utils.render_line(image, [0, gaps * i, image.shape[1], gaps * i])

    image_logging.log("camera_rotation.jpg", image)
