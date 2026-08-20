from datetime import datetime, timedelta, timezone

from polymanager.sum_consistency import (
    check_sum_consistency,
    has_liquidity_masked_mass,
    has_unpriced_outcomes,
    parse_legs,
    scan_event,
)


def _iso(hours_from_now: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours_from_now)).isoformat().replace("+00:00", "Z")


def _market(question: str, yes_price: float, **overrides) -> dict:
    base = {
        "id": question,
        "question": question,
        "outcomePrices": [str(yes_price), str(1 - yes_price)],
        "closed": False,
        "acceptingOrders": True,
        "liquidityNum": 10000,
        "orderMinSize": 5,
    }
    base.update(overrides)
    return base


def test_minimum_basket_cost_buy_no_basket():
    # Real shape (2026-08-20, NBA 2027 Champion): orderMinSize=5 shares per
    # leg, buy_no_basket means paying (1-yes_price) per share on each leg.
    legs = parse_legs(
        [
            _market("Team A wins?", 0.60),  # NO price 0.40 -> 5*0.40=2.00
            _market("Team B wins?", 0.35),  # NO price 0.65 -> 5*0.65=3.25
            _market("Team C wins?", 0.15),  # NO price 0.85 -> 5*0.85=4.25
        ]
    )
    result = check_sum_consistency("Test Tournament", legs)
    assert result is not None
    assert result.direction == "buy_no_basket"
    expected = 5 * 0.40 + 5 * 0.65 + 5 * 0.85
    assert abs(result.minimum_basket_cost_usd() - expected) < 1e-6


def test_minimum_basket_cost_buy_yes_basket():
    legs = parse_legs(
        [
            _market("Candidate A wins?", 0.50),
            _market("Candidate B wins?", 0.30),
            _market("Candidate C wins?", 0.10),  # sum = 0.90
        ]
    )
    result = check_sum_consistency("Test Election", legs)
    assert result is not None
    assert result.direction == "buy_yes_basket"
    expected = 5 * 0.50 + 5 * 0.30 + 5 * 0.10
    assert abs(result.minimum_basket_cost_usd() - expected) < 1e-6


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


def test_has_liquidity_masked_mass_detects_thin_high_probability_leg():
    # Real shape (2026-08-20, "Highest temperature in London on August
    # 20?"): the correct answer priced at 99.75% but with liquidity just
    # under the floor. Regression fixture for the fix.
    raw_markets = [
        _market("19C or below?", 0.0005, liquidityNum=36000),
        _market("20C?", 0.0005, liquidityNum=37000),
        _market("21C?", 0.0005, liquidityNum=30000),
        _market("22C?", 0.0005, liquidityNum=34000),
        _market("23C?", 0.0005, liquidityNum=34000),
        _market("24C?", 0.9975, liquidityNum=1740),  # correct answer, too illiquid to count
        _market("25C?", 0.003, liquidityNum=1825),
        _market("26C?", 0.002, liquidityNum=6238),
        _market("27C or higher?", 0.0005, liquidityNum=3182),
    ]
    legs = parse_legs(raw_markets)
    assert has_liquidity_masked_mass(raw_markets, legs) is True


def test_scan_event_suppresses_liquidity_masked_false_positive():
    event = {
        "title": "Highest temperature in London on August 20?",
        "negRisk": True,
        "markets": [
            _market("19C or below?", 0.0005, liquidityNum=36000),
            _market("20C?", 0.0005, liquidityNum=37000),
            _market("21C?", 0.0005, liquidityNum=30000),
            _market("22C?", 0.0005, liquidityNum=34000),
            _market("23C?", 0.0005, liquidityNum=34000),
            _market("24C?", 0.9975, liquidityNum=1740),
            _market("25C?", 0.003, liquidityNum=1825),
            _market("26C?", 0.002, liquidityNum=6238),
            _market("27C or higher?", 0.0005, liquidityNum=3182),
        ],
    }
    # Without the fix this reported deviation=-99.4pp, buy_yes_basket.
    assert scan_event(event) is None


def test_has_liquidity_masked_mass_false_when_all_mass_counted():
    raw_markets = [
        _market("Candidate A wins?", 0.60, liquidityNum=10000),
        _market("Candidate B wins?", 0.40, liquidityNum=10000),
    ]
    legs = parse_legs(raw_markets)
    assert has_liquidity_masked_mass(raw_markets, legs) is False


def test_in_play_or_imminent_event_is_skipped():
    # Real shape (2026-08-20, "Mjallby AIF vs. FC Red Bull Salzburg"):
    # endDate already ~35 minutes in the past (in-play/just finished),
    # real liquidity on both sides, a genuine-looking 3.5pp deviation --
    # but too close to resolution for a periodic scan to trust the
    # snapshot against in-play repricing risk.
    event = {
        "title": "Test Match",
        "negRisk": True,
        "markets": [
            _market("Team A wins?", 0.13, liquidityNum=137000, endDate=_iso(-0.5)),
            _market("Draw?", 0.225, liquidityNum=19000, endDate=_iso(-0.5)),
            _market("Team B wins?", 0.61, liquidityNum=133000, endDate=_iso(-0.5)),
        ],
    }
    assert scan_event(event) is None


def test_event_well_before_resolution_is_not_skipped():
    event = {
        "title": "Test Election",
        "negRisk": True,
        "markets": [
            _market("Candidate A wins?", 0.60, endDate=_iso(24 * 30)),
            _market("Candidate B wins?", 0.30, endDate=_iso(24 * 30)),
            _market("Candidate C wins?", 0.10, endDate=_iso(24 * 30)),
        ],
    }
    # sum = 1.00, within the noise band -- not flagged, but NOT because of
    # the time filter (confirms the filter doesn't over-suppress).
    assert scan_event(event) is None
    # Nudge one price so the sum is now materially off, and confirm the
    # far-future event still gets scored (not silently dropped by time).
    event["markets"][2] = _market("Candidate C wins?", 0.25, endDate=_iso(24 * 30))
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
