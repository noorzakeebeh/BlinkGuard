"""
CameraHandler owns the OpenCV VideoCapture device.

Responsibilities:
- Open/close/reopen the camera safely
- Report clear error states (unavailable, disconnected, permission denied)
- Never persist frames to disk; frames only ever live in memory for the
  duration of a single processing step.
"""
import cv2
from app.config import FRAME_WIDTH, FRAME_HEIGHT


class CameraError(Exception):
    pass


class CameraHandler:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self._cap = None

    def list_available_cameras(self, max_probe: int = 4):
        """Best-effort probe of camera indices 0..max_probe-1."""
        found = []
        for i in range(max_probe):
            cap = cv2.VideoCapture(i)
            if cap is not None and cap.isOpened():
                found.append(i)
            if cap is not None:
                cap.release()
        return found or [0]

    def open(self):
        self.close()
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            cap.release()
            raise CameraError(
                f"Could not open camera index {self.camera_index}. "
                "It may be unavailable, in use by another app, or access was denied."
            )
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self._cap = cap

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def read_frame(self):
        """Returns a BGR numpy frame, or None if a frame couldn't be read.
        Raises CameraError if the device appears disconnected."""
        if not self.is_open():
            raise CameraError("Camera is not open.")
        ok, frame = self._cap.read()
        if not ok or frame is None:
            raise CameraError("Camera disconnected or stopped producing frames.")
        return frame

    def set_camera_index(self, index: int):
        self.camera_index = index

    def close(self):
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
