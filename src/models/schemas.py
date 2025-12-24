from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional


class Direction(str, Enum):
    CALL = "call"
    PUT = "put"
    BULLISH = "bullish"
    BEARISH = "bearish"


@dataclass
class MarketRegimeState:
    trend_bias: str
    volatility: float
    liquidity: float
    risk_environment: str
    gex: float
    vex: float
    reasoning: str
    as_of: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FlowEvent:
    ticker: str
    direction: Direction
    notional: float
    premium: float
    iv: float
    expiry_horizon: timedelta
    conviction_score: float
    spot_price: float
    strike: float
    expiry: datetime
    volume_multiple: float
    is_sweep: bool = False
    is_block: bool = False
    raw: dict = field(default_factory=dict)


@dataclass
class PriceSnapshot:
    ticker: str
    price: float
    change_pct: float
    volume: float
    vwap: float
    sector_strength: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ohlc: Optional[List[float]] = None


@dataclass
class TechnicalContext:
    ticker: str
    rsi: float
    macd: float
    macd_signal: float
    ema_fast: float
    ema_mid: float
    ema_slow: float
    vwap: float
    volume: float
    volume_trend: float
    bias: str


@dataclass
class Candidate:
    ticker: str
    flow: FlowEvent
    price: PriceSnapshot
    regime: MarketRegimeState
    technical: TechnicalContext
    classification: Optional[str] = None


@dataclass
class ScoreResult:
    score: float
    grade: str
    reasoning: str


@dataclass
class RoutedSignal:
    candidate: Candidate
    score: ScoreResult
    route: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceRecord:
    ticker: str
    entry_time: datetime
    exit_time: datetime
    mfe: float
    win: bool
    drawdown: float
    regime: str
    score: float
