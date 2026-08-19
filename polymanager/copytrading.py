"""Trader Quality Score for copy-trading / smart-money analysis.

Deliberately does not just rank by realized P/L: a whale who got lucky once
scores worse here than a smaller trader with a long, consistent track record.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TraderStats:
    address: str
    roi_pct: float
    realized_pnl_usd: float
    markets_traded: int
    win_rate_pct: float
    avg_position_usd: float
    max_drawdown_pct: float
    specialty: str = "unspecified"
    largest_single_win_pct_of_pnl: float = 0.0  # what share of total P/L came from one trade
    avg_entry_vs_final_price_gap: float = 0.0  # proxy for "enters early" (bigger gap = earlier)


def trader_quality_score(t: TraderStats) -> float:
    """Composite 0-100 score. Weights repeatability over raw size.

    Components (weights sum to 100):
      - sample size (markets traded):      20
      - win rate:                          20
      - ROI:                               20
      - low reliance on one lucky trade:   20 (penalizes concentration)
      - low max drawdown:                  10
      - "enters early" proxy:              10
    """
    # Sample size: log-scaled, saturates around 100+ markets.
    import math

    sample_component = min(20.0, 20.0 * math.log10(max(1, t.markets_traded) + 1) / math.log10(101))

    win_rate_component = 20.0 * max(0.0, min(1.0, t.win_rate_pct / 100.0))

    # ROI: saturates at 100% ROI for full credit; negative ROI scores zero.
    roi_component = 20.0 * max(0.0, min(1.0, t.roi_pct / 100.0))

    # Penalize when most P/L is one trade -- that's variance, not skill.
    concentration_penalty = max(0.0, min(1.0, t.largest_single_win_pct_of_pnl / 100.0))
    consistency_component = 20.0 * (1.0 - concentration_penalty)

    drawdown_component = 10.0 * max(0.0, 1.0 - min(1.0, t.max_drawdown_pct / 100.0))

    earliness_component = 10.0 * max(0.0, min(1.0, t.avg_entry_vs_final_price_gap))

    score = (
        sample_component
        + win_rate_component
        + roi_component
        + consistency_component
        + drawdown_component
        + earliness_component
    )
    return round(score, 1)


def classify_trader_type(t: TraderStats) -> str:
    if t.avg_position_usd > 5000:
        return "whale"
    if t.markets_traded > 50 and t.win_rate_pct > 60 and t.max_drawdown_pct < 20:
        return f"{t.specialty} specialist"
    if t.avg_entry_vs_final_price_gap > 0.5:
        return "breaking-news trader"
    if t.markets_traded < 10:
        return "insufficient sample -- do not weight"
    return "unclassified"


def rank_traders(traders: list[TraderStats]) -> list[dict]:
    ranked = [
        {
            "address": t.address,
            "quality_score": trader_quality_score(t),
            "type": classify_trader_type(t),
            "stats": t,
        }
        for t in traders
    ]
    ranked.sort(key=lambda r: r["quality_score"], reverse=True)
    return ranked
