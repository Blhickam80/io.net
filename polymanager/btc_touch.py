"""Strategy: barrier-touch pricing for "Will Bitcoin reach $X in <month>?"
Polymarket markets.

These resolve YES if BTC/USDT ever trades at or above $X on Binance during
the stated window -- a textbook barrier option, not a narrative bet. This
module detects that market shape, pulls live BTC spot price and realized
volatility from CoinGecko, prices the barrier with
polymanager.models.touch_probability_upper_barrier (via the shared engine
in polymanager.crypto_touch), and compares that model probability to the
market's own price. This is Strategy A/E from the mandate (mispricing /
near-resolution convergence) applied to one specific, well-defined market
family where real math beats narrative.

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

This calibration finding is BTC-SPECIFIC and does not transfer to other
assets -- see polymanager.eth_touch, whose own backtest came out worse
(the model didn't even beat a naive baseline for ETH over the same window).

"Above $X on <date>" (same-day snapshot, no "reach ... at any point"
language) is a different payoff shape -- a terminal-distribution question,
not a touch-anytime barrier -- and is intentionally not priced here.
"""

from __future__ import annotations

from dataclasses import dataclass

from .crypto_touch import estimate_for_asset

# See module docstring: backtested calibration doesn't support trusting this
# strategy above experimental sizing yet. Raise only after re-validating.
CONFIDENCE_CAP = 4

_CALIBRATION_NOTE = (
    "2026-08-20 backtest showed this model overstates upside touch probability "
    "in trending (non-zero-drift) regimes -- see polymanager.backtest and this "
    "module's docstring."
)


@dataclass
class BtcTouchEstimate:
    p_true: float
    confidence: int
    evidence: str


def extract_barrier(question: str) -> float | None:
    from .crypto_touch import extract_barrier as _extract, make_pattern

    return _extract(question, make_pattern("Bitcoin"))


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
    result = estimate_for_asset(
        question,
        end_date_iso,
        asset_name="Bitcoin",
        spot=spot,
        vol_60d=vol_60d,
        confidence_cap=CONFIDENCE_CAP,
        calibration_note=_CALIBRATION_NOTE,
    )
    if result is None:
        return None
    return BtcTouchEstimate(p_true=result.p_true, confidence=result.confidence, evidence=result.evidence)
