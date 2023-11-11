import subprocess
import os
import threading
import logging
import psutil

class RTSPServer:
    """Represents an RTSP server that continually streams images from the camera.
    """
    def __init__(self, binary_path: str, pipeline: str) -> None:
        """Creates a new instance.

        Args:
            binary_path (str): the path to the binary actually running the rtsp server.
            pipeline (str): the GStreamer pipeline specifying how/what to stream.
        """
        self.binary_path = binary_path
        self.pipeline = pipeline
        self.started = threading.Event()

    def start(self) -> None:
        """Starts the server.
        """
        try:
            # We're never quite sure how we got stopped previously.
            # If we crashed it might be that the rtsp server process is still running.
            # That's why we forcefully kill it first just to be sure.
            self.process.terminate()
        except AttributeError:
            pass
        try:
            self.thread.join()
        except AttributeError:
            pass
        self.thread = threading.Thread(target=self.__start_and_monitor, daemon=True)
        self.thread.start()
        self.started.wait()
        self.started.clear()

    def __start_and_monitor(self) -> None:
        for proc in psutil.process_iter():
            if proc.name() == "test-launch":
                logging.debug("Killing RTSP server.")
                proc.kill()
        logging.debug("Restarting nvargus-daemon")
        # SUDO works because we gave the current user privileges using visudo.
        os.system("sudo service nvargus-daemon restart")
        logging.info(
            f"Starting RTSP. Binary={self.binary_path}. Pipeline: {self.pipeline}"
        )
        self.process = subprocess.Popen(
            ["stdbuf", "-o0"] + [self.binary_path, self.pipeline],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
        )
        while self.process.returncode is None:
            for line in self.process.stdout:
                print(line)
                if "stream ready at" in line:
                    self.started.set()
                    logging.info("RTSP Server started.")
            self.process.poll()
        logging.debug(f"RTSP server exited with code {self.process.returncode}")
