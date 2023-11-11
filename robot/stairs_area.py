from guidance.a_star_center_bias_path_finder import AStarCenterBiasPathFinder
from guidance.stairs_map import StairsMap
from path_climbing_plan import PathClimbingPlan
from climbing_plan import ClimbingPlan
from sensor_climbing_plan import SensorClimbingPlan
from path import Path
from navigation import Navigation
import logging

from speaker import Speaker


class StairsInformation:
    """Represents the stairs' dimensions.
    """
    def __init__(
        self,
        step_width_in_cm: int = 250,
        step_height_in_cm: int = 30,
        step_count: int = 5,
    ) -> None:
        """Creates a new instance.

        Args:
            step_width_in_cm (int, optional): the width of the steps in cm. Defaults to 250.
            step_height_in_cm (int, optional): the height of the steps in cm. Defaults to 30.
            step_count (int, optional): the number of steps. Defaults to 5.
        """
        self.step_width_in_cm = step_width_in_cm
        self.step_height_in_cm = step_height_in_cm
        self.step_count = step_count


class StairsArea:
    """Represents the stairs area. Knows how it can be climbed.
    """
    def __init__(
        self,
        navigation: Navigation,
        stairs_information: StairsInformation,
        speaker: Speaker,
    ) -> None:
        """Creates a new instance.

        Args:
            navigation (Navigation): the navigation to use for climbing.
            stairs_information (StairsInformation): metadata about the stairs.
            speaker (Speaker): the speakers used for outputting state information.
        """
        self.navigation: Navigation = navigation
        self.stairs_information: StairsInformation = stairs_information
        self.path: Path = None
        self.plan: ClimbingPlan = None
        self.stairs_map: StairsMap = None
        self.speaker = speaker

    def climb(self) -> None:
        """Climbs the stairs.
        """
        try:
            self.speaker.announce_stairs_area_execute_climbing_plan()
            logging.info("StairsArea - execute plan")
            self.plan.execute()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            if type(self.plan) is SensorClimbingPlan:
                self.speaker.announce_stairs_area_climbing_plan_failed_no_backupplan()
                logging.exception(
                    "StairsArea - climbing failed and no backup plan available."
                )
                raise
            else:
                self.speaker.announce_stairs_area_climbing_plan_failed_has_backupplan()
                logging.exception(
                    f"StairsArea - executing plan failed - use backup plan {e}"
                )
                self.plan = self.__get_backup_plan()
                self.plan.execute()

    def formulate_plan(self) -> None:
        """Formulates a climbing plan or falls back to a backup plan.
        """
        if self.path is not None:
            self.speaker.announce_stairs_area_using_path_climbing_plan()
            logging.info("StairsArea - use PathClimbingPlan")
            self.plan = PathClimbingPlan(
                self.path, self.stairs_map, self.navigation, self.speaker
            )
        else:
            self.speaker.announce_stairs_area_using_sensor_climbing_plan()
            logging.info("StairsArea - use backup Plan")
            self.plan = self.__get_backup_plan()

    def __get_backup_plan(self) -> ClimbingPlan:
        return SensorClimbingPlan(
            self.stairs_map, self.navigation, AStarCenterBiasPathFinder(), self.speaker
        )
