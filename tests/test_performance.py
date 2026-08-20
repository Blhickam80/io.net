from polymanager.performance import compute_performance, render_report


def _row(**overrides) -> dict:
    base = {
        "market": "Will Bitcoin reach $75,000 in August?",
        "side": "NO",
        "strategy": "Tier 3 - Experimental",
        "exit_price": "",
        "profit_loss_usd": "",
        "thesis_correct": "",
    }
    base.update(overrides)
    return base


def test_no_reconciled_rows_returns_empty_report():
    report = compute_performance([_row(), _row(market="NO TRADE", side="-")])
    assert report.n_reconciled == 0
    assert report.n_pending == 1
    assert report.n_no_trade_cycles == 1
    assert report.win_rate_pct is None


def test_mixed_wins_and_losses():
    rows = [
        _row(exit_price="1.0", profit_loss_usd="10.00", thesis_correct="True"),
        _row(exit_price="1.0", profit_loss_usd="5.00", thesis_correct="True"),
        _row(exit_price="0.0", profit_loss_usd="-4.00", thesis_correct="False"),
        _row(),  # still pending
    ]
    report = compute_performance(rows)
    assert report.n_reconciled == 3
    assert report.n_pending == 1
    assert abs(report.win_rate_pct - (2 / 3 * 100)) < 0.1
    assert abs(report.avg_win_usd - 7.5) < 1e-9
    assert abs(report.avg_loss_usd - (-4.0)) < 1e-9
    assert abs(report.profit_factor - (15.0 / 4.0)) < 1e-9
    assert abs(report.total_hypothetical_pnl_usd - 11.0) < 1e-9


def test_no_losses_yet_gives_none_profit_factor():
    rows = [_row(exit_price="1.0", profit_loss_usd="3.00", thesis_correct="True")]
    report = compute_performance(rows)
    assert report.profit_factor is None
    assert report.avg_loss_usd is None


def test_by_strategy_breakdown():
    rows = [
        _row(strategy="Tier 3 - Experimental", exit_price="1.0", profit_loss_usd="5.00", thesis_correct="True"),
        _row(strategy="Tier 3 - Experimental", exit_price="0.0", profit_loss_usd="-2.00", thesis_correct="False"),
        _row(strategy="Tier 2 - Medium Confidence", exit_price="1.0", profit_loss_usd="8.00", thesis_correct="True"),
    ]
    report = compute_performance(rows)
    assert set(report.by_strategy.keys()) == {"Tier 3 - Experimental", "Tier 2 - Medium Confidence"}
    t3 = report.by_strategy["Tier 3 - Experimental"]
    assert t3["n"] == 2
    assert t3["win_rate_pct"] == 50.0
    assert abs(t3["pnl_usd"] - 3.0) < 1e-9


def test_render_report_handles_empty_and_populated():
    empty = render_report(compute_performance([]))
    assert "No reconciled outcomes yet" in empty

    rows = [_row(exit_price="1.0", profit_loss_usd="5.00", thesis_correct="True")]
    populated = render_report(compute_performance(rows))
    assert "Win rate: 100.0%" in populated
    assert "By strategy:" in populated
