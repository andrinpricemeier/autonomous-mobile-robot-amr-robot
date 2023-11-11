from typing import Any


class Camera:
    """Represents a physical camera connected to the Jetson Nano.
    """
    def take_picture(self) -> Any:
        """Takes a picture with the camera.

        Returns:
            Any: the image / picture taken with the camera.
        """
        pass

    def destroy(self) -> None:
        """Cleans up the camera resources.
        """
        pass
