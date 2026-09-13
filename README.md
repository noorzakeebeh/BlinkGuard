# 👁️ BlinkGuard - Desktop Eye Blink & Fatigue Tracking Application

**BlinkGuard** is a real-time computer vision desktop application built with Python. It tracks eye blinks, monitors blink rates, and detects signs of fatigue or prolonged eye strain using facial landmark detection.

---

## 🚀 Features

* **Real-time Face & Eye Detection**: Uses MediaPipe's Face Mesh to track facial landmarks efficiently.
* **Blink Rate Monitoring**: Computes eye aspect ratio (EAR) and counts blinks per minute.
* **System Tray Operation**: Minimizes seamlessly to the system tray for uninterrupted background monitoring.
* **Low Latency & High Performance**: Optimized with OpenCV and DirectShow for minimal webcam latency.

---

## 🛠️ Tech Stack & Requirements

* **Language**: Python 3.11+
* **Core Libraries**:
  * `opencv-python` (Webcam video capture & frame processing)
  * `mediapipe` (Facial landmark mesh estimation)
  * `numpy` (Mathematical computations)
  * `PyQt5` / `tkinter` (Desktop UI components)

---

## 📥 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/noorzakeebeh/BlinkGuard.git](https://github.com/noorzakeebeh/BlinkGuard.git)
   cd BlinkGuard
