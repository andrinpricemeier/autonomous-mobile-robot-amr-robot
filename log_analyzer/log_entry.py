import datetime

class LogEntry():
    def __init__(self, line: str) -> None:
        split_up = line.split("|")
        try:
            self.date = datetime.datetime.strptime(split_up[0], '%Y-%m-%d %H:%M:%S,%f')
        except ValueError:
            self.date = None
        if len(split_up) >= 4:
            self.message = split_up[3]
        else:
            self.message = "N/A"