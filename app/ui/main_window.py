from datetime import date, timedelta

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget,
    QLabel, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent

from app.config import APP_NAME
from app.data.settings_manager import SettingsManager
from app.data.database import DatabaseManager
from app.core.notification_manager import NotificationManager
from app.core.camera_handler import CameraHandler
from app.workers.vision_worker import VisionWorker
from app.ui.theme import apply_theme
from app.ui.tray import TrayController
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.history_page import HistoryPage
from app.ui.pages.insights_page import InsightsPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.privacy_page import PrivacyPage
from app.ui.pages.onboarding_wizard import OnboardingWizard


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle(APP_NAME)
        self.resize(1080, 720)

        self.settings = SettingsManager()
        self.db = DatabaseManager()
        self.session_id = self.db.start_session()

        apply_theme(self.app, self.settings.get("theme", "system"))

        self.tray = TrayController(self.app)
        self.notifications = NotificationManager(
            tray_icon=self.tray.tray_icon,
            sound_enabled=self.settings.get("notification_sound", True),
            enabled=self.settings.get("notifications_enabled", True),
        )
        self.tray.show()
        self._wire_tray()

        self._build_ui()

        if not self.settings.get("calibrated", False):
            self._run_onboarding()

        self._start_worker()

        self._dashboard_refresh_timer = QTimer(self)
        self._dashboard_refresh_timer.timeout.connect(self._refresh_dashboard_chart)
        self._dashboard_refresh_timer.start(5000)

        # Periodically write the still-open session's numbers to the DB so
        # History/Insights reflect today's activity in near-real-time,
        # instead of only updating once the app is fully closed.
        self._checkpoint_timer = QTimer(self)
        self._checkpoint_timer.timeout.connect(self._checkpoint_session)
        self._checkpoint_timer.start(15000)

        self._history_range = "today"
        self._refresh_history()

    # ------------------------------------------------------------- UI build
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav = QWidget()
        nav.setObjectName("SideNav")
        nav.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(12, 20, 12, 20)
        nav_layout.setSpacing(4)

        app_label = QLabel(APP_NAME)
        app_label.setStyleSheet("font-size: 16px; font-weight: 700; margin-bottom: 12px; padding-left: 6px;")
        nav_layout.addWidget(app_label)

        self.nav_buttons = {}
        for key, label in [
            ("dashboard", "Dashboard"), ("history", "History"),
            ("insights", "Insights"), ("settings", "Settings"), ("privacy", "Privacy"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("SideNavButton")
            btn.setCheckable(True)
            btn.setProperty("active", False)
            btn.clicked.connect(lambda _, k=key: self._switch_page(k))
            nav_layout.addWidget(btn)
            self.nav_buttons[key] = btn
        nav_layout.addStretch()
        layout.addWidget(nav)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, stretch=1)

        self.dashboard_page = DashboardPage()
        self.history_page = HistoryPage()
        self.insights_page = InsightsPage()
        self.settings_page = SettingsPage(camera_options=CameraHandler().list_available_cameras())
        self.privacy_page = PrivacyPage()

        self.pages = {
            "dashboard": self.dashboard_page,
            "history": self.history_page,
            "insights": self.insights_page,
            "settings": self.settings_page,
            "privacy": self.privacy_page,
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.settings_page.load_from_settings(self.settings.get_all())

        self.dashboard_page.pause_toggled.connect(self._toggle_pause)
        self.dashboard_page.take_break_clicked.connect(self._take_break)
        self.dashboard_page.end_break_btn.clicked.connect(self._end_break)
        self.history_page.range_changed.connect(self._on_history_range_changed)
        self.settings_page.settings_changed.connect(self._on_settings_changed)
        self.settings_page.recalibrate_requested.connect(self._run_recalibration)
        self.settings_page.camera_test_requested.connect(self._run_camera_test)

        self._switch_page("dashboard")

    def _switch_page(self, key):
        for k, btn in self.nav_buttons.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.setChecked(k == key)
        self.stack.setCurrentWidget(self.pages[key])
        if key in ("history", "insights"):
            self._checkpoint_session()
        if key == "history":
            self._refresh_history()
        if key == "insights":
            self._refresh_insights()

    # ------------------------------------------------------------- onboarding
    def _run_onboarding(self):
        wizard = OnboardingWizard(camera_index=self.settings.get("camera_index", 0), parent=self)
        wizard.exec()
        if wizard.result_baseline_ear is not None:
            self.settings.update({
                "baseline_ear": wizard.result_baseline_ear,
                "calibrated": True,
            })

    def _run_recalibration(self):
        wizard = OnboardingWizard(camera_index=self.settings.get("camera_index", 0), parent=self)
        wizard.stack.setCurrentIndex(3)  # jump straight to calibration page
        wizard.exec()
        if wizard.result_baseline_ear is not None:
            self.settings.update({"baseline_ear": wizard.result_baseline_ear, "calibrated": True})
            if self.worker:
                self.worker.apply_live_settings()

    def _run_camera_test(self):
        wizard = OnboardingWizard(camera_index=self.settings.get("camera_index", 0), parent=self)
        wizard.stack.setCurrentIndex(2)  # jump straight to camera test page
        wizard.exec()

    # ------------------------------------------------------------- worker
    def _start_worker(self):
        self.worker = VisionWorker(self.settings)
        self.worker.stats_updated.connect(self._on_stats_updated)
        self.worker.camera_status_changed.connect(self.dashboard_page.camera_status.set_status)
        self.worker.camera_error.connect(self._on_camera_error)
        self.worker.blink_reminder_needed.connect(self.notifications.notify_blink_reminder)
        self.worker.low_blink_reminder_needed.connect(self._on_low_blink_period)
        self.worker.break_due.connect(self._on_break_due)
        self.worker.minute_aggregate_ready.connect(self._on_minute_aggregate)
        self.worker.start()

    def _on_stats_updated(self, stats: dict):
        self.dashboard_page.update_stats(stats)

    def _on_camera_error(self, message: str):
        self.notifications.notify_system(f"Camera issue: {message}")

    def _on_low_blink_period(self):
        self.notifications.notify_low_blink_rate()
        # Persist the closed low-blink period as a numeric event.
        now = None
        from datetime import datetime
        self.db.record_low_blink_event(
            self.session_id, datetime.now() - timedelta(seconds=30), datetime.now(), 0.0
        )

    def _on_break_due(self, minutes: int):
        self.notifications.notify_break_reminder(minutes)

    def _on_minute_aggregate(self, ts, blink_count, avg_ear):
        self.db.record_blink_minute(self.session_id, ts, blink_count, avg_ear)

    def _refresh_dashboard_chart(self):
        rows = self.db.today_blink_minutes()
        self.dashboard_page.update_chart(rows)

    def _checkpoint_session(self):
        if not getattr(self, "worker", None):
            return
        self.db.checkpoint_session(
            self.session_id,
            screen_time_s=int(self.worker.screen_tracker.screen_time_seconds),
            active_time_s=int(self.worker.screen_tracker.active_time_seconds),
            break_time_s=int(self.worker.screen_tracker.break_time_seconds),
            total_blinks=self.worker.stats.total_blinks,
            longest_no_blink_s=int(self.worker.stats.longest_no_blink_seconds),
            breaks_taken=self.worker.break_manager.breaks_taken,
            low_blink_periods=self.worker.stats.low_blink_period_count,
        )
        if self.stack.currentWidget() is self.history_page:
            self._refresh_history()

    # ------------------------------------------------------------- controls
    def _toggle_pause(self):
        if self.worker.is_paused:
            self.worker.resume()
        else:
            self.worker.pause()
        self.dashboard_page.set_paused_ui(self.worker.is_paused)
        self.tray.set_paused_state(self.worker.is_paused)

    def _take_break(self):
        self.worker.take_break_now()

    def _end_break(self):
        self.worker.end_break_now()

    # ------------------------------------------------------------- settings
    def _on_settings_changed(self, values: dict):
        old_theme = self.settings.get("theme")
        self.settings.update(values)
        if self.worker:
            self.worker.apply_live_settings()
            if values.get("camera_index") is not None:
                self.worker.set_camera_index(values["camera_index"])
        self.notifications.sound_enabled = values.get("notification_sound", True)
        self.notifications.enabled = values.get("notifications_enabled", True)
        if values.get("theme") != old_theme:
            apply_theme(self.app, values.get("theme", "system"))

    # ------------------------------------------------------------- history/insights
    def _on_history_range_changed(self, key: str):
        self._history_range = key
        self._refresh_history()

    def _refresh_history(self):
        key = self._history_range
        if key == "today":
            summary = self.db.get_daily_stats(date.today())
            series = self.db.get_daily_series(1)
        elif key == "yesterday":
            summary = self.db.get_daily_stats(date.today() - timedelta(days=1))
            series = self.db.get_daily_series(2)
        elif key == "7d":
            summary = self.db.get_range_summary(7)
            series = self.db.get_daily_series(7)
        else:
            summary = self.db.get_range_summary(30)
            series = self.db.get_daily_series(30)
        self.history_page.update_summary(summary)
        self.history_page.update_charts(series)

    def _refresh_insights(self):
        series = self.db.get_daily_series(30)
        self.insights_page.set_insights(series)

    # ------------------------------------------------------------- tray wiring
    def _wire_tray(self):
        self.tray.open_requested.connect(self._show_from_tray)
        self.tray.pause_requested.connect(lambda: self._toggle_pause() if not self.worker.is_paused else None)
        self.tray.resume_requested.connect(lambda: self._toggle_pause() if self.worker.is_paused else None)
        self.tray.break_requested.connect(self._take_break)
        self.tray.settings_requested.connect(lambda: (self._show_from_tray(), self._switch_page("settings")))
        self.tray.exit_requested.connect(self._quit_app)

    def _show_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def _quit_app(self):
        self._shutdown()
        self.app.quit()

    # ------------------------------------------------------------- shutdown
    def _shutdown(self):
        if getattr(self, "_shutdown_done", False):
            return
        self._shutdown_done = True
        if getattr(self, "worker", None):
            self.worker.stop()
            self.worker.wait(2000)
            self.db.end_session(
                self.session_id,
                screen_time_s=int(self.worker.screen_tracker.screen_time_seconds),
                active_time_s=int(self.worker.screen_tracker.active_time_seconds),
                break_time_s=int(self.worker.screen_tracker.break_time_seconds),
                total_blinks=self.worker.stats.total_blinks,
                longest_no_blink_s=int(self.worker.stats.longest_no_blink_seconds),
                breaks_taken=self.worker.break_manager.breaks_taken,
                low_blink_periods=self.worker.stats.low_blink_period_count,
            )
        self.db.close()

    def closeEvent(self, event: QCloseEvent):
        # Minimize to tray instead of quitting, so monitoring keeps running.
        if self.tray.tray_icon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
            self.notifications.notify_system("BlinkGuard is still running in the system tray.")
        else:
            self._shutdown()
            event.accept()

    def resizeEvent(self, event):
        # Maximizing/restoring the window can leave some QLabels with a
        # stale partial text render on Windows until the next repaint.
        # Force every label to redraw shortly after any resize so this
        # never lingers on screen.
        super().resizeEvent(event)
        QTimer.singleShot(50, self._force_label_repaint)

    def _force_label_repaint(self):
        from PySide6.QtWidgets import QLabel
        for label in self.findChildren(QLabel):
            label.update()
