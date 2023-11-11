import gi
import os
import logging
import time
from speaker import Speaker, Announcement
from detected_object import DetectedObject
from urllib.request import pathname2url
from random import randrange
from tinyk import RobotPosition
import threading
import queue

gi.require_version("Gst", "1.0")
from gi.repository import Gst

class StartPictogramAnnouncement(Announcement):
    def __init__(self, pictogram: DetectedObject) -> None:
        self.pictogram = pictogram
 
    def output_filename(self) -> str:
        return f"start_{self.pictogram.name}.mp3"

class TargetPictogramAnnouncement(Announcement):
    def __init__(self, pictogram: DetectedObject) -> None:
        self.pictogram = pictogram
 
    def output_filename(self) -> str:
        return f"ziel_{self.pictogram.name}.mp3"

class PathFoundAnnouncement(Announcement):
    def output_filename(self) -> str:
        return "pfad_gefunden.mp3"

class PathNotFoundAnnouncement(Announcement):
    def output_filename(self) -> str:
        return "pfad_nicht_gefunden.mp3"

class RunStartedAnnouncement(Announcement):
    def output_filename(self) -> str:
        return "lauf_gestartet.mp3"

class RunCompletedAnnouncement(Announcement):
    def output_filename(self) -> str:
        return "lauf_beendet.mp3"

class RunStoppedAnnouncement(Announcement):
    def output_filename(self) -> str:
        return "lauf_gestoppt.mp3"

class StateTransitionAnnouncement(Announcement):
    def __init__(self, state_class_name: str) -> None:
        self.state_class_name = state_class_name
 
    def output_filename(self) -> str:
        return f"zustand_{self.state_class_name}.mp3"

class BrickAnnouncement(Announcement):
    def __init__(self, bricks_count: int) -> None:
        self.bricks_count = bricks_count
 
    def output_filename(self) -> str:
        if self.bricks_count <= 12:
            return f"{self.bricks_count}_ziegelstein_erkannt.mp3"
        else:
            return "mehr_als_12_ziegelstein_erkannt.mp3"

class NoTargetPictogramAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "fehler_kein_zielpiktogramm_gesetzt.mp3"

class StartPictogramFoundAreaAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "start_piktogramm_gefunden_flaeche.mp3"

class StartPictogramFoundHeightAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "start_piktogramm_gefunden_hoehe.mp3"

class StairsAreaExecuteClimbingPlanAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "stairs_area_fuehre_steigplan_aus.mp3"

class StairsAreaUsingPathClimbingPlanAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "stairs_area_verwende_pfadsteigplan.mp3"

class StairsAreaUsingSensorClimbingPlanAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "stairs_area_verwende_pfadsteigplan.mp3"

class StairsAreaPlanFailedUsingBackupPlanAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "fehler_stairs_area_steigplan_fehlgeschlagen_verwende_backupplan.mp3"

class StairsAreaPlanFailedNoBackupPlanAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "fehler_stairs_area_steigplan_fehlgeschlagen_kein_backupplan.mp3"

class PathClimbingPlanErrorFoundAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "fehler_pfadsteigplan_fehler_gefunden.mp3"

class PathClimbingPlanCompletedAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "pfadsteigplan_plan_abgeschlossen.mp3"

class PathClimbingObstacleFoundAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "pfadsteigplan_hindernis_gefunden.mp3"

class MoveForwardAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "navigation_fahre_vorwaerts.mp3"

class MoveForwardUntilObstacleAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "navigation_fahre_vorwaerts_bis_hindernis.mp3"

class RotateClockwiseAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "navigation_rotiere_uhrzeigersinn.mp3"

class RotateCounterClockwiseAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "navigation_rotiere_gegen_uhrzeigersinn.mp3"

class MoveBackwardAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "navigation_fahre_rueckwaerts.mp3"

class ClimbAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True
    def output_filename(self) -> str:
        return "navigation_climb.mp3"

class InitMasterAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True

    def output_filename(self) -> str:
        return "navigation_initialisiere_master.mp3"

class ShutdownMasterAnnouncement(Announcement):
    def is_debug_only(self) -> bool:
        return True

    def output_filename(self) -> str:
        return "navigation_fahre_master_herunter.mp3"

class ChangeRobotPositionAnnouncement(Announcement):
    def __init__(self, position: RobotPosition) -> None:
        self.position = position

    def is_debug_only(self) -> bool:
        return True

    def output_filename(self) -> str:
        return f"navigation_neue_position_{self.position.name}.mp3"

class SidewaysLeftAnnouncement(Announcement):
    def __init__(self, movement_in_cm: int) -> None:
        self.movement_in_cm = movement_in_cm

    def is_debug_only(self) -> bool:
        return True

    def output_filename(self) -> str:
        if self.movement_in_cm >= 0 and self.movement_in_cm <= 5:
            return "navigation_seitwaerts_links_0_bis_5_zentimeter.mp3"
        elif self.movement_in_cm > 5 and self.movement_in_cm <= 10:
            return "navigation_seitwaerts_links_5_bis_10_zentimeter.mp3"
        elif self.movement_in_cm > 10 and self.movement_in_cm <= 15:
            return "navigation_seitwaerts_links_10_bis_15_zentimeter.mp3"
        elif self.movement_in_cm > 15 and self.movement_in_cm <= 20:
            return "navigation_seitwaerts_links_15_bis_20_zentimeter.mp3"
        else:
            return "navigation_seitwaerts_links_mehr_als_20_zentimeter.mp3"


class SidewaysRightAnnouncement(Announcement):
    def __init__(self, movement_in_cm: int) -> None:
        self.movement_in_cm = movement_in_cm

    def is_debug_only(self) -> bool:
        return True

    def output_filename(self) -> str:
        if self.movement_in_cm >= 0 and self.movement_in_cm <= 5:
            return "navigation_seitwaerts_rechts_0_bis_5_zentimeter.mp3"
        elif self.movement_in_cm > 5 and self.movement_in_cm <= 10:
            return "navigation_seitwaerts_rechts_5_bis_10_zentimeter.mp3"
        elif self.movement_in_cm > 10 and self.movement_in_cm <= 15:
            return "navigation_seitwaerts_rechts_10_bis_15_zentimeter.mp3"
        elif self.movement_in_cm > 15 and self.movement_in_cm <= 20:
            return "navigation_seitwaerts_rechts_15_bis_20_zentimeter.mp3"
        else:
            return "navigation_seitwaerts_rechts_mehr_als_20_zentimeter.mp3"

class WarmupAnnouncement(Announcement):
    def output_filename(self) -> str:
        return f"warming_up.mp3"

class PressStartButtonAnnouncement(Announcement):
    def output_filename(self) -> str:
        return f"bitte_startknopf_druecken.mp3"

class StartPictogramNotFoundAnnouncement(Announcement):
    def output_filename(self) -> str:
        return f"start_piktogramm_nicht_gefunden.mp3"

class IndianaJonesAnnouncement(Announcement):
    def output_filename(self) -> str:
        return f"indiana_jones.mp3"

class AudienceDetectedAnnouncement(Announcement):
    def output_filename(self) -> str:
        return f"publikum_erkannt.mp3"

class IntroductionAnnouncement(Announcement):
    def output_filename(self) -> str:
        return f"begruessung.mp3"

class FarewellAnnouncement(Announcement):
    def output_filename(self) -> str:
        return f"verabschiedung.mp3"
class USBSpeaker(Speaker):
    """Represents a physical speaker connected by USB to the Jetson Nano.

    Args:
        Speaker ([type]): the superclass.
    """
    def __init__(
        self, audio_dir: str, audio_device_id: str, card_nr: int, is_debugging: bool
    ) -> None:
        self.audio_dir = audio_dir
        self.audio_device_id = audio_device_id
        self.is_enabled = True
        self.is_debugging = is_debugging
        logging.info("Setting volume to 100%.")
        os.system(f"amixer -c {card_nr} set Speaker 100%")
        Gst.init(None)
        self.announcements = queue.Queue()
        # Tobias: Set this to false if background thread doesn't work.
        self.is_background_thread_enabled = False
        if self.is_background_thread_enabled:
            self.thread = threading.Thread(target=self.__consume_background)
            self.thread.daemon = True
            self.thread.start()
        self.__warm_up()    
    
    def announce_indiana_jones(self) -> None:
        self.announcements.put(IndianaJonesAnnouncement())
        self.__consume()

    def announce_start(self, pictogram: DetectedObject) -> None:
        self.announcements.put(StartPictogramAnnouncement(pictogram))
        self.__consume()

    def announce_target(self, pictogram: DetectedObject) -> None:
        self.announcements.put(TargetPictogramAnnouncement(pictogram))
        self.__consume()

    def announce_path_found(self) -> None:
        self.announcements.put(PathFoundAnnouncement())
        self.__consume()

    def announce_path_not_found(self) -> None:
        self.announcements.put(PathNotFoundAnnouncement())
        self.__consume()

    def announce_run_started(self) -> None:
        self.announcements.put(RunStartedAnnouncement())
        self.__consume()

    def announce_run_completed(self) -> None:
        self.announcements.put(RunCompletedAnnouncement())
        self.__consume()

    def announce_run_stopped(self) -> None:
        self.announcements.put(RunStoppedAnnouncement())
        self.__consume()

    def announce_state_transition(self, state_class_name: str) -> None:
        self.announcements.put(StateTransitionAnnouncement(state_class_name))
        self.__consume()

    def announce_bricks(self, bricks_count: int) -> None:
        self.announcements.put(BrickAnnouncement(bricks_count))
        self.__consume()

    def announce_no_target_pictogram(self) -> None:
        self.announcements.put(NoTargetPictogramAnnouncement())
        self.__consume()

    def announce_start_pictogram_found_area(self) -> None:
        self.announcements.put(StartPictogramFoundAreaAnnouncement())
        self.__consume()

    def announce_start_pictogram_found_height(self) -> None:
        self.announcements.put(StartPictogramFoundHeightAnnouncement())
        self.__consume()

    def announce_stairs_area_execute_climbing_plan(self) -> None:
        self.announcements.put(StairsAreaExecuteClimbingPlanAnnouncement())
        self.__consume()

    def announce_stairs_area_using_path_climbing_plan(self) -> None:
        self.announcements.put(StairsAreaUsingPathClimbingPlanAnnouncement())
        self.__consume()

    def announce_stairs_area_using_sensor_climbing_plan(self) -> None:
        self.announcements.put(StairsAreaUsingSensorClimbingPlanAnnouncement())
        self.__consume()

    def announce_stairs_area_climbing_plan_failed_has_backupplan(self) -> None:
        self.announcements.put(StairsAreaPlanFailedUsingBackupPlanAnnouncement())
        self.__consume()

    def announce_stairs_area_climbing_plan_failed_no_backupplan(self) -> None:
        self.announcements.put(StairsAreaPlanFailedNoBackupPlanAnnouncement())
        self.__consume()

    def announce_path_climbing_plan_error_found(self) -> None:
        self.announcements.put(PathClimbingPlanErrorFoundAnnouncement())
        self.__consume()

    def announce_path_climbing_plan_completed(self) -> None:
        self.announcements.put(PathClimbingPlanCompletedAnnouncement())
        self.__consume()

    def announce_path_climbing_plan_obstacle_found(self) -> None:
        self.announcements.put(PathClimbingObstacleFoundAnnouncement())
        self.__consume()

    def announce_move_forward(self) -> None:
        self.announcements.put(MoveForwardAnnouncement())
        self.__consume()

    def announce_move_forward_until_obstacle(self) -> None:
        self.announcements.put(MoveForwardUntilObstacleAnnouncement())
        self.__consume()

    def announce_rotate_clockwise(self) -> None:
        self.announcements.put(RotateClockwiseAnnouncement())
        self.__consume()

    def announce_rotate_counter_clockwise(self) -> None:
        self.announcements.put(RotateCounterClockwiseAnnouncement())
        self.__consume()

    def announce_move_backward(self) -> None:
        self.announcements.put(MoveBackwardAnnouncement())
        self.__consume()

    def announce_climb(self) -> None:
        self.announcements.put(ClimbAnnouncement())
        self.__consume()

    def announce_init_master(self) -> None:
        self.announcements.put(InitMasterAnnouncement())
        self.__consume()

    def announce_shutdown_master(self) -> None:
        self.announcements.put(ShutdownMasterAnnouncement())
        self.__consume()

    def announce_change_robot_position(self, position: RobotPosition) -> None:
        self.announcements.put(ChangeRobotPositionAnnouncement(position))
        self.__consume()

    def announce_sideways_left(self, movement_in_cm: int) -> None:
        self.announcements.put(SidewaysLeftAnnouncement(movement_in_cm))
        self.__consume()

    def announce_sideways_right(self, movement_in_cm: int) -> None:
        self.announcements.put(SidewaysRightAnnouncement(movement_in_cm))
        self.__consume()

    def announce_press_start_button(self) -> None:
        self.announcements.put(PressStartButtonAnnouncement())
        self.__consume()

    def announce_start_pictogram_not_found(self) -> None:
        self.announcements.put(StartPictogramNotFoundAnnouncement())
        self.__consume()

    def announce_audience_detected(self) -> None:
        self.announcements.put(AudienceDetectedAnnouncement())
        self.__consume()

    def announce_introduction(self) -> None:
        self.announcements.put(IntroductionAnnouncement())
        self.__consume()

    def announce_farewell(self) -> None:
        self.announcements.put(FarewellAnnouncement())
        self.__consume()

    def __consume(self):
        if not self.is_background_thread_enabled:
            announcement: Announcement = self.announcements.get()
            if (not self.is_debugging and not announcement.is_debug_only()) or self.is_debugging:
                self.__play(announcement.output_filename())
            self.announcements.task_done()

    def __consume_background(self):        
        while True:
            announcement: Announcement = self.announcements.get()
            if (not self.is_debugging and not announcement.is_debug_only()) or self.is_debugging:
                self.__play(announcement.output_filename())
            self.announcements.task_done()

    def __warm_up(self) -> None:
        self.announcements.put(WarmupAnnouncement())
        self.__consume()

    def __play(self, filename: str) -> None:
        if not self.is_enabled:
            logging.warn("Speaker is disabled. Skipping audio output.")
            return
        retries = 10
        for _ in range(retries):
            try:
                self.__play_with_playbin(filename)
                logging.debug(f"Audio output of {filename} succeeded.")
                return
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.debug(f"Audio output of {filename} failed.")
                logging.exception(e)
                time.sleep(2)
                pass
        logging.warn("Audio output failed. Disabling speaker for the rest of the run.")
        self.is_enabled = False
        # Don't raise an exception. It's not THAT important for the audio output to work.
        # raise Exception("Audio output failed.")

    def __play_with_playbin(self, filename: str) -> None:
        filepath = os.path.abspath(os.path.join(self.audio_dir, f"{filename}"))
        if not os.path.exists(filepath):
            logging.error(f"Audio file {filepath} not found. Ignoring audio output.")
            return
        playbin = Gst.ElementFactory.make("playbin", "playbin")
        playbin.props.uri = "file://" + pathname2url(filepath)
        playbin.props.volume = 1.0
        audiosink = Gst.ElementFactory.make("alsasink", "alsa-output")
        audiosink.set_property("device", self.audio_device_id)
        playbin.set_property("audio-sink", audiosink)
        set_result = playbin.set_state(Gst.State.PLAYING)
        if set_result != Gst.StateChangeReturn.ASYNC:
            raise Exception("playbin.set_state returned " + repr(set_result))
        bus = playbin.get_bus()
        bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
        playbin.set_state(Gst.State.NULL)
