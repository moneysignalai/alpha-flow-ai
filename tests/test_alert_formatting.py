from datetime import datetime, timedelta

from alerts.dispatcher import AlertDispatcher
from models.schemas import Candidate, Direction, FlowEvent, MarketRegimeState, PriceSnapshot, RoutedSignal, ScoreResult, TechnicalContext


def build_signal():
    flow = FlowEvent(
        ticker="NVDA",
        direction=Direction.CALL,
        notional=3_200_000,
        premium=1_000_000,
        iv=0.55,
        expiry_horizon=timedelta(days=23),
        dte=23,
        conviction_score=5.0,
        spot_price=700.0,
        strike=700.0,
        expiry=datetime(2025, 2, 14),
        option_symbol="NVDA250214C00700000",
        side="CALL",
        last_price=9.35,
        bid=9.30,
        ask=9.45,
        volume=12430,
        open_interest=18900,
        volume_multiple=4.0,
    )
    price = PriceSnapshot(ticker="NVDA", price=700.0, change_pct=0.02, volume=2_000_000, vwap=695.0, sector_strength=0.6)
    regime = MarketRegimeState(
        trend_bias="bullish",
        volatility=0.18,
        liquidity=0.9,
        risk_environment="benign",
        gex=0.2,
        vex=0.1,
        reasoning="test",
    )
    technical = TechnicalContext(
        ticker="NVDA",
        rsi=65,
        macd=1.5,
        macd_signal=1.0,
        ema_fast=698,
        ema_mid=690,
        ema_slow=680,
        vwap=695,
        volume=2_000_000,
        volume_trend=1.3,
        bias="bullish",
    )
    candidate = Candidate(
        ticker="NVDA",
        flow=flow,
        price=price,
        regime=regime,
        technical=technical,
        primary_option_symbol=flow.option_symbol,
        primary_expiry=flow.expiry.date(),
        primary_strike=flow.strike,
        primary_side=flow.side,
        primary_dte=flow.dte,
        primary_last_price=flow.last_price,
        primary_bid=flow.bid,
        primary_ask=flow.ask,
        primary_volume=flow.volume,
        primary_open_interest=flow.open_interest,
        primary_notional=flow.notional,
    )
    score = ScoreResult(score=92, grade="A", reasoning="strong flow")
    return RoutedSignal(candidate=candidate, score=score, route="immediate_alert")


def test_alert_contains_option_details():
    dispatcher = AlertDispatcher(config={"alerts": {"transports": {"telegram": {"enabled": False}}}})
    message = dispatcher._format_signal(build_signal())

    assert "Option Symbol: NVDA250214C00700000" in message
    assert "Contract: CALL 700.00" in message
    assert "(23D)" in message
    assert "Volume: 12,430" in message
    assert "OI: 18,900" in message
    assert "Flow Notional" in message
