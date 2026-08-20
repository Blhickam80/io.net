"""Quantitative probability models for specific market shapes.

Currently: barrier-touch probability for "will asset X reach price level L
by time T" markets, using a driftless geometric-Brownian-motion / reflection-
principle approximation. This is standard barrier-option math, not a
narrative guess -- see e.g. the reflection principle for Brownian motion.
"""

from __future__ import annotations

import math


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def touch_probability_upper_barrier(
    spot: float,
    barrier: float,
    daily_vol: float,
    days_remaining: float,
) -> float:
    """P(the asset's price touches `barrier` at least once within
    `days_remaining` days), for a barrier above the current spot price,
    assuming zero drift and lognormal daily returns with volatility
    `daily_vol` (as a decimal, e.g. 0.02 for 2%/day).

    Zero-drift is a deliberately conservative simplifying assumption: it
    ignores any directional trend, so a genuine uptrend would make the real
    touch probability higher than this estimate, not lower.
    """
    if barrier <= spot:
        return 1.0  # already at/above the barrier
    if days_remaining <= 0:
        return 0.0
    if daily_vol <= 0:
        return 0.0

    d = math.log(barrier / spot) / (daily_vol * math.sqrt(days_remaining))
    return 2.0 * (1.0 - _norm_cdf(d))


def realized_daily_vol(prices: list[float]) -> float:
    """Realized daily volatility (stdev of log returns) from a price series."""
    if len(prices) < 2:
        raise ValueError("Need at least 2 price points.")
    log_returns = [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]
    mean = sum(log_returns) / len(log_returns)
    variance = sum((r - mean) ** 2 for r in log_returns) / (len(log_returns) - 1)
    return math.sqrt(variance)
