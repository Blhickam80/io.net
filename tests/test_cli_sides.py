from datetime import datetime, timedelta, timezone

from polymanager.cli import _best_side
from polymanager.scanner import screen_market


def _future_iso(days: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def _screened(yes_price: float):
    raw = {
        "id": "x",
        "question": "Some market?",
        "outcomePrices": [str(yes_price), str(1 - yes_price)],
        "spread": 0.02,
        "liquidityNum": 5000,
        "volume24hr": 1000,
        "endDate": _future_iso(10),
    }
    return screen_market(raw)


def test_best_side_picks_yes_when_model_more_bullish_than_market():
    m = _screened(0.42)
    side, price, side_p_true, edge_pp = _best_side(m, p_true_yes=0.55)
    assert side == "YES"
    assert price == 0.42
    assert side_p_true == 0.55
    assert abs(edge_pp - 13.0) < 1e-9


def test_best_side_picks_no_when_model_less_bullish_than_market():
    # Real shape (2026-08-20): BTC rallied further, market priced YES at
    # 82.5% for "reach $80,000" but the model said only 77.2% -- a real
    # edge on NO that the old YES-only loop discarded entirely.
    m = _screened(0.825)
    side, price, side_p_true, edge_pp = _best_side(m, p_true_yes=0.772)
    assert side == "NO"
    assert abs(price - 0.175) < 1e-9
    assert abs(side_p_true - 0.228) < 1e-9
    assert edge_pp > 0
    assert abs(edge_pp - 5.3) < 0.1


def test_best_side_edges_are_mirror_images():
    m = _screened(0.60)
    _, _, _, yes_edge = _best_side(m, p_true_yes=0.60)  # exactly at market -> no edge either way
    assert abs(yes_edge) < 1e-9
