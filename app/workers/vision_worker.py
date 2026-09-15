"""
VisionWorker runs the camera + computer-vision pipeline on a background
QThread so the UI never freezes while frames are analyzed.

Pipeline per loop iteration:
    Camera -> frame -> EyeDetector (EAR) -> BlinkDetector (blink events)
    -> BlinkStatistics (rate / longest-no-blink / low-blink periods)
    -> ScreenTimeTracker + BreakManager -> NotificationManager

Only numeric results ever cross the thread boundary via Qt signals -- the
raw frame is processed and discarded inside this thread and never emitted,
saved, or transmitted anywhere (see PrivacyManager).
"""
import time
from datetime import datetime

from PySide6.QtCore import QThread, Signal

from app.core.camera_handler import CameraHandler, CameraError
from app.core.eye_detector import EyeDetector
from app.core.blink_detector import BlinkDetector, BlinkDetectorConfig
from app.core.blink_statistics import BlinkStatistics
from app.core.screen_time_tracker import ScreenTimeTracker
from app.core.break_manager import BreakManager
from app.config import CAMERA_FPS_TARGET, FACE_LOST_GRACE_SECONDS


class VisionWorker(QThread):
    # --- outbound signals (numeric/state only, never image data) ---------
    stats_updated = Signal(dict)          # live dashboard numbers
    camera_status_changed = Signal(str)   # "active" | "face_not_detected" | "unavailable" | "paused" | "multiple_faces"
    camera_error = Signal(str)
    blink_reminder_needed = Signal()
    low_blink_reminder_needed = Signal()
    break_due = Signal(int)               # minutes just completed
    calibration_sample = Signal(float)    # raw EAR sample, only during calibration
    minute_aggregate_ready = Signal(object, int, float)  # timestamp, blink_count, avg_ear

    def __init__(self, settings_manager):
        super().__init__()
        self.settings = settings_manager
        self._running = False
        self._paused = False
        self._calibrating = False

        self.camera = CameraHandler(self.settings.get("camera_index", 0))
        self.eye_detector = EyeDetector()
        self.blink_detector = BlinkDetector(BlinkDetectorConfig(
            baseline_ear=self.settings.get("baseline_ear", 0.30),
            sensitivity=self.settings.get("blink_sensitivity", 0.75),
        ))
        self.stats = BlinkStatistics(
            low_rate_threshold=self.settings.get("low_blink_rate_threshold", 8),
            sustain_seconds=self.settings.get("low_blink_sustain_seconds", 30),
        )
        self.screen_tracker = ScreenTimeTracker()
        self.break_manager = BreakManager(
            interval_minutes=self.settings.get("break_interval_minutes", 20),
            duration_minutes=self.settings.get("break_duration_minutes", 5),
            enabled=self.settings.get("breaks_enabled", True),
        )

        self._last_face_seen_time = time.monotonic()
        self._face_currently_lost = True
        self._last_reminder_time = -1e9
        self._minute_bucket_start = None
        self._minute_bucket_blinks = 0
        self._minute_bucket_ear_sum = 0.0
        self._minute_bucket_ear_count = 0

    # ------------------------------------------------------------ controls
    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False
        self.blink_detector.reset()

    @property
    def is_paused(self) -> bool:
        return self._paused

    def stop(self):
        self._running = False

    def begin_calibration(self):
        self._calibrating = True

    def end_calibration(self, baseline_ear: float):
        self._calibrating = False
        self.blink_detector.update_baseline(baseline_ear)
        self.settings.update({"baseline_ear": baseline_ear, "calibrated": True})

    def apply_live_settings(self):
        """Re-read thresholds from settings without restarting the thread."""
        self.blink_detector.update_sensitivity(self.settings.get("blink_sensitivity", 0.75))
        self.blink_detector.update_baseline(self.settings.get("baseline_ear", 0.30))
        self.stats.update_thresholds(
            self.settings.get("low_blink_rate_threshold", 8),
            self.settings.get("low_blink_sustain_seconds", 30),
        )
        self.break_manager.update_config(
            self.settings.get("break_interval_minutes", 20),
            self.settings.get("break_duration_minutes", 5),
            self.settings.get("breaks_enabled", True),
        )

    def set_camera_index(self, index: int):
        self.camera.set_camera_index(index)
        if self.camera.is_open():
            try:
                self.camera.open()
            except CameraError as e:
                self.camera_error.emit(str(e))

    def take_break_now(self):
        self.screen_tracker.start_break()
        self.break_manager.start_break()

    def end_break_now(self):
        self.screen_tracker.end_break()
        self.break_manager.end_break()

    # -------------------------------------------------------------- main loop
    def run(self):
        self._running = True
        try:
            self.camera.open()
        except CameraError as e:
            self.camera_error.emit(str(e))
            self.camera_status_changed.emit("unavailable")
            return

        frame_interval = 1.0 / CAMERA_FPS_TARGET
        last_notify_check = time.monotonic()

        while self._running:
            loop_start = time.monotonic()

            if self._paused:
                self.camera_status_changed.emit("paused")
                time.sleep(0.2)
                continue

            try:
                frame = self.camera.read_frame()
            except CameraError as e:
                self.camera_error.emit(str(e))
                self.camera_status_changed.emit("unavailable")
                time.sleep(1.0)
                continue

            result = self.eye_detector.process(frame)
            now = time.monotonic()

            if self._calibrating:
                if result.face_detected and result.ear is not None:
                    self.calibration_sample.emit(result.ear)
                self.camera_status_changed.emit("active" if result.face_detected else "face_not_detected")
                self._sleep_remaining(loop_start, frame_interval)
                continue

            if result.face_count >= 2:
                self.camera_status_changed.emit("multiple_faces")
                # Do not mix blink info from multiple people: skip blink logic
                # this frame, but keep screen-time ticking based on presence.
                self.screen_tracker.tick(True, self._paused, now)
                self._maybe_run_break_check(now)
                self._sleep_remaining(loop_start, frame_interval)
                continue

            if not result.face_detected:
                if not self._face_currently_lost:
                    self._face_currently_lost = True
                self.camera_status_changed.emit("face_not_detected")
                self.screen_tracker.tick(False, self._paused, now)
                self._maybe_run_break_check(now)
                self._sleep_remaining(loop_start, frame_interval)
                continue

            # Face re-acquired after a loss: avoid treating the gap as "no blink"
            if self._face_currently_lost:
                gap = now - self._last_face_seen_time
                if gap > FACE_LOST_GRACE_SECONDS:
                    self.blink_detector.reset()
                self._face_currently_lost = False
            self._last_face_seen_time = now

            self.camera_status_changed.emit("active")
            self.screen_tracker.tick(True, self._paused, now)

            blinked = self.blink_detector.process_ear(result.ear, now)
            if blinked:
                self.stats.record_blink(now)
                self._minute_bucket_blinks += 1
            self._minute_bucket_ear_sum += result.ear
            self._minute_bucket_ear_count += 1
            self._maybe_flush_minute_bucket(now)

            self.stats.tick(now, on_low_period_closed=self._on_low_period_closed)
            self._maybe_run_break_check(now)
            self._maybe_check_blink_reminders(now)
            self._emit_stats(now)

            self._sleep_remaining(loop_start, frame_interval)

        self.camera.close()

    # ------------------------------------------------------------- helpers
    def _sleep_remaining(self, loop_start: float, frame_interval: float):
        elapsed = time.monotonic() - loop_start
        remaining = frame_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _maybe_flush_minute_bucket(self, now: float):
        if self._minute_bucket_start is None:
            self._minute_bucket_start = now
            return
        if now - self._minute_bucket_start >= 60.0:
            avg_ear = (self._minute_bucket_ear_sum / self._minute_bucket_ear_count
                       if self._minute_bucket_ear_count else 0.0)
            self.minute_aggregate_ready.emit(
                datetime.now(), self._minute_bucket_blinks, avg_ear
            )
            self._minute_bucket_start = now
            self._minute_bucket_blinks = 0
            self._minute_bucket_ear_sum = 0.0
            self._minute_bucket_ear_count = 0

    def _on_low_period_closed(self, period):
        # Surfaced to UI via stats dict on next emit (see _emit_stats); the
        # main window listens for the count increasing and persists it.
        avg_rate = (sum(period.rate_samples) / len(period.rate_samples)
                    if period.rate_samples else 0.0)
        self.low_blink_reminder_needed.emit()

    def _maybe_check_blink_reminders(self, now: float):
        no_blink_threshold = self.settings.get("no_blink_reminder_seconds", 12)
        cooldown = self.settings.get("reminder_cooldown_seconds", 60)
        seconds_idle = self.stats.seconds_since_last_blink(now)

        if seconds_idle >= no_blink_threshold and (now - self._last_reminder_time) >= cooldown:
            self._last_reminder_time = now
            self.blink_reminder_needed.emit()

    def _maybe_run_break_check(self, now: float):
        dt = getattr(self, "_last_break_tick", now)
        elapsed = now - dt
        self._last_break_tick = now
        is_active = not self.screen_tracker.currently_away and not self._paused
        due = self.break_manager.tick(elapsed, is_active)
        if due:
            minutes = int(self.break_manager.interval_seconds // 60)
            self.break_due.emit(minutes)

    def _emit_stats(self, now: float):
        self.stats_updated.emit({
            "blink_rate": round(self.stats.current_blink_rate(now), 1),
            "total_blinks": self.stats.total_blinks,
            "longest_no_blink": round(self.stats.longest_no_blink_seconds, 1),
            "seconds_since_last_blink": round(self.stats.seconds_since_last_blink(now), 1),
            "low_blink_periods": self.stats.low_blink_period_count,
            "is_currently_low": self.stats.is_currently_low,
            "screen_time": self.screen_tracker.screen_time_seconds,
            "active_time": self.screen_tracker.active_time_seconds,
            "break_time": self.screen_tracker.break_time_seconds,
            "breaks_taken": self.break_manager.breaks_taken,
            "minutes_until_break": round(self.break_manager.minutes_until_break, 1),
            "on_break": self.break_manager.on_break,
            "break_remaining_seconds": round(self.break_manager.break_remaining_seconds, 1),
        })
