"""Integration test: verify run_cycle_structured actually enforces the
correlation cap across multiple correlated opportunities in one cycle,
and that accepted opportunities get real BUY actions and journal entries --
regression coverage for three real gaps found live 2026-08-20: actions
were always empty, journal entries were never written for real
opportunities, and the correlation-exposure check (tested in isolation in
polymanager.risk) was never actually called from the cycle.
"""

from __future__ import annotations

import functools
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from polymanager import cli, journal, portfolio
from polymanager.config import MAX_CORRELATED_GROUP_PCT
from polymanager.journal import read_journal


def _future_iso(days: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def _patch_journal_paths(monkeypatch, journal_path) -> None:
    """Route journal writes to a tmp path for the duration of a test.

    Not a plain functools.partial(fn, path=journal_path) for each function:
    journal.record_no_trade() internally calls append_entry(entry, path)
    positionally, and that call resolves `append_entry` via journal.py's
    module namespace at call time -- so if append_entry is *also*
    monkeypatched to a partial with `path` pre-bound as a keyword, the
    positional `path` record_no_trade passes collides with it
    ("got multiple values for argument 'path'"). Wrapping in plain
    functions with `path` as a normal default (not partial-bound) avoids
    the collision either way it's called.
    """
    original_append_entry = journal.append_entry
    original_record_no_trade = journal.record_no_trade
    original_has_open = journal.has_open_unresolved_entry

    def _append_entry(entry, path=journal_path):
        return original_append_entry(entry, path)

    def _record_no_trade(reason, path=journal_path):
        return original_record_no_trade(reason, path)

    def _has_open_unresolved_entry(market_id, side, path=journal_path):
        return original_has_open(market_id, side, path)

    monkeypatch.setattr(journal, "append_entry", _append_entry)
    monkeypatch.setattr(journal, "record_no_trade", _record_no_trade)
    monkeypatch.setattr(journal, "has_open_unresolved_entry", _has_open_unresolved_entry)


def _btc_market(barrier: float, yes_price: float) -> dict:
    return {
        "id": f"btc-{barrier}",
        "question": f"Will Bitcoin reach ${barrier:,.0f} in August?",
        "outcomePrices": [str(yes_price), str(1 - yes_price)],
        "spread": 0.01,
        "liquidityNum": 50000,
        "volume24hr": 10000,
        "endDate": _future_iso(10),
    }


def test_correlation_key_groups_bitcoin_markets_together():
    assert cli._correlation_key("Will Bitcoin reach $80,000 in August?") == cli._correlation_key(
        "Will Bitcoin reach $100,000 in August?"
    )
    assert cli._correlation_key("Will Bitcoin reach $80,000?") != cli._correlation_key("Will the Fed cut rates?")


def test_correlation_cap_enforced_across_correlated_opportunities(tmp_path, monkeypatch):
    # Eight BTC markets all priced well above a low model estimate -> real
    # edge on every one, each sizing to Tier 3's $6 cap (3% of $200).
    # Without the correlation cap, Kelly sizing alone would happily fund
    # all eight ($48) even though they're all correlated bets on the same
    # underlying asset -- that would blow past the $40 (20%) cap.
    barriers = (200_000, 210_000, 220_000, 230_000, 240_000, 250_000, 260_000, 270_000)
    markets = [_btc_market(barrier, 0.90) for barrier in barriers]

    # portfolio.load/journal.append_entry etc. bind their DEFAULT_*_PATH
    # default at function-definition time, so monkeypatching the path
    # constant after import has no effect on already-bound defaults --
    # rebind the functions themselves to a tmp path via partial instead.
    state_path = tmp_path / "portfolio_state.json"
    journal_path = tmp_path / "trading_journal.csv"
    # Pre-create the state file with the real (unpatched) save() so
    # load()'s own internal "if not path.exists(): save(state, path)" call
    # never fires -- that internal call is positional and would collide
    # with a partial-bound `path` keyword on a patched save().
    portfolio.save(portfolio.PortfolioState(), state_path)
    monkeypatch.setattr(portfolio, "load", functools.partial(portfolio.load, path=state_path))
    monkeypatch.setattr(portfolio, "save", functools.partial(portfolio.save, path=state_path))
    _patch_journal_paths(monkeypatch, journal_path)

    with (
        patch.object(cli, "PolymarketClient") as MockClient,
        patch.object(cli, "CoinGeckoClient") as MockCoinGecko,
    ):
        MockClient.return_value.get_markets.return_value = markets
        MockCoinGecko.return_value.get_spot_price.return_value = 72000.0
        MockCoinGecko.return_value.get_realized_daily_vol.return_value = 0.02

        dashboard, opportunities, equity = cli.run_cycle_structured(demo=False)

    # Every accepted opportunity is correlated (all "bitcoin"); their
    # combined size must not exceed the correlation cap of the bankroll
    # used for sizing (state.cash at the time, effectively starting
    # bankroll here since nothing has been spent yet).
    total_invested = sum(o["recommended_investment"] for o in opportunities)
    assert total_invested <= 200.0 * MAX_CORRELATED_GROUP_PCT + 1e-6

    # Fewer than all six should have been accepted, proving the cap
    # actually dropped some rather than everything sailing through.
    assert len(opportunities) < len(markets)

    # Real BUY actions rendered, not the old always-empty placeholder.
    assert opportunities, "expected at least one opportunity given the strong synthetic edge"
    assert "BUY" in dashboard
    assert "NO TRADE" not in dashboard

    # Real journal entries written for the accepted opportunities.
    rows = read_journal(journal_path)
    assert len(rows) == len(opportunities)
    assert all(row["market"].startswith("Will Bitcoin reach") for row in rows)


def test_still_open_opportunity_is_not_rejournaled_every_cycle(tmp_path, monkeypatch):
    # Real bug found live 2026-08-21: with no wallet configured,
    # state.positions never actually gets an accepted opportunity added to
    # it (see the drawdown-throttle finding), so a still-open opportunity
    # never stops looking like a fresh opportunity to cli.py -- it got
    # journaled again every single cycle it stayed open. One real market
    # ("$77,500 in August" NO) was journaled 7 separate times this way
    # before it resolved, and all 7 rows counted as independent losses in
    # performance.py's aggregate stats. Reproduce with two back-to-back
    # cycles on the identical unresolved market/price: only one journal
    # row should exist after both.
    market = _btc_market(300_000, 0.90)

    state_path = tmp_path / "portfolio_state.json"
    journal_path = tmp_path / "trading_journal.csv"
    portfolio.save(portfolio.PortfolioState(), state_path)
    monkeypatch.setattr(portfolio, "load", functools.partial(portfolio.load, path=state_path))
    monkeypatch.setattr(portfolio, "save", functools.partial(portfolio.save, path=state_path))
    _patch_journal_paths(monkeypatch, journal_path)

    with (
        patch.object(cli, "PolymarketClient") as MockClient,
        patch.object(cli, "CoinGeckoClient") as MockCoinGecko,
    ):
        MockClient.return_value.get_markets.return_value = [market]
        MockCoinGecko.return_value.get_spot_price.return_value = 72000.0
        MockCoinGecko.return_value.get_realized_daily_vol.return_value = 0.02

        cli.run_cycle_structured(demo=False)
        cli.run_cycle_structured(demo=False)

    # Exactly one BUY row across both cycles -- the second cycle correctly
    # recognizes the market/side as already open and does not duplicate it
    # (a distinct NO-TRADE trace row for the second cycle is expected and
    # covered by test_all_opportunities_already_open_leaves_no_trade_trace
    # below; this test's own concern is strictly "no duplicate BUY").
    rows = read_journal(journal_path)
    buy_rows = [r for r in rows if r["market"] != "NO TRADE"]
    assert len(buy_rows) == 1, f"expected exactly one BUY row across two identical cycles, got {len(buy_rows)}"


def test_all_opportunities_already_open_leaves_no_trade_trace(tmp_path, monkeypatch):
    # Real gap found live 2026-08-21, immediately after shipping the dedup
    # fix above: a cycle where every opportunity is already an open
    # recommendation correctly writes zero new BUY rows -- but it wrote
    # nothing at all, not even a NO TRADE marker, so the journal had no
    # record the cycle ran. Reproduce: second cycle on the identical
    # unresolved market should append exactly one NO TRADE row, not zero.
    market = _btc_market(300_000, 0.90)

    state_path = tmp_path / "portfolio_state.json"
    journal_path = tmp_path / "trading_journal.csv"
    portfolio.save(portfolio.PortfolioState(), state_path)
    monkeypatch.setattr(portfolio, "load", functools.partial(portfolio.load, path=state_path))
    monkeypatch.setattr(portfolio, "save", functools.partial(portfolio.save, path=state_path))
    _patch_journal_paths(monkeypatch, journal_path)

    with (
        patch.object(cli, "PolymarketClient") as MockClient,
        patch.object(cli, "CoinGeckoClient") as MockCoinGecko,
    ):
        MockClient.return_value.get_markets.return_value = [market]
        MockCoinGecko.return_value.get_spot_price.return_value = 72000.0
        MockCoinGecko.return_value.get_realized_daily_vol.return_value = 0.02

        cli.run_cycle_structured(demo=False)
        cli.run_cycle_structured(demo=False)

    rows = read_journal(journal_path)
    assert len(rows) == 2, f"expected 1 BUY row + 1 NO TRADE trace row, got {len(rows)}"
    assert rows[0]["market"] != "NO TRADE"
    assert rows[1]["market"] == "NO TRADE"
    assert "already have an open" in rows[1]["reason"]
