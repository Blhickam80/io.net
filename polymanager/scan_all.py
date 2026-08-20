"""Convenience entry point: run every live strategy in one command.

- polymanager.cli's per-market cycle (bankroll dashboard, BTC touch pricing)
- polymanager.monotonicity's ladder-consistency scan
- polymanager.sum_consistency's mutually-exclusive-outcome scan

Each strategy still has its own standalone entry point (see README) for
targeted runs; this just saves running three commands during a normal
check-in.
"""

from __future__ import annotations

from . import monotonicity, sum_consistency
from .cli import run_cycle


def main() -> None:
    print("#" * 70)
    print("# MAIN CYCLE (bankroll dashboard + BTC barrier-touch pricing)")
    print("#" * 70)
    print(run_cycle(demo=False))

    print()
    print("#" * 70)
    print("# NESTED-OUTCOME MONOTONICITY SCAN")
    print("#" * 70)
    monotonicity.main()

    print()
    print("#" * 70)
    print("# MUTUALLY-EXCLUSIVE OUTCOME SUM-CONSISTENCY SCAN")
    print("#" * 70)
    sum_consistency.main()


if __name__ == "__main__":
    main()
