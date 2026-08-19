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
