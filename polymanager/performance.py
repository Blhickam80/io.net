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
"""

from __future__ import annotations

from dataclasses import dataclass

from .journal import read_journal


@dataclass
class PerformanceReport:
    n_reconciled: int
    n_pending: int
    n_no_trade_cycles: int
    win_rate_pct: float | None
    avg_win_usd: float | None
    avg_loss_usd: float | None
    profit_factor: float | None  # gross wins / gross losses; None if no losses yet
    total_hypothetical_pnl_usd: float
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
    pending = [r for r in recommendation_rows if not r.get("exit_price")]

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

    return PerformanceReport(
        n_reconciled=len(reconciled),
        n_pending=len(pending),
        n_no_trade_cycles=len(no_trade_rows),
        win_rate_pct=win_rate_pct,
        avg_win_usd=avg_win_usd,
        avg_loss_usd=avg_loss_usd,
        profit_factor=profit_factor,
        total_hypothetical_pnl_usd=total_pnl,
        by_strategy=by_strategy,
    )


def render_report(report: PerformanceReport) -> str:
    lines = [
        "PERFORMANCE ANALYSIS (hypothetical -- no wallet configured, no real capital moved)",
        f"Reconciled recommendations: {report.n_reconciled}",
        f"Still pending (market not yet resolved): {report.n_pending}",
        f"NO TRADE cycles: {report.n_no_trade_cycles}",
    ]
    if report.n_reconciled == 0:
        lines.append("No reconciled outcomes yet -- nothing to analyze until markets resolve.")
        return "\n".join(lines)

    lines += [
        f"Win rate: {report.win_rate_pct}%",
        f"Average win: ${report.avg_win_usd if report.avg_win_usd is not None else 0:,.2f}",
        f"Average loss: ${report.avg_loss_usd if report.avg_loss_usd is not None else 0:,.2f}",
        f"Profit factor: {report.profit_factor if report.profit_factor is not None else 'n/a (no losses yet)'}",
        f"Total hypothetical P/L: ${report.total_hypothetical_pnl_usd:+,.2f}",
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
