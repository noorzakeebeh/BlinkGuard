"""
ScreenTimeTracker measures how long the user has been actively at the
screen versus away, using face presence as a (imperfect but reasonable)
proxy for presence. It intentionally does NOT count time as "active" once
the face has been absent for AWAY_AFTER_SECONDS, so screen-time stats
aren't inflated by an empty desk.

Distinguishes:
- screen_time: total wall-clock time the app has been monitoring (session length)
- active_time: time where the user was actually judged present
- break_time: time explicitly spent on a break (see BreakManager)
"""
import time
from app.config import AWAY_AFTER_SECONDS


class ScreenTimeTracker:
    def __init__(self):
        self._session_start = time.monotonic()
        self._active_seconds = 0.0
        self._break_seconds = 0.0
        self._last_tick = self._session_start
        self._last_face_seen = self._session_start
        self._on_break = False
        self.currently_away = False

    def start_break(self):
        self._on_break = True

    def end_break(self):
        self._on_break = False

    @property
    def on_break(self) -> bool:
        return self._on_break

    def tick(self, face_detected: bool, paused: bool, now: float = None):
        now = now if now is not None else time.monotonic()
        dt = max(0.0, now - self._last_tick)
        self._last_tick = now

        if face_detected:
            self._last_face_seen = now
            self.currently_away = False
        else:
            self.currently_away = (now - self._last_face_seen) >= AWAY_AFTER_SECONDS

        if self._on_break:
            self._break_seconds += dt
        elif not paused and not self.currently_away:
            self._active_seconds += dt

    @property
    def screen_time_seconds(self) -> float:
        return time.monotonic() - self._session_start

    @property
    def active_time_seconds(self) -> float:
        return self._active_seconds

    @property
    def break_time_seconds(self) -> float:
        return self._break_seconds

    @staticmethod
    def format_hms(seconds: float) -> str:
        seconds = int(seconds)
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}h {m}m"
        if m > 0:
            return f"{m}m {s}s"
        return f"{s}s"
