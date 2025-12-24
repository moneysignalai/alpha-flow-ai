from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from core.logging import get_logger
from data.providers import BenzingaProvider, MassivePolygonProvider, with_retry
from models.schemas import PriceSnapshot

logger = get_logger(__name__)


class TTLCache:
    def __init__(self, ttl_seconds: int = 120):
        self.ttl = ttl_seconds
        self.store: Dict[str, tuple[datetime, object]] = {}

    def get(self, key: str):
        if key in self.store:
            ts, value = self.store[key]
            if (datetime.utcnow() - ts).total_seconds() < self.ttl:
                return value
            self.store.pop(key, None)
        return None

    def set(self, key: str, value: object):
        self.store[key] = (datetime.utcnow(), value)


class DataService:
    def __init__(self, market_data_key: str, benzinga_key: str, cache_ttl_seconds: int = 120):
        self.market = MassivePolygonProvider(market_data_key)
        self.benzinga = BenzingaProvider(benzinga_key)
        self.cache = TTLCache(cache_ttl_seconds)

    async def get_price_snapshot(self, ticker: str) -> PriceSnapshot:
        cache_key = f"price:{ticker}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        series = await with_retry(self.market.fetch_ohlc(ticker))
        price = float(series[-1])
        prev = series[-2] if len(series) > 1 else series[-1]
        change_pct = float((price - prev) / prev * 100) if prev else 0
        volume = abs(price * 10_000)
        vwap = sum(series[-20:]) / min(len(series), 20)
        sector_strength = 0.0
        snapshot = PriceSnapshot(
            ticker=ticker,
            price=price,
            change_pct=change_pct,
            volume=volume,
            vwap=vwap,
            sector_strength=sector_strength,
            ohlc=series[-50:],
        )
        self.cache.set(cache_key, snapshot)
        return snapshot

    async def get_greeks(self, ticker: str) -> Dict[str, float]:
        cache_key = f"greeks:{ticker}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        greeks = await with_retry(self.market.fetch_greeks(ticker))
        self.cache.set(cache_key, greeks)
        return greeks

    async def get_options_flow(self, ticker: str):
        return await with_retry(self.market.options_flow(ticker))

    async def get_news(self, ticker: str):
        return await with_retry(self.benzinga.latest_news(ticker))
