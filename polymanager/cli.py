"""Orchestrates one trading cycle (STEP 1-14 of the mandate) and prints the
REQUIRED OUTPUT dashboard.

Usage:
    python -m polymanager.cli                 # live data cycle (needs network)
    python -m polymanager.cli --demo          # offline walkthrough with clearly-labeled sample data

This module deliberately never invents a probability estimate for a real
market and calls it a recommendation. Steps 5-6 (research the event,
estimate true probability) require actual investigation -- news, base
rates, official sources -- that a human or an LLM-with-live-tools must
perform per market. `estimate_true_probability` below currently wires in
exactly one automated, real strategy: polymanager.btc_touch, which prices
"Will Bitcoin reach $X in <month>?" markets against live spot price and
realized volatility (see that module for the math). Every other market
shape still has no automated estimator and correctly falls through to NO
TRADE -- extend this function with more strategies as they're built and
verified, never with a guess dressed up as a model.
"""

from __future__ import annotations

import argparse
import sys

from . import journal, portfolio
from .api import PolymarketClient
from .btc_touch import estimate as btc_touch_estimate
from .coingecko import CoinGeckoClient
from .config import TIERS
from .dashboard import render_buy_action, render_full_dashboard
from .journal import JournalEntry
from .kelly import recommended_position_size
from .risk import CorrelationGroup, check_correlation_limit, drawdown_multiplier
from .scanner import passing_markets


def make_estimator(btc_spot: float | None, btc_vol_60d: float | None):
    """Build the per-cycle estimate_true_probability function, closing over
    ONE fetch of BTC spot/vol (CoinGecko's free tier rate-limits per-market
    fetches almost immediately, and there's only one live BTC price per
    cycle regardless of how many BTC markets are being screened).

    If btc_spot/btc_vol_60d are None (the CoinGecko fetch failed this
    cycle), BTC markets are correctly skipped rather than priced with stale
    or fabricated numbers -- that failure is surfaced separately by the
    caller, not silently folded into "no edge."
    """

    def estimate_true_probability(screened_market) -> tuple[float, int, str] | None:
        if btc_spot is not None and btc_vol_60d is not None:
            btc = btc_touch_estimate(
                screened_market.question,
                screened_market.end_date,
                spot=btc_spot,
                vol_60d=btc_vol_60d,
            )
            if btc is not None:
                return btc.p_true, btc.confidence, btc.evidence
        return None

    return estimate_true_probability


def run_cycle(*, demo: bool) -> str:
    dashboard, _opportunities, _equity = run_cycle_structured(demo=demo)
    return dashboard


def run_cycle_structured(*, demo: bool) -> tuple[str, list[dict], float]:
    """Same as run_cycle, but also returns the raw opportunities list and
    resulting equity for callers that want structured data (e.g.
    polymanager.scan_all logging a summary) instead of parsing the
    rendered dashboard text.
    """
    state = portfolio.load()

    if demo:
        raw_markets = _demo_fixture_markets()
        data_source_note = "SAMPLE DATA -- NOT LIVE. Network egress to Polymarket is unavailable in this environment."
    else:
        try:
            client = PolymarketClient()
            raw_markets = client.get_markets(limit=100)
            data_source_note = "Live data from gamma-api.polymarket.com."
        except Exception as e:  # noqa: BLE001 - surface any network/API failure plainly
            print(
                f"[polymanager] Could not reach Polymarket's API ({e!r}). "
                "No live trades or recommendations can be made without real market "
                "data. Run with --demo to see the pipeline against labeled sample "
                "data, or run this from an environment with outbound network access.",
                file=sys.stderr,
            )
            state.update_high_water_mark()
            dashboard = render_full_dashboard(state, [], [], [])
            journal.record_no_trade("Market data unavailable (network/API error).")
            return dashboard, [], state.equity()

    screened = passing_markets(raw_markets)

    dd_pct = state.drawdown()
    dd_mult, dd_reason = drawdown_multiplier(dd_pct)

    btc_spot: float | None = None
    btc_vol_60d: float | None = None
    btc_data_error: str | None = None
    if not demo:
        try:
            cg = CoinGeckoClient()
            btc_spot = cg.get_spot_price("bitcoin")
            btc_vol_60d = cg.get_realized_daily_vol("bitcoin", days=60)
        except Exception as e:  # noqa: BLE001 - report distinctly from "no edge"
            btc_data_error = repr(e)
            print(
                f"[polymanager] Could not fetch BTC price data from CoinGecko ({btc_data_error}). "
                "BTC barrier-touch markets will be skipped this cycle rather than priced blind.",
                file=sys.stderr,
            )

    estimate_true_probability = make_estimator(btc_spot, btc_vol_60d)

    opportunities = []
    for m in screened:
        est = estimate_true_probability(m)
        if est is None:
            continue
        p_true, confidence, evidence = est

        # Check both sides: a probability estimate below the YES price is
        # exactly a positive edge on NO (p_true_NO = 1-p_true, price_NO =
        # 1-price_YES), and cli.py used to only ever evaluate YES -- which
        # silently missed every NO-side opportunity. Confirmed live
        # 2026-08-20: with BTC having rallied further, several "reach $X"
        # markets showed a real 3-5pp edge on NO (the model saying the
        # market overpriced YES) that this loop was discarding entirely.
        side, side_price, side_p_true, edge_pp = _best_side(m, p_true)

        tier = _select_tier(edge_pp, confidence)
        if tier is None:
            continue
        sizing = recommended_position_size(
            bankroll=state.cash,
            p_true=side_p_true,
            price=side_price,
            confidence=confidence,
            tier_min_pct=TIERS[tier].min_pct,
            tier_max_pct=TIERS[tier].max_pct,
            drawdown_multiplier=dd_mult,
        )
        if sizing["dollar_amount"] <= 0:
            continue
        opportunities.append(
            {
                "market": m.question,
                "side": side,
                "current_price": side_price,
                "target_entry": side_price,
                "estimated_probability": side_p_true,
                "edge_pp": edge_pp,
                "recommended_investment": sizing["dollar_amount"],
                "confidence": confidence,
                "strategy": TIERS[tier].name,
                "reason": evidence,
            }
        )

    opportunities.sort(key=lambda o: o["edge_pp"] * o["confidence"], reverse=True)

    # STEP 9: check portfolio correlation. Opportunities are accepted in
    # ranked order (best edge*confidence first); an opportunity that would
    # push its correlation group's cumulative exposure over
    # MAX_CORRELATED_GROUP_PCT is dropped rather than resized -- found live
    # 2026-08-20 that this check existed and was tested in polymanager.risk
    # but was never actually called from here, so multiple BTC "reach $X"
    # opportunities (all correlated on the same underlying) could in
    # principle have summed past the cap with nothing stopping it. Today's
    # numbers happened to stay under it by coincidence, not by enforcement.
    accepted_positions = [
        {"market_id": _correlation_key(p.question), "dollars": p.dollars_invested} for p in state.positions
    ]
    accepted_opportunities = []
    for opp in opportunities:
        key = _correlation_key(opp["market"])
        group = CorrelationGroup(label=key, market_ids=[key])
        allowed, _resulting_pct = check_correlation_limit(
            group, accepted_positions, opp["recommended_investment"], state.cash
        )
        if not allowed:
            continue
        accepted_positions.append({"market_id": key, "dollars": opp["recommended_investment"]})
        accepted_opportunities.append(opp)
    opportunities = accepted_opportunities

    position_entries = []  # no live marks available without network; see README
    actions = [render_buy_action(opp) for opp in opportunities]

    state.update_high_water_mark()
    portfolio.save(state)

    if not opportunities:
        btc_note = f" BTC data fetch failed ({btc_data_error})." if btc_data_error else ""
        journal.record_no_trade(
            f"{data_source_note} {len(screened)} markets passed the quality filter; "
            "none had a defensible probability estimate exceeding the edge/confidence bar "
            f"(drawdown throttle: {dd_reason}).{btc_note}"
        )
    else:
        for opp in opportunities:
            journal.append_entry(
                JournalEntry(
                    market=opp["market"],
                    side=opp["side"],
                    entry_price=opp["current_price"],
                    amount_usd=opp["recommended_investment"],
                    estimated_true_probability=opp["estimated_probability"],
                    expected_edge_pp=opp["edge_pp"],
                    confidence=opp["confidence"],
                    strategy=opp["strategy"],
                    reason="Recommended by live cycle; not yet executed (no wallet configured).",
                    key_evidence=opp["reason"],
                    exit_condition="Re-evaluate next cycle; exit if edge closes or model assumptions are invalidated.",
                )
            )

    dashboard = render_full_dashboard(state, opportunities, position_entries, actions)
    return dashboard, opportunities, state.equity()


def _correlation_key(question: str) -> str:
    """Coarse correlation grouping: markets on the same underlying asset
    move together even when their specific thresholds differ. This is
    deliberately narrow -- it catches the one clear case this codebase
    currently produces (multiple BTC "reach/dip to $X" opportunities in one
    cycle), not a general correlation-detection engine. Extend it as more
    correlated-market strategies are added.
    """
    if "bitcoin" in question.lower():
        return "correlated:bitcoin"
    return f"standalone:{question}"


def _best_side(screened_market, p_true_yes: float) -> tuple[str, float, float, float]:
    """Return (side, price, side_p_true, edge_pp) for whichever of YES/NO
    has the better (higher) edge, given a probability estimate for YES.

    Exactly one side can have positive edge at a time (they're mirror
    images: edge_NO = -edge_YES), so this just picks whichever is less bad
    -- callers still gate on _select_tier, so a negative edge_pp here
    simply won't qualify for any tier and the market gets skipped, same as
    before.
    """
    yes_edge_pp = (p_true_yes - screened_market.yes_price) * 100
    no_price = screened_market.no_price
    p_true_no = 1.0 - p_true_yes
    no_edge_pp = (p_true_no - no_price) * 100

    if no_edge_pp > yes_edge_pp:
        return "NO", no_price, p_true_no, no_edge_pp
    return "YES", screened_market.yes_price, p_true_yes, yes_edge_pp


def _select_tier(edge_pp: float, confidence: int) -> str | None:
    # Prefer the highest tier the opportunity qualifies for.
    for key in ("T1_HIGH_CONFIDENCE", "T2_MEDIUM_CONFIDENCE", "T3_EXPERIMENTAL"):
        tier = TIERS[key]
        if edge_pp >= tier.min_edge_pp and confidence >= tier.min_confidence:
            return key
    return None


def _demo_fixture_markets() -> list[dict]:
    """Small, clearly synthetic set of markets shaped like the real Gamma
    API response, used only to exercise the pipeline end-to-end offline.
    Values are illustrative, not real Polymarket data.
    """
    return [
        {
            "id": "demo-1",
            "question": "[DEMO] Will it rain in City X on date Y?",
            "outcomePrices": ["0.50", "0.50"],
            "spread": 0.02,
            "liquidityNum": 10000,
            "volume24hr": 3000,
            "endDate": "2026-12-31T00:00:00Z",
        },
        {
            "id": "demo-2",
            "question": "[DEMO] Will illiquid long-shot event Z occur?",
            "outcomePrices": ["0.05", "0.95"],
            "spread": 0.01,
            "liquidityNum": 500,
            "volume24hr": 100,
            "endDate": "2026-09-01T00:00:00Z",
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Polymarket portfolio-manager cycle.")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use bundled synthetic sample data instead of hitting the live API.",
    )
    args = parser.parse_args()
    print(run_cycle(demo=args.demo))


if __name__ == "__main__":
    main()
