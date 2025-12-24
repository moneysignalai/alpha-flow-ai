from __future__ import annotations

import asyncio
import json
from urllib import request
from typing import Dict

from core.logging import StructuredAdapter, get_logger
from core.config import ALERT_STYLE, AlertStyle
from models.schemas import RoutedSignal
from alerts.templates import format_alert

logger = StructuredAdapter(get_logger(__name__), {})


class AlertDispatcher:
    def __init__(self, config: Dict):
        self.config = config or {}
        transports = self.config.get("alerts", {}).get("transports", {})
        self.telegram_cfg = transports.get("telegram", {})
        self.discord_webhook = transports.get("discord", {})
        style_value = self.config.get("alerts", {}).get("style") or ALERT_STYLE
        try:
            self.alert_style = AlertStyle(style_value)
        except Exception:
            self.alert_style = ALERT_STYLE

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
        candidate = signal.candidate
        candidate.grade = candidate.grade or signal.score.grade
        candidate.total_score = candidate.total_score or signal.score.score
        candidate.time_horizon = candidate.time_horizon or signal.route
        return format_alert(candidate, alert_type=signal.route, style=self.alert_style)
