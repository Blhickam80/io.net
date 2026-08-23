"""Walk-forward calibration backtest for the barrier-touch model
(polymanager.models.touch_probability_upper_barrier), the math behind the
BTC strategy in polymanager.btc_touch.

Before this model sizes a real position, it needs evidence it's actually
calibrated: when it says "80% touch probability," does the barrier get
touched roughly 80% of the time across many historical instances? This
walks a real BTC daily-close price series forward in time, and at every
point computes trailing volatility from ONLY prior data (no lookahead),
prices several synthetic barriers, and checks what actually happened next.

Known limitations, stated plainly rather than glossed over:
  - CoinGecko's free tier caps historical daily data at 365 days, so this
    is a single-regime backtest (one continuous year of BTC's price
    history), not a multi-cycle test spanning bull/bear/chop regimes.
    Treat calibration numbers as "how did this do in the last ~year,"
    not "how will this do in general."
  - The outcome check uses daily CLOSING prices as a proxy for "touched
    the barrier," since free daily-granularity intraday highs aren't
    available this far back. This systematically UNDER-counts true
    touches (a barrier crossed intraday and closed back below it is
    missed), so empirical touch rates here are a lower bound on the
    model's real hit rate, not an exact measurement.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import realized_daily_vol, touch_probability_upper_barrier

TRAILING_VOL_WINDOW_DAYS = 60


@dataclass
class BacktestTrial:
    start_index: int
    horizon_days: int
    barrier_offset_pct: float
    spot: float
    barrier: float
    model_p: float
    actual_touch: bool


def run_backtest(
    daily_prices: list[float],
    *,
    horizons: tuple[int, ...] = (7, 14, 21),
    barrier_offsets: tuple[float, ...] = (0.03, 0.05, 0.08, 0.12),
    trailing_window: int = TRAILING_VOL_WINDOW_DAYS,
) -> list[BacktestTrial]:
    """Run every (start day, horizon, barrier offset) combination the data
    supports and return the raw trials. Deterministic given `daily_prices`.
    """
    trials: list[BacktestTrial] = []
    n = len(daily_prices)
    max_horizon = max(horizons)

    for t in range(trailing_window, n - max_horizon):
        trailing = daily_prices[t - trailing_window : t + 1]
        vol = realized_daily_vol(trailing)
        spot = daily_prices[t]

        for horizon in horizons:
            if t + horizon >= n:
                continue
            future_window = daily_prices[t + 1 : t + 1 + horizon]
            future_max = max(future_window)

            for offset in barrier_offsets:
                barrier = spot * (1 + offset)
                model_p = touch_probability_upper_barrier(spot, barrier, vol, horizon)
                actual_touch = future_max >= barrier
                trials.append(
                    BacktestTrial(
                        start_index=t,
                        horizon_days=horizon,
                        barrier_offset_pct=offset,
                        spot=spot,
                        barrier=barrier,
                        model_p=model_p,
                        actual_touch=actual_touch,
                    )
                )
    return trials


def calibration_table(trials: list[BacktestTrial], *, n_buckets: int = 10) -> list[dict]:
    """Bucket trials by predicted probability decile and compare mean
    predicted probability to actual touch frequency in that bucket -- the
    standard reliability-diagram table, in text form.
    """
    if not trials:
        return []

    buckets: list[list[BacktestTrial]] = [[] for _ in range(n_buckets)]
    for trial in trials:
        idx = min(int(trial.model_p * n_buckets), n_buckets - 1)
        buckets[idx].append(trial)

    rows = []
    for i, bucket in enumerate(buckets):
        if not bucket:
            continue
        mean_pred = sum(t.model_p for t in bucket) / len(bucket)
        actual_rate = sum(1 for t in bucket if t.actual_touch) / len(bucket)
        rows.append(
            {
                "bucket_range": f"{i / n_buckets:.0%}-{(i + 1) / n_buckets:.0%}",
                "n": len(bucket),
                "mean_predicted": mean_pred,
                "actual_touch_rate": actual_rate,
                "gap": actual_rate - mean_pred,
            }
        )
    return rows


def brier_score(trials: list[BacktestTrial]) -> float:
    if not trials:
        return float("nan")
    return sum((t.model_p - (1.0 if t.actual_touch else 0.0)) ** 2 for t in trials) / len(trials)


def baseline_brier_score(trials: list[BacktestTrial]) -> float:
    """Brier score of the naive baseline: always predict the overall
    empirical touch rate. A useful model should beat this.
    """
    if not trials:
        return float("nan")
    base_rate = sum(1 for t in trials if t.actual_touch) / len(trials)
    return sum((base_rate - (1.0 if t.actual_touch else 0.0)) ** 2 for t in trials) / len(trials)


def render_report(trials: list[BacktestTrial]) -> str:
    lines = [
        "BTC BARRIER-TOUCH MODEL -- WALK-FORWARD CALIBRATION BACKTEST",
        f"Trials: {len(trials)}",
        "",
        "Caveats: single continuous ~365-day regime; outcome check uses daily",
        "closes as a touch proxy, so actual touch rates below are a LOWER BOUND",
        "on the model's true hit rate (see module docstring).",
        "",
        f"Model Brier score:    {brier_score(trials):.4f}  (lower is better)",
        f"Baseline Brier score: {baseline_brier_score(trials):.4f}  (always predict the base rate)",
        "",
        f"{'Bucket':<10}{'N':>6}{'Mean Pred':>12}{'Actual Rate':>14}{'Gap':>10}",
    ]
    for row in calibration_table(trials):
        lines.append(
            f"{row['bucket_range']:<10}{row['n']:>6}{row['mean_predicted']:>11.1%} "
            f"{row['actual_touch_rate']:>13.1%}{row['gap']:>+9.1%}"
        )
    return "\n".join(lines)


def main() -> None:
    from .coingecko import CoinGeckoClient

    cg = CoinGeckoClient()
    resp = cg.session.get(
        "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
        params={"vs_currency": "usd", "days": 365, "interval": "daily"},
        timeout=30,
    )
    resp.raise_for_status()
    prices = [p[1] for p in resp.json()["prices"]]

    trials = run_backtest(prices)
    print(render_report(trials))


if __name__ == "__main__":
    main()
