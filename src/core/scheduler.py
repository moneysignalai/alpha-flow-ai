from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Iterable

from core.logging import StructuredAdapter, get_logger

logger = StructuredAdapter(get_logger(__name__), {})


class BrainScheduler:
    def __init__(self, interval_seconds: int = 300):
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None

    def start(self, coro: Callable[[Iterable[str]], Awaitable], tickers: Iterable[str]):
        if self._task and not self._task.done():
            return

        async def _runner():
            while True:
                await coro(tickers)
                await asyncio.sleep(self.interval_seconds)

        self._task = asyncio.create_task(_runner())
        logger.info("Scheduler started", extra={"interval": self.interval_seconds})

    async def shutdown(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:  # pragma: no cover - expected path
                pass
        logger.info("Scheduler stopped")
