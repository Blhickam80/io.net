"""Market Selection Filter: reject low-quality markets before any
probability/EV analysis is performed, and compute market-implied
probabilities and spreads for the ones that pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .config import (
    MAX_SPREAD,
    MIN_24H_VOLUME_USD,
    MIN_HOURS_TO_RESOLUTION,
    MIN_LIQUIDITY_USD,
)


@dataclass
class ScreenedMarket:
    market_id: str
    question: str
    yes_price: float
    no_price: float
    spread: float
    liquidity_usd: float
    volume_24h_usd: float
    hours_to_resolution: float
    end_date: str
    rejected: bool
    rejection_reasons: list[str]


def hours_until(end_date_iso: str) -> float:
    end = datetime.fromisoformat(end_date_iso.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return (end - now).total_seconds() / 3600.0


def screen_market(raw: dict) -> ScreenedMarket:
    """Apply the mandatory MARKET SELECTION FILTER to one raw Gamma-API
    market record. Does not reject on soft signals (news, base rates,
    smart-money) -- those feed the probability estimate, not this gate.
    """
    reasons: list[str] = []

    try:
        outcome_prices = raw.get("outcomePrices")
        if isinstance(outcome_prices, str):
            import json

            outcome_prices = json.loads(outcome_prices)
        yes_price = float(outcome_prices[0])
        no_price = float(outcome_prices[1]) if len(outcome_prices) > 1 else 1 - yes_price
    except (TypeError, ValueError, IndexError, KeyError):
        yes_price, no_price = 0.5, 0.5
        reasons.append("Could not parse outcome prices.")

    spread = float(raw.get("spread") or abs(1 - (yes_price + no_price)))
    liquidity = float(raw.get("liquidityNum") or raw.get("liquidity") or 0.0)
    volume_24h = float(raw.get("volume24hr") or 0.0)
    end_date = raw.get("endDate") or ""

    try:
        hours_left = hours_until(end_date) if end_date else -1.0
    except ValueError:
        hours_left = -1.0
        reasons.append("Unparseable endDate.")

    if liquidity < MIN_LIQUIDITY_USD:
        reasons.append(f"Liquidity ${liquidity:,.0f} < minimum ${MIN_LIQUIDITY_USD:,.0f}.")
    if volume_24h < MIN_24H_VOLUME_USD:
        reasons.append(f"24h volume ${volume_24h:,.0f} < minimum ${MIN_24H_VOLUME_USD:,.0f}.")
    if spread > MAX_SPREAD:
        reasons.append(f"Spread {spread:.2%} > maximum {MAX_SPREAD:.2%}.")
    if hours_left < MIN_HOURS_TO_RESOLUTION:
        reasons.append(
            f"Only {hours_left:.1f}h to resolution (minimum {MIN_HOURS_TO_RESOLUTION}h)."
        )
    if raw.get("umaResolutionStatus") in {"disputed", "flagged"}:
        reasons.append("Resolution is disputed/flagged.")
    # Defense in depth: reject closed/non-tradeable markets even if the
    # caller forgot to filter them out upstream. Confirmed live (2026-08-20)
    # that Gamma's /events endpoint happily returns closed, zero-liquidity,
    # already-resolved market instances alongside the live one for the same
    # question text -- trusting active/closed here, not just liquidity
    # numbers, avoids mistaking a dead market's terminal 1.0/0.0 price for a
    # tradeable opportunity.
    if raw.get("closed") is True:
        reasons.append("Market is closed.")
    if raw.get("acceptingOrders") is False:
        reasons.append("Market is not accepting orders.")

    return ScreenedMarket(
        market_id=str(raw.get("id") or raw.get("conditionId") or raw.get("slug") or ""),
        question=raw.get("question", "?"),
        yes_price=yes_price,
        no_price=no_price,
        spread=spread,
        liquidity_usd=liquidity,
        volume_24h_usd=volume_24h,
        hours_to_resolution=hours_left,
        end_date=end_date,
        rejected=len(reasons) > 0,
        rejection_reasons=reasons,
    )


def screen_markets(raw_markets: list[dict]) -> list[ScreenedMarket]:
    return [screen_market(m) for m in raw_markets]


def passing_markets(raw_markets: list[dict]) -> list[ScreenedMarket]:
    return [m for m in screen_markets(raw_markets) if not m.rejected]
