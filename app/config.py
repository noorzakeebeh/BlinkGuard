"""
Central, non-user-editable constants for BlinkGuard.
User-editable values live in Settings (see data/settings_manager.py) and are
seeded from the defaults below on first run.
"""
from pathlib import Path

APP_NAME = "BlinkGuard"
APP_VERSION = "1.0.0"

# --- Storage locations -------------------------------------------------
APP_DIR = Path.home() / ".blinkguard"
DB_PATH = APP_DIR / "blinkguard.db"
SETTINGS_PATH = APP_DIR / "settings.json"

# --- Camera / CV ---------------------------------------------------------
CAMERA_FPS_TARGET = 15          # we don't need 30fps for EAR tracking; saves CPU
FRAME_WIDTH = 480               # downscale for performance
FRAME_HEIGHT = 360
FACE_MESH_MAX_FACES = 2         # detect up to 2 so we can notice "multiple faces"

# MediaPipe FaceMesh landmark indices used for Eye Aspect Ratio (EAR).
# Order per eye: [outer_corner, top1, top2, inner_corner, bottom2, bottom1]
LEFT_EYE_IDX = [362, 385, 387, 263, 373, 380]
RIGHT_EYE_IDX = [33, 160, 158, 133, 153, 144]

# --- Default (user-adjustable) monitoring thresholds ---------------------
DEFAULT_SETTINGS = {
    "monitoring_enabled": True,
    "blink_sensitivity": 0.75,        # multiplier applied to calibrated baseline EAR
    "low_blink_rate_threshold": 8,    # blinks/min below this => "low blink" state
    "low_blink_sustain_seconds": 30,  # how long low rate must persist to log an event
    "no_blink_reminder_seconds": 12,  # trigger reminder if no blink for this long
    "reminder_cooldown_seconds": 60,  # minimum gap between blink reminders

    "breaks_enabled": True,
    "break_interval_minutes": 20,
    "break_duration_minutes": 5,

    "notifications_enabled": True,
    "notification_sound": True,

    "theme": "system",                # "light" | "dark" | "system"
    "start_with_computer": False,

    "camera_index": 0,
    "calibrated": False,
    "baseline_ear": 0.30,             # replaced after calibration
}

# --- Blink detector defaults (used until/if calibration overrides them) --
EAR_CLOSED_RATIO = 0.78   # fraction of baseline EAR considered "closed"
EAR_OPEN_RATIO = 0.85     # fraction of baseline EAR considered "open" again (hysteresis)
MIN_CLOSED_FRAMES = 1     # minimum consecutive closed frames to count as real closure
BLINK_REFRACTORY_MS = 120  # ignore re-triggers within this window (debounce)

# --- Presence / stability heuristics -------------------------------------
FACE_LOST_GRACE_SECONDS = 2.0     # brief face-loss doesn't reset stats immediately
AWAY_AFTER_SECONDS = 45           # no face this long => considered "away" (not screen time)
