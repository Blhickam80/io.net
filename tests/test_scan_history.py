from pathlib import Path

from polymanager.scan_history import ScanSummary, append_summary, read_history


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
