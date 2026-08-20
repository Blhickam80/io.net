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

The model assumes zero price drift. That is NOT unconditionally
conservative -- it only under-states true touch probability when the real
future drift turns out non-negative; in a sustained downtrend it
over-states it, symmetrically. A walk-forward calibration backtest
(polymanager.backtest, run 2026-08-20 against the trailing 365 days of BTC
daily closes -- a year BTC fell ~37% peak-to-trough) confirmed the
over-statement side directly: mean predicted touch probability was 44.0%
against an actual realized rate of 24.7% (shrinkage factor ~0.56). That
gap is not obviously a bug in the touch-probability math -- it lines up
almost exactly with "zero-drift model, strongly negative-drift year" -- but
it means this strategy's raw output cannot be trusted at high confidence
without a live re-check, since we have no way to know in advance whether
the next few weeks will look more like a driftless walk or another trend.
CONFIDENCE_CAP below encodes that: however tight the vol-sensitivity band
looks, this strategy cannot output better than Tier-3/experimental
confidence until it's re-validated (e.g. with a longer or regime-varied
backtest, or a real drift term) and this cap is deliberately raised.

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

# See module docstring: backtested calibration doesn't support trusting this
# strategy above experimental sizing yet. Raise only after re-validating.
CONFIDENCE_CAP = 4


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
    confidence = min(confidence, CONFIDENCE_CAP)

    evidence = (
        f"Barrier-touch model (zero-drift GBM): spot=${spot:,.0f}, barrier=${barrier:,.0f}, "
        f"60d realized daily vol={vol_60d:.2%}, {days_remaining:.1f} days remaining -> "
        f"model P(touch)={p_model:.1%} (vs {p_model_high_vol:.1%} at 1.5x vol). "
        f"Confidence capped at {CONFIDENCE_CAP}/10: 2026-08-20 backtest showed this "
        f"model overstates upside touch probability in trending (non-zero-drift) "
        f"regimes -- see polymanager.backtest and this module's docstring."
    )
    return BtcTouchEstimate(p_true=p_model, confidence=confidence, evidence=evidence)
