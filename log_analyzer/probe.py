from log_fragment import LogFragment, LeafLogFragment, AggregateLogFragment
from typing import List
import re
from re import Match
from log_entry import LogEntry

class Probe():
    def __init__(self, start_regex: str, end_regex: str) -> None:
        self.start_regex = start_regex
        self.end_regex = end_regex

    def scan(self, fragment: LogFragment) -> List[LogFragment]:
        entries = fragment.entries
        fragments = []
        index = 0
        while index < len(entries):
            match = re.search(self.start_regex, entries[index].message)
            if match is not None:
                title = self.get_title(entries[index], match)
                end_index = self.__find_end(entries, index)
                if end_index != -1:
                    fragments.append(LeafLogFragment(title, entries[index:end_index+1].copy()))
                    index = end_index
            index += 1
        return AggregateLogFragment("N/A", fragments)

    def __find_end(self, entries: LogEntry, current_index: int) -> int:
        index = current_index + 1
        while index < len(entries):            
            match = re.search(self.end_regex, entries[index].message)
            if match is not None:
                return index
            index += 1
        return -1

class RunProbe(Probe):
    def __init__(self) -> None:
        super().__init__("Start button pressed. Starting competition run.", "(State RunCompletedState completed.|Audio output of lauf_gestoppt.mp3 succeeded)")

    def scan(self, fragment: LogFragment) -> List[LogFragment]:
        return super().scan(fragment)

    def get_title(self, log_entry: LogEntry, match: Match) -> str:
        return f"Lauf {log_entry.date}"

class ObjectDetectionProbe(Probe):
    def __init__(self) -> None:
        super().__init__("TensorRTObjectDetection starting detection.", "TensorRTObjectDetection detection finished.")

    def scan(self, fragment: LogFragment) -> List[LogFragment]:
        return super().scan(fragment)

    def get_title(self, log_entry: LogEntry, match: Match) -> str:
        return f"Object Detection"

class TinyKProbe(Probe):
    def __init__(self) -> None:
        super().__init__("TinyK send data: ", "create_response: response_type: ResponseType.(completed|failed)")

    def scan(self, fragment: LogFragment) -> List[LogFragment]:
        return super().scan(fragment)

    def get_title(self, log_entry: LogEntry, match: Match) -> str:
        return f"TinyK"

class StateProbe(Probe):
    def __init__(self) -> None:
        super().__init__("Entering state (\w+).", "State \w+ completed")

    def scan(self, fragment: LogFragment) -> List[LogFragment]:
        return super().scan(fragment)

    def get_title(self, log_entry: LogEntry, match: Match) -> str:
        return match.group(1)

