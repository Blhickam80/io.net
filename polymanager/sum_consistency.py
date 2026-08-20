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

from .config import MIN_LIQUIDITY_USD, MAX_CORRELATED_GROUP_PCT
from .scanner import hours_until

# Matches monotonicity's materiality bar: normal market-maker overround
# routinely sits in the 0.5-1.5pp range, so only flag deviations clearly
# outside that.
MIN_SUM_DEVIATION_PP = 2.0

# This strategy scans periodically (minutes to hours between checks, not a
# live order-book feed) and a real basket trade needs to fill every leg
# before prices move. Confirmed live 2026-08-20: a Mjallby-vs-Salzburg
# match with endDate already ~35 minutes in the past (i.e. in-play or just
# finished) showed a real-looking 3.5pp sum deviation on liquid legs -- but
# an in-play match's three separate order books reprice by the second, so
# that gap is far more likely fast-moving noise a bot already closed than
# something a periodic scan can act on. Events within this many hours of
# their endDate are skipped for that reason, not because the math is wrong.
MIN_HOURS_TO_RESOLUTION_FOR_ARB = 24.0


@dataclass
class OutcomeLeg:
    market_id: str
    question: str
    yes_price: float
    liquidity_usd: float
    order_min_size: float = 0.0  # minimum order size in SHARES (Polymarket's orderMinSize)


@dataclass
class SumConsistencyResult:
    event_title: str
    legs: list[OutcomeLeg]
    sum_yes: float
    deviation_pp: float  # (sum_yes - 1.0) * 100
    direction: str  # "buy_yes_basket" (sum < 100%) or "buy_no_basket" (sum > 100%)

    def minimum_basket_cost_usd(self) -> float:
        """Dollar cost of placing the smallest possible order on every leg
        of this basket -- e.g. for a buy_no_basket, order_min_size shares
        of NO on each leg at (1 - yes_price). This is a FLOOR: it's the
        cheapest this trade could possibly be executed for, not a
        recommended size. If this floor alone eats an unreasonable share of
        a small bankroll, the nominal edge in `deviation_pp` was never
        really accessible at that bankroll size.
        """
        total = 0.0
        for leg in self.legs:
            price = leg.yes_price if self.direction == "buy_yes_basket" else (1 - leg.yes_price)
            total += leg.order_min_size * price
        return total


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


def _sum_of_all_priced_markets(raw_markets: list[dict]) -> float:
    """Sum of outcomePrices[0] across every open, priced market in the raw
    event, regardless of liquidity. Used to detect the sibling failure mode
    to has_unpriced_outcomes: a market that DOES have a real price but sits
    just under the liquidity floor, quietly taking its probability mass out
    of the liquid-legs sum with it.
    """
    total = 0.0
    for m in raw_markets:
        if m.get("closed") is True or m.get("acceptingOrders") is False:
            continue
        try:
            prices = m.get("outcomePrices")
            if isinstance(prices, str):
                prices = json.loads(prices)
            total += float(prices[0])
        except (TypeError, ValueError, IndexError, KeyError):
            continue
    return total


def has_liquidity_masked_mass(
    raw_markets: list[dict], liquid_legs: list["OutcomeLeg"], *, threshold_pp: float = MIN_SUM_DEVIATION_PP
) -> bool:
    """True if real, priced probability mass is sitting on a leg (or legs)
    excluded from `liquid_legs` purely for falling under the liquidity
    floor -- not because it lacks a price.

    Confirmed live 2026-08-20 ("Highest temperature in London on August
    20?"): the correct answer, 24C, was priced at 99.75% but had only
    $1,740 liquidity -- just under the $2,000 floor. Excluding it left only
    9 near-zero "wrong" outcomes, summing to 0.6% and reporting a
    nonsensical "-99.4pp, buy the YES basket for pennies" finding. This
    function catches that: if the FULL priced sum (any liquidity) differs
    from the liquid-only sum by more than `threshold_pp`, the outcome set
    used for scoring is missing real mass, and a sum-below-100% finding
    built from it must not be trusted -- see check_sum_consistency, which
    is where that suppression actually happens.
    """
    liquid_sum = sum(leg.yes_price for leg in liquid_legs)
    full_sum = _sum_of_all_priced_markets(raw_markets)
    return (full_sum - liquid_sum) > (threshold_pp / 100)


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
                order_min_size=float(m.get("orderMinSize") or 0.0),
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


def _min_hours_to_resolution(raw_markets: list[dict]) -> float | None:
    """Soonest endDate across the event's markets, in hours from now (can
    be negative if already past -- e.g. an in-play match). None if no
    market has a parseable endDate.
    """
    hours: list[float] = []
    for m in raw_markets:
        end_date = m.get("endDate")
        if not end_date:
            continue
        try:
            hours.append(hours_until(end_date))
        except ValueError:
            continue
    return min(hours) if hours else None


def scan_event(event: dict, **kwargs) -> SumConsistencyResult | None:
    raw_markets = event.get("markets", [])

    min_hours = _min_hours_to_resolution(raw_markets)
    if min_hours is not None and min_hours < MIN_HOURS_TO_RESOLUTION_FOR_ARB:
        # See MIN_HOURS_TO_RESOLUTION_FOR_ARB: too close to (or past) a
        # leg's resolution time for a periodic scan to trust the snapshot.
        return None

    legs = parse_legs(raw_markets)
    incomplete = has_unpriced_outcomes(raw_markets) or has_liquidity_masked_mass(raw_markets, legs)
    return check_sum_consistency(
        event.get("title", "?"),
        legs,
        outcome_set_incomplete=incomplete,
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
    from .config import STARTING_BANKROLL_USD

    events_scanned, results = run_live_scan()
    for result in results:
        print(f"=== {result.event_title} ===")
        print(f"  {len(result.legs)} liquid legs, sum(YES)={result.sum_yes:.1%}, deviation={result.deviation_pp:+.1f}pp")
        print(f"  Direction: {result.direction}")
        min_cost = result.minimum_basket_cost_usd()
        min_cost_pct = min_cost / STARTING_BANKROLL_USD * 100
        print(
            f"  Minimum execution cost (smallest order on every leg): "
            f"${min_cost:,.2f} ({min_cost_pct:.1f}% of a ${STARTING_BANKROLL_USD:.0f} bankroll)"
        )
        if min_cost_pct > MAX_CORRELATED_GROUP_PCT * 100:
            print(
                f"  NOT PRACTICALLY TRADEABLE at this bankroll size: the minimum possible "
                f"execution already exceeds the {MAX_CORRELATED_GROUP_PCT:.0%} correlated-exposure "
                f"cap on its own, before any sizing decision. Nominal edge is real but inaccessible."
            )
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
