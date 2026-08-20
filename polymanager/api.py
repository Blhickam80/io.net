"""Thin HTTP clients for Polymarket's public REST APIs.

No API key is required for read-only market/trader data. Order execution
(polymanager.execution) additionally requires a funded Polygon wallet
private key, which is never read from or written to this repo.

Verified live against gamma-api.polymarket.com, clob.polymarket.com, and
data-api.polymarket.com on 2026-08-20 from an environment with network
access: /markets, /book, /price, and data-api's /positions and /trades all
work as implemented below. There is no public /leaderboard endpoint on
data-api (confirmed: 404, along with every other plausible path tried) --
see get_wallet_positions/get_wallet_activity for the per-wallet alternative
that does exist, which is what copy-trading analysis should be built on.

Network note: these calls need outbound HTTPS to the three hosts above.
Some sandboxed execution environments restrict egress to an allowlist that
excludes them by default -- if calls raise requests.RequestException,
check the environment's network access level before assuming the API is
down.
"""

from __future__ import annotations

import requests

from .config import CLOB_API_BASE, DATA_API_BASE, GAMMA_API_BASE

_TIMEOUT = 20


class PolymarketClient:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()

    def get_markets(
        self,
        *,
        active: bool = True,
        closed: bool = False,
        limit: int = 100,
        order: str = "volume24hr",
        ascending: bool = False,
    ) -> list[dict]:
        """Fetch markets from the Gamma API, most-active first by default."""
        params = {
            "active": str(active).lower(),
            "closed": str(closed).lower(),
            "limit": limit,
            "order": order,
            "ascending": str(ascending).lower(),
        }
        resp = self.session.get(f"{GAMMA_API_BASE}/markets", params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def get_market_by_slug(self, slug: str) -> dict | None:
        resp = self.session.get(
            f"{GAMMA_API_BASE}/markets", params={"slug": slug}, timeout=_TIMEOUT
        )
        resp.raise_for_status()
        results = resp.json()
        return results[0] if results else None

    def get_order_book(self, token_id: str) -> dict:
        """CLOB order book for a specific outcome token."""
        resp = self.session.get(
            f"{CLOB_API_BASE}/book", params={"token_id": token_id}, timeout=_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()

    def get_price(self, token_id: str, side: str = "buy") -> float:
        resp = self.session.get(
            f"{CLOB_API_BASE}/price",
            params={"token_id": token_id, "side": side},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return float(resp.json()["price"])

    def get_wallet_positions(self, wallet_address: str) -> list[dict]:
        resp = self.session.get(
            f"{DATA_API_BASE}/positions",
            params={"user": wallet_address},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def get_wallet_activity(self, wallet_address: str, *, limit: int = 200) -> list[dict]:
        resp = self.session.get(
            f"{DATA_API_BASE}/activity",
            params={"user": wallet_address, "limit": limit},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
