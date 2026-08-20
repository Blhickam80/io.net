from polymanager.watchlist import WatchlistEntry, add_entry, load_watchlist


def test_add_entry_creates_file_with_header(tmp_path):
    path = tmp_path / "watchlist.csv"
    add_entry(WatchlistEntry(address="0xABC", label="whale1", source="twitter @foo", claim="great win rate"), path)

    rows = load_watchlist(path)
    assert len(rows) == 1
    assert rows[0]["address"] == "0xABC"
    assert rows[0]["label"] == "whale1"
    assert rows[0]["claim"] == "great win rate"
    assert rows[0]["date_added"]  # auto-stamped


def test_add_entry_upserts_by_address_case_insensitive(tmp_path):
    path = tmp_path / "watchlist.csv"
    add_entry(WatchlistEntry(address="0xABC", label="whale1", claim="first claim"), path)
    add_entry(WatchlistEntry(address="0xabc", label="whale1", claim="second claim, more context"), path)

    rows = load_watchlist(path)
    assert len(rows) == 1
    assert rows[0]["claim"] == "second claim, more context"


def test_add_entry_preserves_existing_fields_not_overwritten(tmp_path):
    path = tmp_path / "watchlist.csv"
    add_entry(WatchlistEntry(address="0xABC", label="whale1", source="twitter @foo"), path)
    # Second call only adds notes, doesn't blank out label/source.
    add_entry(WatchlistEntry(address="0xABC", notes="checked again 2026-08-21"), path)

    rows = load_watchlist(path)
    assert len(rows) == 1
    assert rows[0]["label"] == "whale1"
    assert rows[0]["source"] == "twitter @foo"
    assert rows[0]["notes"] == "checked again 2026-08-21"


def test_add_entry_keeps_original_date_added_on_update(tmp_path):
    path = tmp_path / "watchlist.csv"
    add_entry(WatchlistEntry(address="0xABC", label="whale1", date_added="2026-01-01"), path)
    add_entry(WatchlistEntry(address="0xABC", notes="follow-up note"), path)  # auto-stamps today

    rows = load_watchlist(path)
    assert rows[0]["date_added"] == "2026-01-01"  # not overwritten by the later call
    assert rows[0]["notes"] == "follow-up note"


def test_load_watchlist_missing_file_returns_empty(tmp_path):
    assert load_watchlist(tmp_path / "does_not_exist.csv") == []


def test_multiple_distinct_addresses_both_kept(tmp_path):
    path = tmp_path / "watchlist.csv"
    add_entry(WatchlistEntry(address="0xAAA", label="trader A"), path)
    add_entry(WatchlistEntry(address="0xBBB", label="trader B"), path)

    rows = load_watchlist(path)
    assert {r["address"] for r in rows} == {"0xAAA", "0xBBB"}
