from polymanager.wallet_research import (
    RealWalletStats,
    _guess_specialty,
    _trade_order_drawdown,
    fetch_wallet_stats,
    to_trader_stats,
)


class _FakeClient:
    def __init__(self, pages: list[list[dict]], open_positions: list[dict] | None = None):
        self._pages = pages
        self._open_positions = open_positions if open_positions is not None else []
        self.calls = 0

    def get_closed_positions(self, address, *, limit=50, offset=0, sort_by="REALIZEDPNL", sort_direction="DESC"):
        self.calls += 1
        page_index = offset // 50
        if page_index >= len(self._pages):
            return []
        return self._pages[page_index]

    def get_wallet_positions(self, address):
        return self._open_positions


def _open_position(cash_pnl: float, cur_price: float, bought: float, title: str = "Some market", end_date: str = "") -> dict:
    return {"cashPnl": cash_pnl, "curPrice": cur_price, "totalBought": bought, "title": title, "endDate": end_date}


def _position(pnl: float, bought: float, title: str = "Some election market", ts: int = 0) -> dict:
    return {"realizedPnl": pnl, "totalBought": bought, "title": title, "timestamp": ts}


def test_trade_order_drawdown_basic_recovery():
    # +100, -60 (peak 100 -> 40, drawdown 60%/$60), +80 (recovers past peak)
    positions = [
        _position(100, 200, ts=1),
        _position(-60, 200, ts=2),
        _position(80, 200, ts=3),
    ]
    pct, usd = _trade_order_drawdown(positions)
    assert abs(pct - 60.0) < 1e-6
    assert abs(usd - 60.0) < 1e-6


def test_trade_order_drawdown_no_positive_peak_yet():
    # Peak stays anchored at the $0 starting baseline (cumulative never
    # goes positive), so pct is correctly suppressed (no positive peak to
    # divide by) -- but the $0 baseline itself is a real reference point,
    # so the dollar figure still reports how far cumulative P/L has sunk
    # below breakeven: -10, then -5 more -> $15 given back from $0.
    positions = [_position(-10, 100, ts=1), _position(-5, 100, ts=2)]
    pct, usd = _trade_order_drawdown(positions)
    assert pct == 0.0
    assert abs(usd - 15.0) < 1e-6


def test_trade_order_drawdown_pct_can_exceed_100_on_tiny_peak():
    # Real shape found live (2026-08-20): peak of $50 followed by a $750
    # loss gives a mathematically-correct-but-huge percentage -- confirm
    # the function doesn't silently clamp it, and that the dollar figure
    # stays sane so callers can tell this case apart from a real blowup.
    # Cumulative: +50 (peak=50) -> -700 (peak(50) - cumulative(-700) = $750 drawdown).
    positions = [_position(50, 100, ts=1), _position(-750, 1000, ts=2)]
    pct, usd = _trade_order_drawdown(positions)
    assert pct > 100.0
    assert abs(usd - 750.0) < 1e-6


def test_fetch_wallet_stats_computes_real_metrics():
    positions = [
        _position(1000, 2000, title="Trump wins election", ts=1),
        _position(-200, 500, title="Bitcoin reaches $100k", ts=2),
        _position(500, 1000, title="Senate control 2026", ts=3),
    ]
    client = _FakeClient([positions])
    stats = fetch_wallet_stats(
        client, "0xabc", "testuser", lifetime_pnl_usd=50000, lifetime_volume_usd=1_000_000, max_positions=150
    )
    assert stats is not None
    assert stats.n_closed_positions_sampled == 3
    assert abs(stats.win_rate_pct - (2 / 3 * 100)) < 0.1  # rounded to 1 decimal by fetch_wallet_stats
    total_bought = 2000 + 500 + 1000
    total_pnl = 1000 - 200 + 500
    assert abs(stats.avg_position_usd - total_bought / 3) < 0.01
    assert abs(stats.total_realized_pnl_usd - total_pnl) < 0.01
    assert abs(stats.capital_weighted_roi_pct - (total_pnl / total_bought * 100)) < 0.01
    # concentration: largest win (1000) / total positive pnl (1000+500=1500)
    assert abs(stats.concentration_pct - (1000 / 1500 * 100)) < 0.1
    assert len(stats.caveats) > 0


def test_fetch_wallet_stats_paginates_up_to_max():
    page1 = [_position(10, 100, ts=i) for i in range(50)]
    page2 = [_position(20, 100, ts=i) for i in range(50, 80)]
    client = _FakeClient([page1, page2])
    stats = fetch_wallet_stats(
        client, "0xabc", "testuser", lifetime_pnl_usd=0, lifetime_volume_usd=0, max_positions=150
    )
    assert stats.n_closed_positions_sampled == 80
    assert client.calls == 3  # page1 (50), page2 (30 returned but asked for 50), page3 empty -> stop


def test_fetch_wallet_stats_returns_none_when_no_positions():
    client = _FakeClient([[]])
    stats = fetch_wallet_stats(client, "0xabc", "testuser", lifetime_pnl_usd=0, lifetime_volume_usd=0)
    assert stats is None


def test_fetch_wallet_stats_folds_in_unredeemed_losses():
    # Real shape found live 2026-08-20 (a watchlisted wallet): all-win
    # /closed-positions history, but 10 resolved losses sitting unredeemed
    # in /positions (curPrice=0, never redeemed because there's nothing to
    # claim on a worthless position). Confirm they get counted as losses,
    # not silently dropped -- the whole reason this fix exists.
    closed = [_position(1000, 2000, title="Win 1", ts=1), _position(500, 1000, title="Win 2", ts=2)]
    open_positions = [
        _open_position(cash_pnl=-300.0, cur_price=0.0, bought=300.0, title="Resolved loss, unredeemed", end_date="2026-08-10"),
        _open_position(cash_pnl=150.0, cur_price=0.6, bought=250.0, title="Still genuinely open"),  # must be excluded
    ]
    client = _FakeClient([closed], open_positions=open_positions)
    stats = fetch_wallet_stats(client, "0xabc", "testuser", lifetime_pnl_usd=0, lifetime_volume_usd=0)

    assert stats is not None
    # 2 closed wins + 1 unredeemed loss = 3 total; the genuinely-open one is excluded.
    assert stats.n_closed_positions_sampled == 3
    assert abs(stats.win_rate_pct - (2 / 3 * 100)) < 0.1
    assert abs(stats.total_realized_pnl_usd - (1000 + 500 - 300)) < 0.01
    assert any("unredeemed" in c.lower() for c in stats.caveats)


def test_fetch_wallet_stats_survives_open_positions_lookup_failure():
    class _BrokenClient(_FakeClient):
        def get_wallet_positions(self, address):
            raise RuntimeError("simulated API failure")

    client = _BrokenClient([[_position(100, 200, ts=1)]])
    stats = fetch_wallet_stats(client, "0xabc", "testuser", lifetime_pnl_usd=0, lifetime_volume_usd=0)
    assert stats is not None
    assert stats.n_closed_positions_sampled == 1


def test_guess_specialty_catches_soccer_moneyline_phrasing():
    # Real shape found live 2026-08-20: this exact title pattern (Polymarket's
    # standard soccer moneyline phrasing) was previously misclassified as
    # "unclassified" for an 18-of-19-soccer wallet.
    titles = [
        "Will Paris Saint-Germain win on 2026-08-12?",
        "Will FC Groningen win on 2026-08-09?",
        "Will West Ham United FC win on 2026-08-16?",
        "Tōkyō Verdy vs. Kashiwa Reysol: O/U 2.5",
    ]
    assert _guess_specialty(titles) == "sports"


def test_to_trader_stats_maps_fields_and_zeroes_earliness():
    w = RealWalletStats(
        address="0xabc",
        username="testuser",
        n_closed_positions_sampled=10,
        win_rate_pct=60.0,
        avg_position_usd=500.0,
        total_realized_pnl_usd=2000.0,
        capital_weighted_roi_pct=25.0,
        concentration_pct=40.0,
        trade_order_drawdown_pct=15.0,
        trade_order_drawdown_usd=300.0,
        specialty_guess="politics",
        lifetime_pnl_usd=100000.0,
        lifetime_volume_usd=2_000_000.0,
        caveats=["some caveat"],
    )
    ts = to_trader_stats(w)
    assert ts.roi_pct == 25.0
    assert ts.win_rate_pct == 60.0
    assert ts.max_drawdown_pct == 15.0
    assert ts.largest_single_win_pct_of_pnl == 40.0
    assert ts.avg_entry_vs_final_price_gap == 0.0  # not computed from real data -- must stay neutral
