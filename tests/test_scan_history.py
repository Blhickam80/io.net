from pathlib import Path

from polymanager.scan_history import (
    ScanSummary,
    append_summary,
    persistent_sum_consistency_titles,
    read_history,
)


def test_append_and_read_roundtrip(tmp_path: Path):
    path = tmp_path / "scan_history.jsonl"
    s1 = ScanSummary.now(
        btc_touch_opportunities=1,
        monotonicity_events_scanned=50,
        monotonicity_violations=0,
        sum_consistency_events_scanned=50,
        sum_consistency_findings=2,
        bankroll_equity=200.0,
    )
    s2 = ScanSummary.now(
        btc_touch_opportunities=0,
        monotonicity_events_scanned=50,
        monotonicity_violations=1,
        sum_consistency_events_scanned=50,
        sum_consistency_findings=0,
        bankroll_equity=205.0,
    )
    append_summary(s1, path)
    append_summary(s2, path)

    history = read_history(path)
    assert len(history) == 2
    assert history[0]["bankroll_equity"] == 200.0
    assert history[1]["monotonicity_violations"] == 1


def test_read_history_missing_file_returns_empty(tmp_path: Path):
    path = tmp_path / "does_not_exist.jsonl"
    assert read_history(path) == []


def test_persistent_titles_requires_at_least_two_tagged_runs():
    # A single scan can't establish persistence -- one data point isn't a trend.
    history = [{"sum_consistency_event_titles": ["Event A", "Event B"]}]
    assert persistent_sum_consistency_titles(history) == set()


def test_persistent_titles_intersects_across_runs_ignoring_untagged():
    # Real shape: older log lines (pre-2026-08-21) have no titles field at
    # all and must be ignored, not treated as "this run found nothing".
    history = [
        {"sum_consistency_event_titles": ["Event A", "Event B", "Event C"]},
        {},  # legacy entry, no titles field
        {"sum_consistency_event_titles": ["Event A", "Event C"]},
        {"sum_consistency_event_titles": ["Event A", "Event B"]},
    ]
    assert persistent_sum_consistency_titles(history) == {"Event A"}


def test_persistent_titles_empty_when_no_overlap():
    history = [
        {"sum_consistency_event_titles": ["Event A"]},
        {"sum_consistency_event_titles": ["Event B"]},
    ]
    assert persistent_sum_consistency_titles(history) == set()
