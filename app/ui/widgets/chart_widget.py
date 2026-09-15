"""
A minimal, dependency-free chart widget drawn with QPainter. Supports simple
bar and line charts, which is all BlinkGuard's dashboards/history need.
Avoids requiring the separate PySide6-QtCharts add-on package.
"""
from typing import List
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QRectF


class SimpleChart(QWidget):
    def __init__(self, kind: str = "bar", accent: str = "#1A56DB", parent=None):
        super().__init__(parent)
        self.kind = kind  # "bar" | "line"
        self.accent = QColor(accent)
        self.labels: List[str] = []
        self.values: List[float] = []
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, labels: List[str], values: List[float]):
        self.labels = labels
        self.values = values
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin_left, margin_bottom, margin_top, margin_right = 36, 26, 12, 12
        plot_w = max(1, w - margin_left - margin_right)
        plot_h = max(1, h - margin_top - margin_bottom)

        text_color = self.palette().text().color()
        grid_color = QColor(text_color)
        grid_color.setAlpha(40)

        max_val = max(self.values) if self.values else 1.0
        max_val = max_val if max_val > 0 else 1.0

        # gridlines + y labels
        painter.setPen(QPen(grid_color, 1))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        for i in range(4):
            frac = i / 3.0
            y = margin_top + plot_h * (1 - frac)
            painter.drawLine(margin_left, int(y), w - margin_right, int(y))
            painter.setPen(QPen(text_color, 1))
            painter.drawText(2, int(y) + 4, f"{max_val * frac:.0f}")
            painter.setPen(QPen(grid_color, 1))

        if not self.values:
            painter.setPen(QPen(text_color, 1))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data yet")
            painter.end()
            return

        n = len(self.values)

        if self.kind == "bar":
            slot_w = plot_w / n
            bar_w = slot_w * 0.55
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.accent)
            for i, v in enumerate(self.values):
                bar_h = (v / max_val) * plot_h
                x = margin_left + i * slot_w + (slot_w - bar_w) / 2
                y = margin_top + plot_h - bar_h
                painter.drawRoundedRect(QRectF(x, y, bar_w, bar_h), 4, 4)
        else:  # line
            pen = QPen(self.accent, 2.5)
            painter.setPen(pen)
            points = []
            for i, v in enumerate(self.values):
                x = margin_left + (i / max(1, n - 1)) * plot_w if n > 1 else margin_left + plot_w / 2
                y = margin_top + plot_h - (v / max_val) * plot_h
                points.append((x, y))
            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                                  int(points[i + 1][0]), int(points[i + 1][1]))
            painter.setBrush(self.accent)
            painter.setPen(Qt.PenStyle.NoPen)
            for x, y in points:
                painter.drawEllipse(QRectF(x - 3, y - 3, 6, 6))

        # x labels (skip some if crowded)
        painter.setPen(QPen(text_color, 1))
        step = max(1, n // 6)
        slot_w = plot_w / n
        for i, label in enumerate(self.labels):
            if i % step != 0 and i != n - 1:
                continue
            x = margin_left + i * slot_w + (slot_w / 2 if self.kind == "bar" else 0)
            painter.drawText(int(x - 15), h - 6, 30, 14, Qt.AlignmentFlag.AlignCenter, label)

        painter.end()
