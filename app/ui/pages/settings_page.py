from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QCheckBox, QSlider,
    QSpinBox, QComboBox, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, Signal


class SettingsPage(QWidget):
    settings_changed = Signal(dict)
    recalibrate_requested = Signal()
    camera_test_requested = Signal()

    def __init__(self, camera_options=None, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        # ---- Blink monitoring section ----
        root.addWidget(self._section_label("Blink Monitoring"))
        card = self._card()
        root.addWidget(card)
        layout = QVBoxLayout(card)

        self.monitoring_enabled_cb = QCheckBox("Enable blink monitoring")
        layout.addWidget(self.monitoring_enabled_cb)

        layout.addWidget(QLabel("Blink sensitivity"))
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(30, 100)
        layout.addWidget(self.sensitivity_slider)

        row = QHBoxLayout()
        row.addWidget(QLabel("Low-blink threshold (blinks/min)"))
        self.low_threshold_spin = QSpinBox()
        self.low_threshold_spin.setRange(1, 30)
        row.addWidget(self.low_threshold_spin)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Minimum time before a blink reminder (sec)"))
        self.no_blink_spin = QSpinBox()
        self.no_blink_spin.setRange(3, 120)
        row2.addWidget(self.no_blink_spin)
        layout.addLayout(row2)

        recal_row = QHBoxLayout()
        recal_btn = QPushButton("Re-run calibration")
        recal_btn.setObjectName("Secondary")
        recal_btn.clicked.connect(self.recalibrate_requested.emit)
        recal_row.addWidget(recal_btn)
        recal_row.addStretch()
        layout.addLayout(recal_row)

        # ---- Breaks section ----
        root.addWidget(self._section_label("Breaks"))
        card2 = self._card()
        root.addWidget(card2)
        layout2 = QVBoxLayout(card2)
        self.breaks_enabled_cb = QCheckBox("Enable break reminders")
        layout2.addWidget(self.breaks_enabled_cb)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Break interval (minutes)"))
        self.break_interval_spin = QSpinBox()
        self.break_interval_spin.setRange(5, 180)
        row3.addWidget(self.break_interval_spin)
        layout2.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Break duration (minutes)"))
        self.break_duration_spin = QSpinBox()
        self.break_duration_spin.setRange(1, 60)
        row4.addWidget(self.break_duration_spin)
        layout2.addLayout(row4)

        # ---- Notifications section ----
        root.addWidget(self._section_label("Notifications"))
        card3 = self._card()
        root.addWidget(card3)
        layout3 = QVBoxLayout(card3)
        self.notifications_enabled_cb = QCheckBox("Enable notifications")
        layout3.addWidget(self.notifications_enabled_cb)
        self.notification_sound_cb = QCheckBox("Enable notification sound")
        layout3.addWidget(self.notification_sound_cb)

        # ---- Camera section ----
        root.addWidget(self._section_label("Camera"))
        card4 = self._card()
        root.addWidget(card4)
        layout4 = QVBoxLayout(card4)
        row5 = QHBoxLayout()
        row5.addWidget(QLabel("Camera"))
        self.camera_combo = QComboBox()
        for idx in (camera_options or [0]):
            self.camera_combo.addItem(f"Camera {idx}", idx)
        row5.addWidget(self.camera_combo)
        row5.addStretch()
        test_btn = QPushButton("Test Camera")
        test_btn.setObjectName("Secondary")
        test_btn.clicked.connect(self.camera_test_requested.emit)
        row5.addWidget(test_btn)
        layout4.addLayout(row5)

        # ---- Appearance section ----
        root.addWidget(self._section_label("Appearance"))
        card5 = self._card()
        root.addWidget(card5)
        layout5 = QHBoxLayout(card5)
        layout5.addWidget(QLabel("Theme"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        layout5.addWidget(self.theme_combo)
        layout5.addStretch()

        # ---- Startup section ----
        root.addWidget(self._section_label("Startup"))
        card6 = self._card()
        root.addWidget(card6)
        layout6 = QVBoxLayout(card6)
        self.start_with_computer_cb = QCheckBox("Start BlinkGuard when my computer starts")
        layout6.addWidget(self.start_with_computer_cb)

        save_row = QHBoxLayout()
        save_row.addStretch()
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self._emit_changes)
        save_row.addWidget(save_btn)
        root.addLayout(save_row)
        root.addStretch()

    def _section_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-weight: 700; font-size: 13px; margin-top: 6px;")
        return label

    def _card(self):
        frame = QFrame()
        frame.setObjectName("Card")
        return frame

    def load_from_settings(self, settings: dict):
        self.monitoring_enabled_cb.setChecked(settings.get("monitoring_enabled", True))
        self.sensitivity_slider.setValue(int(settings.get("blink_sensitivity", 0.75) * 100))
        self.low_threshold_spin.setValue(int(settings.get("low_blink_rate_threshold", 8)))
        self.no_blink_spin.setValue(int(settings.get("no_blink_reminder_seconds", 12)))

        self.breaks_enabled_cb.setChecked(settings.get("breaks_enabled", True))
        self.break_interval_spin.setValue(int(settings.get("break_interval_minutes", 20)))
        self.break_duration_spin.setValue(int(settings.get("break_duration_minutes", 5)))

        self.notifications_enabled_cb.setChecked(settings.get("notifications_enabled", True))
        self.notification_sound_cb.setChecked(settings.get("notification_sound", True))

        cam_idx = self.camera_combo.findData(settings.get("camera_index", 0))
        if cam_idx >= 0:
            self.camera_combo.setCurrentIndex(cam_idx)

        theme = settings.get("theme", "system")
        self.theme_combo.setCurrentText(theme.capitalize())

        self.start_with_computer_cb.setChecked(settings.get("start_with_computer", False))

    def _emit_changes(self):
        self.settings_changed.emit({
            "monitoring_enabled": self.monitoring_enabled_cb.isChecked(),
            "blink_sensitivity": self.sensitivity_slider.value() / 100.0,
            "low_blink_rate_threshold": self.low_threshold_spin.value(),
            "no_blink_reminder_seconds": self.no_blink_spin.value(),
            "breaks_enabled": self.breaks_enabled_cb.isChecked(),
            "break_interval_minutes": self.break_interval_spin.value(),
            "break_duration_minutes": self.break_duration_spin.value(),
            "notifications_enabled": self.notifications_enabled_cb.isChecked(),
            "notification_sound": self.notification_sound_cb.isChecked(),
            "camera_index": self.camera_combo.currentData(),
            "theme": self.theme_combo.currentText().lower(),
            "start_with_computer": self.start_with_computer_cb.isChecked(),
        })
