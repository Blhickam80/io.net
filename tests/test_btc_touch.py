from datetime import datetime, timedelta, timezone

from polymanager.btc_touch import estimate, extract_barrier


def _future_iso(days: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def test_extract_barrier():
    assert extract_barrier("Will Bitcoin reach $72,500 in August?") == 72500.0
    assert extract_barrier("Will Bitcoin reach $75000 in August?") == 75000.0
    assert extract_barrier("Will the price of Bitcoin be above $70,000 on August 20?") is None


def test_estimate_skips_non_matching_question():
    result = estimate(
        "Will the price of Bitcoin be above $70,000 on August 20?",
        _future_iso(1),
        spot=71970,
        vol_60d=0.02,
    )
    assert result is None


def test_estimate_near_barrier_gives_high_probability():
    # Spot already within ~1% of barrier with 10 days left -> high touch probability.
    result = estimate("Will Bitcoin reach $72,500 in August?", _future_iso(10), spot=71970, vol_60d=0.02)
    assert result is not None
    assert result.p_true > 0.7
    assert 1 <= result.confidence <= 10


def test_estimate_far_barrier_gives_lower_probability():
    near = estimate("Will Bitcoin reach $72,500 in August?", _future_iso(10), spot=71970, vol_60d=0.015)
    far = estimate("Will Bitcoin reach $95,000 in August?", _future_iso(10), spot=71970, vol_60d=0.015)
    assert far.p_true < near.p_true
