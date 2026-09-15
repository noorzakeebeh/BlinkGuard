"""
SettingsManager persists user-adjustable preferences to a small JSON file.
Kept separate from the SQLite database because settings are simple key/value
config, not relational statistics.
"""
import json
import copy
import threading
from pathlib import Path

from app.config import SETTINGS_PATH, APP_DIR, DEFAULT_SETTINGS


class SettingsManager:
    def __init__(self, path: Path = SETTINGS_PATH):
        self._path = path
        self._lock = threading.Lock()
        self._values = copy.deepcopy(DEFAULT_SETTINGS)
        self._load()

    def _load(self):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                # merge so new keys added in future versions get defaults
                merged = copy.deepcopy(DEFAULT_SETTINGS)
                merged.update(stored)
                self._values = merged
            except (json.JSONDecodeError, OSError):
                self._values = copy.deepcopy(DEFAULT_SETTINGS)
        else:
            self._save()

    def _save(self):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._values, f, indent=2)
        tmp_path.replace(self._path)

    def get(self, key, default=None):
        with self._lock:
            return self._values.get(key, default)

    def get_all(self):
        with self._lock:
            return copy.deepcopy(self._values)

    def set(self, key, value):
        with self._lock:
            self._values[key] = value
            self._save()

    def update(self, mapping: dict):
        with self._lock:
            self._values.update(mapping)
            self._save()

    def reset_to_defaults(self):
        with self._lock:
            self._values = copy.deepcopy(DEFAULT_SETTINGS)
            self._save()
