from __future__ import annotations

from typing import Optional

from core.config import ALERT_STYLE, AlertStyle
from models.schemas import Candidate


def _fmt_price(value: Optional[float]) -> str:
    return f"{value:.2f}" if value is not None else "n/a"


def _fmt_int(value: Optional[int]) -> str:
    return f"{value:,}" if value is not None else "n/a"


def _fmt_number(value: Optional[float]) -> str:
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "n/a"


def _safe(value, fallback="n/a"):
    return value if value not in (None, "") else fallback


def _side(candidate: Candidate) -> str:
    return (candidate.primary_side or candidate.flow.side or "").upper() or "n/a"


def format_short_alert(candidate: Candidate, alert_type: str) -> str:
    """
    Very compact alert for power users. One screen, no fluff.
    """
    c = candidate
    side = _side(c)
    return (
        f"🦈 {c.symbol or c.ticker} {side} ALERT ({c.grade or 'n/a'})\n"
        f"Contract: {c.primary_strike or c.flow.strike}{side[:1]} {c.primary_expiry or c.flow.expiry.date()} ({c.primary_dte or c.flow.dte}D)\n"
        f"Opt: {c.primary_option_symbol or c.flow.option_symbol}\n"
        f"Last: {_fmt_price(c.primary_last_price or c.flow.last_price)}  Bid/Ask: {_fmt_price(c.primary_bid or c.flow.bid)} x {_fmt_price(c.primary_ask or c.flow.ask)}\n"
        f"Vol/OI: {_fmt_int(c.primary_volume or c.flow.volume)} / {_fmt_int(c.primary_open_interest or c.flow.open_interest)}\n"
        f"Flow Notional: ${_fmt_number(c.primary_notional or c.flow.notional)}\n"
        f"Conf: {int(c.total_score or 0)}%  Timeframe: {_safe(c.time_horizon, alert_type)}"
    )


def format_medium_alert(candidate: Candidate, alert_type: str) -> str:
    """
    Default style: readable explanation, still concise.
    """
    c = candidate
    side = _side(c)

    lines = [
        f"🦈 AI Trade Signal — {c.grade or 'n/a'}",
        "",
        f"Underlying: {c.symbol or c.ticker}",
        f"Direction: {side} ({(c.direction or c.flow.direction.value).title()} Bias)",
        f"Confidence: {int(c.total_score or 0)}% | Timeframe: {_safe(c.time_horizon, alert_type)}",
        "",
        "Options Contract:",
        f"• Contract: {c.primary_strike or c.flow.strike}{side[:1]} {c.primary_expiry or c.flow.expiry.date()} ({c.primary_dte or c.flow.dte}D)",
        f"• Option Symbol: {c.primary_option_symbol or c.flow.option_symbol}",
        f"• Last: {_fmt_price(c.primary_last_price or c.flow.last_price)}   Bid/Ask: {_fmt_price(c.primary_bid or c.flow.bid)} x {_fmt_price(c.primary_ask or c.flow.ask)}",
        f"• Volume: {_fmt_int(c.primary_volume or c.flow.volume)}   OI: {_fmt_int(c.primary_open_interest or c.flow.open_interest)}",
        f"• Flow Notional: ${_fmt_number(c.primary_notional or c.flow.notional)}",
        "",
        "Why This Matters:",
        f"• Flow: {(c.flow_score or 0):.1f} score (size/structure quality)",
        f"• Technicals: {(c.technical_score or 0):.1f} score (trend/levels/momentum)",
        f"• Regime/Catalyst: {((c.regime_score or 0) + (c.catalyst_score or 0)):.1f} combined",
    ]

    if getattr(c, "anomaly_flag", False):
        lines.append(f"• Anomaly: rare pattern detected (strength {(c.anomaly_strength or 0):.0f}/100)")

    lines.append("")
    lines.append("Execution Notes:")
    if (c.execution_quality_score or 0) < 40:
        lines.append("• Caution: execution risk (spreads/liquidity) — size carefully.")
    else:
        lines.append("• Execution-friendly: liquidity and spreads acceptable.")

    return "\n".join(lines)


def format_deep_dive_alert(candidate: Candidate, alert_type: str) -> str:
    """
    Deep-dive explanation for users who want full context and reasoning.
    Longer-form, narrative style.
    """
    c = candidate
    side = _side(c)

    lines = [
        "🧠 AI Deep-Dive Trade Signal",
        f"Ticker: {c.symbol or c.ticker}",
        f"Direction: {side} ({(c.direction or c.flow.direction.value).title()} setup)",
        f"Grade: {c.grade or 'n/a'} | Confidence: {int(c.total_score or 0)}% | Timeframe: {_safe(c.time_horizon, alert_type)}",
        "",
        "Options Contract Details:",
        f"• Contract: {c.primary_strike or c.flow.strike}{side[:1]} {c.primary_expiry or c.flow.expiry.date()} ({c.primary_dte or c.flow.dte} days to expiry)",
        f"• Option Symbol: {c.primary_option_symbol or c.flow.option_symbol}",
        f"• Last: {_fmt_price(c.primary_last_price or c.flow.last_price)}   Bid/Ask: {_fmt_price(c.primary_bid or c.flow.bid)} x {_fmt_price(c.primary_ask or c.flow.ask)}",
        f"• Volume: {_fmt_int(c.primary_volume or c.flow.volume)}   Open Interest: {_fmt_int(c.primary_open_interest or c.flow.open_interest)}",
        f"• Flow Notional Driving Setup: ${_fmt_number(c.primary_notional or c.flow.notional)}",
        "",
        "Flow & Smart Money Behavior:",
        f"• Flow Strength Score: {(c.flow_score or 0):.1f}/40",
        f"• Pattern: {_safe(c.flow_pattern, 'structure n/a')} (e.g. sweeps vs blocks, clustering)",
        "",
        "Price Action & Technical Context:",
        f"• Intraday Trend: {_safe(c.intraday_trend, 'n/a')} | Daily Trend: {_safe(c.daily_trend, 'n/a')}",
        f"• Price vs VWAP: {_safe(c.price_vs_vwap, 'n/a')} | vs EMA9/20: {_safe(c.price_vs_ema9, 'n/a')}/{_safe(c.price_vs_ema20, 'n/a')}",
        f"• RSI: intraday {(c.rsi_intraday or 0):.1f} | daily {(c.rsi_daily or 0):.1f}",
        f"• Technical Score: {(c.technical_score or 0):.1f}/30",
        "",
        "Market Regime & Structure:",
        f"• GEX: {_safe(c.gex_sign, 'n/a')} ({(c.gex_magnitude or 0):.2f} gamma) | VEX: {_safe(c.vex_state, 'n/a')}",
        f"• Regime Score: {(c.regime_score or 0):.1f}/20",
        "",
        "Catalyst & Context:",
        f"• Event Type: {_safe(c.event_type, 'n/a')} | hasUpcomingEvent={_safe(c.has_upcoming_event, False)} | daysToEvent={_safe(c.days_to_event, 'n/a')}",
        f"• Catalyst Score: {(c.catalyst_score or 0):.1f}/10",
        "",
        "Sector & Correlation:",
        f"• Sector Alignment: {(c.sector_alignment_score or 0):.1f}",
        f"• ETF / Cohort Support: {(c.etf_alignment_score or 0):.1f}",
        "",
        "Execution & Risk:",
        f"• Execution Quality Score: {(c.execution_quality_score or 0):.1f}",
    ]

    if c.avoid_trade_reason:
        lines.append(f"• Caution Flag: {c.avoid_trade_reason}")

    if getattr(c, "anomaly_flag", False):
        lines.append(f"• Rare/Anomaly Signal: strength {(c.anomaly_strength or 0):.0f}/100")

    lines.append("")
    lines.append("AI Summary (Plain English):")
    lines.append(c.summary_text or "AI summary not generated yet, but scores indicate a structured, data-backed setup.")

    return "\n".join(lines)


def format_alert(candidate: Candidate, alert_type: str, style: AlertStyle | None = None) -> str:
    if style is None:
        style = ALERT_STYLE
    try:
        style = AlertStyle(style)
    except Exception:
        style = ALERT_STYLE

    if style == AlertStyle.SHORT:
        return format_short_alert(candidate, alert_type)
    if style == AlertStyle.MEDIUM:
        return format_medium_alert(candidate, alert_type)
    if style == AlertStyle.DEEP_DIVE:
        return format_deep_dive_alert(candidate, alert_type)
    return format_medium_alert(candidate, alert_type)
