"""
BreakManager tracks continuous active screen time (separate from blink
monitoring) and signals when a break is due. It also supports the user
manually starting/ending a break via the tray menu or dashboard button.
"""
import time


class BreakManager:
    def __init__(self, interval_minutes: int = 20, duration_minutes: int = 5,
                 enabled: bool = True):
        self.interval_seconds = interval_minutes * 60
        self.duration_seconds = duration_minutes * 60
        self.enabled = enabled
        self._continuous_active_seconds = 0.0
        self._break_remaining = 0.0
        self.breaks_taken = 0
        self.on_break = False

    def update_config(self, interval_minutes: int, duration_minutes: int, enabled: bool):
        self.interval_seconds = interval_minutes * 60
        self.duration_seconds = duration_minutes * 60
        self.enabled = enabled

    def start_break(self):
        self.on_break = True
        self._break_remaining = self.duration_seconds
        self._continuous_active_seconds = 0.0
        self.breaks_taken += 1

    def end_break(self):
        self.on_break = False
        self._break_remaining = 0.0

    def tick(self, dt_seconds: float, is_active: bool) -> bool:
        """Advance the manager by dt_seconds. Returns True if a break just
        became due (caller should trigger a notification)."""
        if self.on_break:
            self._break_remaining -= dt_seconds
            if self._break_remaining <= 0:
                self.end_break()
            return False

        if not self.enabled:
            return False

        if is_active:
            self._continuous_active_seconds += dt_seconds

        if self._continuous_active_seconds >= self.interval_seconds:
            # Reset the counter so we don't fire again immediately; the
            # notification cooldown in NotificationManager provides a second
            # layer of spam protection regardless.
            self._continuous_active_seconds = 0.0
            return True
        return False

    @property
    def minutes_until_break(self) -> float:
        remaining = max(0.0, self.interval_seconds - self._continuous_active_seconds)
        return remaining / 60.0

    @property
    def break_remaining_seconds(self) -> float:
        return max(0.0, self._break_remaining)
