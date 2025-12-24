from __future__ import annotations

from typing import List

from core.logging import get_logger
from models.schemas import Candidate, FlowEvent, MarketRegimeState, PriceSnapshot, TechnicalContext

logger = get_logger(__name__)


class CandidateBuilder:
    def build(self, flows: List[FlowEvent], price: PriceSnapshot, regime: MarketRegimeState, technical: TechnicalContext) -> List[Candidate]:
        ticker_flows = [f for f in flows if f.ticker == price.ticker]
        if not ticker_flows:
            return []

        primary = max(ticker_flows, key=lambda f: f.notional)
        candidate = Candidate(
            ticker=primary.ticker,
            symbol=primary.ticker,
            flow=primary,
            price=price,
            regime=regime,
            technical=technical,
            direction=primary.direction.value,
            primary_option_symbol=primary.option_symbol,
            primary_expiry=primary.expiry.date(),
            primary_strike=primary.strike,
            primary_side=primary.side,
            primary_dte=primary.dte,
            primary_last_price=primary.last_price,
            primary_bid=primary.bid,
            primary_ask=primary.ask,
            primary_volume=primary.volume,
            primary_open_interest=primary.open_interest,
            primary_notional=primary.notional,
        )
        return [candidate]
