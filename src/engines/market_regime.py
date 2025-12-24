from __future__ import annotations

import math
from datetime import datetime
from statistics import median, pstdev
from typing import Iterable

from core.logging import get_logger
from models.schemas import MarketRegimeState

logger = get_logger(__name__)


class MarketRegimeEngine:
    def __init__(self):
        self.history: list[MarketRegimeState] = []

    def evaluate(self, ohlc_series: Iterable[float], gex: float, vex: float) -> MarketRegimeState:
        prices = list(ohlc_series)
        if len(prices) < 5:
            raise ValueError("Not enough data to evaluate regime")

        returns = [(prices[i + 1] - prices[i]) / prices[i] for i in range(len(prices) - 1)]
        volatility = float(pstdev(returns) * math.sqrt(252)) if len(returns) > 1 else 0
        trend = float((prices[-1] - prices[0]) / prices[0])
        liquidity = float(median([abs(r) for r in returns])) if returns else 0

        trend_bias = "bullish" if trend > 0.02 else "bearish" if trend < -0.02 else "neutral"
        risk_env = self._risk_environment(volatility, liquidity, vex)

        regime = MarketRegimeState(
            as_of=datetime.utcnow(),
            trend_bias=trend_bias,
            volatility=volatility,
            liquidity=liquidity,
            risk_environment=risk_env,
            gex=gex,
            vex=vex,
            reasoning=f"trend={trend_bias} vol={volatility:.2f} liquidity={liquidity:.4f} gex={gex:.2f} vex={vex:.2f}",
        )
        self.history.append(regime)
        return regime

    @staticmethod
    def _risk_environment(volatility: float, liquidity: float, vex: float) -> str:
        if volatility > 0.4 or vex > 0.6:
            return "high_risk"
        if liquidity < 0.002:
            return "illiquid"
        return "balanced"
