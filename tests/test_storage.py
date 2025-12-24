from datetime import datetime, timedelta

from core.storage import AlertStore
from models.schemas import Candidate, Direction, FlowEvent, MarketRegimeState, PriceSnapshot, RoutedSignal, ScoreResult, TechnicalContext


def build_signal(route: str = "intraday_watch") -> RoutedSignal:
    flow = FlowEvent(
        ticker="AAPL",
        direction=Direction.CALL,
        notional=1_000_000,
        premium=50_000,
        iv=0.4,
        expiry_horizon=timedelta(days=7),
        conviction_score=0.85,
        spot_price=190.0,
        strike=195.0,
        expiry=datetime.utcnow() + timedelta(days=7),
        volume_multiple=5,
    )
    price = PriceSnapshot(
        ticker="AAPL",
        price=190.0,
        change_pct=0.02,
        volume=1_000_000,
        vwap=189.5,
        sector_strength=0.5,
        ohlc=[185, 188, 191, 190],
    )
    regime = MarketRegimeState(
        trend_bias="bullish",
        volatility=0.2,
        liquidity=0.8,
        risk_environment="benign",
        gex=1.2,
        vex=0.4,
        reasoning="test regime",
    )
    technical = TechnicalContext(
        ticker="AAPL",
        rsi=55,
        macd=1.2,
        macd_signal=1.0,
        ema_fast=188,
        ema_mid=185,
        ema_slow=180,
        vwap=189.5,
        volume=1_000_000,
        volume_trend=1.1,
        bias="bullish",
    )
    candidate = Candidate(ticker="AAPL", flow=flow, price=price, regime=regime, technical=technical)
    score = ScoreResult(score=78, grade="B", reasoning="solid flow")
    return RoutedSignal(candidate=candidate, score=score, route=route)


def test_record_and_fetch_pending(tmp_path):
    db_path = tmp_path / "alerts.db"
    store = AlertStore(db_path=str(db_path), intraday_expiry_minutes=120, swing_expiry_days=5)

    signal = build_signal("intraday_watch")
    store.record_signal(signal, metadata={"has_news": False})

    pending = store.get_pending_for_checks()
    assert len(pending) == 1
    record = pending[0]
    assert record["ticker"] == "AAPL"
    assert record["route"] == "intraday_watch"
    assert record["payload"]["route"] == "intraday_watch"

    store.mark_checked(record["id"], movement_observed=1.5)
    still_pending = store.get_pending_for_checks()
    assert still_pending == []


def test_expire_stale(tmp_path):
    db_path = tmp_path / "alerts.db"
    store = AlertStore(db_path=str(db_path), intraday_expiry_minutes=0, swing_expiry_days=0)

    signal = build_signal("intraday_watch")
    store.record_signal(signal)

    # Expire immediately due to zero minute expiry
    store.expire_stale()
    assert store.get_pending_for_checks() == []
