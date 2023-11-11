from typing import Any
import Jetson.GPIO as GPIO


class Button:
    """Represents a physical button on the robot, e.g. start or stop button.
    """
    def __init__(self, pin: int, bounce_time: int = 10) -> None:
        """Creates a new instance.

        Args:
            pin (int): the pin to use for the button
            bounce_time (int, optional): the bounce time. Defaults to 10.
        """
        self.pin = pin
        self.bounce_time = bounce_time
        self.reset()

    def reset(self) -> None:
        """Cleans up registrations for the button.
        """
        GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.IN)

    def wait_for_edge(self, edge: int) -> None:
        """Blocks until the edge is activated.

        Args:
            edge (int): the edge (e.g. RISING) to wait for.
        """
        GPIO.wait_for_edge(self.pin, edge)

    def register_callback(self, callback: Any, edge: int) -> None:
        """Registers a callback to call when an edge is activated.

        Args:
            callback (Any): the callback
            edge (int): the edge (e.g. RISING).
        """
        GPIO.add_event_detect(
            self.pin, edge, callback=callback, bouncetime=self.bounce_time
        )

    def unregister_callback(self) -> None:
        """Cancels the registration for detecting an edge.
        """
        GPIO.remove_event_detect(self.pin)

    def is_input_low(self) -> bool:
        """Checks whether the pin input is low. This can be used for checking
        whether the button was actually pressed or whether it was just some sort of interference.

        Returns:
            bool: true if input is low.
        """
        return GPIO.input(self.pin) == GPIO.LOW

    def __del__(self):
        """Tries to clean up the button registration and free up the pins.
        """
        try:
            GPIO.cleanup()
        except:
            pass
