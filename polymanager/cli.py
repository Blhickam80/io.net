"""Orchestrates one trading cycle (STEP 1-14 of the mandate) and prints the
REQUIRED OUTPUT dashboard.

Usage:
    python -m polymanager.cli                 # live data cycle (needs network)
    python -m polymanager.cli --demo          # offline walkthrough with clearly-labeled sample data

This module deliberately never invents a probability estimate for a real
market and calls it a recommendation. Steps 5-6 (research the event,
estimate true probability) require actual investigation -- news, base
rates, official sources -- that a human or an LLM-with-live-tools must
perform per market. Wire your estimator into `estimate_true_probability`
below; until you do, every market falls through to NO TRADE, which is the
only honest default.
"""

from __future__ import annotations

import argparse
import sys

from . import journal, portfolio
from .api import PolymarketClient
from .config import TIERS
from .dashboard import render_full_dashboard
from .kelly import recommended_position_size
from .risk import drawdown_multiplier
from .scanner import passing_markets


def estimate_true_probability(screened_market) -> tuple[float, int, str] | None:
    """Return (p_true, confidence_1_to_10, evidence_summary) for a screened
    market, or None if there isn't a defensible estimate.

    THIS IS THE RESEARCH HOOK. The default implementation refuses to
    guess -- it has no news/polling/base-rate access from inside this pure
    function -- so it always returns None (i.e. "no edge identified"),
    which correctly routes every market to NO TRADE rather than fabricating
    an edge. Replace this with real research (news search, base rates,
    official data) before relying on this for actual capital allocation.
    """
    return None


def run_cycle(*, demo: bool) -> str:
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
            return dashboard

    screened = passing_markets(raw_markets)

    dd_pct = state.drawdown()
    dd_mult, dd_reason = drawdown_multiplier(dd_pct)

    opportunities = []
    for m in screened:
        est = estimate_true_probability(m)
        if est is None:
            continue
        p_true, confidence, evidence = est
        edge_pp = (p_true - m.yes_price) * 100
        tier = _select_tier(edge_pp, confidence)
        if tier is None:
            continue
        sizing = recommended_position_size(
            bankroll=state.cash,
            p_true=p_true,
            price=m.yes_price,
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
                "side": "YES",
                "current_price": m.yes_price,
                "target_entry": m.yes_price,
                "estimated_probability": p_true,
                "edge_pp": edge_pp,
                "recommended_investment": sizing["dollar_amount"],
                "confidence": confidence,
                "strategy": TIERS[tier].name,
                "reason": evidence,
            }
        )

    opportunities.sort(key=lambda o: o["edge_pp"] * o["confidence"], reverse=True)

    position_entries = []  # no live marks available without network; see README
    actions = []

    state.update_high_water_mark()
    portfolio.save(state)

    if not opportunities:
        journal.record_no_trade(
            f"{data_source_note} {len(screened)} markets passed the quality filter; "
            "none had a defensible probability estimate exceeding the edge/confidence bar "
            f"(drawdown throttle: {dd_reason})."
        )

    return render_full_dashboard(state, opportunities, position_entries, actions)


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
