from datetime import datetime, timedelta, timezone

from polymanager.cli import make_estimator
from polymanager.scanner import screen_market


def _future_iso(days: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def _screened(question: str, yes_price: float):
    raw = {
        "id": "x",
        "question": question,
        "outcomePrices": [str(yes_price), str(1 - yes_price)],
        "spread": 0.02,
        "liquidityNum": 5000,
        "volume24hr": 1000,
        "endDate": _future_iso(10),
    }
    return screen_market(raw)


def test_estimator_returns_none_without_btc_data():
    estimator = make_estimator(None, None)
    m = _screened("Will Bitcoin reach $72,500 in August?", 0.60)
    assert estimator(m) is None


def test_estimator_prices_btc_market_when_data_available():
    estimator = make_estimator(71970.0, 0.02)
    m = _screened("Will Bitcoin reach $72,500 in August?", 0.60)
    result = estimator(m)
    assert result is not None
    p_true, confidence, evidence = result
    assert 0.0 <= p_true <= 1.0
    assert 1 <= confidence <= 10
    assert "Barrier-touch model" in evidence


def test_estimator_ignores_non_btc_market():
    estimator = make_estimator(71970.0, 0.02)
    m = _screened("Will the Fed decrease interest rates?", 0.10)
    assert estimator(m) is None
