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
        transports = self.config.get("alerts", {}).get("transports", {})
        self.telegram_cfg = transports.get("telegram", {})
        self.discord_webhook = transports.get("discord", {})

    async def dispatch(self, signal: RoutedSignal):
        tasks = []
        if self.telegram_cfg.get("enabled"):
            tasks.append(asyncio.create_task(self._send_telegram(signal)))
        if self.discord_webhook.get("enabled") and self.discord_webhook.get("webhook_url"):
            tasks.append(asyncio.create_task(self._send_discord(signal)))
        if tasks:
            await asyncio.gather(*tasks)

    async def _send_telegram(self, signal: RoutedSignal):
        bot_token = self.telegram_cfg.get("bot_token")
        chat_id = self.telegram_cfg.get("chat_id")
        if not bot_token or not chat_id:
            logger.warning("Telegram transport missing bot_token or chat_id; skipping")
            return
        message = self._format_signal(signal)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": message})
        req = request.Request(url, data=payload.encode(), headers={"Content-Type": "application/json"})
        try:
            await asyncio.to_thread(request.urlopen, req, timeout=5)
            logger.info("Sent telegram alert", extra={"ticker": signal.candidate.ticker, "route": signal.route})
        except Exception as exc:  # pragma: no cover - network best effort
            logger.warning(f"Failed to send telegram alert: {exc}")

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
