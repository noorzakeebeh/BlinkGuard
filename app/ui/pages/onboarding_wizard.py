from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QWidget, QProgressBar
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from app.core.privacy_manager import PrivacyManager
from app.workers.calibration_worker import CalibrationWorker

CALIBRATION_SECONDS = 8


class OnboardingWizard(QDialog):
    """First-launch flow: Welcome -> Privacy -> Camera test -> Calibration -> Done.
    Returns the calibrated baseline EAR via self.result_baseline_ear after exec()."""

    def __init__(self, camera_index: int = 0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to BlinkGuard")
        self.setMinimumSize(560, 460)
        self.camera_index = camera_index
        self.result_baseline_ear = None
        self._ear_samples = []
        self._calib_worker = None

        root = QVBoxLayout(self)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, stretch=1)

        nav = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.back_btn.setObjectName("Secondary")
        self.back_btn.clicked.connect(self._go_back)
        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("Primary")
        self.next_btn.clicked.connect(self._go_next)
        nav.addWidget(self.back_btn)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        root.addLayout(nav)

        self.stack.addWidget(self._build_welcome_page())
        self.stack.addWidget(self._build_privacy_page())
        self.stack.addWidget(self._build_camera_page())
        self.stack.addWidget(self._build_calibration_page())
        self.stack.addWidget(self._build_done_page())

        self.stack.currentChanged.connect(self._on_page_changed)
        self._on_page_changed(0)

    # ------------------------------------------------------------- pages
    def _page_wrap(self, title, body_widget):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        t = QLabel(title)
        t.setObjectName("PageTitle")
        layout.addWidget(t)
        layout.addWidget(body_widget, stretch=1)
        return w

    def _build_welcome_page(self):
        body = QLabel(
            "BlinkGuard helps you build healthier screen habits by watching your "
            "blinking behavior in real time and gently nudging you when you go too "
            "long without blinking or take too long without a break.\n\n"
            "Everything runs locally on your computer \u2014 nothing is uploaded."
        )
        body.setWordWrap(True)
        return self._page_wrap("Welcome", body)

    def _build_privacy_page(self):
        body = QLabel(PrivacyManager.get_privacy_statement())
        body.setWordWrap(True)
        return self._page_wrap("Your Privacy", body)

    def _build_camera_page(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        self.camera_preview_label = QLabel("Click \"Start Camera Test\" below.")
        self.camera_preview_label.setMinimumHeight(240)
        self.camera_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_preview_label.setStyleSheet("background:#00000010; border-radius: 10px;")
        layout.addWidget(self.camera_preview_label)

        self.camera_status_label = QLabel("Camera not started yet.")
        layout.addWidget(self.camera_status_label)

        test_btn = QPushButton("Start Camera Test")
        test_btn.setObjectName("Secondary")
        test_btn.clicked.connect(self._start_camera_test)
        layout.addWidget(test_btn)
        return self._page_wrap("Camera Permission & Test", container)

    def _build_calibration_page(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        instructions = QLabel(
            "1. Sit normally in front of the camera.\n"
            "2. Look at the screen.\n"
            "3. Blink naturally for a few seconds while we measure your baseline."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.calib_progress = QProgressBar()
        self.calib_progress.setRange(0, CALIBRATION_SECONDS)
        layout.addWidget(self.calib_progress)

        self.calib_status_label = QLabel("Not started")
        layout.addWidget(self.calib_status_label)

        start_btn = QPushButton("Start Calibration")
        start_btn.setObjectName("Primary")
        start_btn.clicked.connect(self._start_calibration)
        layout.addWidget(start_btn)
        return self._page_wrap("Calibration", container)

    def _build_done_page(self):
        body = QLabel(
            "You're all set! BlinkGuard will now start monitoring your blinking "
            "in the background. You can adjust everything later in Settings."
        )
        body.setWordWrap(True)
        return self._page_wrap("All Set", body)

    # ------------------------------------------------------------- nav logic
    def _on_page_changed(self, index):
        self.back_btn.setEnabled(index > 0)
        is_last = index == self.stack.count() - 1
        self.next_btn.setText("Finish" if is_last else "Next")
        # Require calibration completion before allowing "Next" off that page
        if index == 3:
            self.next_btn.setEnabled(self.result_baseline_ear is not None)
        else:
            self.next_btn.setEnabled(True)

    def _go_next(self):
        if self.stack.currentIndex() == self.stack.count() - 1:
            self._cleanup_worker()
            self.accept()
            return
        self.stack.setCurrentIndex(self.stack.currentIndex() + 1)

    def _go_back(self):
        self._cleanup_worker()
        self.stack.setCurrentIndex(max(0, self.stack.currentIndex() - 1))

    def _cleanup_worker(self):
        if self._calib_worker is not None:
            self._calib_worker.stop()
            self._calib_worker.wait(1000)
            self._calib_worker = None

    # ------------------------------------------------------------- camera test
    def _start_camera_test(self):
        self._cleanup_worker()
        self.camera_status_label.setText("Starting camera...")
        self._calib_worker = CalibrationWorker(self.camera_index, emit_preview=True)
        self._calib_worker.frame_ready.connect(self._on_preview_frame)
        self._calib_worker.face_status.connect(
            lambda ok: self.camera_status_label.setText(
                "Face detected \u2713" if ok else "No face detected \u2014 adjust lighting/position"
            )
        )
        self._calib_worker.error.connect(
            lambda msg: self.camera_status_label.setText(f"Camera error: {msg}")
        )
        self._calib_worker.start()

    def _on_preview_frame(self, qimg):
        pix = QPixmap.fromImage(qimg).scaled(
            self.camera_preview_label.width(), self.camera_preview_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.camera_preview_label.setPixmap(pix)

    # ------------------------------------------------------------- calibration
    def _start_calibration(self):
        self._cleanup_worker()
        self._ear_samples = []
        self.calib_progress.setValue(0)
        self.calib_status_label.setText("Blink naturally...")

        self._calib_worker = CalibrationWorker(self.camera_index, emit_preview=False)
        self._calib_worker.ear_sample.connect(self._on_ear_sample)
        self._calib_worker.error.connect(
            lambda msg: self.calib_status_label.setText(f"Camera error: {msg}")
        )
        self._calib_worker.start()

        from PySide6.QtCore import QTimer
        self._calib_elapsed = 0
        self._calib_timer = QTimer(self)
        self._calib_timer.timeout.connect(self._tick_calibration)
        self._calib_timer.start(1000)

    def _tick_calibration(self):
        self._calib_elapsed += 1
        self.calib_progress.setValue(self._calib_elapsed)
        if self._calib_elapsed >= CALIBRATION_SECONDS:
            self._calib_timer.stop()
            self._finish_calibration()

    def _on_ear_sample(self, ear: float):
        self._ear_samples.append(ear)

    def _finish_calibration(self):
        self._cleanup_worker()
        if self._ear_samples:
            # Use a high percentile rather than the max to reduce sensitivity
            # to a single lucky wide-open-eye frame.
            samples_sorted = sorted(self._ear_samples)
            idx = int(len(samples_sorted) * 0.9)
            baseline = samples_sorted[min(idx, len(samples_sorted) - 1)]
            self.result_baseline_ear = round(float(baseline), 4)
            self.calib_status_label.setText(f"Calibration complete. Baseline EAR: {self.result_baseline_ear}")
        else:
            self.result_baseline_ear = 0.30  # sensible fallback default
            self.calib_status_label.setText(
                "No face detected during calibration \u2014 using default sensitivity. "
                "You can re-run calibration anytime from Settings."
            )
        self._on_page_changed(self.stack.currentIndex())

    def closeEvent(self, event):
        self._cleanup_worker()
        super().closeEvent(event)
