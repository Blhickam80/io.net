import csv
from pathlib import Path

from polymanager.journal import DEFAULT_JOURNAL_PATH, FIELDNAMES, JournalEntry, append_entry
from polymanager.reconcile import reconcile


class _FakeClient:
    def __init__(self, markets_by_id: dict):
        self._markets = markets_by_id

    def get_market_by_id(self, market_id):
        return self._markets.get(market_id)


def _write_journal(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})


def _entry_row(**overrides) -> dict:
    base = {
        "date": "2026-08-20T00:00:00+00:00",
        "market": "Will Bitcoin reach $75,000 in August?",
        "market_id": "3257342",
        "side": "NO",
        "entry_price": "0.39",
        "amount_usd": "5.00",
        "estimated_true_probability": "0.42",
        "expected_edge_pp": "3.0",
        "confidence": "4",
        "strategy": "Tier 3 - Experimental",
        "reason": "Recommended by live cycle; not yet executed (no wallet configured).",
        "key_evidence": "model says X",
        "exit_condition": "re-evaluate",
        "exit_price": "",
        "profit_loss_usd": "",
        "thesis_correct": "",
        "lesson_learned": "",
    }
    base.update(overrides)
    return base


def test_reconcile_resolved_market_wins(tmp_path, monkeypatch):
    path = tmp_path / "journal.csv"
    monkeypatch.setattr("polymanager.reconcile.read_journal", lambda: _read(path))
    monkeypatch.setattr("polymanager.reconcile.rewrite_all", lambda rows, p=path: _write_journal(path, rows))

    _write_journal(path, [_entry_row()])

    # NO side won: market resolved YES=0 / NO=1 (BTC never touched $75k).
    client = _FakeClient({"3257342": {"outcomePrices": '["0", "1"]', "closed": True}})
    summary = reconcile(client)

    assert summary["resolved"] == 1
    assert summary["still_pending"] == 0
    rows = _read(path)
    row = rows[0]
    assert row["exit_price"] == "1.0000"
    # shares = 5.00/0.39 = 12.82; payout = 12.82*1.0 = 12.82; pnl = 12.82-5.00 = 7.82
    assert float(row["profit_loss_usd"]) > 0
    assert row["thesis_correct"] == "True"
    assert "HYPOTHETICAL" in row["lesson_learned"]


def test_reconcile_resolved_market_loses(tmp_path, monkeypatch):
    path = tmp_path / "journal.csv"
    monkeypatch.setattr("polymanager.reconcile.read_journal", lambda: _read(path))
    monkeypatch.setattr("polymanager.reconcile.rewrite_all", lambda rows, p=path: _write_journal(path, rows))

    _write_journal(path, [_entry_row()])

    # NO side lost: market resolved YES=1 (BTC did touch $75k).
    client = _FakeClient({"3257342": {"outcomePrices": '["1", "0"]', "closed": True}})
    summary = reconcile(client)

    rows = _read(path)
    row = rows[0]
    assert row["exit_price"] == "0.0000"
    assert float(row["profit_loss_usd"]) < 0
    assert row["thesis_correct"] == "False"


def test_reconcile_leaves_unresolved_market_pending(tmp_path, monkeypatch):
    path = tmp_path / "journal.csv"
    monkeypatch.setattr("polymanager.reconcile.read_journal", lambda: _read(path))
    monkeypatch.setattr("polymanager.reconcile.rewrite_all", lambda rows, p=path: _write_journal(path, rows))

    _write_journal(path, [_entry_row()])

    client = _FakeClient({"3257342": {"outcomePrices": '["0.42", "0.58"]', "closed": False}})
    summary = reconcile(client)

    assert summary["resolved"] == 0
    assert summary["still_pending"] == 1
    rows = _read(path)
    assert rows[0]["exit_price"] == ""


def test_reconcile_skips_rows_without_market_id(tmp_path, monkeypatch):
    path = tmp_path / "journal.csv"
    monkeypatch.setattr("polymanager.reconcile.read_journal", lambda: _read(path))
    monkeypatch.setattr("polymanager.reconcile.rewrite_all", lambda rows, p=path: _write_journal(path, rows))

    _write_journal(path, [_entry_row(market_id="")])

    summary = reconcile(_FakeClient({}))
    assert summary["skipped_no_market_id"] == 1
    assert summary["checked"] == 0


def test_reconcile_skips_no_trade_and_already_reconciled_rows(tmp_path, monkeypatch):
    path = tmp_path / "journal.csv"
    monkeypatch.setattr("polymanager.reconcile.read_journal", lambda: _read(path))
    monkeypatch.setattr("polymanager.reconcile.rewrite_all", lambda rows, p=path: _write_journal(path, rows))

    _write_journal(
        path,
        [
            _entry_row(market="NO TRADE", side="-", market_id=""),
            _entry_row(exit_price="0.5000", profit_loss_usd="1.00", thesis_correct="True"),
        ],
    )

    summary = reconcile(_FakeClient({"3257342": {"outcomePrices": '["1", "0"]', "closed": True}}))
    assert summary["checked"] == 0
    assert summary["resolved"] == 0


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))
