# 👁️ BlinkGuard

**BlinkGuard** is a privacy-first desktop application that helps people who spend long
hours in front of a screen build healthier eye habits. It uses your webcam and
real-time computer vision to intelligently monitor your blinking behavior — not a
fixed timer — and gently nudges you when you've gone too long without blinking, when
your blink rate drops, or when it's time for a screen break.

All processing happens **locally on your machine**. No camera frame, image, or video
is ever saved or uploaded — see [Privacy](#-privacy) below.

> BlinkGuard is a wellness/reminder tool. It is not a medical device and does not
> diagnose, treat, or guarantee protection from any eye condition.

---

## Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [How It Works](#-how-it-works)
  - [Computer Vision Pipeline](#computer-vision-pipeline)
  - [Blink Detection Algorithm](#blink-detection-algorithm)
  - [Notification Anti-Spam Logic](#notification-anti-spam-logic)
  - [Database Schema](#database-schema)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Known Limitations](#-known-limitations)
- [Roadmap](#-roadmap)
- [Privacy](#-privacy)
- [Health Disclaimer](#-health-disclaimer)
- [License](#-license)
- [Author](#-author)

---

## ✨ Features

- **Intelligent blink monitoring** — reacts to your actual blinking behavior instead
  of firing on a fixed timer.
- **Real-time Eye Aspect Ratio (EAR) tracking** via MediaPipe Face Mesh landmarks.
- **Robust blink detection** using a hysteresis state machine with debouncing —
  avoids double-counting and false positives from lighting, head movement, or
  camera noise.
- **Rolling blink-rate calculation** (blinks per minute), longest no-blink duration,
  and sustained low-blink-period detection.
- **Gentle, cooldown-gated reminders** — never spammy.
- **Independent break reminders** with configurable interval and duration.
- **Screen time tracking** — today's screen time, current session, active time,
  break time, and number of breaks.
- **Modern dashboard** with live stats and charts.
- **History page** with Today / Yesterday / Last 7 days / Last 30 days views.
- **Insights page** generating plain-language observations from your local data only
  (no external AI API involved).
- **Native desktop notifications** with optional sound.
- **Full Settings page** — monitoring sensitivity, thresholds, breaks, notifications,
  camera selection, and appearance.
- **Light / Dark / System themes.**
- **System tray integration** — minimizes without stopping monitoring; tray menu for
  pause/resume, break, settings, and exit.
- **Start with computer** option.
- **Pause/Resume monitoring** at any time, with a clear on-screen state.
- **First-run calibration wizard** — Welcome → Privacy → Camera Test → Calibration.
- **Multiple-face handling** — focuses on the primary (largest/closest) face and
  never mixes blink data from different people.
- **Comprehensive error handling** — camera unavailable, permission denied, no face
  detected, camera disconnected, poor lighting, and more — the app never crashes.
- **Local SQLite storage** of aggregated numeric statistics only — never images.

## 🛠 Tech Stack

| Layer               | Technology            |
|----------------------|-----------------------|
| Language              | Python 3.10+          |
| Computer Vision       | OpenCV, MediaPipe Face Mesh |
| Numerical processing  | NumPy                 |
| Desktop UI            | PySide6 (Qt for Python) |
| Local database        | SQLite                |
| Background processing | QThread (Qt threading) |

## 🧠 How It Works

### Computer Vision Pipeline

```
Camera → Frame Capture → Face Detection → Facial Landmarks (MediaPipe Face Mesh)
       → Eye Landmarks → Eye Aspect Ratio (EAR) → Blink Detection
       → Blink Rate Calculation → Health/Break Monitoring → Notifications
```

Each frame is captured, analyzed in memory, reduced to a numeric EAR value, and then
**immediately discarded**. Nothing from this pipeline is written to disk.

### Blink Detection Algorithm

For each eye, six MediaPipe landmarks are used to compute the **Eye Aspect Ratio**:

```
EAR = ( ||p2 − p6|| + ||p3 − p5|| ) / ( 2 × ||p1 − p4|| )
```

where `p1..p6` are `[outer_corner, top1, top2, inner_corner, bottom2, bottom1]`. The
left and right EAR values are averaged to reduce single-eye noise.

A **hysteresis state machine** turns the EAR stream into discrete blink events:

- `OPEN → CLOSED` when EAR drops below a *closed* threshold.
- `CLOSED → OPEN` when EAR rises back above a higher *open* threshold — this
  transition is counted as **exactly one blink**.

Using two thresholds with a gap between them (rather than one) prevents the rapid
on/off flicker that a single threshold produces near the boundary. A minimum
consecutive-closed-frame count and a refractory (debounce) period further guard
against counting a single noisy frame or camera glitch as a blink.

Thresholds are **calibrated per user**: during onboarding (or re-calibration from
Settings), the app records a short baseline of natural blinking and derives
personalized thresholds from it, rather than relying on one hard-coded value that
may not suit every face or camera.

### Notification Anti-Spam Logic

Two independent, cooldown-gated notification categories exist: **blink reminders**
and **break reminders**. A notification only fires when:

1. The triggering condition is genuinely true (e.g., no blink for N seconds, or a
   sustained low blink rate), **and**
2. A face is currently visible and monitoring is not paused, **and**
3. The minimum cooldown period since the last notification *of that category* has
   elapsed.

Sustained conditions (like a low blink rate) must also persist for a minimum
duration before they're even logged as an event — a single missed blink or one slow
minute never triggers anything.

### Database Schema

Only aggregated, numeric session data is stored — **never** frames or images.

| Table              | Purpose                                                        |
|---------------------|------------------------------------------------------------------|
| `sessions`          | Per-session totals: screen/active/break time, blinks, breaks taken |
| `blink_minutes`     | Per-minute blink counts, used to draw the daily blink-rate chart |
| `low_blink_events`  | Start/end time and average rate of each sustained low-blink period |
| `daily_stats`       | Rolled-up per-day summary for fast History/Insights queries      |

## 📦 Installation

**Requirements:** Python 3.10+, a webcam.

```bash
git clone https://github.com/noorzakeebeh/BlinkGuard.git
cd BlinkGuard/blinkguard
pip install -r requirements.txt
```

> **Important:** `requirements.txt` pins `mediapipe==0.10.13`. Newer MediaPipe
> releases removed the legacy `solutions.face_mesh` API in favor of a Tasks-based
> API that requires downloading an external model file. Pinning this version keeps
> BlinkGuard fully offline and self-contained, with no model downloads needed.

## 📦 Building a Standalone Executable / Publishing Releases

For a full step-by-step walkthrough (packaging with PyInstaller, building for
Windows/macOS/Linux, and setting up automatic GitHub Releases via GitHub
Actions), see **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**.

## ▶️ Usage

```bash
python main.py
```

On first launch, BlinkGuard walks you through:

1. **Welcome** — a short overview of what the app does.
2. **Privacy** — exactly what is and isn't done with your camera feed.
3. **Camera Test** — confirms your webcam works and a face is detected.
4. **Calibration** — a few seconds of natural blinking to set your personal baseline.

After setup, BlinkGuard runs in the background and can be minimized to the system
tray without interrupting monitoring. Use the tray menu to pause/resume monitoring,
start a break, open Settings, or exit.

## 🗂 Project Structure

```
blinkguard/
├── main.py                        # Application entry point
├── requirements.txt
└── app/
    ├── config.py                  # Constants and default settings
    ├── core/                      # Pure logic, no UI dependencies
    │   ├── camera_handler.py      # OpenCV VideoCapture lifecycle
    │   ├── eye_detector.py        # MediaPipe Face Mesh + EAR computation
    │   ├── blink_detector.py      # Hysteresis blink state machine
    │   ├── blink_statistics.py    # Rolling rate, longest gap, low-blink periods
    │   ├── screen_time_tracker.py # Active/away/break time tracking
    │   ├── break_manager.py       # Break interval/duration logic
    │   ├── notification_manager.py# Cooldown-gated notifications
    │   └── privacy_manager.py     # Central privacy/disclaimer text
    ├── data/
    │   ├── database.py            # SQLite schema and queries
    │   └── settings_manager.py    # JSON-backed user settings
    ├── workers/
    │   ├── vision_worker.py       # Background QThread running the full CV pipeline
    │   └── calibration_worker.py  # Lightweight thread for camera test/calibration
    └── ui/
        ├── main_window.py         # Navigation and orchestration
        ├── theme.py                # Light/Dark/System stylesheets
        ├── tray.py                 # System tray integration
        ├── pages/                  # Dashboard, History, Insights, Settings, Privacy, Onboarding
        └── widgets/                 # Stat cards, charts, camera status indicator
```

## ⚙️ Configuration

All user-adjustable options are available from the **Settings** page:

- Blink monitoring: enable/disable, sensitivity, low-blink threshold, minimum time
  before a reminder.
- Breaks: enable/disable, interval, duration.
- Notifications: enable/disable, sound on/off.
- Camera: device selection, live preview/test.
- Appearance: Light / Dark / System.
- Start BlinkGuard when your computer starts.

Settings are stored locally in `~/.blinkguard/settings.json`; statistics are stored
in `~/.blinkguard/blinkguard.db` (SQLite).

## ⚠️ Known Limitations

- Blink detection accuracy depends on lighting, camera quality, and face angle;
  calibration significantly improves reliability but cannot eliminate all edge cases.
- "Start with computer" registers a launch entry using OS-specific mechanisms and
  may require re-confirmation after major OS updates.
- Screen-time tracking uses face presence as a proxy for attentiveness — it cannot
  detect whether you're actually looking at the screen versus simply near the camera.
- Very poor lighting or extreme head angles may cause temporary face-detection loss;
  the app is designed to recover gracefully rather than misreport this as "not
  blinking."

## 🗺 Roadmap

- Per-eye asymmetry detection (e.g., partial ptosis awareness)
- Exportable CSV/PDF reports from History
- Optional ambient-light-aware sensitivity auto-tuning
- Multi-monitor-aware break reminders

## 🔒 Privacy

BlinkGuard processes your camera feed entirely on your own computer.

**What happens to each camera frame:**
1. A frame is captured from your webcam.
2. It is analyzed locally to find your eyes and estimate blinking.
3. Only numeric results (blink yes/no, eye-openness value) are kept.
4. The frame itself is immediately discarded.

**What BlinkGuard never does:**
- Never saves photos, video, or camera recordings.
- Never uploads camera data anywhere.
- Never sends anything to an external server or third-party API for blink detection.

**What is stored locally (SQLite, on your machine only):**
- Session start/end times
- Screen time, active time, and break time (in seconds)
- Blink counts and blink-rate aggregates
- Longest no-blink duration and low-blink-period counts

None of this data leaves your computer unless you explicitly export or back it up
yourself. The full statement is also available inside the app's **Privacy** page.

## 🩺 Health Disclaimer

BlinkGuard is designed to encourage healthy screen habits and regular blinking. It
is **not a medical device**. It does not diagnose, treat, or guarantee protection
from any eye condition or disease. If you experience eye pain, vision changes, or
persistent discomfort, please consult an eye care professional.

## 📄 License

**All rights reserved.** This project is proprietary and private. No license is
granted for use, copying, modification, or distribution without the express written
permission of the author.

© 2026 Noor Mahmoud Jamal Al Zakeebeh. All rights reserved.

## 👤 Author

**Noor Mahmoud Jamal Al Zakeebeh**
📧 [nooraschool206@gmail.com](mailto:nooraschool206@gmail.com)
🔗 [github.com/noorzakeebeh/BlinkGuard](https://github.com/noorzakeebeh/BlinkGuard)
