"""Thin HTTP clients for Polymarket's public REST APIs.

No API key is required for read-only market/trader data. Order execution
(polymanager.execution) additionally requires a funded Polygon wallet
private key, which is never read from or written to this repo.

Verified live against gamma-api.polymarket.com, clob.polymarket.com, and
data-api.polymarket.com on 2026-08-20 from an environment with network
access: /markets, /book, /price, and data-api's /positions, /trades,
/closed-positions, and /v1/leaderboard all work as implemented below.

CORRECTION (2026-08-20, same day): an earlier version of this module and
its docstring claimed no public /leaderboard endpoint exists on data-api.
That was wrong -- the real path is /v1/leaderboard (versioned, undocumented
without checking docs.polymarket.com/api-reference directly; guessing
plausible unversioned paths like /leaderboard is what produced the false
404-everywhere conclusion). Confirmed against the official OpenAPI spec at
https://docs.polymarket.com/api-reference/core/get-trader-leaderboard-rankings.md
and tested live. Lesson: prefer checking documented API specs over guessing
endpoint shapes from pattern-matching other paths.

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

    def get_market_by_id(self, market_id: str) -> dict | None:
        """Single-market lookup by Gamma's numeric id, for checking whether
        a previously-recommended market has resolved. The path-based
        /markets/{id} route is the reliable one -- confirmed live
        2026-08-20 that the ?id= query-param form returns an empty list
        instead (likely expects a different param name/type); don't repeat
        that mistake by guessing again.
        """
        resp = self.session.get(f"{GAMMA_API_BASE}/markets/{market_id}", timeout=_TIMEOUT)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

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

    def get_wallet_trades(self, wallet_address: str, *, limit: int = 500, offset: int = 0) -> list[dict]:
        resp = self.session.get(
            f"{DATA_API_BASE}/trades",
            params={"user": wallet_address, "limit": limit, "offset": offset},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def get_closed_positions(
        self,
        wallet_address: str,
        *,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "REALIZEDPNL",
        sort_direction: str = "DESC",
    ) -> list[dict]:
        """Per-market realized P/L for a wallet's already-resolved positions.
        `limit` is capped at 50 server-side; paginate with `offset` (up to
        100000) for more history.
        """
        resp = self.session.get(
            f"{DATA_API_BASE}/closed-positions",
            params={
                "user": wallet_address,
                "limit": limit,
                "offset": offset,
                "sortBy": sort_by,
                "sortDirection": sort_direction,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def get_leaderboard(
        self,
        *,
        category: str = "OVERALL",
        time_period: str = "ALL",
        order_by: str = "PNL",
        limit: int = 25,
        offset: int = 0,
        user: str | None = None,
    ) -> list[dict]:
        """Top traders by PNL or volume. `limit` is capped at 50 server-side.
        Pass `user` (a wallet address) to limit results to that single user
        -- per the documented API, only meaningful if that wallet actually
        ranks within `category`/`time_period`; returns [] otherwise.
        """
        params = {
            "category": category,
            "timePeriod": time_period,
            "orderBy": order_by,
            "limit": limit,
            "offset": offset,
        }
        if user is not None:
            params["user"] = user
        resp = self.session.get(
            f"{DATA_API_BASE}/v1/leaderboard",
            params=params,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
