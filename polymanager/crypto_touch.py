"""Generic barrier-touch pricing for "Will <Asset> reach $X in <month>?"
Polymarket markets -- the shared engine behind polymanager.btc_touch and
polymanager.eth_touch.

Each asset gets its OWN CONFIDENCE_CAP because each asset's backtest result
is different (see polymanager.backtest run against each asset's own price
history) -- BTC's calibration finding does not transfer to ETH or any other
asset, and this module never assumes it does. Callers must pass an
explicit confidence_cap; there is no shared default.

See polymanager.btc_touch's module docstring for the full explanation of
the zero-drift assumption, why it isn't unconditionally conservative, and
why a per-asset backtest is required before trusting this above
experimental sizing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from .models import touch_probability_upper_barrier


@dataclass
class CryptoTouchEstimate:
    p_true: float
    confidence: int
    evidence: str


def make_pattern(asset_name: str) -> re.Pattern:
    return re.compile(rf"will\s+{re.escape(asset_name)}\s+reach\s+\$?([\d,]+)", re.IGNORECASE)


def extract_barrier(question: str, pattern: re.Pattern) -> float | None:
    m = pattern.search(question)
    if not m:
        return None
    return float(m.group(1).replace(",", ""))


def estimate_for_asset(
    question: str,
    end_date_iso: str,
    *,
    asset_name: str,
    spot: float,
    vol_60d: float,
    confidence_cap: int,
    calibration_note: str,
) -> CryptoTouchEstimate | None:
    """Price one market given an already-fetched spot price and realized
    volatility for `asset_name`. `confidence_cap` and `calibration_note`
    must come from that asset's own backtest -- see btc_touch.py/eth_touch.py.
    """
    pattern = make_pattern(asset_name)
    barrier = extract_barrier(question, pattern)
    if barrier is None:
        return None

    end = datetime.fromisoformat(end_date_iso.replace("Z", "+00:00"))
    days_remaining = max(0.0, (end - datetime.now(timezone.utc)).total_seconds() / 86400.0)

    p_model = touch_probability_upper_barrier(spot, barrier, vol_60d, days_remaining)

    # Confidence reflects model/vol-regime uncertainty, not just edge size:
    # re-price at 1.5x realized vol and see how much the estimate moves. A
    # big swing under a plausible alternate vol assumption means the point
    # estimate is fragile, so confidence should be lower even if the
    # nominal edge looks large.
    p_model_high_vol = touch_probability_upper_barrier(spot, barrier, vol_60d * 1.5, days_remaining)
    spread = abs(p_model_high_vol - p_model)
    if spread < 0.05:
        confidence = 7
    elif spread < 0.15:
        confidence = 6
    else:
        confidence = 5
    confidence = min(confidence, confidence_cap)

    evidence = (
        f"Barrier-touch model (zero-drift GBM): spot=${spot:,.0f}, barrier=${barrier:,.0f}, "
        f"60d realized daily vol={vol_60d:.2%}, {days_remaining:.1f} days remaining -> "
        f"model P(touch)={p_model:.1%} (vs {p_model_high_vol:.1%} at 1.5x vol). "
        f"Confidence capped at {confidence_cap}/10: {calibration_note}"
    )
    return CryptoTouchEstimate(p_true=p_model, confidence=confidence, evidence=evidence)
