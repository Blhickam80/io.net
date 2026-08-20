"""Kelly-criterion position sizing for binary prediction-market shares.

Buying a YES share at price P that pays $1 on resolution is a bet with net
odds b = (1-P)/P (win (1-P) per P risked) and probability of winning p_true.
Standard Kelly f* = (b*p - q) / b simplifies, for this payoff structure, to:

    f* = (p_true - P) / (1 - P)

which is exactly the edge divided by the "room to fair value." It is
negative (no bet) whenever P exceeds p_true, and undefined at P=1.
"""

from __future__ import annotations

from .config import KELLY_FRACTION_BY_CONFIDENCE, MAX_SINGLE_POSITION_PCT


def full_kelly_fraction(p_true: float, price: float) -> float:
    """Full-Kelly bankroll fraction for buying a share at `price`.

    Returns 0.0 (no bet) whenever the implied edge is non-positive.
    """
    if not (0.0 < price < 1.0):
        raise ValueError(f"price must be in (0, 1), got {price}")
    if not (0.0 <= p_true <= 1.0):
        raise ValueError(f"p_true must be in [0, 1], got {p_true}")

    edge = p_true - price
    if edge <= 0:
        return 0.0
    return edge / (1.0 - price)


def kelly_multiplier_for_confidence(confidence: int) -> float:
    """Map a 1-10 confidence score to a fractional-Kelly multiplier.

    Lower confidence -> smaller fraction of full Kelly, since our probability
    estimates carry model error that full Kelly does not account for.
    """
    for threshold, multiplier in KELLY_FRACTION_BY_CONFIDENCE:
        if confidence >= threshold:
            return multiplier
    return 0.0


def recommended_position_size(
    *,
    bankroll: float,
    p_true: float,
    price: float,
    confidence: int,
    tier_min_pct: float,
    tier_max_pct: float,
    drawdown_multiplier: float = 1.0,
    hard_cap_pct: float = MAX_SINGLE_POSITION_PCT,
) -> dict:
    """Combine fractional Kelly with the tier band, drawdown throttle, and
    hard cap to produce a final recommended dollar position size.

    The result is: min(fractional_kelly, tier_max) scaled by the drawdown
    multiplier, floored at zero, and never allowed to exceed the hard cap --
    then floored again against tier_min *only if* it clears the tier's own
    edge/confidence bar (callers are expected to have already screened that;
    this function trusts its inputs).

    Audit (2026-08-20): under the live config (config.TIERS, which caps
    Tier 1 -- the highest -- at 0.12, and config.DRAWDOWN_RULES, whose
    multipliers are all <= 1.0), hard_cap_pct is currently redundant:
    tier_capped * drawdown_multiplier can never exceed 0.12 in the first
    place, so the `min(final_pct, hard_cap_pct)` line never actually
    changes the output. It is not dead code, though (see
    test_hard_cap_does_bind_if_a_tier_max_ever_exceeds_it) -- it starts
    binding immediately if a tier's max_pct is ever widened past 12%.
    """
    f_full = full_kelly_fraction(p_true, price)
    if f_full <= 0.0:
        return {
            "full_kelly_pct": 0.0,
            "fractional_kelly_pct": 0.0,
            "tier_capped_pct": 0.0,
            "final_pct": 0.0,
            "dollar_amount": 0.0,
            "reason": "No positive edge: full-Kelly fraction is zero or negative.",
        }

    kelly_mult = kelly_multiplier_for_confidence(confidence)
    f_fractional = f_full * kelly_mult

    tier_capped = min(f_fractional, tier_max_pct)
    tier_capped = max(tier_capped, 0.0)
    if tier_capped < tier_min_pct and tier_capped > 0.0:
        # Fractional Kelly says less than the tier's floor is warranted --
        # respect Kelly, not the floor. The floor is a ceiling-adjacent
        # sizing guide, not a mandate to size beyond what the math supports.
        pass

    final_pct = tier_capped * drawdown_multiplier
    final_pct = min(final_pct, hard_cap_pct)
    dollar_amount = round(bankroll * final_pct, 2)

    return {
        "full_kelly_pct": round(f_full * 100, 2),
        "fractional_kelly_pct": round(f_fractional * 100, 2),
        "tier_capped_pct": round(tier_capped * 100, 2),
        "final_pct": round(final_pct * 100, 2),
        "dollar_amount": dollar_amount,
        "reason": "ok",
    }
