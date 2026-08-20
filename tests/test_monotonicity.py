from polymanager.monotonicity import find_violations, parse_rung, scan_event_markets


def _raw(question: str, yes_price: float, **overrides) -> dict:
    base = {
        "id": question,
        "question": question,
        "outcomePrices": [str(yes_price), str(1 - yes_price)],
        "closed": False,
        "acceptingOrders": True,
        "liquidityNum": 10000,  # well above MIN_LIQUIDITY_USD by default
    }
    base.update(overrides)
    return base


def test_parse_rung_reach():
    rung = parse_rung(_raw("Will Bitcoin reach $72,500 in August?", 0.5))
    assert rung is not None
    assert rung.direction == "reach"
    assert rung.threshold == 72500.0


def test_parse_rung_dip():
    rung = parse_rung(_raw("Will Bitcoin dip to $50,000 in August?", 0.02))
    assert rung is not None
    assert rung.direction == "dip"
    assert rung.threshold == 50000.0


def test_parse_rung_skips_closed_market():
    assert parse_rung(_raw("Will Bitcoin reach $72,500 in August?", 1.0, closed=True)) is None


def test_parse_rung_skips_non_matching_question():
    assert parse_rung(_raw("Will the Fed cut rates?", 0.3)) is None


def test_no_violation_on_consistent_ladder():
    markets = [
        _raw("Will Bitcoin reach $72,500 in August?", 0.82),
        _raw("Will Bitcoin reach $75,000 in August?", 0.45),
        _raw("Will Bitcoin reach $77,500 in August?", 0.25),
    ]
    assert scan_event_markets(markets) == []


def test_detects_injected_violation():
    # $77,500 (harder) priced ABOVE $75,000 (easier) -- a real inconsistency.
    markets = [
        _raw("Will Bitcoin reach $72,500 in August?", 0.82),
        _raw("Will Bitcoin reach $75,000 in August?", 0.45),
        _raw("Will Bitcoin reach $77,500 in August?", 0.60),
    ]
    violations = scan_event_markets(markets)
    assert len(violations) == 1
    v = violations[0]
    assert v.easier.threshold == 75000.0
    assert v.harder.threshold == 77500.0
    assert abs(v.magnitude_pp - 15.0) < 1e-9


def test_dip_direction_violation():
    # Dipping to $40,000 (harder/lower) priced ABOVE dipping to $50,000 (easier).
    markets = [
        _raw("Will Bitcoin dip to $50,000 in August?", 0.10),
        _raw("Will Bitcoin dip to $40,000 in August?", 0.30),
    ]
    violations = scan_event_markets(markets)
    assert len(violations) == 1
    assert violations[0].easier.threshold == 50000.0
    assert violations[0].harder.threshold == 40000.0


def test_tiny_magnitude_violation_is_filtered_as_noise():
    # Real-world shape from live data (2026-08-20): deep out-of-the-money
    # tail markets show ~0.1-0.3pp "violations" that are just tick-size/
    # spread noise, not executable arbitrage -- these must not be reported.
    markets = [
        _raw("Will Bitcoin dip to $52,000 August 17-23?", 0.002),
        _raw("Will Bitcoin dip to $50,000 August 17-23?", 0.004),
    ]
    assert scan_event_markets(markets) == []


def test_low_liquidity_violation_is_filtered():
    markets = [
        _raw("Will Bitcoin reach $72,500 in August?", 0.82, liquidityNum=50),
        _raw("Will Bitcoin reach $75,000 in August?", 0.95, liquidityNum=50),
    ]
    assert scan_event_markets(markets) == []


def test_closed_stale_instance_does_not_trigger_false_violation():
    # Real-world shape from live data (2026-08-20): a closed instance sits
    # at a stale 1.0 price next to the live, currently-tradeable instance.
    markets = [
        _raw("Will Bitcoin dip to $62,500 in August?", 1.0, closed=True, acceptingOrders=False, id="stale"),
        _raw("Will Bitcoin dip to $62,500 in August?", 0.06, id="live"),
        _raw("Will Bitcoin dip to $65,000 in August?", 0.16, id="live2"),
    ]
    assert scan_event_markets(markets) == []
