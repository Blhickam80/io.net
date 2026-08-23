from polymanager.risk import (
    CorrelationGroup,
    check_correlation_limit,
    current_drawdown,
    drawdown_multiplier,
)


def test_current_drawdown():
    assert current_drawdown(200, 200) == 0.0
    assert abs(current_drawdown(180, 200) - 0.10) < 1e-9
    assert abs(current_drawdown(140, 200) - 0.30) < 1e-9


def test_drawdown_multiplier_tiers():
    assert drawdown_multiplier(0.0)[0] == 1.0
    assert drawdown_multiplier(0.10)[0] == 0.5
    assert drawdown_multiplier(0.20)[0] == 0.25
    assert drawdown_multiplier(0.30)[0] == 0.0
    assert drawdown_multiplier(0.45)[0] == 0.0


def test_correlation_limit_blocks_over_concentration():
    group = CorrelationGroup(label="US election", market_ids=["m1", "m2"])
    open_positions = [{"market_id": "m1", "dollars": 30.0}]
    allowed, resulting_pct = check_correlation_limit(
        group, open_positions, proposed_dollars=10.0, bankroll=200.0, limit_pct=0.20
    )
    # existing 30/200=15%, +10/200=5% -> 20% exactly, at the limit -> allowed
    assert allowed
    assert abs(resulting_pct - 0.20) < 1e-9

    allowed2, resulting_pct2 = check_correlation_limit(
        group, open_positions, proposed_dollars=11.0, bankroll=200.0, limit_pct=0.20
    )
    assert not allowed2


def test_correlation_limit_blocks_new_exposure_at_zero_bankroll():
    # Real bug found live 2026-08-21: the old fallback made resulting_pct
    # default to 0.0 whenever bankroll <= 0, reporting ANY proposed_dollars
    # as "0% exposure" and always allowing it -- the exact opposite of
    # correct (zero capital should block any new exposure, not wave it
    # through). Currently unreachable in this deployment since state.cash
    # never actually decreases, but a genuine correctness bug regardless.
    group = CorrelationGroup(label="x", market_ids=["m1"])
    allowed, resulting_pct = check_correlation_limit(
        group, [], proposed_dollars=1000.0, bankroll=0.0, limit_pct=0.20
    )
    assert allowed is False
    assert resulting_pct == 0.0


def test_correlation_limit_blocks_new_exposure_at_negative_bankroll():
    group = CorrelationGroup(label="x", market_ids=["m1"])
    allowed, _ = check_correlation_limit(group, [], proposed_dollars=1000.0, bankroll=-50.0, limit_pct=0.20)
    assert allowed is False


def test_correlation_limit_allows_zero_proposed_at_zero_bankroll():
    # A no-op proposal (adding nothing) at zero bankroll is harmless and
    # should not be blocked -- only a genuinely new positive exposure
    # should be rejected when there's no capital to size it against.
    group = CorrelationGroup(label="x", market_ids=["m1"])
    allowed, _ = check_correlation_limit(group, [], proposed_dollars=0.0, bankroll=0.0, limit_pct=0.20)
    assert allowed is True


def test_correlation_cap_binds_under_realistic_btc_opportunity_counts():
    """Regression/audit test for a real question raised 2026-08-20: with
    both BTC and ETH touch strategies now live, does MAX_CORRELATED_GROUP_PCT
    (20%) ever actually reject anything, or is it dead code in practice
    given today's small Tier-3-only position sizes ($6 max each, since
    btc_touch's CONFIDENCE_CAP=4 structurally limits it to Tier 3)?

    Verified live the same day: a real cycle produced 4 simultaneous BTC
    opportunities at $6/$6/$6/$2.59 (10.3% of a $200 bankroll) -- under the
    cap, so nothing was rejected that day. This test confirms the mechanism
    itself is NOT dead: replaying cli.py's accept-in-ranked-order loop with
    8 opportunities at the real $6 Tier-3 size correctly accepts the first
    6 (18%) and rejects the 7th and 8th (would reach 21%). The cap is real
    and reachable; it simply hadn't been exercised by that day's specific
    market conditions.
    """
    group = CorrelationGroup(label="correlated:bitcoin", market_ids=["correlated:bitcoin"])
    accepted_positions: list[dict] = []
    accepted_count = 0
    for _ in range(8):
        allowed, _pct = check_correlation_limit(group, accepted_positions, proposed_dollars=6.00, bankroll=200.0)
        if allowed:
            accepted_positions.append({"market_id": "correlated:bitcoin", "dollars": 6.00})
            accepted_count += 1

    assert accepted_count == 6  # 6 * $6 = $36 = 18% of $200, the last accepted step under 20%
    assert sum(p["dollars"] for p in accepted_positions) == 36.00
