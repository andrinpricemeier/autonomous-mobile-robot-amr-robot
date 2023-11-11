import cv2
import queue
import threading
import logging
from typing import Any


class VideoCapture:
    """Reponsible for continually reading out and saving the newest image from the RTSP server camera stream.
    This is necessary because OpenCV by default buffers 10 images. We only want the latest though.
    """
    def __init__(self, name: str) -> None:
        """Creates a new instance.

        Args:
            name (str): the OpenCV command to open the capture.
        """
        self.cap = cv2.VideoCapture(name)
        self.q = queue.Queue()
        self.is_running = True
        self.thread = threading.Thread(target=self._reader)
        self.thread.daemon = True
        self.thread.start()

    def _reader(self) -> None:
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self, timeout: int = 1) -> Any:
        """Reads the latest image.

        Args:
            timeout (int, optional): the time to wait for a new image. Defaults to 1.

        Returns:
            Any: the camera image.
        """
        return self.q.get(timeout=timeout)

    def destroy(self) -> None:
        logging.debug("Stopping video capture.")
        self.is_running = False
        self.thread.join()
        logging.debug("Releasing video capture.")
        self.cap.release()
