from __future__ import annotations

from models.schemas import Candidate, ScoreResult


class ScoringEngine:
    def __init__(self):
        self.weights = {
            "flow": 0.4,
            "technical": 0.25,
            "regime": 0.2,
            "news": 0.15,
        }

    def score(self, candidate: Candidate, has_news: bool = False) -> ScoreResult:
        flow_score = min(candidate.flow.conviction_score / 5, 1)
        tech_score = self._tech_score(candidate)
        regime_score = 1 - min(candidate.regime.volatility, 1)
        news_score = 1.0 if has_news else 0.4

        raw = (
            flow_score * self.weights["flow"]
            + tech_score * self.weights["technical"]
            + regime_score * self.weights["regime"]
            + news_score * self.weights["news"]
        )
        score = round(raw * 100, 2)
        grade = self._grade(score)
        reasoning = f"flow={flow_score:.2f} tech={tech_score:.2f} regime={regime_score:.2f} news={news_score:.2f}"
        return ScoreResult(score=score, grade=grade, reasoning=reasoning)

    def _tech_score(self, candidate: Candidate) -> float:
        rsi_score = 1 - abs(candidate.technical.rsi - 50) / 50
        macd_trend = 1 if candidate.technical.macd > candidate.technical.macd_signal else 0.3
        bias_score = 1 if candidate.technical.bias == "bullish" and candidate.flow.direction.value == "call" else 0.8
        return max(0, min((rsi_score * 0.4 + macd_trend * 0.3 + bias_score * 0.3), 1))

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 85:
            return "A"
        if score >= 65:
            return "B"
        if score >= 50:
            return "C"
        return "D"
