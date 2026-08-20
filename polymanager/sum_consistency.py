"""Strategy F (cross-market inconsistency): mutually-exclusive outcome sum.

For Polymarket's "negRisk" multi-outcome event groups (elections, "next PM
of X," "who wins the championship," ...) exactly one market resolves YES.
Summed across every outcome, YES prices should sit near 100%: a small
overround (market-maker margin) above 100% is normal, not an inefficiency.
A sum materially BELOW 100% means the whole basket of YES shares can be
bought for less than the $1 it's guaranteed to pay out -- risk-free profit
if every leg can actually be filled. A sum materially ABOVE 100% means the
opposite: a basket of NO shares nets a guaranteed profit
(payout = n-1 per basket, cost = n - sum(YES); profit = sum(YES) - 1).

Live-checked 2026-08-20 against several real negRisk events -- Fed Decision
in September (5 outcomes: sum=100.85%), Next PM of Ethiopia (8 priced
candidates: sum=101.1%), among others: every sum sat within ~1-1.5% of
100%, consistent with normal market-maker margin. No material arbitrage
found. Expected: sum consistency is an extremely well-known check that
professional arbers actively enforce on Polymarket's biggest events, so
persistent violations above execution costs should be rare.

Two caveats, stated plainly:
  - COMPLETENESS: this check is only valid when the priced, liquid legs
    represent (very nearly) the full mutually-exclusive, exhaustive
    outcome set. An event with an illiquid/unpriced "other candidate"
    catch-all (common -- see the Ethiopia example) has some probability
    mass this check can't see, which pushes the *true* sum higher than
    what's computed here. That only strengthens a "sum is already >=100%,
    no arb" finding; it should make you suspicious of an apparent
    "sum < 100%" finding on an incomplete-looking outcome set, not confident
    in it.
  - EXECUTION RISK: capturing this arb, if a real one appears, means
    filling EVERY leg of an N-outcome basket near-simultaneously before
    prices move. N can exceed 100 for events like a presidential primary.
    That is a much harder execution problem than a single-market trade and
    belongs in the sizing decision, not just the nominal-edge calculation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .config import MIN_LIQUIDITY_USD

# Matches monotonicity's materiality bar: normal market-maker overround
# routinely sits in the 0.5-1.5pp range, so only flag deviations clearly
# outside that.
MIN_SUM_DEVIATION_PP = 2.0


@dataclass
class OutcomeLeg:
    market_id: str
    question: str
    yes_price: float
    liquidity_usd: float


@dataclass
class SumConsistencyResult:
    event_title: str
    legs: list[OutcomeLeg]
    sum_yes: float
    deviation_pp: float  # (sum_yes - 1.0) * 100
    direction: str  # "buy_yes_basket" (sum < 100%) or "buy_no_basket" (sum > 100%)


def has_unpriced_outcomes(raw_markets: list[dict]) -> bool:
    """True if any market in the raw event has never traded / has no
    quotable price at all (outcomePrices missing or unparseable).

    Verified live 2026-08-20 (event 30829, "Democratic Presidential
    Nominee 2028"): 51 of 128 markets are priced; the other 77 have no
    price at all. Summing even every PRICED market (ignoring liquidity
    entirely) still only reached 91.4% -- so the "missing" ~8.6% isn't
    sitting in a thinly-liquid-but-priced tail, it's implied residual
    probability spread across those 77 untraded outcomes, which have no
    orderbook to actually buy YES on. That makes a sum-below-100% finding
    on an event with unpriced outcomes NOT a real, executable arbitrage --
    see check_sum_consistency, which suppresses that direction here.
    """
    for m in raw_markets:
        prices = m.get("outcomePrices")
        if not prices:
            return True
        if isinstance(prices, str):
            try:
                prices = json.loads(prices)
            except (TypeError, ValueError):
                return True
        if not prices:
            return True
    return False


def parse_legs(raw_markets: list[dict], *, min_liquidity_usd: float = MIN_LIQUIDITY_USD) -> list[OutcomeLeg]:
    """Extract priced, liquid, currently-tradeable outcome legs from an
    event's market list. Illiquid/unpriced placeholder markets (e.g. an
    unannounced "Person X" candidate slot) are dropped -- see COMPLETENESS
    above for why that's a conservative, not a distorting, choice.
    """
    legs = []
    for m in raw_markets:
        if m.get("closed") is True or m.get("acceptingOrders") is False:
            continue
        try:
            prices = m.get("outcomePrices")
            if isinstance(prices, str):
                prices = json.loads(prices)
            yes_price = float(prices[0])
        except (TypeError, ValueError, IndexError, KeyError):
            continue
        liquidity = float(m.get("liquidityNum") or m.get("liquidity") or 0.0)
        if liquidity < min_liquidity_usd:
            continue
        legs.append(
            OutcomeLeg(
                market_id=str(m.get("id", "")),
                question=m.get("question", "?"),
                yes_price=yes_price,
                liquidity_usd=liquidity,
            )
        )
    return legs


def check_sum_consistency(
    event_title: str,
    legs: list[OutcomeLeg],
    *,
    min_deviation_pp: float = MIN_SUM_DEVIATION_PP,
    min_legs: int = 2,
    outcome_set_incomplete: bool = False,
) -> SumConsistencyResult | None:
    if len(legs) < min_legs:
        return None
    sum_yes = sum(leg.yes_price for leg in legs)
    deviation_pp = (sum_yes - 1.0) * 100
    if abs(deviation_pp) <= min_deviation_pp:
        return None
    direction = "buy_yes_basket" if deviation_pp < 0 else "buy_no_basket"
    if direction == "buy_yes_basket" and outcome_set_incomplete:
        # See has_unpriced_outcomes: a sum-below-100% reading on an event
        # with untraded outcomes almost certainly reflects real probability
        # mass sitting in those untradeable legs, not free money. The
        # opposite direction (sum already >=100% before counting the
        # untraded legs) only gets MORE true as missing mass is added, so
        # it is not suppressed.
        return None
    return SumConsistencyResult(
        event_title=event_title, legs=legs, sum_yes=sum_yes, deviation_pp=deviation_pp, direction=direction
    )


def scan_event(event: dict, **kwargs) -> SumConsistencyResult | None:
    raw_markets = event.get("markets", [])
    legs = parse_legs(raw_markets)
    return check_sum_consistency(
        event.get("title", "?"),
        legs,
        outcome_set_incomplete=has_unpriced_outcomes(raw_markets),
        **kwargs,
    )


def run_live_scan() -> tuple[int, list[SumConsistencyResult]]:
    """Returns (events_scanned, [result, ...]) for every negRisk event with
    a material sum-consistency finding.
    """
    import requests

    resp = requests.get(
        "https://gamma-api.polymarket.com/events",
        params={"active": "true", "closed": "false", "limit": 50, "order": "volume24hr", "ascending": "false"},
        timeout=30,
    )
    resp.raise_for_status()
    events = resp.json()

    results = []
    for event in events:
        if not event.get("negRisk"):
            continue
        result = scan_event(event)
        if result is not None:
            results.append(result)
    return len(events), results


def main() -> None:
    events_scanned, results = run_live_scan()
    for result in results:
        print(f"=== {result.event_title} ===")
        print(f"  {len(result.legs)} liquid legs, sum(YES)={result.sum_yes:.1%}, deviation={result.deviation_pp:+.1f}pp")
        print(f"  Direction: {result.direction}")
        if result.direction == "buy_no_basket":
            print(
                f"  CAVEAT: capturing this means buying NO on all {len(result.legs)} legs "
                "near-simultaneously and holding until the event resolves (often months for a "
                "championship market) -- weigh capital lock-up and execution slippage across "
                "that many legs against the nominal edge before sizing anything."
            )

    print(f"\nScanned {events_scanned} events. Material sum-consistency findings: {len(results)}.")


if __name__ == "__main__":
    main()
