"""
CalibrationWorker is a small, self-contained QThread used for two things
outside the main monitoring loop:
  1. Camera preview / "Test Camera" in Settings and onboarding
  2. Calibration: collecting a short sample of EAR values while the user
     blinks naturally, to establish a personal baseline "open eye" EAR.

Kept separate from VisionWorker so calibration/testing never has to fight
over ownership of the running monitoring session.
"""
import time
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from app.core.camera_handler import CameraHandler, CameraError
from app.core.eye_detector import EyeDetector


class CalibrationWorker(QThread):
    frame_ready = Signal(QImage)   # preview only, never persisted to disk
    ear_sample = Signal(float)
    face_status = Signal(bool)
    error = Signal(str)

    def __init__(self, camera_index: int = 0, emit_preview: bool = True):
        super().__init__()
        self.camera_index = camera_index
        self.emit_preview = emit_preview
        self._running = False

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        camera = CameraHandler(self.camera_index)
        detector = EyeDetector()
        try:
            camera.open()
        except CameraError as e:
            self.error.emit(str(e))
            return

        try:
            while self._running:
                try:
                    frame = camera.read_frame()
                except CameraError as e:
                    self.error.emit(str(e))
                    break

                result = detector.process(frame)
                self.face_status.emit(result.face_detected)
                if result.face_detected and result.ear is not None:
                    self.ear_sample.emit(result.ear)

                if self.emit_preview:
                    # Convert for on-screen preview ONLY; never written to disk.
                    rgb = frame[:, :, ::-1].copy()
                    h, w, ch = rgb.shape
                    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                    self.frame_ready.emit(qimg.copy())

                time.sleep(0.05)
        finally:
            camera.close()
            detector.close()
