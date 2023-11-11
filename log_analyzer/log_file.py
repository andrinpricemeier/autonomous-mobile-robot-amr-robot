from log_fragment import LogFragment, LeafLogFragment
from log_entry import LogEntry

class LogFile():
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    def parse(self) -> LogFragment:
        entries = []
        with open(self.filepath) as f:
            for line in f.readlines():
                entries.append(LogEntry(line))            
        return LeafLogFragment(self.filepath, entries)
