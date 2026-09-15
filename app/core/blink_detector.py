"""
BlinkDetector converts a stream of EAR (Eye Aspect Ratio) values into
discrete blink events using a hysteresis state machine.

Why hysteresis instead of a single threshold?
A single EAR threshold causes rapid on/off flicker right around the boundary
(noise from lighting, camera jitter, landmark jitter). Using two thresholds
(a lower "closed" threshold and a higher "open" threshold with a gap between
them) means the eye must clearly close, then clearly reopen, before we count
anything -- this eliminates most double counting and false blinks.

State machine:
    OPEN --(EAR drops below closed_threshold)--> CLOSED
    CLOSED --(EAR rises above open_threshold)--> OPEN  => emit one blink

A minimum "closed frame count" and a refractory (debounce) period further
guard against counting camera glitches or a single noisy frame as a blink.

Thresholds are derived from a calibrated baseline EAR (see calibration flow)
multiplied by configurable ratios, so the system adapts per-user/per-camera
instead of relying on one hard-coded number.
"""
import time
from dataclasses import dataclass

from app.config import (
    EAR_CLOSED_RATIO, EAR_OPEN_RATIO, MIN_CLOSED_FRAMES, BLINK_REFRACTORY_MS,
)


@dataclass
class BlinkDetectorConfig:
    baseline_ear: float = 0.30
    sensitivity: float = 0.75  # scales how aggressively thresholds tighten/loosen


class BlinkDetector:
    STATE_OPEN = "open"
    STATE_CLOSED = "closed"

    def __init__(self, config: BlinkDetectorConfig):
        self.config = config
        self._state = self.STATE_OPEN
        self._closed_frame_count = 0
        self._last_blink_time = 0.0
        self._recompute_thresholds()

    def _recompute_thresholds(self):
        base = self.config.baseline_ear
        # sensitivity nudges the closed threshold: higher sensitivity => counts
        # smaller eye closures as blinks (closed threshold moves up, closer to open).
        sens = max(0.3, min(1.0, self.config.sensitivity))
        closed_ratio = EAR_CLOSED_RATIO + (sens - 0.75) * 0.15
        self.closed_threshold = base * closed_ratio
        self.open_threshold = base * EAR_OPEN_RATIO

    def update_baseline(self, baseline_ear: float):
        self.config.baseline_ear = baseline_ear
        self._recompute_thresholds()

    def update_sensitivity(self, sensitivity: float):
        self.config.sensitivity = sensitivity
        self._recompute_thresholds()

    def reset(self):
        """Call when face is lost/reacquired to avoid a stale half-blink state
        being misinterpreted once tracking resumes."""
        self._state = self.STATE_OPEN
        self._closed_frame_count = 0

    def process_ear(self, ear: float, now: float = None) -> bool:
        """Feed one EAR sample. Returns True exactly on the frame a blink
        completes (open -> closed -> open)."""
        now = now if now is not None else time.monotonic()

        if self._state == self.STATE_OPEN:
            if ear < self.closed_threshold:
                self._state = self.STATE_CLOSED
                self._closed_frame_count = 1
            return False

        # STATE_CLOSED
        if ear < self.open_threshold:
            self._closed_frame_count += 1
            return False

        # Eye has reopened.
        was_valid_closure = self._closed_frame_count >= MIN_CLOSED_FRAMES
        refractory_ok = (now - self._last_blink_time) * 1000.0 >= BLINK_REFRACTORY_MS
        self._state = self.STATE_OPEN
        self._closed_frame_count = 0

        if was_valid_closure and refractory_ok:
            self._last_blink_time = now
            return True
        return False
