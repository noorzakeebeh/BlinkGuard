from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal

from app.ui.widgets.stat_card import StatCard
from app.ui.widgets.chart_widget import SimpleChart
from app.ui.widgets.camera_status_widget import CameraStatusWidget
from app.core.screen_time_tracker import ScreenTimeTracker


class DashboardPage(QWidget):
    pause_toggled = Signal()
    take_break_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("Today's Eye Activity")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch()

        self.camera_status = CameraStatusWidget()
        header.addWidget(self.camera_status)
        root.addLayout(header)

        controls = QHBoxLayout()
        self.monitoring_label = QLabel("Monitoring: ON")
        self.monitoring_label.setStyleSheet("font-weight: 600;")
        controls.addWidget(self.monitoring_label)
        controls.addStretch()

        self.pause_btn = QPushButton("Pause Monitoring")
        self.pause_btn.setObjectName("Secondary")
        self.pause_btn.clicked.connect(self.pause_toggled.emit)
        controls.addWidget(self.pause_btn)

        self.break_btn = QPushButton("Take a Break")
        self.break_btn.setObjectName("Primary")
        self.break_btn.clicked.connect(self.take_break_clicked.emit)
        controls.addWidget(self.break_btn)
        root.addLayout(controls)

        # --- stat cards grid ------------------------------------------------
        grid = QGridLayout()
        grid.setSpacing(14)
        self.card_blink_rate = StatCard("\U0001F441\ufe0f", "Blinks per minute")
        self.card_longest_gap = StatCard("\u23F1\ufe0f", "Longest time without blinking")
        self.card_screen_time = StatCard("\U0001F5A5\ufe0f", "Screen time today")
        self.card_breaks = StatCard("\u2615", "Breaks taken")
        self.card_low_periods = StatCard("\u26A0\ufe0f", "Low-blink periods")
        self.card_session = StatCard("\u23F3", "Current session")

        grid.addWidget(self.card_blink_rate, 0, 0)
        grid.addWidget(self.card_longest_gap, 0, 1)
        grid.addWidget(self.card_screen_time, 0, 2)
        grid.addWidget(self.card_breaks, 1, 0)
        grid.addWidget(self.card_low_periods, 1, 1)
        grid.addWidget(self.card_session, 1, 2)
        root.addLayout(grid)

        # --- chart ------------------------------------------------------
        chart_card = QFrame()
        chart_card.setObjectName("Card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(18, 16, 18, 16)
        chart_title = QLabel("Blink rate throughout the day")
        chart_title.setStyleSheet("font-weight: 600;")
        chart_layout.addWidget(chart_title)
        self.blink_chart = SimpleChart(kind="line")
        chart_layout.addWidget(self.blink_chart)
        root.addWidget(chart_card, stretch=1)

        # --- break banner (hidden unless on break) ------------------------
        self.break_banner = QFrame()
        self.break_banner.setObjectName("Card")
        self.break_banner.setVisible(False)
        banner_layout = QHBoxLayout(self.break_banner)
        self.break_banner_label = QLabel("On a break")
        banner_layout.addWidget(self.break_banner_label)
        banner_layout.addStretch()
        self.end_break_btn = QPushButton("End Break")
        self.end_break_btn.setObjectName("Secondary")
        banner_layout.addWidget(self.end_break_btn)
        root.addWidget(self.break_banner)

    def set_paused_ui(self, paused: bool):
        self.monitoring_label.setText("Monitoring: PAUSED" if paused else "Monitoring: ON")
        self.pause_btn.setText("Resume Monitoring" if paused else "Pause Monitoring")

    def update_stats(self, stats: dict):
        self.card_blink_rate.set_value(f"{stats['blink_rate']:.0f}")
        self.card_blink_rate.set_alert(stats.get("is_currently_low", False))

        self.card_longest_gap.set_value(
            f"{stats['longest_no_blink']:.0f} sec"
        )
        self.card_screen_time.set_value(ScreenTimeTracker.format_hms(stats["screen_time"]))
        self.card_breaks.set_value(str(stats["breaks_taken"]))
        self.card_low_periods.set_value(str(stats["low_blink_periods"]))
        self.card_low_periods.set_alert(stats["low_blink_periods"] > 0)
        self.card_session.set_value(ScreenTimeTracker.format_hms(stats["active_time"]))

        on_break = stats.get("on_break", False)
        self.break_banner.setVisible(on_break)
        if on_break:
            remaining = int(stats.get("break_remaining_seconds", 0))
            self.break_banner_label.setText(f"\u2615 On a break \u2014 {remaining}s remaining")

    def update_chart(self, minute_rows: list):
        labels = [r["minute_timestamp"][11:16] for r in minute_rows][-30:]
        values = [r["blink_count"] for r in minute_rows][-30:]
        self.blink_chart.set_data(labels, values)
