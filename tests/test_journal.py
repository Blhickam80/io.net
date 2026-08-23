from polymanager.journal import (
    JournalEntry,
    append_entry,
    has_open_unresolved_entry,
    read_journal,
    record_no_trade,
    rewrite_all,
)


def _entry(market_id: str, side: str, **overrides) -> JournalEntry:
    defaults = dict(
        market=f"Will Bitcoin reach ${market_id} in August?",
        market_id=market_id,
        side=side,
        entry_price=0.5,
        amount_usd=6.0,
        estimated_true_probability=0.6,
        expected_edge_pp=5.0,
        confidence=4,
        strategy="Tier 3 - Experimental",
        reason="test",
        key_evidence="test",
        exit_condition="test",
    )
    defaults.update(overrides)
    return JournalEntry(**defaults)


def test_append_and_read_roundtrip(tmp_path):
    path = tmp_path / "journal.csv"
    append_entry(_entry("btc-1", "NO"), path)
    append_entry(_entry("btc-2", "YES"), path)

    rows = read_journal(path)
    assert len(rows) == 2
    assert rows[0]["market_id"] == "btc-1"
    assert rows[1]["side"] == "YES"


def test_record_no_trade_writes_placeholder_row(tmp_path):
    path = tmp_path / "journal.csv"
    record_no_trade("no edge this cycle", path)

    rows = read_journal(path)
    assert len(rows) == 1
    assert rows[0]["market"] == "NO TRADE"
    assert rows[0]["reason"] == "no edge this cycle"


def test_rewrite_all_overwrites_full_file(tmp_path):
    path = tmp_path / "journal.csv"
    append_entry(_entry("btc-1", "NO"), path)
    rows = read_journal(path)
    rows[0]["resolved_at"] = "2026-08-21T00:00:00Z"
    rows[0]["profit_loss_usd"] = "-1.50"
    rewrite_all(rows, path)

    reread = read_journal(path)
    assert len(reread) == 1
    assert reread[0]["resolved_at"] == "2026-08-21T00:00:00Z"
    assert reread[0]["profit_loss_usd"] == "-1.50"


def test_has_open_unresolved_entry_false_when_journal_empty(tmp_path):
    path = tmp_path / "journal.csv"
    assert has_open_unresolved_entry("btc-1", "NO", path) is False


def test_has_open_unresolved_entry_false_for_empty_market_id(tmp_path):
    # NO TRADE rows have market_id="" -- must never match anything.
    path = tmp_path / "journal.csv"
    record_no_trade("no edge", path)
    assert has_open_unresolved_entry("", "-", path) is False


def test_has_open_unresolved_entry_true_for_matching_open_row(tmp_path):
    # Regression for the real bug found live 2026-08-21: without this
    # check, cli.py journaled the same still-open market/side every cycle
    # it stayed open, and one real BTC "$77,500 in August" NO call got
    # journaled 7 separate times before resolving -- all 7 counted as
    # independent losses in performance.py's aggregate stats once
    # reconciled, when it was really one wrong prediction weighted 7x.
    path = tmp_path / "journal.csv"
    append_entry(_entry("btc-77500", "NO"), path)
    assert has_open_unresolved_entry("btc-77500", "NO", path) is True


def test_has_open_unresolved_entry_false_once_resolved(tmp_path):
    path = tmp_path / "journal.csv"
    append_entry(_entry("btc-77500", "NO"), path)
    rows = read_journal(path)
    rows[0]["resolved_at"] = "2026-08-21T00:00:00Z"
    rewrite_all(rows, path)

    # Resolved -> no longer "open," so a fresh recommendation on the same
    # market/side after resolution is a legitimately new, independent bet.
    assert has_open_unresolved_entry("btc-77500", "NO", path) is False


def test_has_open_unresolved_entry_distinguishes_side(tmp_path):
    path = tmp_path / "journal.csv"
    append_entry(_entry("btc-77500", "NO"), path)
    assert has_open_unresolved_entry("btc-77500", "YES", path) is False
