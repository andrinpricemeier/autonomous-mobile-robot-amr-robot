from typing import Any
from button import Button
import logging
import Jetson.GPIO as GPIO
import _thread
import threading


class EmergencyStopWatchdog:
    """Represents the emergency stop button.
    """
    def __init__(self, stop_button: Button) -> None:
        """Creates a new instance.

        Args:
            stop_button (Button): the physical button that is pressed.
        """
        self.stop_button = stop_button
        self.thread = threading.Thread(target=self.__start_watching)
        self.thread.daemon = True

    def activate(self) -> None:
        """Activates the emergency stop button.
        """
        logging.info("Emergency stop watchdog activated.")
        self.thread.start()

    def __start_watching(self) -> None:
        # Deactivated because it kept getting accidentally activated during the climbing process.
        while True:
            pass
        self.stop_button.reset()
        self.stop_button.wait_for_edge(GPIO.FALLING)
        logging.warn("Emergency stop button pressed. Stopping run.")
        # Raises a KeyboardInterrupt exception on the main thread.
        _thread.interrupt_main()
