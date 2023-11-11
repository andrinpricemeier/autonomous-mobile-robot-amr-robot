from typing import Any
from camera import Camera


class FakeCamera(Camera):
    """Represents a camera that simulates a physical camera for testing purposes.

    Args:
        Camera ([type]): the superclass.
    """
    def __init__(self) -> None:
        """Creates a new instance.
        """
        self.images = []
        self.current_image = 0

    def add_image(self, image: Any) -> None:
        """Adds a new image that is played back when a picture is taken with this class.

        Args:
            image (Any): the image to record.
        """
        self.images.append(image)

    def take_picture(self) -> Any:
        """Takes a picture. In this case taking a picture means cycling through the images that were recorded.

        Returns:
            Any: the image.
        """
        image = self.images[self.current_image % len(self.images)]
        self.current_image = (self.current_image + 1) % len(self.images)
        return image
