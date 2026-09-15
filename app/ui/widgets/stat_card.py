from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt


class StatCard(QFrame):
    def __init__(self, icon: str, label: str, value: str = "--", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(
            "font-size: 20px; font-family: 'Segoe UI Emoji', 'Noto Color Emoji', "
            "'Apple Color Emoji', sans-serif;"
        )
        top.addWidget(icon_label)
        top.addStretch()
        layout.addLayout(top)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        font = self.value_label.font()
        font.setStyleStrategy(font.StyleStrategy.PreferAntialias | font.StyleStrategy.PreferQuality)
        self.value_label.setFont(font)
        layout.addWidget(self.value_label)

        self.caption_label = QLabel(label)
        self.caption_label.setObjectName("StatLabel")
        layout.addWidget(self.caption_label)

    def set_value(self, value: str):
        self.value_label.setText(value)

    def set_alert(self, is_alert: bool):
        color = "#D64545" if is_alert else None
        if color:
            self.value_label.setStyleSheet(f"color: {color};")
        else:
            self.value_label.setStyleSheet("")
