"""
DatabaseManager wraps a local SQLite database.

PRIVACY NOTE: This module never receives or stores camera frames, images,
or any biometric imagery. Only numeric/aggregated session statistics are
persisted (counts, durations, rates, timestamps).

Schema
------
sessions
    id, date, start_time, end_time,
    screen_time_seconds, active_time_seconds, break_time_seconds,
    total_blinks, longest_no_blink_seconds, breaks_taken, low_blink_periods

blink_minutes
    id, session_id, minute_timestamp, blink_count, avg_ear
    (per-minute aggregate used to draw the "blink rate throughout the day" chart)

low_blink_events
    id, session_id, start_time, end_time, avg_blink_rate

daily_stats  (materialized rollup per calendar day, refreshed on session close
              and periodically, to make History queries fast)
    date (PK), total_blinks, avg_blink_rate, longest_no_blink_seconds,
    screen_time_seconds, active_time_seconds, break_time_seconds,
    breaks_taken, low_blink_periods
"""
import sqlite3
import threading
from datetime import datetime, date, timedelta
from pathlib import Path

from app.config import DB_PATH, APP_DIR

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    screen_time_seconds INTEGER DEFAULT 0,
    active_time_seconds INTEGER DEFAULT 0,
    break_time_seconds INTEGER DEFAULT 0,
    total_blinks INTEGER DEFAULT 0,
    longest_no_blink_seconds INTEGER DEFAULT 0,
    breaks_taken INTEGER DEFAULT 0,
    low_blink_periods INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS blink_minutes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    minute_timestamp TEXT NOT NULL,
    blink_count INTEGER DEFAULT 0,
    avg_ear REAL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS low_blink_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    avg_blink_rate REAL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS daily_stats (
    date TEXT PRIMARY KEY,
    total_blinks INTEGER DEFAULT 0,
    avg_blink_rate REAL DEFAULT 0,
    longest_no_blink_seconds INTEGER DEFAULT 0,
    screen_time_seconds INTEGER DEFAULT 0,
    active_time_seconds INTEGER DEFAULT 0,
    break_time_seconds INTEGER DEFAULT 0,
    breaks_taken INTEGER DEFAULT 0,
    low_blink_periods INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_blink_minutes_session ON blink_minutes(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date);
"""


class DatabaseManager:
    def __init__(self, path: Path = DB_PATH):
        APP_DIR.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    # ---------------------------------------------------------------- sessions
    def start_session(self) -> int:
        now = datetime.now()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO sessions (date, start_time) VALUES (?, ?)",
                (now.date().isoformat(), now.isoformat()),
            )
            self._conn.commit()
            return cur.lastrowid

    def checkpoint_session(self, session_id: int, screen_time_s: int, active_time_s: int,
                            break_time_s: int, total_blinks: int, longest_no_blink_s: int,
                            breaks_taken: int, low_blink_periods: int):
        """Write the current running session's numbers into the sessions
        table WITHOUT closing it, then refresh the daily rollup. This is
        what lets History/Insights show live progress instead of only
        updating once the app fully closes."""
        with self._lock:
            self._conn.execute(
                """UPDATE sessions SET screen_time_seconds=?, active_time_seconds=?,
                   break_time_seconds=?, total_blinks=?, longest_no_blink_seconds=?,
                   breaks_taken=?, low_blink_periods=? WHERE id=?""",
                (screen_time_s, active_time_s, break_time_s, total_blinks,
                 longest_no_blink_s, breaks_taken, low_blink_periods, session_id),
            )
            self._conn.commit()
        self._refresh_daily_stats(date.today().isoformat())

    def end_session(self, session_id: int, screen_time_s: int, active_time_s: int,
                     break_time_s: int, total_blinks: int, longest_no_blink_s: int,
                     breaks_taken: int, low_blink_periods: int):
        with self._lock:
            self._conn.execute(
                """UPDATE sessions SET end_time=?, screen_time_seconds=?,
                   active_time_seconds=?, break_time_seconds=?, total_blinks=?,
                   longest_no_blink_seconds=?, breaks_taken=?, low_blink_periods=?
                   WHERE id=?""",
                (datetime.now().isoformat(), screen_time_s, active_time_s,
                 break_time_s, total_blinks, longest_no_blink_s, breaks_taken,
                 low_blink_periods, session_id),
            )
            self._conn.commit()
        self._refresh_daily_stats(date.today().isoformat())

    # ------------------------------------------------------------ blink data
    def record_blink_minute(self, session_id: int, minute_ts: datetime,
                             blink_count: int, avg_ear: float):
        with self._lock:
            self._conn.execute(
                """INSERT INTO blink_minutes (session_id, minute_timestamp,
                   blink_count, avg_ear) VALUES (?, ?, ?, ?)""",
                (session_id, minute_ts.isoformat(), blink_count, avg_ear),
            )
            self._conn.commit()

    def record_low_blink_event(self, session_id: int, start_time: datetime,
                                end_time: datetime, avg_blink_rate: float):
        with self._lock:
            self._conn.execute(
                """INSERT INTO low_blink_events (session_id, start_time,
                   end_time, avg_blink_rate) VALUES (?, ?, ?, ?)""",
                (session_id, start_time.isoformat(), end_time.isoformat(),
                 avg_blink_rate),
            )
            self._conn.commit()

    def today_blink_minutes(self):
        today = date.today().isoformat()
        with self._lock:
            rows = self._conn.execute(
                """SELECT bm.minute_timestamp, bm.blink_count FROM blink_minutes bm
                   JOIN sessions s ON bm.session_id = s.id
                   WHERE s.date = ? ORDER BY bm.minute_timestamp""",
                (today,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------- rollups
    def _refresh_daily_stats(self, day: str):
        with self._lock:
            row = self._conn.execute(
                """SELECT
                       COALESCE(SUM(total_blinks),0) as total_blinks,
                       COALESCE(SUM(screen_time_seconds),0) as screen_time_seconds,
                       COALESCE(SUM(active_time_seconds),0) as active_time_seconds,
                       COALESCE(SUM(break_time_seconds),0) as break_time_seconds,
                       COALESCE(SUM(breaks_taken),0) as breaks_taken,
                       COALESCE(SUM(low_blink_periods),0) as low_blink_periods,
                       COALESCE(MAX(longest_no_blink_seconds),0) as longest_no_blink_seconds
                   FROM sessions WHERE date = ?""",
                (day,),
            ).fetchone()
            active_minutes = max(row["active_time_seconds"] / 60.0, 1e-6)
            avg_rate = row["total_blinks"] / active_minutes if row["active_time_seconds"] else 0
            self._conn.execute(
                """INSERT INTO daily_stats (date, total_blinks, avg_blink_rate,
                       longest_no_blink_seconds, screen_time_seconds,
                       active_time_seconds, break_time_seconds, breaks_taken,
                       low_blink_periods)
                   VALUES (?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(date) DO UPDATE SET
                       total_blinks=excluded.total_blinks,
                       avg_blink_rate=excluded.avg_blink_rate,
                       longest_no_blink_seconds=excluded.longest_no_blink_seconds,
                       screen_time_seconds=excluded.screen_time_seconds,
                       active_time_seconds=excluded.active_time_seconds,
                       break_time_seconds=excluded.break_time_seconds,
                       breaks_taken=excluded.breaks_taken,
                       low_blink_periods=excluded.low_blink_periods""",
                (day, row["total_blinks"], round(avg_rate, 1),
                 row["longest_no_blink_seconds"], row["screen_time_seconds"],
                 row["active_time_seconds"], row["break_time_seconds"],
                 row["breaks_taken"], row["low_blink_periods"]),
            )
            self._conn.commit()

    def get_daily_stats(self, day: date) -> dict:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM daily_stats WHERE date = ?", (day.isoformat(),)
            ).fetchone()
        return dict(row) if row else {
            "date": day.isoformat(), "total_blinks": 0, "avg_blink_rate": 0,
            "longest_no_blink_seconds": 0, "screen_time_seconds": 0,
            "active_time_seconds": 0, "break_time_seconds": 0,
            "breaks_taken": 0, "low_blink_periods": 0,
        }

    def get_range_summary(self, days: int) -> dict:
        """Aggregate stats over the last `days` calendar days (inclusive of today)."""
        start = (date.today() - timedelta(days=days - 1)).isoformat()
        with self._lock:
            row = self._conn.execute(
                """SELECT
                       COALESCE(SUM(total_blinks),0) as total_blinks,
                       COALESCE(AVG(avg_blink_rate),0) as avg_blink_rate,
                       COALESCE(MAX(longest_no_blink_seconds),0) as longest_no_blink_seconds,
                       COALESCE(SUM(screen_time_seconds),0) as screen_time_seconds,
                       COALESCE(SUM(active_time_seconds),0) as active_time_seconds,
                       COALESCE(SUM(break_time_seconds),0) as break_time_seconds,
                       COALESCE(SUM(breaks_taken),0) as breaks_taken,
                       COALESCE(SUM(low_blink_periods),0) as low_blink_periods
                   FROM daily_stats WHERE date >= ?""",
                (start,),
            ).fetchone()
        return dict(row)

    def get_daily_series(self, days: int) -> list:
        """List of per-day dicts for the last `days` days, oldest first (for charts)."""
        start = (date.today() - timedelta(days=days - 1)).isoformat()
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM daily_stats WHERE date >= ? ORDER BY date ASC",
                (start,),
            ).fetchall()
        by_date = {r["date"]: dict(r) for r in rows}
        series = []
        for i in range(days):
            d = (date.today() - timedelta(days=days - 1 - i)).isoformat()
            series.append(by_date.get(d, {
                "date": d, "total_blinks": 0, "avg_blink_rate": 0,
                "longest_no_blink_seconds": 0, "screen_time_seconds": 0,
                "active_time_seconds": 0, "break_time_seconds": 0,
                "breaks_taken": 0, "low_blink_periods": 0,
            }))
        return series

    def close(self):
        with self._lock:
            self._conn.close()
