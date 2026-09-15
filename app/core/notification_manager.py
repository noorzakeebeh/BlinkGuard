"""
NotificationManager centralizes all outbound notifications and enforces
per-category cooldowns so the user is never spammed. Each notification
category (blink, break) has its own independent cooldown clock.

Uses PySide6's QSystemTrayIcon.showMessage for native-feeling desktop
notifications (works cross-platform without extra dependencies). Sound is
played via QApplication.beep() when enabled, kept deliberately simple/quiet.
"""
import time
from dataclasses import dataclass
from typing import Optional, Callable

from PySide6.QtWidgets import QSystemTrayIcon, QApplication


@dataclass
class NotificationCategory:
    cooldown_seconds: float
    last_fired: float = -1e9

    def ready(self, now: float) -> bool:
        return (now - self.last_fired) >= self.cooldown_seconds

    def mark_fired(self, now: float):
        self.last_fired = now


class NotificationManager:
    def __init__(self, tray_icon: Optional[QSystemTrayIcon] = None,
                 sound_enabled: bool = True, enabled: bool = True):
        self.tray_icon = tray_icon
        self.sound_enabled = sound_enabled
        self.enabled = enabled
        self.categories = {
            "blink": NotificationCategory(cooldown_seconds=60),
            "break": NotificationCategory(cooldown_seconds=60),
            "system": NotificationCategory(cooldown_seconds=5),
        }
        self.on_notify: Optional[Callable[[str, str, str], None]] = None

    def set_tray_icon(self, tray_icon: QSystemTrayIcon):
        self.tray_icon = tray_icon

    def set_cooldown(self, category: str, seconds: float):
        if category in self.categories:
            self.categories[category].cooldown_seconds = seconds

    def _fire(self, category: str, title: str, message: str) -> bool:
        cat = self.categories.setdefault(category, NotificationCategory(60))
        now = time.monotonic()
        if not self.enabled or not cat.ready(now):
            return False
        cat.mark_fired(now)
        if self.tray_icon is not None and self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                title, message, QSystemTrayIcon.MessageIcon.Information, 5000
            )
        if self.sound_enabled:
            try:
                QApplication.beep()
            except Exception:
                pass
        if self.on_notify:
            self.on_notify(category, title, message)
        return True

    def notify_blink_reminder(self) -> bool:
        return self._fire("blink", "BlinkGuard", "\U0001F440 Don't forget to blink!")

    def notify_low_blink_rate(self) -> bool:
        return self._fire(
            "blink", "BlinkGuard",
            "Your blink rate has been low for a while \u2014 try to blink more.",
        )

    def notify_break_reminder(self, minutes: int) -> bool:
        return self._fire(
            "break", "BlinkGuard",
            f"\u2615 You've been on screen for {minutes} min. Time for a short break.",
        )

    def notify_system(self, message: str) -> bool:
        return self._fire("system", "BlinkGuard", message)
