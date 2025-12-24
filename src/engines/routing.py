from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from models.schemas import RoutedSignal, ScoreResult


class QueueItem(RoutedSignal):
    expires_at: datetime


class RoutingEngine:
    def __init__(self, intraday_expiry_minutes: int = 60, swing_expiry_days: int = 10):
        self.immediate: List[RoutedSignal] = []
        self.intraday: List[RoutedSignal] = []
        self.swing: List[RoutedSignal] = []
        self.rejected: List[RoutedSignal] = []
        self.intraday_expiry = timedelta(minutes=intraday_expiry_minutes)
        self.swing_expiry = timedelta(days=swing_expiry_days)

    def route(self, score: ScoreResult, routed_signal: RoutedSignal) -> str:
        route = self._determine_route(score.score)
        routed_signal.route = route
        if route == "immediate_alert":
            self.immediate.append(routed_signal)
        elif route == "intraday_watch":
            self.intraday.append(routed_signal)
        elif route == "swing_watch":
            self.swing.append(routed_signal)
        else:
            self.rejected.append(routed_signal)
        return route

    def refresh_queues(self):
        now = datetime.utcnow()
        self.intraday = [s for s in self.intraday if (now - s.created_at) < self.intraday_expiry]
        self.swing = [s for s in self.swing if (now - s.created_at) < self.swing_expiry]

        promotions: List[RoutedSignal] = []
        for s in list(self.intraday):
            if s.score.score >= 85:
                promotions.append(s)
        for p in promotions:
            self.intraday.remove(p)
            p.route = "immediate_alert"
            self.immediate.append(p)

    @staticmethod
    def _determine_route(score: float) -> str:
        if score >= 85:
            return "immediate_alert"
        if score >= 65:
            return "intraday_watch"
        if score >= 50:
            return "swing_watch"
        return "reject"
