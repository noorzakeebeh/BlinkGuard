from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout, QFrame
)
from PySide6.QtCore import Signal

from app.ui.widgets.stat_card import StatCard
from app.ui.widgets.chart_widget import SimpleChart
from app.core.screen_time_tracker import ScreenTimeTracker

RANGE_OPTIONS = [("Today", 1), ("Yesterday", 1), ("Last 7 days", 7), ("Last 30 days", 30)]


class HistoryPage(QWidget):
    range_changed = Signal(str)  # emits the range key: "today"|"yesterday"|"7d"|"30d"

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        title = QLabel("History")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        tabs = QHBoxLayout()
        self.tab_buttons = {}
        for label, key in [("Today", "today"), ("Yesterday", "yesterday"),
                            ("Last 7 days", "7d"), ("Last 30 days", "30d")]:
            btn = QPushButton(label)
            btn.setObjectName("Secondary")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, k=key: self._on_tab_clicked(k))
            tabs.addWidget(btn)
            self.tab_buttons[key] = btn
        tabs.addStretch()
        root.addLayout(tabs)
        self.tab_buttons["today"].setChecked(True)

        grid = QGridLayout()
        grid.setSpacing(14)
        self.card_avg_rate = StatCard("\U0001F441\ufe0f", "Average blink rate")
        self.card_total_blinks = StatCard("\U0001F522", "Total blinks")
        self.card_longest_gap = StatCard("\u23F1\ufe0f", "Longest period without blinking")
        self.card_screen_time = StatCard("\U0001F5A5\ufe0f", "Screen time")
        self.card_breaks = StatCard("\u2615", "Breaks taken")
        self.card_low_periods = StatCard("\u26A0\ufe0f", "Low-blink periods")
        grid.addWidget(self.card_avg_rate, 0, 0)
        grid.addWidget(self.card_total_blinks, 0, 1)
        grid.addWidget(self.card_longest_gap, 0, 2)
        grid.addWidget(self.card_screen_time, 1, 0)
        grid.addWidget(self.card_breaks, 1, 1)
        grid.addWidget(self.card_low_periods, 1, 2)
        root.addLayout(grid)

        charts_row = QHBoxLayout()
        self.screen_time_chart_card, self.screen_time_chart = self._make_chart_card(
            "Screen time by day", "bar", "#1A56DB")
        self.breaks_chart_card, self.breaks_chart = self._make_chart_card(
            "Break frequency", "bar", "#2E9E5B")
        charts_row.addWidget(self.screen_time_chart_card)
        charts_row.addWidget(self.breaks_chart_card)
        root.addLayout(charts_row)

        charts_row2 = QHBoxLayout()
        self.low_blink_chart_card, self.low_blink_chart = self._make_chart_card(
            "Low-blink periods", "bar", "#D64545")
        self.blink_rate_chart_card, self.blink_rate_chart = self._make_chart_card(
            "Average blink rate", "line", "#7B3FE4")
        charts_row2.addWidget(self.low_blink_chart_card)
        charts_row2.addWidget(self.blink_rate_chart_card)
        root.addLayout(charts_row2)

    def _make_chart_card(self, title, kind, color):
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        label = QLabel(title)
        label.setStyleSheet("font-weight: 600;")
        layout.addWidget(label)
        chart = SimpleChart(kind=kind, accent=color)
        layout.addWidget(chart)
        return card, chart

    def _on_tab_clicked(self, key):
        for k, btn in self.tab_buttons.items():
            btn.setChecked(k == key)
        self.range_changed.emit(key)

    def update_summary(self, summary: dict):
        self.card_avg_rate.set_value(f"{summary.get('avg_blink_rate', 0):.1f}")
        self.card_total_blinks.set_value(str(summary.get("total_blinks", 0)))
        self.card_longest_gap.set_value(f"{summary.get('longest_no_blink_seconds', 0):.0f} sec")
        self.card_screen_time.set_value(ScreenTimeTracker.format_hms(summary.get("screen_time_seconds", 0)))
        self.card_breaks.set_value(str(summary.get("breaks_taken", 0)))
        self.card_low_periods.set_value(str(summary.get("low_blink_periods", 0)))

    def update_charts(self, daily_series: list):
        labels = [d["date"][5:] for d in daily_series]
        self.screen_time_chart.set_data(labels, [d["screen_time_seconds"] / 60.0 for d in daily_series])
        self.breaks_chart.set_data(labels, [d["breaks_taken"] for d in daily_series])
        self.low_blink_chart.set_data(labels, [d["low_blink_periods"] for d in daily_series])
        self.blink_rate_chart.set_data(labels, [d["avg_blink_rate"] for d in daily_series])
