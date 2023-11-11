from typing import Any
import logging
from camera import Camera
import queue
from videocapture import VideoCapture
from videostreamer import VideoStreamer
from rtsp_server import RTSPServer


class CSICamera(Camera):
    """Represents a physical camera connected through CSI to the Jetson Nano.

    Args:
        Camera ([type]): the superclass.
    """
    def __init__(
        self,
        rtsp_server: RTSPServer,
        rtsp_url: str,
        streaming: bool = False,
        streaming_port: int = 9005,
    ) -> None:
        """Creates a new instance.

        Args:
            rtsp_server (RTSPServer): the RTSP server streaming images that are captured.
            rtsp_url (str): the URL to connect to the RTSP server.
            streaming (bool, optional): Whether to start streaming images to the web interface. Defaults to False.
            streaming_port (int, optional): The port of the stream. Defaults to 9005.
        """
        self.rtsp_server = rtsp_server
        self.rtsp_url = rtsp_url
        self.streaming = streaming
        self.streaming_port = streaming_port
        self.camera: VideoCapture = None
        self.__init_camera()
        if self.streaming:
            logging.debug("CSICamera - StartStreaming")
            self.streamer = VideoStreamer(streaming_port, self.take_picture)

    def take_picture(self) -> Any:
        return self.__take_picture_with_retries(3)

    def __take_picture_with_retries(self, retries: int) -> Any:
        try:
            return self.camera.read()
        except queue.Empty:
            if retries == 0:
                raise Exception("Camera is not responsive. Giving up.")
            else:
                logging.exception("Camera failed. Restarting.")
                self.__init_camera()
                logging.warn("Camera restarted. Taking picture.")
                return self.__take_picture_with_retries(retries - 1)

    def __init_camera(self) -> None:
        self.rtsp_server.start()
        logging.debug("Opening camera")
        try:
            self.camera.destroy()
        except AttributeError:
            pass
        self.camera = VideoCapture(self.rtsp_url)
        logging.debug("Camera opened")

    def destroy(self) -> None:
        self.camera.destroy()
