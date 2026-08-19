"""Drawdown throttling and correlation-exposure checks."""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import DRAWDOWN_RULES, MAX_CORRELATED_GROUP_PCT


def current_drawdown(equity: float, high_water_mark: float) -> float:
    if high_water_mark <= 0:
        return 0.0
    return max(0.0, (high_water_mark - equity) / high_water_mark)


def drawdown_multiplier(drawdown_pct: float) -> tuple[float, str]:
    """Return (size_multiplier, description) for the current drawdown level.

    DRAWDOWN_RULES is sorted descending by threshold; the first rule whose
    threshold the drawdown meets or exceeds applies.
    """
    for threshold, multiplier, description in DRAWDOWN_RULES:
        if drawdown_pct >= threshold:
            return multiplier, description
    return 1.0, "Normal sizing."


@dataclass
class CorrelationGroup:
    """A set of positions whose outcomes are not independent (e.g. all
    depend on the same election, the same rate decision, the same team).
    """

    label: str
    market_ids: list[str] = field(default_factory=list)


def correlated_exposure_pct(
    group: CorrelationGroup,
    open_positions: list[dict],
    bankroll: float,
) -> float:
    """Sum of dollars invested across positions in `group`, as a fraction of
    bankroll. Positions are dicts with at least 'market_id' and 'dollars'.
    """
    total = sum(
        p["dollars"] for p in open_positions if p["market_id"] in group.market_ids
    )
    return total / bankroll if bankroll > 0 else 0.0


def check_correlation_limit(
    group: CorrelationGroup,
    open_positions: list[dict],
    proposed_dollars: float,
    bankroll: float,
    limit_pct: float = MAX_CORRELATED_GROUP_PCT,
) -> tuple[bool, float]:
    """Return (allowed, resulting_pct) for adding `proposed_dollars` more to
    a correlated group, given a cap on aggregate correlated exposure.
    """
    existing_pct = correlated_exposure_pct(group, open_positions, bankroll)
    resulting_pct = existing_pct + (proposed_dollars / bankroll if bankroll > 0 else 0.0)
    return resulting_pct <= limit_pct, resulting_pct
