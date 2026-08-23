"""Shared P/L-sequence statistics: peak-to-trough drawdown on a cumulative
P/L series. Originally built inline in polymanager.wallet_research (for
real trader wallets' realized P/L history) and duplicated here because
polymanager.performance needs the identical calculation for this
project's own hypothetical recommendation outcomes -- extracted once both
needed it.
"""

from __future__ import annotations


def cumulative_pnl_drawdown(pnls_in_order: list[float]) -> tuple[float, float]:
    """Max peak-to-trough decline in a cumulative P/L series, in the order
    given. Returns (pct, usd).

    The percentage figure has a real sharp edge: normalizing by the running
    PEAK means a series whose cumulative P/L only ever reached a small peak
    before a later loss reports a mathematically-correct-but-huge
    percentage (confirmed live 2026-08-20 in wallet_research.py: one real
    wallet showed 1646% "drawdown" on a $17,791 swing). There's no
    bankroll/equity base to normalize against, only the cumulative-P/L path
    itself -- read the dollar figure alongside the percentage, not instead
    of it.
    """
    cumulative = 0.0
    peak = 0.0
    max_drawdown_pct = 0.0
    max_drawdown_usd = 0.0
    for pnl in pnls_in_order:
        cumulative += pnl
        peak = max(peak, cumulative)
        drawdown_usd = peak - cumulative
        max_drawdown_usd = max(max_drawdown_usd, drawdown_usd)
        if peak > 0:
            max_drawdown_pct = max(max_drawdown_pct, drawdown_usd / peak)
    return max_drawdown_pct * 100, max_drawdown_usd
