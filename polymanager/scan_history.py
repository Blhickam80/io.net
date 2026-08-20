"""Append-only log of every scan_all run, so repeated check-ins across a
day (or longer) build a real record instead of each run being disposable
console output. Complements the trading journal (which only records
trade-level decisions) with per-cycle strategy-level summaries -- the
mandate's "track strategy-specific performance over time" requirement
can't be met from a single run.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_HISTORY_PATH = Path(__file__).resolve().parent.parent / "data" / "scan_history.jsonl"


@dataclass
class ScanSummary:
    timestamp: str
    btc_touch_opportunities: int
    monotonicity_events_scanned: int
    monotonicity_violations: int
    sum_consistency_events_scanned: int
    sum_consistency_findings: int
    bankroll_equity: float
    reconciled_this_run: int = 0
    reconciled_hypothetical_pnl: float = 0.0
    notes: str = ""

    @classmethod
    def now(cls, **kwargs) -> "ScanSummary":
        return cls(timestamp=datetime.now(timezone.utc).isoformat(), **kwargs)


def append_summary(summary: ScanSummary, path: Path = DEFAULT_HISTORY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(asdict(summary)) + "\n")


def read_history(path: Path = DEFAULT_HISTORY_PATH) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]
