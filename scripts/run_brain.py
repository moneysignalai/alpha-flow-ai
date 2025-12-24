#!/usr/bin/env python
from __future__ import annotations

import asyncio
import os

from core.brain import TradingBrain
from core.config import load_config
from core.logging import get_logger
from core.scheduler import BrainScheduler

logger = get_logger(__name__)


def bootstrap_config():
    config_path = os.getenv("ALPHA_FLOW_CONFIG", "config/settings.yaml")
    return load_config(config_path)


async def main():
    config = bootstrap_config()
    brain = TradingBrain(config)
    tickers = ["AAPL", "MSFT", "TSLA", "NVDA"]

    async def run_once(symbols):
        await brain.refresh(symbols)

    scheduler = BrainScheduler(interval_seconds=config.get("app", {}).get("scheduler_interval_seconds", 300))
    scheduler.start(run_once, tickers)
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        await scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
