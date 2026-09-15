"""
BlinkStatistics maintains rolling, in-memory statistics derived from the
stream of blink events produced by BlinkDetector:

- blinks per minute (rolling 60s window, so it reacts to recent behavior
  rather than being diluted by the whole session)
- longest time without a blink (per session)
- low-blink-period detection: when the rolling rate stays below a
  configurable threshold for a sustained duration, a "low blink period" is
  opened; it closes once the rate recovers, and is only logged if it lasted
  long enough to be meaningful (avoids logging noise from one slow patch).

All of this operates purely on timestamps and counts -- no images.
"""
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class LowBlinkPeriod:
    start_time: float
    end_time: Optional[float] = None
    rate_samples: List[float] = field(default_factory=list)


class BlinkStatistics:
    def __init__(self, low_rate_threshold: float = 8.0, sustain_seconds: float = 30.0,
                 rolling_window_seconds: float = 60.0):
        self.low_rate_threshold = low_rate_threshold
        self.sustain_seconds = sustain_seconds
        self.rolling_window_seconds = rolling_window_seconds

        self._blink_timestamps = deque()   # for rolling rate calc
        self.total_blinks = 0
        self.longest_no_blink_seconds = 0.0
        self.last_blink_time: Optional[float] = None
        self._session_start = time.monotonic()

        self._below_threshold_since: Optional[float] = None
        self.completed_low_blink_periods: List[LowBlinkPeriod] = []
        self._active_low_period: Optional[LowBlinkPeriod] = None

    def record_blink(self, now: float = None):
        now = now if now is not None else time.monotonic()
        if self.last_blink_time is not None:
            gap = now - self.last_blink_time
            self.longest_no_blink_seconds = max(self.longest_no_blink_seconds, gap)
        self.last_blink_time = now
        self.total_blinks += 1
        self._blink_timestamps.append(now)
        self._trim_window(now)

    def _trim_window(self, now: float):
        cutoff = now - self.rolling_window_seconds
        while self._blink_timestamps and self._blink_timestamps[0] < cutoff:
            self._blink_timestamps.popleft()

    def current_blink_rate(self, now: float = None) -> float:
        """Blinks-per-minute extrapolated from the rolling window."""
        now = now if now is not None else time.monotonic()
        self._trim_window(now)
        window = min(self.rolling_window_seconds, max(now - self._session_start, 1e-6))
        count = len(self._blink_timestamps)
        return (count / window) * 60.0

    def seconds_since_last_blink(self, now: float = None) -> float:
        now = now if now is not None else time.monotonic()
        if self.last_blink_time is None:
            return now - self._session_start
        return now - self.last_blink_time

    def tick(self, now: float = None, session_id_provider=None, on_low_period_closed=None):
        """Call periodically (e.g. once per processed frame) to update the
        longest-no-blink figure in real time and manage low-blink-period
        open/close transitions. `on_low_period_closed(period)` is invoked
        when a sustained low period ends, so the caller can persist it."""
        now = now if now is not None else time.monotonic()

        # Keep longest-no-blink current even while no new blink has happened.
        gap = self.seconds_since_last_blink(now)
        self.longest_no_blink_seconds = max(self.longest_no_blink_seconds, gap)

        rate = self.current_blink_rate(now)
        if rate < self.low_rate_threshold:
            if self._below_threshold_since is None:
                self._below_threshold_since = now
                self._active_low_period = LowBlinkPeriod(start_time=now)
            self._active_low_period.rate_samples.append(rate)
        else:
            if self._below_threshold_since is not None:
                duration = now - self._below_threshold_since
                if duration >= self.sustain_seconds and self._active_low_period:
                    self._active_low_period.end_time = now
                    self.completed_low_blink_periods.append(self._active_low_period)
                    if on_low_period_closed:
                        on_low_period_closed(self._active_low_period)
                self._below_threshold_since = None
                self._active_low_period = None

    @property
    def low_blink_period_count(self) -> int:
        return len(self.completed_low_blink_periods)

    @property
    def is_currently_low(self) -> bool:
        if self._below_threshold_since is None:
            return False
        return (time.monotonic() - self._below_threshold_since) >= self.sustain_seconds

    def update_thresholds(self, low_rate_threshold: float, sustain_seconds: float):
        self.low_rate_threshold = low_rate_threshold
        self.sustain_seconds = sustain_seconds
