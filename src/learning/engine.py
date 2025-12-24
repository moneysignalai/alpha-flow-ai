from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from core.logging import get_logger
from models.schemas import PerformanceRecord

logger = get_logger(__name__)


class LearningEngine:
    def __init__(self):
        self.records: List[PerformanceRecord] = []
        self.ticker_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {"wins": 0, "losses": 0, "mfe": 0.0})

    def record_performance(self, record: PerformanceRecord):
        self.records.append(record)
        stats = self.ticker_stats[record.ticker]
        stats["wins"] += 1 if record.win else 0
        stats["losses"] += 0 if record.win else 1
        stats["mfe"] = (stats["mfe"] + record.mfe) / 2 if stats["mfe"] else record.mfe

    def reliability(self, ticker: str) -> float:
        stats = self.ticker_stats.get(ticker, {"wins": 0, "losses": 0})
        total = stats.get("wins", 0) + stats.get("losses", 0)
        if total == 0:
            return 0.5
        return stats.get("wins", 0) / total

    def adjust_weights(self, scoring_engine):
        for ticker, stats in self.ticker_stats.items():
            reliability = self.reliability(ticker)
            if reliability > 0.6:
                scoring_engine.weights["flow"] = min(scoring_engine.weights["flow"] + 0.05, 0.5)
            else:
                scoring_engine.weights["flow"] = max(scoring_engine.weights["flow"] - 0.05, 0.3)
        logger.info("Adjusted scoring weights", extra={"weights": scoring_engine.weights})
