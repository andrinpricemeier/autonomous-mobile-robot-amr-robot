from log_file import LogFile
from probe import RunProbe, ObjectDetectionProbe, TinyKProbe, StateProbe
from log_fragment import AggregateLogFragment, LogFragment


log = LogFile("data/robot_04.06.2021-09.06.2021.run")
fragment = log.parse()
runs = RunProbe().scan(fragment)
for run in runs.fragments:
    print("")
    print("")
    print(f"{run.title}: {run.total_in_seconds}s ({run.count})")
    print("Summary")
    ods = ObjectDetectionProbe().scan(run)  
    print(f"ObjectDetection: {ods.total_in_seconds}s ({ods.count})")
    tinyk = TinyKProbe().scan(run)
    print(f"TinyK: {tinyk.total_in_seconds}s ({tinyk.count})")
    print("States")
    state = StateProbe().scan(run)
    for stateFragment in state.fragments:
        print(f"{stateFragment.title}: {stateFragment.total_in_seconds}s ({stateFragment.count})")
