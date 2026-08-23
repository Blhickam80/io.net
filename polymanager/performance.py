"""Performance Analysis: aggregate the (reconciled) trading journal into
the metrics the mandate's PERFORMANCE ANALYSIS section calls for --
win rate, average win/loss, profit factor, strategy-specific breakdown --
none of which existed as a computed view before this. polymanager.dashboard
only ever renders a single cycle's snapshot; this looks across every
reconciled outcome in the journal's history.

Every number here is HYPOTHETICAL, same caveat as polymanager.reconcile:
no wallet is configured, so these are recommendation-quality metrics
(would this system's calls have made money if followed?), not a record of
real trading performance.

WHY hypothetical_max_drawdown EXISTS AT ALL (audited 2026-08-20):
polymanager.risk's drawdown-throttle system (DRAWDOWN_RULES, checked every
cycle via polymanager.cli) is structurally unreachable in this deployment.
Confirmed by reading polymanager.portfolio.PortfolioState: cli.py never
appends to state.positions or decrements state.cash anywhere (verified by
grep -- the only reference to state.positions is a read, for correlation
accounting). So equity() is permanently cash ($200, never spent) plus zero
open positions, exactly equal to high_water_mark forever, so drawdown() is
always precisely 0.0 -- not "hasn't triggered yet" like the correlation
cap (see README), but genuinely unreachable given the current no-wallet
architecture. hypothetical_max_drawdown_pct/usd below is the closest real
substitute available without a wallet: a peak-to-trough curve over this
system's own reconciled recommendation outcomes, giving the mandate's
"Maximum Drawdown" metric something real to report on, rather than staying
permanently and misleadingly at 0%.
"""

from __future__ import annotations

from dataclasses import dataclass

from .journal import read_journal
from .pnl_stats import cumulative_pnl_drawdown


@dataclass
class PerformanceReport:
    n_reconciled: int
    n_pending: int
    n_unreconcilable: int
    n_no_trade_cycles: int
    win_rate_pct: float | None
    avg_win_usd: float | None
    avg_loss_usd: float | None
    profit_factor: float | None  # gross wins / gross losses; None if no losses yet
    total_hypothetical_pnl_usd: float
    hypothetical_max_drawdown_pct: float
    hypothetical_max_drawdown_usd: float
    by_strategy: dict[str, dict]  # strategy name -> {n, win_rate_pct, pnl_usd}


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compute_performance(rows: list[dict] | None = None) -> PerformanceReport:
    rows = rows if rows is not None else read_journal()

    no_trade_rows = [r for r in rows if r.get("market") == "NO TRADE"]
    recommendation_rows = [r for r in rows if r.get("side") in ("YES", "NO")]
    reconciled = [r for r in recommendation_rows if r.get("exit_price")]
    unreconciled = [r for r in recommendation_rows if not r.get("exit_price")]
    # polymanager.reconcile permanently skips any row with no market_id
    # (recorded before that field was captured) -- it will never resolve,
    # so it isn't "pending" in the sense of "waiting for a market to
    # settle." Real gap found live 2026-08-21: 11 such rows from the
    # project's first hour were silently inflating this count with no
    # path to ever becoming reconciled.
    pending = [r for r in unreconciled if r.get("market_id")]
    unreconcilable = [r for r in unreconciled if not r.get("market_id")]

    wins = [r for r in reconciled if r.get("thesis_correct") == "True"]
    losses = [r for r in reconciled if r.get("thesis_correct") == "False"]

    win_pnls = [_to_float(r["profit_loss_usd"]) for r in wins]
    win_pnls = [p for p in win_pnls if p is not None]
    loss_pnls = [_to_float(r["profit_loss_usd"]) for r in losses]
    loss_pnls = [p for p in loss_pnls if p is not None]

    win_rate_pct = round(len(wins) / len(reconciled) * 100, 1) if reconciled else None
    avg_win_usd = round(sum(win_pnls) / len(win_pnls), 2) if win_pnls else None
    avg_loss_usd = round(sum(loss_pnls) / len(loss_pnls), 2) if loss_pnls else None
    gross_wins = sum(win_pnls)
    gross_losses = abs(sum(loss_pnls))
    profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else None
    total_pnl = round(gross_wins - gross_losses, 2)

    by_strategy: dict[str, dict] = {}
    for r in reconciled:
        strategy = r.get("strategy", "unknown")
        bucket = by_strategy.setdefault(strategy, {"n": 0, "wins": 0, "pnl_usd": 0.0})
        bucket["n"] += 1
        if r.get("thesis_correct") == "True":
            bucket["wins"] += 1
        pnl = _to_float(r.get("profit_loss_usd", ""))
        if pnl is not None:
            bucket["pnl_usd"] += pnl
    for strategy, bucket in by_strategy.items():
        bucket["win_rate_pct"] = round(bucket["wins"] / bucket["n"] * 100, 1) if bucket["n"] else None
        bucket["pnl_usd"] = round(bucket["pnl_usd"], 2)
        del bucket["wins"]

    # Order by resolved_at (when polymanager.reconcile noticed the outcome,
    # stamped at reconciliation time) rather than the recommendation's own
    # `date` -- a slow-resolving December market recommended today would
    # otherwise sort before a fast-resolving one recommended tomorrow,
    # which is backwards for a P/L-over-time curve. resolved_at is a
    # reconciliation-cadence proxy for actual resolution time, not exact to
    # the minute, but it's monotonically correct relative to when this
    # system learned each outcome.
    ordered = sorted(reconciled, key=lambda r: r.get("resolved_at", ""))
    ordered_pnls = [p for p in (_to_float(r.get("profit_loss_usd", "")) for r in ordered) if p is not None]
    dd_pct, dd_usd = cumulative_pnl_drawdown(ordered_pnls)

    return PerformanceReport(
        n_reconciled=len(reconciled),
        n_pending=len(pending),
        n_unreconcilable=len(unreconcilable),
        n_no_trade_cycles=len(no_trade_rows),
        win_rate_pct=win_rate_pct,
        avg_win_usd=avg_win_usd,
        avg_loss_usd=avg_loss_usd,
        profit_factor=profit_factor,
        total_hypothetical_pnl_usd=total_pnl,
        hypothetical_max_drawdown_pct=round(dd_pct, 1),
        hypothetical_max_drawdown_usd=round(dd_usd, 2),
        by_strategy=by_strategy,
    )


def render_report(report: PerformanceReport) -> str:
    lines = [
        "PERFORMANCE ANALYSIS (hypothetical -- no wallet configured, no real capital moved)",
        f"Reconciled recommendations: {report.n_reconciled}",
        f"Still pending (market not yet resolved): {report.n_pending}",
        f"NO TRADE cycles: {report.n_no_trade_cycles}",
    ]
    if report.n_unreconcilable:
        lines.append(
            f"Unreconcilable (recorded before market_id capture existed -- will never resolve): "
            f"{report.n_unreconcilable}"
        )
    if report.n_reconciled == 0:
        lines.append("No reconciled outcomes yet -- nothing to analyze until markets resolve.")
        return "\n".join(lines)

    lines += [
        f"Win rate: {report.win_rate_pct}%",
        f"Average win: ${report.avg_win_usd if report.avg_win_usd is not None else 0:,.2f}",
        f"Average loss: ${report.avg_loss_usd if report.avg_loss_usd is not None else 0:,.2f}",
        f"Profit factor: {report.profit_factor if report.profit_factor is not None else 'n/a (no losses yet)'}",
        f"Total hypothetical P/L: ${report.total_hypothetical_pnl_usd:+,.2f}",
        f"Hypothetical max drawdown: {report.hypothetical_max_drawdown_pct}% "
        f"(${report.hypothetical_max_drawdown_usd:,.2f}) -- see module docstring, "
        "not equivalent to real portfolio drawdown (that's structurally 0% until "
        "a wallet is configured and real capital moves; see README).",
        "",
        "By strategy:",
    ]
    for strategy, stats in sorted(report.by_strategy.items()):
        lines.append(
            f"  {strategy}: n={stats['n']}, win rate={stats['win_rate_pct']}%, P/L=${stats['pnl_usd']:+,.2f}"
        )
    return "\n".join(lines)


def main() -> None:
    print(render_report(compute_performance()))


if __name__ == "__main__":
    main()
