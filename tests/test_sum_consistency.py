from polymanager.sum_consistency import (
    check_sum_consistency,
    has_unpriced_outcomes,
    parse_legs,
    scan_event,
)


def _market(question: str, yes_price: float, **overrides) -> dict:
    base = {
        "id": question,
        "question": question,
        "outcomePrices": [str(yes_price), str(1 - yes_price)],
        "closed": False,
        "acceptingOrders": True,
        "liquidityNum": 10000,
    }
    base.update(overrides)
    return base


def test_normal_overround_is_not_flagged():
    legs = parse_legs(
        [
            _market("Candidate A wins?", 0.60),
            _market("Candidate B wins?", 0.30),
            _market("Candidate C wins?", 0.11),
        ]
    )
    assert check_sum_consistency("Test Election", legs) is None  # sum=1.01, within noise band


def test_underpriced_basket_flagged_as_buy_yes():
    legs = parse_legs(
        [
            _market("Candidate A wins?", 0.50),
            _market("Candidate B wins?", 0.30),
            _market("Candidate C wins?", 0.10),  # sum = 0.90 -> 10pp underpriced
        ]
    )
    result = check_sum_consistency("Test Election", legs)
    assert result is not None
    assert result.direction == "buy_yes_basket"
    assert abs(result.deviation_pp - (-10.0)) < 1e-9


def test_overpriced_basket_flagged_as_buy_no():
    legs = parse_legs(
        [
            _market("Candidate A wins?", 0.60),
            _market("Candidate B wins?", 0.35),
            _market("Candidate C wins?", 0.15),  # sum = 1.10 -> 10pp overpriced
        ]
    )
    result = check_sum_consistency("Test Election", legs)
    assert result is not None
    assert result.direction == "buy_no_basket"
    assert abs(result.deviation_pp - 10.0) < 1e-9


def test_illiquid_and_closed_legs_are_excluded():
    legs = parse_legs(
        [
            _market("Candidate A wins?", 0.60),
            _market("Candidate B wins?", 0.30),
            _market("Candidate C wins?", 0.001, liquidityNum=10),  # too illiquid
            _market("Stale duplicate wins?", 1.0, closed=True),
        ]
    )
    assert len(legs) == 2


def test_too_few_legs_returns_none():
    legs = parse_legs([_market("Only outcome?", 0.99)])
    assert check_sum_consistency("Degenerate event", legs) is None


def test_has_unpriced_outcomes_detects_untraded_placeholder():
    markets = [
        _market("Candidate A wins?", 0.60),
        {"id": "placeholder", "question": "Person Z wins?", "outcomePrices": None},
    ]
    assert has_unpriced_outcomes(markets) is True


def test_has_unpriced_outcomes_false_when_all_priced():
    markets = [_market("Candidate A wins?", 0.60), _market("Candidate B wins?", 0.35)]
    assert has_unpriced_outcomes(markets) is False


def test_underpriced_basket_suppressed_when_outcome_set_incomplete():
    # Real shape from live data (2026-08-20, "Democratic Presidential
    # Nominee 2028"): 51 of 128 markets priced, summing to 91.4% -- but 77
    # outcomes have literally never traded, so the missing ~8.6% is very
    # likely real probability mass on those untradeable legs, not free
    # money. scan_event must suppress this direction when unpriced
    # outcomes exist in the raw event.
    event = {
        "title": "Test Presidential Primary",
        "markets": [
            _market("Candidate A wins?", 0.50),
            _market("Candidate B wins?", 0.30),
            _market("Candidate C wins?", 0.10),  # sum = 0.90 among priced legs
            {"id": "unpriced-1", "question": "Long-shot candidate D wins?", "outcomePrices": None},
        ],
    }
    assert scan_event(event) is None


def test_overpriced_basket_not_suppressed_when_outcome_set_incomplete():
    # Sum already exceeds 100% among priced legs -- adding more (currently
    # unpriced) legs only pushes the true sum higher, so this direction
    # must NOT be suppressed by incompleteness.
    event = {
        "title": "Test Tournament",
        "markets": [
            _market("Team A wins?", 0.60),
            _market("Team B wins?", 0.35),
            _market("Team C wins?", 0.15),  # sum = 1.10 among priced legs
            {"id": "unpriced-1", "question": "Team Z wins?", "outcomePrices": None},
        ],
    }
    result = scan_event(event)
    assert result is not None
    assert result.direction == "buy_no_basket"


def test_real_fed_september_2026_event_no_material_finding():
    # Real live data captured 2026-08-20 (event id 481717, "Fed Decision in
    # September?"): sum=100.85%, well within the noise band -- regression
    # fixture so a future threshold change doesn't silently start flagging
    # normal overround as an "opportunity."
    event = {
        "title": "Fed Decision in September?",
        "negRisk": True,
        "markets": [
            _market("Will the Fed decrease interest rates by 50+ bps after the September 2026 meeting?", 0.0025),
            _market("Will the Fed decrease interest rates by 25 bps after the September 2026 meeting?", 0.0125),
            _market("Will there be no change in Fed interest rates after the September 2026 meeting?", 0.725),
            _market("Will the Fed increase interest rates by 25 bps after the September 2026 meeting?", 0.265),
            _market("Will the Fed increase interest rates by 50+ bps after the September 2026 meeting?", 0.0035),
        ],
    }
    assert scan_event(event) is None
