from button import Button
from emergency_stop_watchdog import EmergencyStopWatchdog
from state import State
import logging
from competition_area import CompetitionArea
from object_detection import ObjectDetection
from navigation import Navigation
from speaker import Speaker
from camera import Camera


class Robot:
    """Represents the physical robot.
    Responsible for executing the state machine representing a competition run.
    """
    def __init__(self) -> None:
        """Creates a new instance.
        """
        self.competition_area: CompetitionArea = None
        self.camera: Camera = None
        self.speaker: Speaker = None
        self.navigation: Navigation = None
        self.object_detection: ObjectDetection = None
        self.width_in_cm: int = None
        self.movements_in_cm: int = None
        self.start_stop_button: Button = None
        self.emergency_stop_watchdog: EmergencyStopWatchdog = None

    def transition(self, state: State) -> None:
        """Changes the state.

        Args:
            state (State): the state to change into.
        """
        self.current_state = state

    def end_run(self) -> None:
        """Ends the run.
        """
        logging.info("Ending run.")
        self.current_state = None

    def run(self) -> None:
        """Executes the state machine.
        """
        try:
            while self.current_state is not None:
                state = self.current_state
                state_class_name = type(state).__name__
                logging.debug(f"Entering state {state_class_name}.")
                if self.speaker is not None:
                    self.speaker.announce_state_transition(state_class_name)
                state.enter()
                logging.debug(f"State {state_class_name} completed.")
        except KeyboardInterrupt:
            # This is the global exception handler that is executed when the emergency stop button is pressed.
            self.speaker.announce_run_stopped()
            self.navigation.shutdown()
            # Hard shutdown since we can't do anything anymore. Shut down as soon as possible to prevent any strange behavior.
            quit()
        except Exception:
            logging.exception("Unhandled exception. Stopping robot.")
            self.speaker.announce_run_stopped()
            self.navigation.shutdown()
            quit()
