"""Minimal CoinGecko client: BTC spot price and realized volatility.

Used only by polymanager.btc_touch to price "will BTC reach $X" style
Polymarket markets against real crypto price data. No API key required for
these endpoints. Verified live on 2026-08-20.
"""

from __future__ import annotations

import requests

from .models import realized_daily_vol

_TIMEOUT = 20
_BASE = "https://api.coingecko.com/api/v3"


class CoinGeckoClient:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()

    def get_spot_price(self, coin_id: str = "bitcoin", vs_currency: str = "usd") -> float:
        resp = self.session.get(
            f"{_BASE}/simple/price",
            params={"ids": coin_id, "vs_currencies": vs_currency},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return float(resp.json()[coin_id][vs_currency])

    def get_realized_daily_vol(
        self, coin_id: str = "bitcoin", *, vs_currency: str = "usd", days: int = 60
    ) -> float:
        resp = self.session.get(
            f"{_BASE}/coins/{coin_id}/market_chart",
            params={"vs_currency": vs_currency, "days": days, "interval": "daily"},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        prices = [p[1] for p in resp.json()["prices"]]
        return realized_daily_vol(prices)
