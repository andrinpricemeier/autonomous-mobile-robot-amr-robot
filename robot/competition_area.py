from start_area import StartArea
from stairs_area import StairsArea
from target_area import TargetArea


class CompetitionArea:
    """Represents the entire competition area.
    Used to record any useful state needed by the states.
    """
    def __init__(
        self, start_area: StartArea, stairs_area: StairsArea, target_area: TargetArea
    ) -> None:
        """Creates a new instance.

        Args:
            start_area (StartArea): The start area.
            stairs_area (StairsArea): The stairs area.
            target_area (TargetArea): The target area.
        """
        self.start_area = start_area
        self.stairs_area = stairs_area
        self.target_area = target_area
