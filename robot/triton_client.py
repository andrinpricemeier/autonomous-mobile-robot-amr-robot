import tritonclient.grpc as grpcclient
import logging
from typing import Any


class TritonClient:
    """Represents a client for communicating with the Triton server.
    """
    def __init__(self, url: str, model_name: str, timeout_in_seconds: int) -> None:
        """Creates a new instance.

        Args:
            url (str): the URL of the triton server.
            model_name (str): the name of the ML model to use.
            timeout_in_seconds (int): the timeout in seconds to wait for the request.
        """
        self.model_name = model_name
        self.timeout_in_seconds = timeout_in_seconds
        self.client = grpcclient.InferenceServerClient(url=url)

    def infer(self, image: Any, width: float, height: float) -> Any:
        """Sends the object detection request to the triton server.

        Args:
            image (Any): the image.
            width (float): the image width.
            height (float): the image height.

        Returns:
            Any: the object detection results. The structure of these results differ based on the ML model in use.
        """
        inputs = []
        outputs = []
        inputs.append(grpcclient.InferInput("data", [1, 3, width, height], "FP32"))
        outputs.append(grpcclient.InferRequestedOutput("prob"))
        inputs[0].set_data_from_numpy(image)
        logging.debug("Inferring through Triton server.")
        results = self.client.infer(
            model_name=self.model_name,
            inputs=inputs,
            outputs=outputs,
            client_timeout=self.timeout_in_seconds,
        )
        logging.debug("Inference completed.")
        return results.as_numpy("prob")
