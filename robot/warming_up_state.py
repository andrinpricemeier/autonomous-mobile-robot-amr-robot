from edge_detection import EdgeDetection
from typing import Any
from path_object_detection import PathObjectDetection
from usb_speaker import USBSpeaker
from csi_camera import CSICamera
from tinyk import TinyK
from navigation import Navigation
from initialized_state import InitializedState
from state import State
from robot import Robot
from button import Button
from detected_object import DetectedObject
from tensorrt_object_detection import TensorRTObjectDetection
from triton_client import TritonClient
from rtsp_server import RTSPServer
import configparser
import logging.config
import image_logging
import logging
import img_utils
from tinyk_serial import UART

from start_area import StartArea
from stairs_area import StairsArea, StairsInformation
from target_area import TargetArea
from competition_area import CompetitionArea
from pictogram_detection import PictogramDetection
from stairs_detection import StairsDetection
from manual_driving_state import ManualDrivingState
from emergency_stop_watchdog import EmergencyStopWatchdog


class WarmingUpState(State):
    """Responsible for warming up the robot, that includes starting
    the object detection, the camera, speakers and other things.

    Args:
        State ([type]): the superclass.
    """
    def __init__(self, robot: Robot) -> None:
        self.robot = robot

    def enter(self) -> None:
        self.__init_logging()
        # Manually announce state because the logger is not initialized yet.
        logging.debug("Entering state WarmingUpState")
        self.__init_debugging()

        config = self.__read_config()

        self.__init_img_utils(config["Debugging"]["ImageRendering"] == "yes")

        client = TritonClient(
            config["ObjectDetection"]["TritonServerURL"],
            config["ObjectDetection"]["TritonServerModel"],
            int(config["ObjectDetection"]["TritonServerTimeoutInSeconds"]),
        )
        self.robot.object_detection = TensorRTObjectDetection(
            client, config["ObjectDetection"]["WarmupImage"]
        )
        uart = UART(
            config["UART"]["Port"],
            int(config["UART"]["BaudRate"]),
            int(config["UART"]["WriteTimeoutInSeconds"]),
            int(config["UART"]["ReadTimeoutInSeconds"]),
        )
        self.robot.speaker = USBSpeaker(
            config["Audio"]["AudioDirectory"],
            config["Audio"]["AudioDeviceId"],
            int(config["Audio"]["CardNr"]),
            config["Audio"]["Debugging"] == "yes",
        )
        tinyK = TinyK(uart)
        self.robot.navigation = Navigation(tinyK, self.robot.speaker)

        self.robot.width_in_cm = int(config["Robot"]["WidthInCm"])
        self.robot.movements_in_cm = int(config["Robot"]["MovementsInCm"])

        self.robot.camera = CSICamera(
            RTSPServer(
                config["Video"]["RTSPServerBinary"],
                config["Video"]["RTSPServerPipeline"],
            ),
            config["Video"]["RTSPServerURL"],
            config["Debugging"]["CameraStreaming"] == "yes",
            int(config["Debugging"]["CameraStreamingPort"]),
        )
        start_stop_button: Button = Button(
            int(config["StartStopButton"]["Pin"]),
            int(config["StartStopButton"]["BounceTimeInMs"]),
        )
        self.robot.start_stop_button = start_stop_button
        self.robot.emergency_stop_watchdog = EmergencyStopWatchdog(start_stop_button)
        self.robot.competition_area = self.init_competition_area(
            config, tinyK
        )
        self.manual_driving = config["Debugging"]["ManualDriving"] == "yes"

        # result: NavigationResult = self.robot.navigation.initialize()

        # if result.success:
        if self.manual_driving:
            self.robot.transition(ManualDrivingState(self.robot))
        else:
            self.robot.transition(InitializedState(self.robot))
        # else:
        #    logging.error(
        #        "Unable to initialize Navigation - check if TinyK is running!"
        #    )

    def init_competition_area(self, config: Any, tinyK: TinyK) -> CompetitionArea:
        start_area = self.__init_start_area(config, tinyK)
        stairs_area = self.__init_stairs_area(config)
        target_area = self.__init_target_area(config)
        return CompetitionArea(start_area, stairs_area, target_area)

    def __init_logging(self) -> None:
        logging.config.fileConfig(fname="logger.conf")

    def __init_debugging(self) -> None:
        image_logging.configure(fname="robot.conf")

    def __init_img_utils(self, image_rendering: bool) -> None:
        img_utils.set_rendering_enabled(image_rendering)

    def __read_config(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read("robot.conf")
        return config

    def __init_start_area(self, config: Any, tinyK: TinyK) -> StartArea:
        return StartArea(
            self.robot.navigation,
            self.robot.camera,
            EdgeDetection(self.robot.object_detection),
            PictogramDetection(self.robot.object_detection),
            StairsDetection(self.robot.object_detection),
            PathObjectDetection(self.robot.object_detection),
            self.robot.speaker,
            float(config["StartArea"]["StartPictogramMinAreaNormalized"]),
            float(config["StartArea"]["StairsOptimalPositionMinXOffsetNormalized"]),
            int(config["StairsArea"]["StairsWidthInCm"]),
            int(config["StairsArea"]["StepWidthInCm"])
        )

    def __init_stairs_area(self, config: Any) -> StairsArea:
        # TODO: Add additional parameters!
        return StairsArea(
            navigation=self.robot.navigation,
            stairs_information=StairsInformation(
                step_width_in_cm=int(config["StairsArea"]["StepWidthInCm"]),
                step_height_in_cm=int(config["StairsArea"]["StepHeightInCm"]),
                step_count=int(config["StairsArea"]["StepCount"]),
            ),
            speaker=self.robot.speaker,
        )

    def __init_target_area(self, config: Any) -> TargetArea:
        pictogram_order = [
            DetectedObject[config["TargetArea"]["Pictogram" + str(i)]]
            for i in range(1, 6)
        ]

        distance_to_flag_in_cm = int(config["TargetArea"]["DistanceToFlagInCm"])

        pictogram_width_in_cm = int(config["TargetArea"]["PictogramWidthInCm"])

        distance_between_pictograms_in_cm = int(config["TargetArea"]["DistanceBetweenPictogramsInCm"])


        return TargetArea(
            self.robot.navigation,
            self.robot.camera,
            self.robot.speaker,
            PictogramDetection(self.robot.object_detection),
            pictogram_order,
            distance_to_flag_in_cm,
            pictogram_width_in_cm,
            distance_between_pictograms_in_cm
        )
