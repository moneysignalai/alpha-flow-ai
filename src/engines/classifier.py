from __future__ import annotations

from models.schemas import Candidate


class ClassificationEngine:
    def classify(self, candidate: Candidate) -> str:
        flow = candidate.flow
        tech = candidate.technical
        regime = candidate.regime

        if abs(candidate.price.change_pct) > 3 and candidate.price.ticker in {candidate.flow.ticker}:
            label = "breakout" if candidate.price.change_pct > 0 else "breakdown"
        elif tech.bias == "bullish" and flow.direction.value == "call":
            label = "momentum"
        elif tech.bias == "bearish" and flow.direction.value == "put":
            label = "momentum"
        elif abs(tech.rsi - 50) < 5:
            label = "reversal"
        elif "earnings" in " ".join(candidate.flow.raw.keys()).lower():
            label = "pre-earnings"
        elif abs(regime.gex) > abs(regime.vex):
            label = "gamma"
        else:
            label = "structural"
        candidate.classification = label
        return label
