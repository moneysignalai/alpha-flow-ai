from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List

from core.logging import get_logger

logger = get_logger(__name__)


class ProviderError(Exception):
    pass


class BaseProvider:
    async def fetch(self, *args, **kwargs):
        raise NotImplementedError


class PolygonProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def fetch_ohlc(self, ticker: str, lookback: int = 50) -> List[float]:
        base = random.uniform(80, 150)
        series = []
        price = base
        for _ in range(lookback):
            price += random.uniform(-1, 1)
            series.append(round(price, 2))
        return series

    async def fetch_greeks(self, ticker: str) -> Dict[str, float]:
        return {"delta": random.uniform(-1, 1), "gamma": random.uniform(-1, 1), "vega": random.uniform(0, 1)}


class BenzingaProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def latest_news(self, ticker: str) -> List[Dict]:
        now = datetime.utcnow()
        return [
            {"ticker": ticker, "headline": f"{ticker} beats estimates", "timestamp": now - timedelta(minutes=15)},
            {"ticker": ticker, "headline": f"{ticker} announces guidance", "timestamp": now - timedelta(hours=2)},
        ]


class MassiveProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def options_flow(self, ticker: str) -> List[Dict]:
        now = datetime.utcnow()
        flows = []
        for _ in range(random.randint(3, 8)):
            premium = random.uniform(250_000, 2_000_000)
            flows.append(
                {
                    "ticker": ticker,
                    "direction": random.choice(["call", "put"]),
                    "notional": premium * random.uniform(3, 6),
                    "premium": premium,
                    "iv": random.uniform(0.25, 0.9),
                    "expiry": now + timedelta(days=random.randint(5, 45)),
                    "strike": random.uniform(0.8, 1.2) * random.uniform(80, 120),
                    "spot": random.uniform(80, 120),
                    "volume_multiple": random.uniform(1.5, 10),
                    "is_sweep": random.choice([True, False]),
                    "is_block": random.choice([True, False]),
                }
            )
        return flows


async def with_retry(coro, attempts: int = 3, base_delay: float = 0.1):
    for i in range(attempts):
        try:
            return await coro
        except Exception as exc:  # pragma: no cover - defensive
            if i == attempts - 1:
                raise
            await asyncio.sleep(base_delay * (2**i))
