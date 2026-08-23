from polymanager.copytrading import (
    TraderStats,
    classify_trader_type,
    meets_copy_target_bar,
    rank_traders,
    trader_quality_score,
)


def _stats(**overrides) -> TraderStats:
    defaults = dict(
        address="0xabc",
        roi_pct=10.0,
        realized_pnl_usd=1000.0,
        markets_traded=100,
        win_rate_pct=60.0,
        avg_position_usd=500.0,
        max_drawdown_pct=15.0,
        specialty="politics",
        largest_single_win_pct_of_pnl=10.0,
        avg_entry_vs_final_price_gap=0.0,
    )
    defaults.update(overrides)
    return TraderStats(**defaults)


def test_meets_copy_target_bar_passes_when_all_four_conditions_clear():
    passed, reasons = meets_copy_target_bar(_stats())
    assert passed is True
    assert reasons == []


def test_meets_copy_target_bar_fails_on_negative_roi():
    passed, reasons = meets_copy_target_bar(_stats(roi_pct=-2.19))
    assert passed is False
    assert any("ROI" in r for r in reasons)


def test_meets_copy_target_bar_reports_every_failing_condition_not_just_first():
    # Real shape found live 2026-08-21 (C63AMG watchlist wallet): positive
    # ROI and strong win rate, but catastrophic drawdown -- must surface
    # the drawdown failure even though ROI/win-rate/sample all pass.
    passed, reasons = meets_copy_target_bar(
        _stats(roi_pct=7.46, win_rate_pct=70.7, markets_traded=150, max_drawdown_pct=114.7)
    )
    assert passed is False
    assert len(reasons) == 1
    assert "drawdown" in reasons[0]


def test_meets_copy_target_bar_all_four_can_fail_at_once():
    passed, reasons = meets_copy_target_bar(
        _stats(roi_pct=-5.0, win_rate_pct=30.0, markets_traded=5, max_drawdown_pct=90.0)
    )
    assert passed is False
    assert len(reasons) == 4


def test_quality_score_can_rank_a_net_loser_above_a_net_winner():
    # Real, live-observed paradox (2026-08-21 watchlist run): BTC1UPDOWN
    # had -2.19% real ROI but scored 60.3 -- highest of 5 real wallets --
    # because sample size, win rate, and low concentration are scored
    # independently of profitability, and the ROI component tops out at
    # only 20 of 100 points. This is exactly why quality_score alone must
    # never be read as a copy recommendation -- meets_copy_target_bar()
    # exists precisely to catch what this test demonstrates.
    net_loser_big_sample = _stats(
        roi_pct=-2.19, win_rate_pct=58.9, markets_traded=197,
        max_drawdown_pct=0.0, largest_single_win_pct_of_pnl=7.2,
    )
    net_winner_small_sample = _stats(
        roi_pct=14.33, win_rate_pct=62.1, markets_traded=29,
        max_drawdown_pct=62.3, largest_single_win_pct_of_pnl=32.1,
    )
    assert trader_quality_score(net_loser_big_sample) > trader_quality_score(net_winner_small_sample)
    # ...but the bar correctly fails the loser and (for a different reason) the winner too.
    assert meets_copy_target_bar(net_loser_big_sample)[0] is False
    assert meets_copy_target_bar(net_winner_small_sample)[0] is False


def test_classify_trader_type_whale_by_position_size():
    assert classify_trader_type(_stats(avg_position_usd=6000.0)) == "whale"


def test_classify_trader_type_specialist():
    assert classify_trader_type(
        _stats(avg_position_usd=100.0, markets_traded=60, win_rate_pct=65.0, max_drawdown_pct=10.0, specialty="sports")
    ) == "sports specialist"


def test_classify_trader_type_insufficient_sample():
    assert classify_trader_type(_stats(avg_position_usd=100.0, markets_traded=5)) == "insufficient sample -- do not weight"


def test_rank_traders_includes_copy_target_verdict():
    ranked = rank_traders([_stats(address="0xgood"), _stats(address="0xbad", roi_pct=-1.0)])
    by_addr = {r["address"]: r for r in ranked}
    assert by_addr["0xgood"]["meets_copy_target_bar"] is True
    assert by_addr["0xbad"]["meets_copy_target_bar"] is False
    assert by_addr["0xbad"]["copy_target_gaps"]
