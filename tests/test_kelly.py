from polymanager.kelly import (
    full_kelly_fraction,
    kelly_multiplier_for_confidence,
    recommended_position_size,
)


def test_full_kelly_positive_edge():
    # p_true=0.55, price=0.42 -> edge=0.13, f* = 0.13/0.58
    f = full_kelly_fraction(0.55, 0.42)
    assert abs(f - (0.13 / 0.58)) < 1e-9


def test_full_kelly_no_edge_returns_zero():
    assert full_kelly_fraction(0.42, 0.42) == 0.0
    assert full_kelly_fraction(0.30, 0.42) == 0.0


def test_full_kelly_negative_edge_high_price_low_value():
    # A 90%-likely event at $0.91 has negative edge -> no bet.
    assert full_kelly_fraction(0.90, 0.91) == 0.0


def test_kelly_multiplier_scales_with_confidence():
    assert kelly_multiplier_for_confidence(9) == 0.5
    assert kelly_multiplier_for_confidence(7) == 1 / 3
    assert kelly_multiplier_for_confidence(5) == 0.25
    assert kelly_multiplier_for_confidence(4) == 1 / 8
    assert kelly_multiplier_for_confidence(2) == 0.0


def test_kelly_multiplier_confidence_4_matches_t3_floor():
    # T3_EXPERIMENTAL.min_confidence is 4 -- a confidence-4 opportunity
    # that qualifies for Tier 3 must not size to exactly zero, or the
    # tier's own floor becomes unfundable by construction. Regression for
    # the real bug found live 2026-08-20 (polymanager.btc_touch's
    # CONFIDENCE_CAP=4 meant that whole strategy could never trade).
    from polymanager.config import TIERS

    assert kelly_multiplier_for_confidence(TIERS["T3_EXPERIMENTAL"].min_confidence) > 0.0


def test_recommended_position_size_respects_hard_cap():
    result = recommended_position_size(
        bankroll=200.0,
        p_true=0.95,
        price=0.10,  # huge apparent edge
        confidence=9,
        tier_min_pct=0.05,
        tier_max_pct=0.12,
        drawdown_multiplier=1.0,
        hard_cap_pct=0.12,
    )
    assert result["final_pct"] <= 12.0
    assert result["dollar_amount"] <= 24.01


def test_recommended_position_size_zero_when_no_edge():
    result = recommended_position_size(
        bankroll=200.0,
        p_true=0.50,
        price=0.60,
        confidence=8,
        tier_min_pct=0.05,
        tier_max_pct=0.12,
    )
    assert result["dollar_amount"] == 0.0
    assert result["final_pct"] == 0.0
