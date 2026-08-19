"""Trading journal: one row per decision (trade or explicit no-trade),
append-only CSV so the history is diffable and greppable in git.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_JOURNAL_PATH = Path(__file__).resolve().parent.parent / "data" / "trading_journal.csv"

FIELDNAMES = [
    "date",
    "market",
    "side",
    "entry_price",
    "amount_usd",
    "estimated_true_probability",
    "expected_edge_pp",
    "confidence",
    "strategy",
    "reason",
    "key_evidence",
    "exit_condition",
    "exit_price",
    "profit_loss_usd",
    "thesis_correct",
    "lesson_learned",
]


@dataclass
class JournalEntry:
    market: str
    side: str
    entry_price: float
    amount_usd: float
    estimated_true_probability: float
    expected_edge_pp: float
    confidence: int
    strategy: str
    reason: str
    key_evidence: str
    exit_condition: str
    date: str = ""
    exit_price: str = ""
    profit_loss_usd: str = ""
    thesis_correct: str = ""
    lesson_learned: str = ""

    def __post_init__(self):
        if not self.date:
            self.date = datetime.now(timezone.utc).isoformat()


def append_entry(entry: JournalEntry, path: Path = DEFAULT_JOURNAL_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if is_new:
            writer.writeheader()
        row = {k: getattr(entry, k) for k in FIELDNAMES}
        writer.writerow(row)


def read_journal(path: Path = DEFAULT_JOURNAL_PATH) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def record_no_trade(reason: str, path: Path = DEFAULT_JOURNAL_PATH) -> None:
    entry = JournalEntry(
        market="NO TRADE",
        side="-",
        entry_price=0.0,
        amount_usd=0.0,
        estimated_true_probability=0.0,
        expected_edge_pp=0.0,
        confidence=0,
        strategy="-",
        reason=reason,
        key_evidence="-",
        exit_condition="-",
    )
    append_entry(entry, path)
