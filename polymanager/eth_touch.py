"""Strategy: barrier-touch pricing for "Will Ethereum reach $X in <month>?"
Polymarket markets -- the ETH counterpart to polymanager.btc_touch, sharing
the same engine (polymanager.crypto_touch) but with its OWN backtest and
its OWN (much lower) confidence cap. BTC's calibration finding does not
transfer here.

Ran the identical walk-forward backtest (polymanager.backtest.run_backtest,
unchanged -- it already took a generic price series) against ETH's own
trailing 365-day daily closes, 2026-08-20. ETH fell ~46% peak-to-trough
over that window (steeper than BTC's ~37%), and the result was worse than
BTC's: model Brier score 0.2359 vs. a naive always-predict-the-base-rate
baseline of 0.2320 -- the zero-drift touch model did not even beat the
naive baseline for ETH over this period. That is a materially different
(and worse) finding than BTC's, not a copy of it.

CONFIDENCE_CAP is set below every tier's min_confidence floor (Tier 3's is
4) specifically so this strategy can be wired into the live pipeline for
transparency and monitoring -- so it shows up and can be watched, not
hidden -- while being structurally incapable of producing a sized
recommendation until a real re-validation (longer history, a different
model, or a demonstrated recovery in calibration) changes that.
"""

from __future__ import annotations

from dataclasses import dataclass

from .crypto_touch import estimate_for_asset

# Deliberately below every tier's min_confidence (Tier 3 = 4) -- see module
# docstring. This strategy cannot currently produce a sized recommendation.
CONFIDENCE_CAP = 2

_CALIBRATION_NOTE = (
    "2026-08-20 backtest against ETH's own price history found this model's "
    "Brier score (0.2359) WORSE than a naive always-predict-the-base-rate "
    "baseline (0.2320) -- it does not currently beat a coin flip for ETH. "
    "Capped below every tier's floor until re-validated -- see this "
    "module's docstring and polymanager.backtest."
)


@dataclass
class EthTouchEstimate:
    p_true: float
    confidence: int
    evidence: str


def estimate(
    question: str,
    end_date_iso: str,
    *,
    spot: float,
    vol_60d: float,
) -> EthTouchEstimate | None:
    """Price one market given an already-fetched ETH spot price and
    realized volatility. See polymanager.btc_touch.estimate for the
    calling convention (identical) -- fetch spot/vol once per cycle.
    """
    result = estimate_for_asset(
        question,
        end_date_iso,
        asset_name="Ethereum",
        spot=spot,
        vol_60d=vol_60d,
        confidence_cap=CONFIDENCE_CAP,
        calibration_note=_CALIBRATION_NOTE,
    )
    if result is None:
        return None
    return EthTouchEstimate(p_true=result.p_true, confidence=result.confidence, evidence=result.evidence)
