"""User-curated trader watchlist: wallet addresses sourced from outside
Polymarket's own leaderboard (Twitter posts, articles, word of mouth about
"who's actually good") get logged here, then run through the exact same
real-data analysis as polymanager.wallet_research's top-10-by-PNL scan.

A claim that a wallet is a good trader is not itself evidence -- it's a
lead. Nothing here is trusted until fetch_wallet_stats() pulls that
wallet's real closed-position history from data-api.polymarket.com and
computes the same win-rate/ROI/concentration/drawdown numbers used
elsewhere in this repo. If a claimed address returns no usable history,
that's reported plainly, not smoothed over.

CSV, not JSONL, because entries are keyed by address and may get updated
(more context added, a re-run of the stats) rather than purely appended --
same append-then-occasionally-rewrite pattern as polymanager.journal.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .api import PolymarketClient
from .copytrading import rank_traders
from .wallet_research import fetch_wallet_stats, to_trader_stats

DEFAULT_WATCHLIST_PATH = Path(__file__).resolve().parent.parent / "data" / "trader_watchlist.csv"

FIELDNAMES = ["address", "label", "source", "claim", "date_added", "notes"]


@dataclass
class WatchlistEntry:
    address: str
    label: str = ""  # username/handle if known, else blank
    source: str = ""  # e.g. "twitter @handle", "article: <title/url>"
    claim: str = ""  # what the source claims about this trader, verbatim/paraphrased
    date_added: str = ""
    notes: str = ""

    def __post_init__(self):
        if not self.date_added:
            self.date_added = datetime.now(timezone.utc).date().isoformat()


def load_watchlist(path: Path = DEFAULT_WATCHLIST_PATH) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def add_entry(entry: WatchlistEntry, path: Path = DEFAULT_WATCHLIST_PATH) -> None:
    """Upsert by address (case-insensitive): updates the existing row if
    this address is already on the list, otherwise appends a new one.
    """
    rows = load_watchlist(path)
    addr_lower = entry.address.lower()
    for i, row in enumerate(rows):
        if row.get("address", "").lower() == addr_lower:
            # date_added is "when this wallet was first added" -- keep the
            # original even on an update, not the auto-stamped date on this
            # call's WatchlistEntry (__post_init__ always fills it in).
            updates = {k: v for k, v in asdict(entry).items() if v and k != "date_added"}
            rows[i] = {**row, **updates}
            break
    else:
        rows.append(asdict(entry))

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})


def _lifetime_stats(client: PolymarketClient, address: str) -> tuple[float, float]:
    """Best-effort lookup of a wallet's lifetime PNL/volume from the
    leaderboard (works if the wallet ranks in the OVERALL/ALL-time list);
    falls back to (0.0, 0.0) if it doesn't rank there -- most watchlist
    wallets from outside sources won't be top-50 whales.
    """
    try:
        entries = client.get_leaderboard(category="OVERALL", time_period="ALL", user=address, limit=1)
        if entries:
            return float(entries[0].get("pnl", 0.0)), float(entries[0].get("vol", 0.0))
    except Exception:  # noqa: BLE001 - leaderboard lookup is best-effort only
        pass
    return 0.0, 0.0


def research_watchlist(path: Path = DEFAULT_WATCHLIST_PATH, client: PolymarketClient | None = None) -> None:
    client = client or PolymarketClient()
    entries = load_watchlist(path)
    if not entries:
        print("Watchlist is empty -- nothing to research yet.")
        return

    print(f"Researching {len(entries)} watchlisted wallet(s) against real closed-position data:\n")
    results = []
    for row in entries:
        address = row["address"]
        label = row.get("label") or address
        lifetime_pnl, lifetime_vol = _lifetime_stats(client, address)
        stats = fetch_wallet_stats(client, address, label, lifetime_pnl_usd=lifetime_pnl, lifetime_volume_usd=lifetime_vol)
        if stats is None:
            print(f"=== {label} ({address}) === NO closed-position history found -- unverified claim.")
            if row.get("claim"):
                print(f"  Claim (source: {row.get('source', '?')}): {row['claim']}")
            print()
            continue
        results.append(stats)
        print(f"=== {label} ({address}) ===")
        if row.get("claim"):
            print(f"  Claim (source: {row.get('source', '?')}): {row['claim']}")
        print(f"  Lifetime PNL (leaderboard lookup): ${stats.lifetime_pnl_usd:,.0f}" + (" (not top-ranked)" if stats.lifetime_pnl_usd == 0 else ""))
        print(f"  Sampled closed positions: {stats.n_closed_positions_sampled}")
        print(f"  Win rate: {stats.win_rate_pct}%")
        print(f"  Avg position size: ${stats.avg_position_usd:,.0f}")
        print(f"  Capital-weighted ROI: {stats.capital_weighted_roi_pct}%")
        print(f"  Concentration (top win): {stats.concentration_pct}% of realized gains")
        print(f"  Trade-order drawdown: {stats.trade_order_drawdown_pct}% (${stats.trade_order_drawdown_usd:,.0f})")
        print(f"  Specialty guess: {stats.specialty_guess}")
        print()

    if not results:
        return
    ranked = rank_traders([to_trader_stats(r) for r in results])
    print("=== Quality-score ranking ===")
    for row in ranked:
        print(f"  {row['quality_score']:>5.1f}  {row['stats'].address}  type={row['type']}")


def main() -> None:
    research_watchlist()


if __name__ == "__main__":
    main()
