from object_detection import ObjectDetection
import configparser
import os
from triton_client import TritonClient
from rtsp_server import RTSPServer
from tensorrt_object_detection import TensorRTObjectDetection


def get_triton_object_detection_from_config(fname: str) -> ObjectDetection:
    config = __read_config(fname)
    client = TritonClient(
        config["ObjectDetection"]["TritonServerURL"],
        config["ObjectDetection"]["TritonServerModel"],
        int(config["ObjectDetection"]["TritonServerTimeoutInSeconds"]),
    )
    warmup_image = config["ObjectDetection"]["WarmupImage"]
    if not os.path.isfile(warmup_image):
        warmup_image = "robot/images/warmup_image.jpg"
    return TensorRTObjectDetection(client, warmup_image)


def __read_config(fname: str) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(fname)
    return config


def get_filename(filename: str) -> str:
    if os.path.isfile(filename):
        return filename
    else:
        return f"robot/{filename}"
