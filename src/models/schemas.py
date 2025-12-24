from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
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
    dte: int
    conviction_score: float
    spot_price: float
    strike: float
    expiry: datetime
    option_symbol: str
    side: str
    volume_multiple: float
    last_price: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
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
    primary_option_symbol: Optional[str] = None
    primary_expiry: Optional[date] = None
    primary_strike: Optional[float] = None
    primary_side: Optional[str] = None
    primary_dte: Optional[int] = None
    primary_last_price: Optional[float] = None
    primary_bid: Optional[float] = None
    primary_ask: Optional[float] = None
    primary_volume: Optional[int] = None
    primary_open_interest: Optional[int] = None
    primary_notional: Optional[float] = None


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
