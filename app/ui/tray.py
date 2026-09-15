from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, Signal, QObject


def _make_icon() -> QIcon:
    """Simple generated eye-like icon so the app doesn't need an external
    asset file to run."""
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#1A56DB"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 16, 56, 32)
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawEllipse(24, 24, 16, 16)
    painter.end()
    return QIcon(pix)


class TrayController(QObject):
    open_requested = Signal()
    pause_requested = Signal()
    resume_requested = Signal()
    break_requested = Signal()
    settings_requested = Signal()
    exit_requested = Signal()

    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self.tray_icon = QSystemTrayIcon(_make_icon(), app)
        self.tray_icon.setToolTip("BlinkGuard")

        self.menu = QMenu()
        self.open_action = self.menu.addAction("Open BlinkGuard")
        self.open_action.triggered.connect(self.open_requested.emit)

        self.pause_action = self.menu.addAction("Pause Monitoring")
        self.pause_action.triggered.connect(self.pause_requested.emit)
        self.resume_action = self.menu.addAction("Resume Monitoring")
        self.resume_action.triggered.connect(self.resume_requested.emit)
        self.resume_action.setVisible(False)

        self.break_action = self.menu.addAction("Take a Break")
        self.break_action.triggered.connect(self.break_requested.emit)

        self.menu.addSeparator()
        self.settings_action = self.menu.addAction("Settings")
        self.settings_action.triggered.connect(self.settings_requested.emit)

        self.menu.addSeparator()
        self.exit_action = self.menu.addAction("Exit")
        self.exit_action.triggered.connect(self.exit_requested.emit)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_requested.emit()

    def show(self):
        if self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.show()

    def set_paused_state(self, paused: bool):
        self.pause_action.setVisible(not paused)
        self.resume_action.setVisible(paused)
