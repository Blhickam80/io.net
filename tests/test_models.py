import math

from polymanager.models import realized_daily_vol, touch_probability_upper_barrier


def test_touch_probability_already_above_barrier():
    assert touch_probability_upper_barrier(spot=100, barrier=90, daily_vol=0.02, days_remaining=5) == 1.0


def test_touch_probability_no_time_left():
    assert touch_probability_upper_barrier(spot=100, barrier=110, daily_vol=0.02, days_remaining=0) == 0.0


def test_touch_probability_increases_with_time_and_vol():
    p_short = touch_probability_upper_barrier(spot=100, barrier=105, daily_vol=0.02, days_remaining=5)
    p_long = touch_probability_upper_barrier(spot=100, barrier=105, daily_vol=0.02, days_remaining=30)
    assert p_long > p_short

    p_low_vol = touch_probability_upper_barrier(spot=100, barrier=105, daily_vol=0.01, days_remaining=10)
    p_high_vol = touch_probability_upper_barrier(spot=100, barrier=105, daily_vol=0.03, days_remaining=10)
    assert p_high_vol > p_low_vol


def test_touch_probability_bounded():
    p = touch_probability_upper_barrier(spot=100, barrier=150, daily_vol=0.02, days_remaining=10)
    assert 0.0 <= p <= 1.0


def test_realized_daily_vol_constant_price_is_zero():
    assert realized_daily_vol([100.0] * 10) == 0.0


def test_realized_daily_vol_matches_known_series():
    # log returns of +0.01 each step -> stdev of returns is 0 (constant), so vol == 0
    prices = [100 * math.exp(0.01 * i) for i in range(10)]
    assert abs(realized_daily_vol(prices)) < 1e-9
