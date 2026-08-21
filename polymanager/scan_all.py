"""Convenience entry point: run every live strategy in one command and log
a summary to data/scan_history.jsonl for tracking over time.

- polymanager.cli's per-market cycle (bankroll dashboard, BTC touch pricing)
- polymanager.monotonicity's ladder-consistency scan
- polymanager.sum_consistency's mutually-exclusive-outcome scan

Each strategy still has its own standalone entry point (see README) for
targeted runs; this just saves running three commands during a normal
check-in, and keeps a running record besides.
"""

from __future__ import annotations

from . import monotonicity, performance, reconcile, sum_consistency
from .cli import run_cycle_structured
from .scan_history import ScanSummary, append_summary


def main() -> None:
    print("#" * 70)
    print("# JOURNAL RECONCILIATION (check past recommendations for resolution)")
    print("#" * 70)
    recon_summary = reconcile.reconcile()
    print(f"  Checked: {recon_summary['checked']}, resolved this run: {recon_summary['resolved']}, "
          f"still pending: {recon_summary['still_pending']}")
    if recon_summary["resolved"]:
        print(f"  Hypothetical P/L on newly-resolved recommendations: ${recon_summary['hypothetical_pnl_total']:+.2f} "
              f"(win rate {recon_summary['win_rate_pct']}%) -- hypothetical, no wallet configured.")

    print()
    print("#" * 70)
    print("# MAIN CYCLE (bankroll dashboard + BTC barrier-touch pricing)")
    print("#" * 70)
    dashboard, opportunities, equity = run_cycle_structured(demo=False)
    print(dashboard)

    print()
    print("#" * 70)
    print("# NESTED-OUTCOME MONOTONICITY SCAN")
    print("#" * 70)
    mono_events_scanned, mono_found = monotonicity.run_live_scan()
    for title, v in mono_found:
        print(f"=== {title} ===")
        print(
            f"  VIOLATION: '{v.easier.question}' @ {v.easier.yes_price:.1%} vs "
            f"'{v.harder.question}' @ {v.harder.yes_price:.1%} "
            f"(harder outcome overpriced by {v.magnitude_pp:.1f}pp)"
        )
    print(f"\nScanned {mono_events_scanned} events. Total violations found: {len(mono_found)}.")

    print()
    print("#" * 70)
    print("# MUTUALLY-EXCLUSIVE OUTCOME SUM-CONSISTENCY SCAN")
    print("#" * 70)
    sum_events_scanned, sum_results = sum_consistency.run_live_scan()
    for result in sum_results:
        print(f"=== {result.event_title} ===")
        print(f"  {len(result.legs)} liquid legs, sum(YES)={result.sum_yes:.1%}, deviation={result.deviation_pp:+.1f}pp")
        print(f"  Direction: {result.direction}")
    print(f"\nScanned {sum_events_scanned} events. Material sum-consistency findings: {len(sum_results)}.")

    summary = ScanSummary.now(
        btc_touch_opportunities=len(opportunities),
        monotonicity_events_scanned=mono_events_scanned,
        monotonicity_violations=len(mono_found),
        sum_consistency_events_scanned=sum_events_scanned,
        sum_consistency_findings=len(sum_results),
        sum_consistency_event_titles=[result.event_title for result in sum_results],
        bankroll_equity=equity,
        reconciled_this_run=recon_summary["resolved"],
        reconciled_hypothetical_pnl=recon_summary["hypothetical_pnl_total"],
    )
    append_summary(summary)
    print(f"\nScan summary logged to data/scan_history.jsonl ({summary.timestamp}).")

    print()
    print("#" * 70)
    print("# PERFORMANCE ANALYSIS")
    print("#" * 70)
    print(performance.render_report(performance.compute_performance()))


if __name__ == "__main__":
    main()
