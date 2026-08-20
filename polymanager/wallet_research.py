"""Real copy-trading analysis built from Polymarket's actual public data.

polymanager.copytrading defines TraderStats/trader_quality_score() against
an idealized field set (win_rate, max_drawdown, avg_position, a lucky-trade
concentration measure, ...). This module is the honest bridge from what
Polymarket's public API actually returns to what that scorer needs -- and
is explicit about the fields it CANNOT verify rather than inventing them.

What's real and verifiable, from /closed-positions (each row already
carries Polymarket's own computed realizedPnl per resolved market -- no
P/L reconstruction needed):
  - win_rate: fraction of positions with realizedPnl > 0
  - avg_position_usd: mean totalBought across positions
  - capital_weighted_roi_pct: sum(realizedPnl) / sum(totalBought) -- a real
    return-on-capital-deployed figure, not a volume-based proxy
  - concentration: largest single win as a share of total realized gains
    (directly answers the mandate's "did profit come from one lucky
    trade?" question)
  - trade_order_drawdown_pct: max peak-to-trough decline in CUMULATIVE
    realized P/L ordered by position-close timestamp

CORRECTION, found live 2026-08-20 researching a real watchlisted wallet:
/closed-positions alone is survivorship-biased. Confirmed directly via
/positions (the "open" endpoint) on a real wallet: 10 of its markets had
resolved against it (curPrice=0, endDate already past, cashPnl deeply
negative -- e.g. -$46,828 on one) but were STILL showing as "open"
because nobody has to spend gas redeeming a worthless position -- there's
nothing to claim. Only wins reliably get redeemed (and therefore show up
in /closed-positions), because redeeming is how you collect the payout.
Relying on /closed-positions alone measured that wallet's win rate at
94.7%; once genuinely-resolved-but-unredeemed losses are counted the real
figure is far lower. fetch_wallet_stats() below now also scans
/positions and folds in any position with curPrice <= 0.001 (the same
"genuinely settled" threshold polymanager.reconcile uses) as a loss,
using its cashPnl (captures fees) and endDate (as a timestamp proxy,
since open positions don't carry the `timestamp` field closed ones do).
This correction applies to every wallet this module has ever scored,
including the earlier top-10-leaderboard run in this README -- treat any
number computed before this fix as upper-bound-on-win-rate, not fact.

What's NOT computed here, and why -- reported explicitly rather than
guessed:
  - True mark-to-market drawdown: would need intraday equity snapshots,
    which the public API doesn't expose. trade_order_drawdown_pct is a
    real but different thing (see its docstring).
  - "How early they enter": would need each trade's entry price/time
    matched against that market's full historical price path to see where
    in the distribution they bought. Not attempted -- avgPrice extremity is
    a weak, unlabeled proxy at best and is deliberately left out rather
    than presented as this signal.
  - Unrealized P/L on positions that are GENUINELY still open (curPrice
    between 0 and 1, market not yet resolved): still excluded, correctly
    -- a trader's live edge could differ from their settled history, and
    an in-progress position's current mark isn't a verdict on the trade.
  - Sample size ("markets_traded") only counts positions actually returned
    by this module's pagination (see fetch_wallet_stats), not the wallet's
    full lifetime history, for large/expensive wallets.
"""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass

from .api import PolymarketClient
from .copytrading import TraderStats
from .pnl_stats import cumulative_pnl_drawdown

# Same "genuinely settled" threshold polymanager.reconcile uses for a
# resolved market's price -- 0 or 1, not just "very small/large."
_SETTLED_PRICE_EPSILON = 0.001


def _end_date_to_timestamp(end_date: str) -> float:
    """Open positions carry `endDate` (a date string), not the Unix
    `timestamp` closed positions have. Used only to order the drawdown
    curve -- unparseable/missing dates sort first (0), which is a safe
    default since it only affects relative ordering among the small number
    of unredeemed-loss positions this is applied to.
    """
    if not end_date:
        return 0.0
    try:
        return datetime.fromisoformat(end_date.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return 0.0


def _unredeemed_losses_as_closed(open_positions: list[dict]) -> list[dict]:
    """Convert open positions that have genuinely resolved against the
    wallet (curPrice near 0) into closed-position-shaped dicts, so they
    can be folded into the same win/loss/PnL/drawdown math. Uses cashPnl
    (captures entry fees) rather than reconstructing from totalBought.
    Positions with curPrice strictly between 0 and 1 are real open risk,
    not yet decided, and are correctly left out.
    """
    losses = []
    for p in open_positions:
        cur_price = p.get("curPrice")
        if cur_price is None or float(cur_price) > _SETTLED_PRICE_EPSILON:
            continue
        losses.append(
            {
                "realizedPnl": float(p.get("cashPnl", 0.0)),
                "totalBought": float(p.get("totalBought", 0.0)),
                "title": p.get("title", ""),
                "timestamp": _end_date_to_timestamp(p.get("endDate", "")),
            }
        )
    return losses

# Rough keyword buckets for a specialization guess from market titles.
# Deliberately coarse -- this is a hint, not a verified classification.
_SPECIALTY_KEYWORDS = {
    "politics": ("president", "election", "senate", "congress", "governor", "prime minister", "poll"),
    "crypto": ("bitcoin", "ethereum", "btc", "eth", "crypto"),
    # "win on <date>" and "O/U"/"spread:" catch Polymarket's common soccer
    # moneyline/totals phrasing (e.g. "Will Paris Saint-Germain win on
    # 2026-08-12?"), missed entirely before this fix -- confirmed live
    # 2026-08-20 misclassifying an 18-of-19-soccer-market wallet as
    # "unclassified."
    "sports": (
        "nba", "nfl", "premier league", "champions league", "world cup", "match", "vs ",
        "win on", "o/u", "spread:", " fc ", "fc?", "calcio", "united fc",
    ),
    "macro": ("fed", "interest rate", "inflation", "gdp", "recession"),
}


def _guess_specialty(titles: list[str]) -> str:
    counts = {k: 0 for k in _SPECIALTY_KEYWORDS}
    for title in titles:
        lower = title.lower()
        for specialty, keywords in _SPECIALTY_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                counts[specialty] += 1
    if not any(counts.values()):
        return "unclassified"
    top = max(counts, key=lambda k: counts[k])
    return top if counts[top] >= len(titles) * 0.3 else "mixed"


@dataclass
class RealWalletStats:
    address: str
    username: str
    n_closed_positions_sampled: int
    win_rate_pct: float
    avg_position_usd: float
    total_realized_pnl_usd: float
    capital_weighted_roi_pct: float
    concentration_pct: float  # largest single win / total positive realized PnL
    trade_order_drawdown_pct: float
    trade_order_drawdown_usd: float
    specialty_guess: str
    lifetime_pnl_usd: float  # from the leaderboard, not this sample
    lifetime_volume_usd: float
    caveats: list[str]


def _trade_order_drawdown(closed_positions: list[dict]) -> tuple[float, float]:
    """Max peak-to-trough decline in cumulative realized P/L, ordered by
    when each position closed. Returns (pct, usd). This is NOT true
    mark-to-market drawdown (it ignores unrealized swings while positions
    were open, and treats every position's P/L as landing all at once at
    close) -- it is a real, honest measure of "how much cumulative realized
    P/L gave back before recovering," computed from data Polymarket
    actually reports. See polymanager.pnl_stats.cumulative_pnl_drawdown for
    the shared math (also used by polymanager.performance) and its
    docstring for the percentage figure's real sharp edge.
    """
    ordered = sorted(closed_positions, key=lambda p: p.get("timestamp", 0))
    pnls = [float(p.get("realizedPnl", 0.0)) for p in ordered]
    return cumulative_pnl_drawdown(pnls)


def fetch_wallet_stats(
    client: PolymarketClient,
    address: str,
    username: str,
    *,
    lifetime_pnl_usd: float,
    lifetime_volume_usd: float,
    max_positions: int = 150,
) -> RealWalletStats | None:
    """Pull up to `max_positions` closed positions (paginated 50 at a time,
    the server's per-page cap), plus any open position that has genuinely
    resolved against the wallet but never been redeemed (see module
    docstring's CORRECTION), and compute the real, verifiable stats
    described in this module's docstring. Returns None if the wallet has no
    settled-position history available at all (e.g. still fully open with
    no resolved losses either, or the address is wrong).
    """
    positions: list[dict] = []
    offset = 0
    while len(positions) < max_positions:
        page = client.get_closed_positions(address, limit=50, offset=offset, sort_by="TIMESTAMP")
        if not page:
            break
        positions.extend(page)
        offset += 50

    n_closed = len(positions)

    try:
        open_positions = client.get_wallet_positions(address)
        unredeemed_losses = _unredeemed_losses_as_closed(open_positions)
    except Exception:  # noqa: BLE001 - this enrichment is best-effort; don't fail the whole scan for it
        unredeemed_losses = []
    positions.extend(unredeemed_losses)

    if not positions:
        return None

    wins = [p for p in positions if float(p.get("realizedPnl", 0.0)) > 0]
    win_rate_pct = len(wins) / len(positions) * 100

    total_bought = sum(float(p.get("totalBought", 0.0)) for p in positions)
    avg_position_usd = total_bought / len(positions) if positions else 0.0

    total_realized_pnl = sum(float(p.get("realizedPnl", 0.0)) for p in positions)
    capital_weighted_roi_pct = (total_realized_pnl / total_bought * 100) if total_bought > 0 else 0.0

    total_positive_pnl = sum(float(p.get("realizedPnl", 0.0)) for p in wins)
    largest_win = max((float(p.get("realizedPnl", 0.0)) for p in wins), default=0.0)
    concentration_pct = (largest_win / total_positive_pnl * 100) if total_positive_pnl > 0 else 0.0

    drawdown_pct, drawdown_usd = _trade_order_drawdown(positions)
    specialty = _guess_specialty([p.get("title", "") for p in positions])

    caveats = [
        f"Based on {n_closed} redeemed/closed positions plus {len(unredeemed_losses)} genuinely-resolved-but-"
        f"unredeemed losses ({len(positions)} total) -- sampled, not necessarily full lifetime history.",
        "Genuinely still-open (undecided) positions are correctly excluded entirely.",
        "trade_order_drawdown_pct is realized-P/L-ordered, not true mark-to-market drawdown, and can "
        "exceed 100% when the cumulative-P/L peak it's normalized against was small -- read it "
        "alongside trade_order_drawdown_usd, not alone.",
        "specialty_guess is a coarse keyword match on market titles, not a verified classification.",
        "'How early they enter' is not computed -- would need full historical price paths per market.",
    ]

    return RealWalletStats(
        address=address,
        username=username,
        n_closed_positions_sampled=len(positions),
        win_rate_pct=round(win_rate_pct, 1),
        avg_position_usd=round(avg_position_usd, 2),
        total_realized_pnl_usd=round(total_realized_pnl, 2),
        capital_weighted_roi_pct=round(capital_weighted_roi_pct, 2),
        concentration_pct=round(concentration_pct, 1),
        trade_order_drawdown_pct=round(drawdown_pct, 1),
        trade_order_drawdown_usd=round(drawdown_usd, 2),
        specialty_guess=specialty,
        lifetime_pnl_usd=lifetime_pnl_usd,
        lifetime_volume_usd=lifetime_volume_usd,
        caveats=caveats,
    )


def to_trader_stats(w: RealWalletStats) -> TraderStats:
    """Map onto polymanager.copytrading.TraderStats for scoring. Fields
    with no real-data source (largest_single_win_pct_of_pnl IS available
    here and mapped; avg_entry_vs_final_price_gap is NOT and is left at its
    dataclass default of 0.0 -- meaning the "enters early" component of
    trader_quality_score is always neutral/zero for wallets scored this
    way. Callers should not read a nonzero "enters early" contribution into
    scores produced from this function.
    """
    return TraderStats(
        address=w.address,
        roi_pct=w.capital_weighted_roi_pct,
        realized_pnl_usd=w.total_realized_pnl_usd,
        markets_traded=w.n_closed_positions_sampled,
        win_rate_pct=w.win_rate_pct,
        avg_position_usd=w.avg_position_usd,
        max_drawdown_pct=w.trade_order_drawdown_pct,
        specialty=w.specialty_guess,
        largest_single_win_pct_of_pnl=w.concentration_pct,
    )


def main() -> None:
    client = PolymarketClient()
    leaders = client.get_leaderboard(category="OVERALL", time_period="ALL", order_by="PNL", limit=10)

    print(f"Top {len(leaders)} traders by all-time PNL (live, data-api.polymarket.com/v1/leaderboard):\n")
    results: list[RealWalletStats] = []
    for entry in leaders:
        address = entry["proxyWallet"]
        username = entry.get("userName") or address
        stats = fetch_wallet_stats(
            client,
            address,
            username,
            lifetime_pnl_usd=entry["pnl"],
            lifetime_volume_usd=entry["vol"],
        )
        if stats is None:
            print(f"{username}: no closed-position history returned -- skipped.")
            continue
        results.append(stats)
        print(f"=== {username} ({address}) ===")
        print(f"  Lifetime PNL (leaderboard): ${stats.lifetime_pnl_usd:,.0f}")
        print(f"  Sampled closed positions:   {stats.n_closed_positions_sampled}")
        print(f"  Win rate:                   {stats.win_rate_pct}%")
        print(f"  Avg position size:          ${stats.avg_position_usd:,.0f}")
        print(f"  Capital-weighted ROI:       {stats.capital_weighted_roi_pct}%")
        print(f"  Concentration (top win):    {stats.concentration_pct}% of realized gains")
        print(
            f"  Trade-order drawdown:       {stats.trade_order_drawdown_pct}% "
            f"(${stats.trade_order_drawdown_usd:,.0f})"
        )
        print(f"  Specialty guess:            {stats.specialty_guess}")
        print()

    if not results:
        print("No wallets returned usable closed-position data.")
        return

    from .copytrading import rank_traders

    ranked = rank_traders([to_trader_stats(r) for r in results])
    print("=== Quality-score ranking (see caveats above: 'enters early' component is always 0 here) ===")
    for row in ranked:
        print(f"  {row['quality_score']:>5.1f}  {row['stats'].address}  type={row['type']}")


if __name__ == "__main__":
    main()
