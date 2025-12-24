from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from models.schemas import RoutedSignal


class AlertStore:
    """SQLite-backed store for queued alerts needing follow-up movement checks."""

    def __init__(
        self,
        db_path: str = "data/alerts.db",
        intraday_expiry_minutes: int = 60,
        swing_expiry_days: int = 10,
    ):
        self.db_path = db_path
        self.intraday_expiry = timedelta(minutes=intraday_expiry_minutes)
        self.swing_expiry = timedelta(days=swing_expiry_days)
        self._ensure_directory()
        self._ensure_schema()

    def _ensure_directory(self):
        directory = os.path.dirname(self.db_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    route TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    score REAL,
                    grade TEXT,
                    direction TEXT,
                    reasoning TEXT,
                    payload TEXT,
                    last_checked_at TEXT,
                    movement_observed REAL
                )
                """
            )
            conn.commit()

    def _expiry_for_route(self, route: str) -> Optional[datetime]:
        now = datetime.utcnow()
        if route == "intraday_watch":
            return now + self.intraday_expiry
        if route == "swing_watch":
            return now + self.swing_expiry
        if route == "immediate_alert":
            return now + timedelta(hours=4)
        return None

    def record_signal(self, signal: RoutedSignal, metadata: Optional[Dict] = None):
        if signal.route == "reject":
            return

        expires_at = self._expiry_for_route(signal.route)
        payload = {
            "candidate": {
                "ticker": signal.candidate.ticker,
                "classification": signal.candidate.classification,
                "flow": {
                    "direction": signal.candidate.flow.direction.value,
                    "notional": signal.candidate.flow.notional,
                    "premium": signal.candidate.flow.premium,
                    "expiry": signal.candidate.flow.expiry.isoformat(),
                    "expiry_horizon_days": signal.candidate.flow.expiry_horizon.days,
                    "spot_price": signal.candidate.flow.spot_price,
                    "strike": signal.candidate.flow.strike,
                },
                "regime": signal.candidate.regime.risk_environment,
                "technical_bias": signal.candidate.technical.bias,
            },
            "score": asdict(signal.score),
            "route": signal.route,
            "metadata": metadata or {},
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO alerts (
                    ticker, route, status, created_at, expires_at, score, grade, direction, reasoning, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.candidate.ticker,
                    signal.route,
                    "pending",
                    signal.created_at.isoformat(),
                    expires_at.isoformat() if expires_at else None,
                    signal.score.score,
                    signal.score.grade,
                    signal.candidate.flow.direction.value,
                    signal.score.reasoning,
                    json.dumps(payload),
                ),
            )
            conn.commit()

    def expire_stale(self):
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """UPDATE alerts SET status='expired' WHERE status='pending' AND expires_at IS NOT NULL AND expires_at < ?""",
                (now,),
            )
            conn.commit()

    def get_pending_for_checks(self, limit: int = 50) -> List[Dict]:
        self.expire_stale()
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT id, ticker, route, created_at, expires_at, score, grade, direction, reasoning, payload
                FROM alerts
                WHERE status='pending' AND (expires_at IS NULL OR expires_at >= ?)
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (now, limit),
            )
            rows = cursor.fetchall()
        results: List[Dict] = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "ticker": row[1],
                    "route": row[2],
                    "created_at": row[3],
                    "expires_at": row[4],
                    "score": row[5],
                    "grade": row[6],
                    "direction": row[7],
                    "reasoning": row[8],
                    "payload": json.loads(row[9]) if row[9] else {},
                }
            )
        return results

    def mark_checked(self, alert_id: int, movement_observed: float = 0.0):
        with self._connect() as conn:
            conn.execute(
                """UPDATE alerts SET status='checked', last_checked_at=?, movement_observed=? WHERE id=?""",
                (datetime.utcnow().isoformat(), movement_observed, alert_id),
            )
            conn.commit()
