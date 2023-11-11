from typing import List
from log_entry import LogEntry

class LogFragment():
    def __init__(self, title: str, count: int, total_in_seconds: float) -> None:
        self.title = title
        self.count = count
        self.total_in_seconds = total_in_seconds

class AggregateLogFragment(LogFragment):
    def __init__(self, title: str, fragments: List[LogFragment]) -> None:
        self.fragments = fragments
        super().__init__(title, self.__calc_count(), self.__calc_total_in_seconds() )

    def __calc_count(self) -> int:
        sum = 0
        for fragment in self.fragments:
            sum += fragment.count
        return sum

    def __calc_total_in_seconds(self) -> float:
        total = 0
        for fragment in self.fragments:
            total += fragment.total_in_seconds
        return total

class LeafLogFragment(LogFragment):
    def __init__(self, title: str, entries: List[LogEntry]) -> None:
        self.entries: List[LogEntry] = entries
        super().__init__(title, self.__calc_count(), self.__calc_total_in_seconds())

    def __calc_count(self) -> int:
        return len(self.entries)

    def __calc_total_in_seconds(self) -> float:
        if len(self.entries) <= 1:
            return 0
        first = self.entries[0].date
        last = self.entries[len(self.entries) - 1].date
        delta = last - first
        return delta.total_seconds()
