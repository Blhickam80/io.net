"""Append-only log of every scan_all run, so repeated check-ins across a
day (or longer) build a real record instead of each run being disposable
console output. Complements the trading journal (which only records
trade-level decisions) with per-cycle strategy-level summaries -- the
mandate's "track strategy-specific performance over time" requirement
can't be met from a single run.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
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
    # Which specific events had a sum-consistency finding this run. A raw
    # *count* staying stable across scans (e.g. "6 findings" every time)
    # doesn't tell you whether it's the same structural mispricing persisting
    # or a different rotating set of events coincidentally landing on the
    # same count -- added 2026-08-21 to make that answerable from the log
    # instead of requiring a fresh live scan each time.
    sum_consistency_event_titles: list[str] = field(default_factory=list)

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


def persistent_sum_consistency_titles(history: list[dict]) -> set[str]:
    """Event titles that had a sum-consistency finding in *every* scan that
    recorded any titles at all (older entries with no titles field are
    ignored rather than treated as "title absent"). Empty if fewer than 2
    such scans exist -- persistence isn't meaningful from a single sample.
    """
    tagged_runs = [set(h["sum_consistency_event_titles"]) for h in history if h.get("sum_consistency_event_titles")]
    if len(tagged_runs) < 2:
        return set()
    return set.intersection(*tagged_runs)
