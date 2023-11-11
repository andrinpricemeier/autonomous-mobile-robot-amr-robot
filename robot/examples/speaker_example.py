import os, sys, inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from detected_object import DetectedObject
from usb_speaker import USBSpeaker


speaker = USBSpeaker("../audio", "hw:2,0", 2, True)
speaker.announce_path_found()
speaker.announce_path_not_found()
speaker.announce_run_started()
speaker.announce_run_completed()
speaker.announce_run_stopped()
speaker.announce_start(DetectedObject.hammer)
speaker.announce_start(DetectedObject.pencil)
speaker.announce_start(DetectedObject.bucket)
speaker.announce_start(DetectedObject.ruler)
speaker.announce_start(DetectedObject.wrench)
speaker.announce_start(DetectedObject.taco)
speaker.announce_target(DetectedObject.hammer)
speaker.announce_target(DetectedObject.pencil)
speaker.announce_target(DetectedObject.bucket)
speaker.announce_target(DetectedObject.ruler)
speaker.announce_target(DetectedObject.wrench)
speaker.announce_target(DetectedObject.taco)
