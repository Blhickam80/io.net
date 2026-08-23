from polymanager.backtest import (
    baseline_brier_score,
    brier_score,
    calibration_table,
    run_backtest,
)


def _flat_price_series(n: int = 200, price: float = 100.0) -> list[float]:
    return [price] * n


def _stepped_series() -> list[float]:
    # 100 flat days, then a sustained ramp so some barriers get touched and
    # some don't -- gives run_backtest something non-trivial to chew on.
    flat = [100.0] * 100
    ramp = [100.0 * (1.01**i) for i in range(1, 60)]
    return flat + ramp


def test_run_backtest_flat_series_never_touches():
    prices = _flat_price_series()
    trials = run_backtest(prices, horizons=(7,), barrier_offsets=(0.05,))
    assert len(trials) > 0
    assert all(not t.actual_touch for t in trials)
    # Model should assign a low (not necessarily zero) probability when vol is 0.
    assert all(t.model_p == 0.0 for t in trials)  # zero vol -> model says impossible


def test_run_backtest_produces_some_touches_on_ramp():
    prices = _stepped_series()
    trials = run_backtest(prices, horizons=(7, 14), barrier_offsets=(0.03, 0.05))
    assert len(trials) > 0
    assert any(t.actual_touch for t in trials)
    assert any(not t.actual_touch for t in trials)


def test_calibration_table_buckets_sum_to_total():
    prices = _stepped_series()
    trials = run_backtest(prices, horizons=(7,), barrier_offsets=(0.03, 0.08))
    table = calibration_table(trials, n_buckets=5)
    assert sum(row["n"] for row in table) == len(trials)


def test_brier_score_bounded_and_model_beats_or_matches_baseline_on_ramp():
    prices = _stepped_series()
    trials = run_backtest(prices, horizons=(7, 14), barrier_offsets=(0.03, 0.05, 0.08))
    model_score = brier_score(trials)
    baseline_score = baseline_brier_score(trials)
    assert 0.0 <= model_score <= 1.0
    assert 0.0 <= baseline_score <= 1.0
