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
        primary_symbol = c.primary_option_symbol or c.flow.option_symbol
        primary_expiry = c.primary_expiry or c.flow.expiry.date()
        contract_line = (
            f"Options Contract:\n"
            f"• Contract: {self._fmt_contract_side(c.primary_side or c.flow.side)} "
            f"{self._fmt_number(c.primary_strike or c.flow.strike)} {primary_expiry} "
            f"({self._fmt_int(c.primary_dte or c.flow.dte)}D)\n"
            f"• Option Symbol: {primary_symbol or 'n/a'}\n"
            f"• Last: {self._fmt_price(c.primary_last_price or c.flow.last_price)}   "
            f"Bid/Ask: {self._fmt_price(c.primary_bid or c.flow.bid)} x {self._fmt_price(c.primary_ask or c.flow.ask)}\n"
            f"• Volume: {self._fmt_int(c.primary_volume or c.flow.volume)}   "
            f"OI: {self._fmt_int(c.primary_open_interest or c.flow.open_interest)}\n"
            f"• Flow Notional (headline trade): ${self._fmt_number(c.primary_notional or c.flow.notional)}"
        )

        return (
            f"🦈 AI Trade Signal — {signal.score.grade}\n"
            f"Ticker: {c.ticker}\n"
            f"Direction: {c.flow.direction.value.upper()}\n"
            f"Confidence: {signal.score.score}% | Grade: {signal.score.grade}\n"
            f"Time: {signal.created_at.isoformat()} | Expiry: {primary_expiry}\n"
            f"\n{contract_line}\n\n"
            f"Reasoning:\n{signal.score.reasoning}\n"
            f"Risk: {c.regime.risk_environment} | Anomaly: vol x{c.flow.volume_multiple:.2f}"
        )

    @staticmethod
    def _fmt_price(value):
        return f"{value:.2f}" if value is not None else "n/a"

    @staticmethod
    def _fmt_int(value):
        return f"{value:,}" if value is not None else "n/a"

    @staticmethod
    def _fmt_number(value):
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return "n/a"

    @staticmethod
    def _fmt_contract_side(side: str) -> str:
        return side.upper() if side else "n/a"
