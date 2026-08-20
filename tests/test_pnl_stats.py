from polymanager.pnl_stats import cumulative_pnl_drawdown


def test_basic_recovery():
    # +100, -60 (peak 100 -> 40, drawdown 60%/$60), +80 (recovers past peak)
    pct, usd = cumulative_pnl_drawdown([100, -60, 80])
    assert abs(pct - 60.0) < 1e-9
    assert abs(usd - 60.0) < 1e-9


def test_no_positive_peak_yet_reports_zero_pct_but_real_usd():
    pct, usd = cumulative_pnl_drawdown([-10, -5])
    assert pct == 0.0
    assert abs(usd - 15.0) < 1e-9


def test_pct_can_exceed_100_on_tiny_peak():
    pct, usd = cumulative_pnl_drawdown([50, -750])
    assert pct > 100.0
    assert abs(usd - 750.0) < 1e-9


def test_empty_series():
    pct, usd = cumulative_pnl_drawdown([])
    assert pct == 0.0
    assert usd == 0.0


def test_monotonically_increasing_has_zero_drawdown():
    pct, usd = cumulative_pnl_drawdown([10, 20, 30])
    assert pct == 0.0
    assert usd == 0.0
