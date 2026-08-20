"""Real copy-trading analysis built from Polymarket's actual public data.

polymanager.copytrading defines TraderStats/trader_quality_score() against
an idealized field set (win_rate, max_drawdown, avg_position, a lucky-trade
concentration measure, ...). This module is the honest bridge from what
Polymarket's public API actually returns to what that scorer needs -- and
is explicit about the fields it CANNOT verify rather than inventing them.

What's real and verifiable, from /closed-positions (each row already
carries Polymarket's own computed realizedPnl per resolved market -- no
P/L reconstruction needed):
  - win_rate: fraction of closed positions with realizedPnl > 0
  - avg_position_usd: mean totalBought across closed positions
  - capital_weighted_roi_pct: sum(realizedPnl) / sum(totalBought) -- a real
    return-on-capital-deployed figure, not a volume-based proxy
  - concentration: largest single win as a share of total realized gains
    (directly answers the mandate's "did profit come from one lucky
    trade?" question)
  - trade_order_drawdown_pct: max peak-to-trough decline in CUMULATIVE
    realized P/L ordered by position-close timestamp

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
  - Unrealized P/L on currently open positions: /closed-positions is
    exactly that -- closed only. A trader's live edge could differ from
    their closed-position history.
  - Sample size ("markets_traded") only counts positions actually returned
    by this module's pagination (see fetch_wallet_stats), not the wallet's
    full lifetime history, for large/expensive wallets.
"""

from __future__ import annotations

from dataclasses import dataclass

from .api import PolymarketClient
from .copytrading import TraderStats

# Rough keyword buckets for a specialization guess from market titles.
# Deliberately coarse -- this is a hint, not a verified classification.
_SPECIALTY_KEYWORDS = {
    "politics": ("president", "election", "senate", "congress", "governor", "prime minister", "poll"),
    "crypto": ("bitcoin", "ethereum", "btc", "eth", "crypto"),
    "sports": ("nba", "nfl", "premier league", "champions league", "world cup", "match", "vs "),
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
    actually reports.

    The percentage figure has a real sharp edge, confirmed live
    (2026-08-20): normalizing by the running PEAK means a trader whose
    cumulative P/L only ever reached a small peak (say $50) before a later
    loss of $750 reports a mathematically-correct-but-useless "1500%
    drawdown" -- there's no bankroll/equity base to normalize against, only
    the cumulative-realized-dollars path itself. This is why the dollar
    figure is returned too and should be read alongside the percentage,
    not instead of it: a small-dollar, huge-percent drawdown on a
    high-frequency, small-stakes trader is a very different situation from
    a large-dollar drawdown on a whale.
    """
    ordered = sorted(closed_positions, key=lambda p: p.get("timestamp", 0))
    cumulative = 0.0
    peak = 0.0
    max_drawdown_pct = 0.0
    max_drawdown_usd = 0.0
    for p in ordered:
        cumulative += float(p.get("realizedPnl", 0.0))
        peak = max(peak, cumulative)
        drawdown_usd = peak - cumulative
        max_drawdown_usd = max(max_drawdown_usd, drawdown_usd)
        if peak > 0:
            max_drawdown_pct = max(max_drawdown_pct, drawdown_usd / peak)
    return max_drawdown_pct * 100, max_drawdown_usd


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
    the server's per-page cap) and compute the real, verifiable stats
    described in this module's docstring. Returns None if the wallet has no
    closed-position history available (e.g. still fully open, or the
    address is wrong).
    """
    positions: list[dict] = []
    offset = 0
    while len(positions) < max_positions:
        page = client.get_closed_positions(address, limit=50, offset=offset, sort_by="TIMESTAMP")
        if not page:
            break
        positions.extend(page)
        offset += 50

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
        f"Based on {len(positions)} closed positions only (sampled, not necessarily full lifetime history).",
        "Excludes currently open/unrealized positions entirely.",
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
