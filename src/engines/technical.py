from __future__ import annotations

from typing import List

from models.schemas import TechnicalContext


class TechnicalEngine:
    def evaluate(self, ticker: str, prices: List[float], volume: float, vwap: float, sector_strength: float) -> TechnicalContext:
        rsi = self._rsi(prices)
        macd, signal = self._macd(prices)
        ema_fast = self._ema(prices, 9)
        ema_mid = self._ema(prices, 20)
        ema_slow = self._ema(prices, 50)
        avg_price = sum(prices[-10:]) / min(len(prices), 10) if prices else 1
        volume_trend = volume / avg_price
        bias = self._bias(prices, ema_fast, ema_mid, ema_slow, vwap)
        return TechnicalContext(
            ticker=ticker,
            rsi=rsi,
            macd=macd,
            macd_signal=signal,
            ema_fast=ema_fast,
            ema_mid=ema_mid,
            ema_slow=ema_slow,
            vwap=vwap,
            volume=volume,
            volume_trend=volume_trend,
            bias=bias,
        )

    def _ema(self, prices: List[float], span: int) -> float:
        if not prices:
            return 0.0
        k = 2 / (span + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = price * k + ema * (1 - k)
        return ema

    def _rsi(self, prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        gains = []
        losses = []
        for i in range(1, len(prices)):
            delta = prices[i] - prices[i - 1]
            if delta >= 0:
                gains.append(delta)
            else:
                losses.append(-delta)
        avg_gain = sum(gains[-period:]) / period if gains else 0
        avg_loss = sum(losses[-period:]) / period if losses else 0
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        return 100 - (100 / (1 + rs)) if rs else 50.0

    def _macd(self, prices: List[float]) -> tuple[float, float]:
        if len(prices) < 35:
            return 0.0, 0.0
        ema12 = self._ema(prices, 12)
        ema26 = self._ema(prices, 26)
        macd = ema12 - ema26
        signal = self._ema([macd] * 9, 9)
        return macd, signal

    def _bias(self, prices: List[float], ema_fast: float, ema_mid: float, ema_slow: float, vwap: float) -> str:
        if not prices:
            return "neutral"
        price = prices[-1]
        bullish = price > ema_fast > ema_mid > ema_slow and price > vwap
        bearish = price < ema_fast < ema_mid < ema_slow and price < vwap
        if bullish:
            return "bullish"
        if bearish:
            return "bearish"
        return "neutral"
