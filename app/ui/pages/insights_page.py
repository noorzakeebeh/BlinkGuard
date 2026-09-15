from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class InsightsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        title = QLabel("Insights")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        subtitle = QLabel("Patterns from your locally stored activity \u2014 no data leaves your device.")
        subtitle.setObjectName("StatLabel")
        root.addWidget(subtitle)

        self.insights_container = QVBoxLayout()
        root.addLayout(self.insights_container)
        root.addStretch()

    def _card(self, text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        return card

    def clear(self):
        while self.insights_container.count():
            item = self.insights_container.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def set_insights(self, daily_series: list):
        """Generate plain-language insights purely from local aggregated
        numbers -- no external AI call is used or needed for this."""
        self.clear()
        days_with_data = [d for d in daily_series if d.get("screen_time_seconds", 0) > 0]

        if not days_with_data:
            self.insights_container.addWidget(
                self._card("Not enough data yet. Use BlinkGuard for a few days to see insights here.")
            )
            return

        longest_session_day = max(days_with_data, key=lambda d: d["screen_time_seconds"])
        self.insights_container.addWidget(self._card(
            f"Your longest screen time was on {self._weekday(longest_session_day['date'])} "
            f"({self._fmt_hm(longest_session_day['screen_time_seconds'])})."
        ))

        # correlation-ish observation: compare blink rate on longer vs shorter days
        if len(days_with_data) >= 3:
            sorted_by_time = sorted(days_with_data, key=lambda d: d["screen_time_seconds"])
            lower_half = sorted_by_time[: len(sorted_by_time) // 2]
            upper_half = sorted_by_time[len(sorted_by_time) // 2:]
            avg_rate_low = sum(d["avg_blink_rate"] for d in lower_half) / max(1, len(lower_half))
            avg_rate_high = sum(d["avg_blink_rate"] for d in upper_half) / max(1, len(upper_half))
            if avg_rate_high < avg_rate_low - 0.5:
                self.insights_container.addWidget(self._card(
                    "Your blink rate tends to be lower on days with longer screen sessions. "
                    "Consider more frequent short breaks on heavy screen days."
                ))
            elif avg_rate_high > avg_rate_low + 0.5:
                self.insights_container.addWidget(self._card(
                    "Your blink rate has actually held up well even on longer screen days \u2014 nice consistency."
                ))

        today = daily_series[-1] if daily_series else None
        if today and today.get("breaks_taken", 0) > 0:
            self.insights_container.addWidget(self._card(
                f"You took {today['breaks_taken']} break(s) today."
            ))

        total_low_periods = sum(d.get("low_blink_periods", 0) for d in days_with_data)
        if total_low_periods > 0:
            self.insights_container.addWidget(self._card(
                f"You had {total_low_periods} low-blink period(s) across the selected range. "
                "Try to take a moment to consciously blink during focused, screen-heavy tasks."
            ))

        avg_rate_overall = sum(d["avg_blink_rate"] for d in days_with_data) / len(days_with_data)
        self.insights_container.addWidget(self._card(
            f"Your average blink rate over this period was {avg_rate_overall:.1f} blinks/min."
        ))

    @staticmethod
    def _weekday(date_str: str) -> str:
        from datetime import date as _date
        y, m, d = map(int, date_str.split("-"))
        return _date(y, m, d).strftime("%A")

    @staticmethod
    def _fmt_hm(seconds: float) -> str:
        seconds = int(seconds)
        h, rem = divmod(seconds, 3600)
        m, _ = divmod(rem, 60)
        return f"{h}h {m}m" if h else f"{m}m"
