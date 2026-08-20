"""Strategy: barrier-touch pricing for "Will Bitcoin reach $X in <month>?"
Polymarket markets.

These resolve YES if BTC/USDT ever trades at or above $X on Binance during
the stated window -- a textbook barrier option, not a narrative bet. This
module detects that market shape, pulls live BTC spot price and realized
volatility from CoinGecko, prices the barrier with
polymanager.models.touch_probability_upper_barrier, and compares that model
probability to the market's own price. This is Strategy A/E from the
mandate (mispricing / near-resolution convergence) applied to one specific,
well-defined family where real math beats narrative.

Deliberately conservative: the model assumes zero price drift, so a genuine
uptrend makes the *true* edge larger than what this reports, never smaller
-- it will not manufacture a bullish edge out of momentum alone.

"Above $X on <date>" (same-day snapshot, no "reach ... at any point"
language) is a different payoff shape -- a terminal-distribution question,
not a touch-anytime barrier -- and is intentionally not priced here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from .models import touch_probability_upper_barrier

_PATTERN = re.compile(r"will\s+bitcoin\s+reach\s+\$?([\d,]+)", re.IGNORECASE)


@dataclass
class BtcTouchEstimate:
    p_true: float
    confidence: int
    evidence: str


def extract_barrier(question: str) -> float | None:
    m = _PATTERN.search(question)
    if not m:
        return None
    return float(m.group(1).replace(",", ""))


def estimate(
    question: str,
    end_date_iso: str,
    *,
    spot: float,
    vol_60d: float,
) -> BtcTouchEstimate | None:
    """Price one market given an already-fetched spot price and realized
    volatility. Callers should fetch spot/vol ONCE per cycle (see
    polymanager.cli.run_cycle) and pass them in here for every matching
    market -- CoinGecko's free tier rate-limits per-market fetches almost
    immediately, and there's only one live BTC price per cycle anyway.
    """
    barrier = extract_barrier(question)
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

    evidence = (
        f"Barrier-touch model (zero-drift GBM): spot=${spot:,.0f}, barrier=${barrier:,.0f}, "
        f"60d realized daily vol={vol_60d:.2%}, {days_remaining:.1f} days remaining -> "
        f"model P(touch)={p_model:.1%} (vs {p_model_high_vol:.1%} at 1.5x vol, "
        f"confidence set from that sensitivity)."
    )
    return BtcTouchEstimate(p_true=p_model, confidence=confidence, evidence=evidence)
