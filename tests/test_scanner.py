from datetime import datetime, timedelta, timezone

from polymanager.scanner import screen_market


def _future_iso(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def test_passes_healthy_market():
    raw = {
        "id": "1",
        "question": "Healthy market?",
        "outcomePrices": ["0.40", "0.60"],
        "spread": 0.02,
        "liquidityNum": 5000,
        "volume24hr": 1000,
        "endDate": _future_iso(10),
    }
    m = screen_market(raw)
    assert not m.rejected
    assert m.yes_price == 0.40


def test_rejects_thin_liquidity():
    raw = {
        "id": "2",
        "question": "Thin market?",
        "outcomePrices": ["0.40", "0.60"],
        "spread": 0.02,
        "liquidityNum": 100,
        "volume24hr": 1000,
        "endDate": _future_iso(10),
    }
    m = screen_market(raw)
    assert m.rejected
    assert any("Liquidity" in r for r in m.rejection_reasons)


def test_rejects_wide_spread():
    raw = {
        "id": "3",
        "question": "Wide spread market?",
        "outcomePrices": ["0.40", "0.55"],
        "spread": 0.15,
        "liquidityNum": 5000,
        "volume24hr": 1000,
        "endDate": _future_iso(10),
    }
    m = screen_market(raw)
    assert m.rejected
    assert any("Spread" in r for r in m.rejection_reasons)


def test_rejects_near_resolution():
    raw = {
        "id": "4",
        "question": "About to resolve?",
        "outcomePrices": ["0.40", "0.60"],
        "spread": 0.01,
        "liquidityNum": 5000,
        "volume24hr": 1000,
        "endDate": _future_iso(0),
    }
    m = screen_market(raw)
    assert m.rejected
    assert any("resolution" in r for r in m.rejection_reasons)


def test_rejects_closed_market_even_with_healthy_looking_stats():
    # Real Gamma /events data (2026-08-20): a closed, already-resolved
    # market instance can carry a stale 1.0/0.0 price sitting right next to
    # a live instance of "the same" question -- liquidity/volume checks
    # alone won't catch this if the closed record happens to retain old
    # numbers, so `closed`/`acceptingOrders` must be checked directly.
    raw = {
        "id": "5",
        "question": "Will Bitcoin dip to $62,500 in August?",
        "outcomePrices": ["1", "0"],
        "spread": 0.0,
        "liquidityNum": 5000,
        "volume24hr": 1000,
        "endDate": _future_iso(10),
        "closed": True,
        "acceptingOrders": False,
    }
    m = screen_market(raw)
    assert m.rejected
    assert any("closed" in r.lower() for r in m.rejection_reasons)
    assert any("not accepting orders" in r.lower() for r in m.rejection_reasons)


def test_open_market_without_closed_field_is_not_penalized():
    raw = {
        "id": "6",
        "question": "Normal open market?",
        "outcomePrices": ["0.40", "0.60"],
        "spread": 0.02,
        "liquidityNum": 5000,
        "volume24hr": 1000,
        "endDate": _future_iso(10),
    }
    m = screen_market(raw)
    assert not m.rejected
