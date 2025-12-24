from __future__ import annotations

import asyncio
import json
from urllib import request
from typing import Dict

from core.logging import StructuredAdapter, get_logger
from models.schemas import RoutedSignal

logger = StructuredAdapter(get_logger(__name__), {})


class AlertDispatcher:
    def __init__(self, config: Dict):
        self.config = config or {}
        self.discord_webhook = self.config.get("alerts", {}).get("transports", {}).get("discord", {})

    async def dispatch(self, signal: RoutedSignal):
        tasks = []
        if self.discord_webhook.get("enabled") and self.discord_webhook.get("webhook_url"):
            tasks.append(asyncio.create_task(self._send_discord(signal)))
        if tasks:
            await asyncio.gather(*tasks)

    async def _send_discord(self, signal: RoutedSignal):
        payload = json.dumps({"content": self._format_signal(signal)}).encode()
        req = request.Request(self.discord_webhook.get("webhook_url"), data=payload, headers={"Content-Type": "application/json"})
        try:
            await asyncio.to_thread(request.urlopen, req, timeout=5)
            logger.info("Sent discord alert", extra={"ticker": signal.candidate.ticker, "route": signal.route})
        except Exception as exc:  # pragma: no cover - network best effort
            logger.warning(f"Failed to send discord alert: {exc}")

    def _format_signal(self, signal: RoutedSignal) -> str:
        c = signal.candidate
        return (
            f"[{signal.route.upper()}] {c.ticker} {c.flow.direction.value.upper()} | "
            f"Score: {signal.score.score} ({signal.score.grade})\n"
            f"Why: {signal.score.reasoning}\n"
            f"Time: {signal.created_at.isoformat()} | Expiry: {c.flow.expiry.date()}\n"
            f"Risk: {c.regime.risk_environment} | Anomaly: vol x{c.flow.volume_multiple:.2f}"
        )
