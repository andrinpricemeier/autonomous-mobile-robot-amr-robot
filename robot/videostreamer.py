from typing import Any
from flask import Response, Flask
import cv2
import logging
import threading


class EndpointAction(object):
    def __init__(self, action: Any) -> None:
        self.action = action
        self.response = Response(status=200, headers={})

    def __call__(self, *args: Any) -> Any:
        self.response = self.action()
        return self.response


class FlaskAppWrapper(object):
    def __init__(self, name: str, port: int) -> None:
        self.app = Flask(name)
        self.port = str(port)

    def run(self) -> None:
        self.app.run("0.0.0.0", port=self.port)

    def add_endpoint(
        self, endpoint: Any = None, endpoint_name: Any = None, handler: Any = None
    ) -> None:
        self.app.add_url_rule(endpoint, endpoint_name, EndpointAction(handler))


class VideoStreamer:
    def __init__(self, port: int, get_frame: Any) -> None:
        logging.debug("VideoStreamer - init")
        self.port = port
        self.app = Flask(__name__)
        self.get_frame = get_frame

        a = FlaskAppWrapper("wrap", self.port)
        a.add_endpoint(endpoint="/", endpoint_name="stream", handler=self.get_stream)

        self.video_thread = threading.Thread(target=a.run)
        self.video_thread.start()

    def get_stream(self) -> Response:
        return Response(
            self.stream(), mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    def stream(self) -> Any:
        while True:
            try:
                yield b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + bytearray(
                    cv2.imencode(".jpg", self.get_frame())[1]
                ) + b"\r\n"
            except KeyboardInterrupt:
                raise
            except Exception:
                logging.exception("VideoStreamer - No Frame available")
