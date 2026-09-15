from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

STATUS_MAP = {
    "active": ("\U0001F7E2", "Camera active"),
    "face_not_detected": ("\U0001F7E1", "Face not detected"),
    "unavailable": ("\U0001F534", "Camera unavailable"),
    "paused": ("\u26AA", "Monitoring paused"),
    "multiple_faces": ("\U0001F7E1", "Multiple faces detected"),
}


class CameraStatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.icon_label = QLabel("\u26AA")
        self.icon_label.setStyleSheet(
            "font-family: 'Segoe UI Emoji', 'Noto Color Emoji', 'Apple Color Emoji', sans-serif;"
        )
        self.text_label = QLabel("Monitoring paused")
        self.text_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch()

    def set_status(self, status: str):
        icon, text = STATUS_MAP.get(status, ("\u26AA", "Unknown"))
        self.icon_label.setText(icon)
        self.text_label.setText(text)
