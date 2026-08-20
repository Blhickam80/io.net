from datetime import datetime, timedelta, timezone

from polymanager.eth_touch import CONFIDENCE_CAP, estimate


def _future_iso(days: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def test_confidence_cap_is_below_every_tier_floor():
    from polymanager.config import TIERS

    min_floor = min(tier.min_confidence for tier in TIERS.values())
    assert CONFIDENCE_CAP < min_floor, (
        "ETH's backtest (Brier score worse than baseline) does not support sizing any trade -- "
        "CONFIDENCE_CAP must stay below every tier's floor until re-validated."
    )


def test_estimate_never_produces_tier_qualifying_confidence():
    result = estimate("Will Ethereum reach $3,000 in August?", _future_iso(10), spot=2330.0, vol_60d=0.03)
    assert result is not None
    assert result.confidence <= CONFIDENCE_CAP


def test_estimate_skips_non_eth_question():
    result = estimate("Will Bitcoin reach $72,500 in August?", _future_iso(10), spot=2330.0, vol_60d=0.03)
    assert result is None
