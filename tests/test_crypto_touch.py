from datetime import datetime, timedelta, timezone

from polymanager.crypto_touch import estimate_for_asset, extract_barrier, make_pattern


def _future_iso(days: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def test_make_pattern_matches_asset_name_only():
    btc_pattern = make_pattern("Bitcoin")
    eth_pattern = make_pattern("Ethereum")
    assert extract_barrier("Will Bitcoin reach $72,500 in August?", btc_pattern) == 72500.0
    assert extract_barrier("Will Bitcoin reach $72,500 in August?", eth_pattern) is None
    assert extract_barrier("Will Ethereum reach $3,000 in August?", eth_pattern) == 3000.0
    assert extract_barrier("Will Ethereum reach $3,000 in August?", btc_pattern) is None


def test_extract_barrier_handles_decimal_threshold():
    # Same bug class as polymanager.monotonicity (found live 2026-08-21):
    # [\d,]+ alone would silently truncate "$4,500.50" to 4500.0, which
    # here would corrupt the barrier fed into touch_probability_upper_barrier
    # and therefore the resulting probability estimate. No live BTC/ETH
    # market has used a decimal threshold yet -- this guards against one.
    pattern = make_pattern("Ethereum")
    assert extract_barrier("Will Ethereum reach $4,500.50 in August?", pattern) == 4500.50


def test_estimate_for_asset_respects_confidence_cap():
    result = estimate_for_asset(
        "Will Ethereum reach $2,400 in August?",
        _future_iso(5),
        asset_name="Ethereum",
        spot=2330.0,
        vol_60d=0.03,
        confidence_cap=2,
        calibration_note="test note",
    )
    assert result is not None
    assert result.confidence <= 2
    assert "test note" in result.evidence


def test_estimate_for_asset_skips_non_matching_question():
    result = estimate_for_asset(
        "Will Bitcoin reach $72,500 in August?",
        _future_iso(5),
        asset_name="Ethereum",
        spot=2330.0,
        vol_60d=0.03,
        confidence_cap=4,
        calibration_note="test note",
    )
    assert result is None
