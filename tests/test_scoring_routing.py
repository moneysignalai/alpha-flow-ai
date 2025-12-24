from datetime import datetime, timedelta

from engines.scoring import ScoringEngine
from engines.routing import RoutingEngine
from models.schemas import Candidate, Direction, FlowEvent, MarketRegimeState, PriceSnapshot, TechnicalContext


def make_candidate(score_boost: float = 1.0) -> Candidate:
    flow = FlowEvent(
        ticker="AAPL",
        direction=Direction.CALL,
        notional=1_000_000 * score_boost,
        premium=500_000 * score_boost,
        iv=0.4,
        expiry_horizon=timedelta(days=20),
        dte=20,
        conviction_score=4 * score_boost,
        spot_price=150,
        strike=155,
        expiry=datetime.utcnow() + timedelta(days=30),
        option_symbol="AAPL250215C00155000",
        side="CALL",
        last_price=4.2,
        bid=4.1,
        ask=4.3,
        volume=1200,
        open_interest=5000,
        volume_multiple=4,
    )
    price = PriceSnapshot(ticker="AAPL", price=150, change_pct=2.5, volume=1_200_000, vwap=148, sector_strength=0.5)
    regime = MarketRegimeState(
        trend_bias="bullish",
        volatility=0.2,
        liquidity=0.01,
        risk_environment="balanced",
        gex=0.1,
        vex=0.2,
        reasoning="test",
    )
    tech = TechnicalContext(
        ticker="AAPL",
        rsi=60,
        macd=1,
        macd_signal=0.5,
        ema_fast=149,
        ema_mid=148,
        ema_slow=146,
        vwap=148,
        volume=1_200_000,
        volume_trend=1.2,
        bias="bullish",
    )
    return Candidate(ticker="AAPL", flow=flow, price=price, regime=regime, technical=tech)


def test_scoring_and_routing():
    candidate = make_candidate()
    scoring = ScoringEngine()
    route_engine = RoutingEngine()

    score = scoring.score(candidate, has_news=True)
    signal_route = route_engine.route(score, routed_signal=score_to_signal(candidate, score))

    assert score.score >= 85
    assert signal_route == "immediate_alert"


def test_queue_refresh_and_promotion():
    candidate = make_candidate(score_boost=0.7)
    scoring = ScoringEngine()
    route_engine = RoutingEngine()
    score = scoring.score(candidate, has_news=False)
    routed = score_to_signal(candidate, score)
    route_engine.route(score, routed)
    assert routed.route in {"intraday_watch", "swing_watch"}
    routed.score.score = 90
    route_engine.refresh_queues()
    assert any(sig.route == "immediate_alert" for sig in route_engine.immediate)


def score_to_signal(candidate: Candidate, score):
    from models.schemas import RoutedSignal

    return RoutedSignal(candidate=candidate, score=score, route="pending")
