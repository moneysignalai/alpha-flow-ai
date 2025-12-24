from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, Iterable, List

from alerts.dispatcher import AlertDispatcher
from core.logging import StructuredAdapter, get_logger
from data.service import DataService
from engines.candidate_builder import CandidateBuilder
from engines.classifier import ClassificationEngine
from engines.market_regime import MarketRegimeEngine
from engines.options_flow import OptionsFlowEngine
from engines.routing import RoutingEngine
from engines.scoring import ScoringEngine
from engines.technical import TechnicalEngine
from core.storage import AlertStore
from learning.engine import LearningEngine
from models.schemas import Candidate, RoutedSignal

logger = StructuredAdapter(get_logger(__name__), {})


class TradingBrain:
    def __init__(self, config: Dict):
        self.config = config
        md = self.config.get("market_data", {})
        news = self.config.get("news", {})
        self.data = DataService(
            market_data_key=md.get("massive_polygon_api_key", ""),
            benzinga_key=news.get("benzinga_api_key", ""),
            cache_ttl_seconds=md.get("cache_ttl_seconds", 120),
        )
        self.regime_engine = MarketRegimeEngine()
        self.flow_engine = OptionsFlowEngine()
        self.tech_engine = TechnicalEngine()
        self.candidate_builder = CandidateBuilder()
        self.classifier = ClassificationEngine()
        self.scoring = ScoringEngine()
        self.routing = RoutingEngine(
            intraday_expiry_minutes=self.config.get("queues", {}).get("intraday_refresh_minutes", 60),
            swing_expiry_days=self.config.get("queues", {}).get("expiry_days", 10),
        )
        self.alert_store = AlertStore(
            db_path=self.config.get("storage", {}).get("path", "data/alerts.db"),
            intraday_expiry_minutes=self.config.get("queues", {}).get("intraday_refresh_minutes", 60),
            swing_expiry_days=self.config.get("queues", {}).get("expiry_days", 10),
        )
        self.alerts = AlertDispatcher(config)
        self.learning = LearningEngine()

    async def run_for_ticker(self, ticker: str) -> List[RoutedSignal]:
        price = await self.data.get_price_snapshot(ticker)
        raw_flows = await self.data.get_options_flow(ticker)
        flows = self.flow_engine.detect(raw_flows)
        greeks = await self.data.get_greeks(ticker)
        gex = greeks.get("gamma", 0)
        vex = abs(greeks.get("vega", 0))
        regime = self.regime_engine.evaluate(price.ohlc or [], gex=gex, vex=vex)
        technical = self.tech_engine.evaluate(ticker, price.ohlc or [], price.volume, price.vwap, price.sector_strength)
        candidates = self.candidate_builder.build(flows, price, regime, technical)
        routed: List[RoutedSignal] = []
        news_items = await self.data.get_news(ticker)
        has_news = bool(news_items)
        for candidate in candidates:
            self.classifier.classify(candidate)
            score = self.scoring.score(candidate, has_news=has_news)
            signal = RoutedSignal(candidate=candidate, score=score, route="pending")
            route = self.routing.route(score, signal)
            if route == "immediate_alert":
                await self.alerts.dispatch(signal)
            self.alert_store.record_signal(signal, metadata={"has_news": has_news})
            routed.append(signal)
        return routed

    async def refresh(self, tickers: Iterable[str]) -> List[RoutedSignal]:
        signals: List[RoutedSignal] = []
        for ticker in tickers:
            try:
                signals.extend(await self.run_for_ticker(ticker))
            except Exception as exc:
                logger.warning(f"Failed to run for ticker {ticker}: {exc}")
        self.routing.refresh_queues()
        self.alert_store.expire_stale()
        self.learning.adjust_weights(self.scoring)
        return signals
