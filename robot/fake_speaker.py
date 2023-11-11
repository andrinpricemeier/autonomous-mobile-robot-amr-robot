from detected_object import DetectedObject
from speaker import Speaker
import logging


class FakeSpeaker(Speaker):
    """Represents a pseudo-speaker useful for testing.

    Args:
        Speaker ([type]): [description]
    """
    def announce_start(self, pictogram: DetectedObject) -> None:
        self.start_pictogram = pictogram
        logging.info("announce_start : {0}".format(pictogram))

    def announce_target(self, pictogram: DetectedObject) -> None:
        self.target_pictogram = pictogram
        logging.info("announce_target : {0}".format(pictogram))

    def announce_path_found(self) -> None:
        self.calculate_path = True
        logging.info("announce_calculate_path")

    def announce_path_not_found(self) -> None:
        logging.info("announce_path_not_found")

    def announce_run_started(self) -> None:
        logging.info("announce_run_started")

    def announce_run_completed(self) -> None:
        logging.info("announce_run_completed")

    def announce_run_stopped(self) -> None:
        logging.info("announce_run_stopped")

    def announce_state_transition(self, state_class_name: str) -> None:
        logging.info("announce_state_transition")

    def announce_sideways_left(self, movement_in_cm: int) -> None:
        logging.info("announce_sideways_left")

    def announce_sideways_right(self, movement_in_cm: int) -> None:
        logging.info("announce_sidways_right")

    def announce_bricks(self, bricks_count: int) -> None:
        logging.info("announce_bricks")
