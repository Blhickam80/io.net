"""Order execution.

Paper-trading (the default, and the only mode this repo runs unattended):
records the intended trade into the portfolio/journal without touching a
real wallet.

Live execution is intentionally not wired to any wallet by default. It
requires the operator to set POLYMARKET_PRIVATE_KEY (a funded Polygon
wallet key) and have the optional `py-clob-client` dependency installed.
Nothing in this repo reads, stores, or transmits that key anywhere other
than directly to py-clob-client for local order signing -- and it must
never be committed to source control.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class LiveExecutionUnavailable(RuntimeError):
    pass


@dataclass
class TradeIntent:
    market_id: str
    question: str
    side: str  # YES or NO
    max_entry_price: float
    dollars: float


def paper_fill(intent: TradeIntent, fill_price: float) -> dict:
    """Simulate a fill at `fill_price` (e.g. the current best ask), rejecting
    it if that price is worse than the max entry price the strategy set.
    """
    if fill_price > intent.max_entry_price:
        return {
            "filled": False,
            "reason": f"Fill price ${fill_price:.3f} exceeds max entry ${intent.max_entry_price:.3f}.",
        }
    shares = round(intent.dollars / fill_price, 4)
    return {
        "filled": True,
        "fill_price": fill_price,
        "shares": shares,
        "dollars": intent.dollars,
    }


def live_execute(intent: TradeIntent) -> dict:
    """Place a real order via py-clob-client. Requires POLYMARKET_PRIVATE_KEY.

    Raises LiveExecutionUnavailable if the key is not set or the client
    library is not installed -- this is deliberate: the manager must never
    silently fall back from a requested live trade to a paper trade.
    """
    private_key = os.environ.get("POLYMARKET_PRIVATE_KEY")
    if not private_key:
        raise LiveExecutionUnavailable(
            "POLYMARKET_PRIVATE_KEY is not set. Live execution requires the "
            "operator's own funded Polygon wallet key; set it as an "
            "environment variable (never commit it) to enable live trading."
        )
    try:
        from py_clob_client.client import ClobClient  # type: ignore
    except ImportError as e:
        raise LiveExecutionUnavailable(
            "py-clob-client is not installed. Run `pip install py-clob-client` "
            "to enable live execution."
        ) from e

    raise LiveExecutionUnavailable(
        "Live order placement is not wired up in this repo -- add the "
        "ClobClient order-building/signing call here once you have "
        "reviewed and approved it. This stub deliberately stops short of "
        "sending a real order without an explicit, reviewed implementation."
    )
