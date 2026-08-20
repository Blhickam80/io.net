"""Strategy F (cross-market inconsistency): nested-outcome monotonicity.

Polymarket runs "ladder" event groups like "What price will Bitcoin hit in
<month>?", containing many binary markets such as "Will Bitcoin reach
$72,500 in August?" and "Will Bitcoin reach $75,000 in August?" within the
same window. These are logically nested: touching $75,000 implies having
already touched $72,500, so P(reach $75,000) can never legitimately exceed
P(reach $72,500). The same logic applies in reverse for "dip to $X"
markets: a lower dip threshold is strictly harder to reach than a higher
one, so P(dip to $40,000) can never exceed P(dip to $50,000).

If a ladder ever prices a harder outcome higher than an easier one, that is
a real, model-free, no-research-needed inconsistency: sell the mispriced
(overpriced relative to its neighbor) side. This module finds those
violations mechanically -- no probability estimation involved.

Live-checked 2026-08-20 against Polymarket's actual "Bitcoin hit in August"
ladder (30 markets, event id 780132): zero violations found in the
tradeable (open, accepting-orders) markets. Efficient-market result, not a
bug -- ladder monotonicity is an obvious, well-known check that market
makers actively enforce, so violations should be rare and likely small/
short-lived when they do appear. Re-run this regularly; it costs nothing
but a market fetch and is a legitimate live opportunity scan even though
today's answer was "nothing here."
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import MIN_LIQUIDITY_USD

_REACH_PATTERN = re.compile(r"reach\s+\$?([\d,]+)", re.IGNORECASE)
_DIP_PATTERN = re.compile(r"dip\s+to\s+\$?([\d,]+)", re.IGNORECASE)

# Live-checked 2026-08-20: a naive scan across 50 active events found 12
# "violations," every one of them 0.1-0.3pp on deep out-of-the-money tail
# markets (prices under 2%). That's smaller than Polymarket's own price
# tick size and typical bid-ask spread on those markets -- not real,
# executable arbitrage, just quantization/spread noise. Anything smaller
# than this is not reported.
MIN_VIOLATION_MAGNITUDE_PP = 2.0


@dataclass
class LadderRung:
    market_id: str
    question: str
    threshold: float
    yes_price: float
    direction: str  # "reach" (upper barrier) or "dip" (lower barrier)
    liquidity_usd: float


@dataclass
class MonotonicityViolation:
    easier: LadderRung
    harder: LadderRung
    magnitude_pp: float  # how many percentage points too high `harder` is priced


def parse_rung(raw_market: dict) -> LadderRung | None:
    """Build a LadderRung from a raw Gamma-API market record, or None if it
    doesn't match a "reach $X" / "dip to $X" question shape, is closed, or
    isn't currently accepting orders (see polymanager.scanner for why that
    check matters -- closed instances of "the same" question can carry
    stale terminal prices).
    """
    if raw_market.get("closed") is True or raw_market.get("acceptingOrders") is False:
        return None

    question = raw_market.get("question", "")
    reach_match = _REACH_PATTERN.search(question)
    dip_match = _DIP_PATTERN.search(question)
    if reach_match:
        direction, threshold_str = "reach", reach_match.group(1)
    elif dip_match:
        direction, threshold_str = "dip", dip_match.group(1)
    else:
        return None

    try:
        outcome_prices = raw_market.get("outcomePrices")
        if isinstance(outcome_prices, str):
            import json

            outcome_prices = json.loads(outcome_prices)
        yes_price = float(outcome_prices[0])
    except (TypeError, ValueError, IndexError, KeyError):
        return None

    liquidity = float(raw_market.get("liquidityNum") or raw_market.get("liquidity") or 0.0)

    return LadderRung(
        market_id=str(raw_market.get("id", "")),
        question=question,
        threshold=float(threshold_str.replace(",", "")),
        yes_price=yes_price,
        direction=direction,
        liquidity_usd=liquidity,
    )


def find_violations(
    rungs: list[LadderRung],
    *,
    min_magnitude_pp: float = MIN_VIOLATION_MAGNITUDE_PP,
    min_liquidity_usd: float = MIN_LIQUIDITY_USD,
) -> list[MonotonicityViolation]:
    """Check every same-direction pair for a monotonicity violation.

    "reach": higher threshold is harder -> price must be non-increasing as
    threshold rises.
    "dip": lower threshold is harder -> price must be non-increasing as
    threshold falls.

    Only reports violations at least `min_magnitude_pp` wide with both legs
    meeting `min_liquidity_usd` -- see MIN_VIOLATION_MAGNITUDE_PP for why:
    tiny-magnitude violations on thin, deep-out-of-the-money legs are tick-
    size/spread noise, not real executable arbitrage.
    """
    violations: list[MonotonicityViolation] = []

    for direction, harder_is_higher_threshold in (("reach", True), ("dip", False)):
        group = [r for r in rungs if r.direction == direction]
        # Sort by difficulty ascending: easiest first.
        group.sort(key=lambda r: r.threshold, reverse=not harder_is_higher_threshold)

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                easier, harder = group[i], group[j]
                magnitude_pp = (harder.yes_price - easier.yes_price) * 100
                if magnitude_pp <= min_magnitude_pp:
                    continue
                if easier.liquidity_usd < min_liquidity_usd or harder.liquidity_usd < min_liquidity_usd:
                    continue
                violations.append(
                    MonotonicityViolation(easier=easier, harder=harder, magnitude_pp=magnitude_pp)
                )
    return violations


def scan_event_markets(raw_markets: list[dict]) -> list[MonotonicityViolation]:
    """Convenience entry point: parse every market in an event's market
    list and return any monotonicity violations found among them.
    """
    rungs = [r for r in (parse_rung(m) for m in raw_markets) if r is not None]
    return find_violations(rungs)


def main() -> None:
    """Live scan: pull active events with the most markets (ladder-style
    events tend to have the highest market counts) from Gamma's /events
    endpoint and check each one for violations. This is a separate entry
    point from polymanager.cli's per-market cycle -- a violation is a pair
    trade (short the overpriced rung, long the underpriced one), not a
    single-side probability estimate, so it doesn't fit that pipeline's
    Kelly-sizing interface without forcing a shape it wasn't designed for.
    """
    import requests

    resp = requests.get(
        "https://gamma-api.polymarket.com/events",
        params={"active": "true", "closed": "false", "limit": 50, "order": "volume24hr", "ascending": "false"},
        timeout=30,
    )
    resp.raise_for_status()
    events = resp.json()

    total_violations = 0
    for event in events:
        markets = event.get("markets", [])
        if len(markets) < 3:
            continue
        violations = scan_event_markets(markets)
        if violations:
            total_violations += len(violations)
            print(f"=== {event.get('title')} (event {event.get('id')}) ===")
            for v in violations:
                print(
                    f"  VIOLATION: '{v.easier.question}' @ {v.easier.yes_price:.1%} vs "
                    f"'{v.harder.question}' @ {v.harder.yes_price:.1%} "
                    f"(harder outcome overpriced by {v.magnitude_pp:.1f}pp)"
                )

    print(f"\nScanned {len(events)} events. Total violations found: {total_violations}.")


if __name__ == "__main__":
    main()
