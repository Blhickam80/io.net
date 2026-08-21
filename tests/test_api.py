from polymanager.api import PolymarketClient


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeSession:
    def __init__(self, response_json, status_code=200):
        self.response_json = response_json
        self.status_code = status_code
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        return _FakeResponse(self.response_json, self.status_code)


def _client(response_json, status_code=200):
    session = _FakeSession(response_json, status_code)
    return PolymarketClient(session=session), session


def test_get_markets_passes_query_params_correctly():
    client, session = _client([{"id": "1"}])
    result = client.get_markets(active=True, closed=False, limit=25, order="volume24hr", ascending=False)
    assert result == [{"id": "1"}]
    url, params, _ = session.calls[0]
    assert url.endswith("/markets")
    assert params == {"active": "true", "closed": "false", "limit": 25, "order": "volume24hr", "ascending": "false"}


def test_get_market_by_slug_returns_first_result():
    client, session = _client([{"id": "1", "slug": "will-x"}, {"id": "2", "slug": "will-x"}])
    result = client.get_market_by_slug("will-x")
    assert result == {"id": "1", "slug": "will-x"}
    assert session.calls[0][1] == {"slug": "will-x"}


def test_get_market_by_slug_returns_none_when_empty():
    client, _ = _client([])
    assert client.get_market_by_slug("does-not-exist") is None


def test_get_market_by_id_uses_path_not_query_param():
    # Real bug found live 2026-08-20: the ?id= query-param form silently
    # returns an empty list on Gamma's API -- the path form is the only
    # one that works. Confirm the client builds a path, not a query param.
    client, session = _client({"id": "12345"})
    result = client.get_market_by_id("12345")
    assert result == {"id": "12345"}
    url, params, _ = session.calls[0]
    assert url.endswith("/markets/12345")
    assert params is None


def test_get_market_by_id_returns_none_on_404():
    client, _ = _client({}, status_code=404)
    assert client.get_market_by_id("does-not-exist") is None


def test_get_wallet_positions_passes_user_param():
    client, session = _client([{"asset": "x"}])
    result = client.get_wallet_positions("0xabc")
    assert result == [{"asset": "x"}]
    assert session.calls[0][1] == {"user": "0xabc"}


def test_get_wallet_activity_passes_user_and_limit():
    client, session = _client([])
    client.get_wallet_activity("0xabc", limit=50)
    assert session.calls[0][1] == {"user": "0xabc", "limit": 50}


def test_get_wallet_trades_passes_pagination_params():
    client, session = _client([])
    client.get_wallet_trades("0xabc", limit=100, offset=200)
    assert session.calls[0][1] == {"user": "0xabc", "limit": 100, "offset": 200}


def test_get_closed_positions_passes_sort_and_pagination_params():
    client, session = _client([])
    client.get_closed_positions("0xabc", limit=50, offset=100, sort_by="TIMESTAMP", sort_direction="ASC")
    assert session.calls[0][1] == {
        "user": "0xabc",
        "limit": 50,
        "offset": 100,
        "sortBy": "TIMESTAMP",
        "sortDirection": "ASC",
    }


def test_get_leaderboard_omits_user_param_when_not_given():
    client, session = _client([])
    client.get_leaderboard(category="OVERALL", time_period="ALL", limit=10)
    params = session.calls[0][1]
    assert "user" not in params


def test_get_leaderboard_includes_user_param_when_given():
    client, session = _client([])
    client.get_leaderboard(category="OVERALL", time_period="ALL", user="0xabc", limit=1)
    params = session.calls[0][1]
    assert params["user"] == "0xabc"


def test_get_price_converts_string_price_to_float():
    client, session = _client({"price": "0.42"})
    result = client.get_price("token-1", side="buy")
    assert result == 0.42
    assert session.calls[0][1] == {"token_id": "token-1", "side": "buy"}


def test_get_order_book_passes_token_id():
    client, session = _client({"bids": [], "asks": []})
    result = client.get_order_book("token-1")
    assert result == {"bids": [], "asks": []}
    assert session.calls[0][1] == {"token_id": "token-1"}
