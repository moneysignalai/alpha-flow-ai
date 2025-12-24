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
        candidate.total_score = score
        candidate.grade = grade
        candidate.flow_score = round(flow_score * 40, 1)
        candidate.technical_score = round(tech_score * 30, 1)
        candidate.regime_score = round(regime_score * 20, 1)
        candidate.catalyst_score = round(news_score * 10, 1)
        candidate.execution_quality_score = candidate.execution_quality_score or round(tech_score * 100, 1)
        candidate.gex_sign = candidate.gex_sign or ("pos" if candidate.regime.gex >= 0 else "neg")
        candidate.gex_magnitude = candidate.gex_magnitude or abs(candidate.regime.gex)
        candidate.vex_state = candidate.vex_state or ("elevated" if candidate.regime.vex > 0.2 else "normal")
        candidate.rsi_intraday = candidate.rsi_intraday or candidate.technical.rsi
        candidate.rsi_daily = candidate.rsi_daily or candidate.technical.rsi
        candidate.price_vs_vwap = candidate.price_vs_vwap or ("above" if candidate.price.price >= candidate.price.vwap else "below")
        candidate.price_vs_ema9 = candidate.price_vs_ema9 or ("above" if candidate.price.price >= candidate.technical.ema_fast else "below")
        candidate.price_vs_ema20 = candidate.price_vs_ema20 or ("above" if candidate.price.price >= candidate.technical.ema_mid else "below")
        candidate.intraday_trend = candidate.intraday_trend or candidate.technical.bias
        candidate.daily_trend = candidate.daily_trend or candidate.regime.trend_bias
        candidate.flow_pattern = candidate.flow_pattern or ("sweep" if candidate.flow.is_sweep else "block" if candidate.flow.is_block else "mixed")
        candidate.time_horizon = candidate.time_horizon or "unknown"
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
