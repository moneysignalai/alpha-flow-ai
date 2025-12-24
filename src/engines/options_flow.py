from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from core.logging import get_logger
from models.schemas import Direction, FlowEvent

logger = get_logger(__name__)


class OptionsFlowEngine:
    def __init__(self, min_premium: float = 250_000, min_volume_multiple: float = 2.0):
        self.min_premium = min_premium
        self.min_volume_multiple = min_volume_multiple

    def detect(self, raw_flows: Iterable[dict]) -> List[FlowEvent]:
        events: List[FlowEvent] = []
        for flow in raw_flows:
            if flow.get("premium", 0) < self.min_premium:
                continue
            if flow.get("volume_multiple", 0) < self.min_volume_multiple:
                continue
            expiry = flow.get("expiry")
            if isinstance(expiry, str):
                expiry = datetime.fromisoformat(expiry)
            direction = Direction.CALL if flow.get("direction") == "call" else Direction.PUT
            conviction = self._conviction(flow)
            expiry_horizon = expiry - datetime.utcnow()
            dte = max(int(expiry_horizon.days), 0)
            event = FlowEvent(
                ticker=flow.get("ticker"),
                direction=direction,
                notional=float(flow.get("notional")),
                premium=float(flow.get("premium")),
                iv=float(flow.get("iv")),
                expiry_horizon=expiry_horizon,
                dte=dte,
                conviction_score=conviction,
                spot_price=float(flow.get("spot")),
                strike=float(flow.get("strike")),
                expiry=expiry,
                option_symbol=flow.get("option_symbol") or flow.get("optionSymbol") or "",
                side=(flow.get("side") or direction.value).upper(),
                last_price=self._safe_float(flow.get("last_price")),
                bid=self._safe_float(flow.get("bid")),
                ask=self._safe_float(flow.get("ask")),
                volume=self._safe_int(flow.get("volume")),
                open_interest=self._safe_int(flow.get("open_interest")),
                volume_multiple=float(flow.get("volume_multiple")),
                is_sweep=bool(flow.get("is_sweep", False)),
                is_block=bool(flow.get("is_block", False)),
                raw=flow,
            )
            events.append(event)
        return sorted(events, key=lambda e: e.conviction_score, reverse=True)

    def _conviction(self, flow: dict) -> float:
        weight = 0
        weight += min(flow.get("premium", 0) / 1_000_000, 3)
        weight += 1.5 if flow.get("is_sweep") else 0
        weight += 1.0 if flow.get("is_block") else 0
        weight += min(flow.get("volume_multiple", 1), 3)
        return weight

    @staticmethod
    def _safe_float(value):
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value):
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None
