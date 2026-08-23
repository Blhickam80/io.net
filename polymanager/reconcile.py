"""Journal reconciliation: check whether previously-recommended markets
have since resolved, and record what actually happened.

The mandate's journal section explicitly calls for this ("Later record:
Exit Price, Profit/Loss, Was the original thesis correct? What did we
learn?") -- and it was a real gap: journal entries were written once, at
recommendation time, and nothing ever went back to fill in the outcome.
Confirmed live 2026-08-20 that this isn't hypothetical: one of the BTC
"reach $X" markets already resolved (YES, touched $72,500) within hours of
being screened, so short-duration recommendations can resolve well within
a single day's check-in cadence.

IMPORTANT: no wallet is configured (see polymanager/execution.py) and
recommendations from polymanager.cli are exactly that -- recommendations,
never executed trades. This module computes what WOULD have happened had
the recommended size been taken at the recorded entry price, purely for
learning/calibration purposes. It never touches polymanager.portfolio's
cash or realized_pnl (no real capital moved), and every reconciled row
says so explicitly in its lesson_learned text so this is never mistaken
for a record of real money changing hands.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .api import PolymarketClient
from .journal import read_journal, rewrite_all


def _final_side_price(market: dict, side: str) -> float | None:
    """Resolved price for the recommended side (YES or NO), or None if the
    market isn't actually resolved yet (outcomePrices not at/near 0 or 1).
    """
    try:
        import json

        prices = market.get("outcomePrices")
        if isinstance(prices, str):
            prices = json.loads(prices)
        yes_price = float(prices[0])
        no_price = float(prices[1]) if len(prices) > 1 else 1 - yes_price
    except (TypeError, ValueError, IndexError, KeyError):
        return None

    # Require a genuinely settled price, not just "closed" -- a market can
    # be closed pending resolution with prices still mid-range.
    if not (yes_price <= 0.001 or yes_price >= 0.999):
        return None

    return yes_price if side == "YES" else no_price


def reconcile(client: PolymarketClient | None = None) -> dict:
    """Check every unreconciled real recommendation in the journal against
    its market's current state, fill in outcomes for anything resolved,
    and rewrite the journal. Returns a summary dict.
    """
    client = client or PolymarketClient()
    rows = read_journal()

    checked = 0
    resolved = 0
    still_pending = 0
    skipped_no_market_id = 0
    hypothetical_pnl_total = 0.0
    wins = 0

    for row in rows:
        if row.get("market") == "NO TRADE" or row.get("side") not in ("YES", "NO"):
            continue
        if row.get("exit_price"):
            continue  # already reconciled
        market_id = row.get("market_id", "")
        if not market_id:
            skipped_no_market_id += 1
            continue

        checked += 1
        market = client.get_market_by_id(market_id)
        if market is None:
            still_pending += 1
            continue

        final_price = _final_side_price(market, row["side"])
        if final_price is None:
            still_pending += 1
            continue

        entry_price = float(row["entry_price"])
        amount_usd = float(row["amount_usd"])
        shares = amount_usd / entry_price if entry_price > 0 else 0.0
        payout = shares * final_price
        pnl = payout - amount_usd
        thesis_correct = pnl > 0

        row["exit_price"] = f"{final_price:.4f}"
        row["profit_loss_usd"] = f"{pnl:.2f}"
        row["thesis_correct"] = str(thesis_correct)
        row["resolved_at"] = datetime.now(timezone.utc).isoformat()
        row["lesson_learned"] = (
            f"HYPOTHETICAL (recommendation was never executed live, no wallet configured): "
            f"market resolved {row['side']} side to {final_price:.2f}. "
            f"Would have {'gained' if pnl > 0 else 'lost'} ${abs(pnl):.2f} on ${amount_usd:.2f} recommended. "
            f"Estimated probability was {row['estimated_true_probability']}, edge was "
            f"{row['expected_edge_pp']}pp -- thesis {'held up' if thesis_correct else 'did not hold up'}."
        )

        resolved += 1
        hypothetical_pnl_total += pnl
        if thesis_correct:
            wins += 1

    if resolved:
        rewrite_all(rows)

    return {
        "checked": checked,
        "resolved": resolved,
        "still_pending": still_pending,
        "skipped_no_market_id": skipped_no_market_id,
        "hypothetical_pnl_total": round(hypothetical_pnl_total, 2),
        "wins": wins,
        "win_rate_pct": round(wins / resolved * 100, 1) if resolved else None,
    }


def main() -> None:
    summary = reconcile()
    print("Journal reconciliation:")
    print(f"  Candidates checked (had a market_id, not yet reconciled): {summary['checked']}")
    print(f"  Skipped (no market_id captured -- recorded before this feature existed): {summary['skipped_no_market_id']}")
    print(f"  Resolved and reconciled this run: {summary['resolved']}")
    print(f"  Still pending (market not yet resolved): {summary['still_pending']}")
    if summary["resolved"]:
        print(f"  Hypothetical P/L on newly-reconciled recommendations: ${summary['hypothetical_pnl_total']:+.2f}")
        print(f"  Hypothetical win rate: {summary['win_rate_pct']}% ({summary['wins']}/{summary['resolved']})")
        print("  (Hypothetical: no wallet configured, nothing here was real capital.)")


if __name__ == "__main__":
    main()
