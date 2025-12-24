from __future__ import annotations

from typing import List

from core.logging import get_logger
from models.schemas import Candidate, FlowEvent, MarketRegimeState, PriceSnapshot, TechnicalContext

logger = get_logger(__name__)


class CandidateBuilder:
    def build(self, flows: List[FlowEvent], price: PriceSnapshot, regime: MarketRegimeState, technical: TechnicalContext) -> List[Candidate]:
        candidates: List[Candidate] = []
        for flow in flows:
            if flow.ticker != price.ticker:
                continue
            candidate = Candidate(
                ticker=flow.ticker,
                flow=flow,
                price=price,
                regime=regime,
                technical=technical,
            )
            candidates.append(candidate)
        return candidates
