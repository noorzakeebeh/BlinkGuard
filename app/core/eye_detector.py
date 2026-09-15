"""
EyeDetector wraps MediaPipe Face Landmarker (Face Mesh) to extract eye
landmarks and compute the Eye Aspect Ratio (EAR) per frame.

EAR formula (per eye), using 6 landmarks p1..p6 ordered
[outer_corner, top1, top2, inner_corner, bottom2, bottom1]:

    EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)

A larger EAR means the eye is more open; EAR drops sharply during a blink.
Averaging both eyes reduces noise from asymmetric detection.

This module receives a frame, runs inference, and returns only numeric
results (EAR value, face count, bounding info). It does not retain or
persist the frame anywhere.
"""
from dataclasses import dataclass
from typing import Optional, List

import numpy as np
import cv2
import mediapipe as mp

from app.config import LEFT_EYE_IDX, RIGHT_EYE_IDX, FACE_MESH_MAX_FACES


@dataclass
class EyeFrameResult:
    face_detected: bool
    face_count: int
    ear: Optional[float]          # averaged EAR of the primary face, if detected
    left_ear: Optional[float]
    right_ear: Optional[float]
    face_box_area_ratio: Optional[float]  # relative size, used to pick "primary" face


class EyeDetector:
    def __init__(self):
        self._mp_face_mesh = mp.solutions.face_mesh
        self._face_mesh = self._mp_face_mesh.FaceMesh(
            max_num_faces=FACE_MESH_MAX_FACES,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    @staticmethod
    def _dist(a, b) -> float:
        return float(np.linalg.norm(np.array(a) - np.array(b)))

    def _ear_for_eye(self, landmarks, idx, w, h) -> float:
        pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in idx]
        p1, p2, p3, p4, p5, p6 = pts
        vertical = self._dist(p2, p6) + self._dist(p3, p5)
        horizontal = self._dist(p1, p4)
        if horizontal <= 1e-6:
            return 0.0
        return vertical / (2.0 * horizontal)

    def process(self, frame_bgr: np.ndarray) -> EyeFrameResult:
        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self._face_mesh.process(frame_rgb)

        if not results.multi_face_landmarks:
            return EyeFrameResult(False, 0, None, None, None, None)

        faces = results.multi_face_landmarks
        face_count = len(faces)

        # Pick the "primary" face = the one with the largest bounding box
        # (i.e. closest to the camera), as required when multiple faces appear.
        best_landmarks = None
        best_area_ratio = -1.0
        for face_landmarks in faces:
            xs = [lm.x for lm in face_landmarks.landmark]
            ys = [lm.y for lm in face_landmarks.landmark]
            area_ratio = (max(xs) - min(xs)) * (max(ys) - min(ys))
            if area_ratio > best_area_ratio:
                best_area_ratio = area_ratio
                best_landmarks = face_landmarks.landmark

        left_ear = self._ear_for_eye(best_landmarks, LEFT_EYE_IDX, w, h)
        right_ear = self._ear_for_eye(best_landmarks, RIGHT_EYE_IDX, w, h)
        avg_ear = (left_ear + right_ear) / 2.0

        return EyeFrameResult(
            face_detected=True,
            face_count=face_count,
            ear=avg_ear,
            left_ear=left_ear,
            right_ear=right_ear,
            face_box_area_ratio=best_area_ratio,
        )

    def close(self):
        self._face_mesh.close()
