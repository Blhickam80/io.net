from polymanager.portfolio import Position, PortfolioState, load, save


def _position(market_id: str, dollars_invested: float) -> Position:
    return Position(
        market_id=market_id,
        question=f"Will X reach {market_id}?",
        side="NO",
        entry_price=0.5,
        shares=dollars_invested / 0.5,
        dollars_invested=dollars_invested,
        estimated_probability=0.6,
        catalyst="test",
        resolution_date="2026-12-31T00:00:00Z",
        exit_conditions="test",
        strategy="Tier 3 - Experimental",
        opened_at="2026-08-21T00:00:00Z",
    )


def test_default_state_starts_at_bankroll_with_no_positions():
    state = PortfolioState()
    assert state.cash == state.starting_bankroll
    assert state.capital_invested == 0.0
    assert state.equity() == state.starting_bankroll
    assert state.drawdown() == 0.0


def test_capital_invested_sums_open_positions():
    state = PortfolioState(cash=150.0, positions=[_position("a", 30.0), _position("b", 20.0)])
    assert state.capital_invested == 50.0


def test_equity_without_marks_uses_cost_basis_as_unrealized_pl_zero():
    # No live mark-to-market data available -> equity() must fall back to
    # cost basis (assume 0 unrealized P/L), not silently drop the position
    # or double/under-count it.
    state = PortfolioState(cash=150.0, positions=[_position("a", 50.0)])
    assert state.equity() == 200.0


def test_equity_uses_live_mark_when_provided_instead_of_cost_basis():
    state = PortfolioState(cash=150.0, positions=[_position("a", 50.0)])
    # Position now worth $70 (up from its $50 cost basis) per a live mark.
    assert state.equity({"a": 70.0}) == 220.0


def test_equity_falls_back_to_cost_basis_for_positions_missing_from_marks():
    # A live-marks dict that only covers *some* open positions must not
    # silently zero out the ones it doesn't cover.
    state = PortfolioState(cash=100.0, positions=[_position("a", 30.0), _position("b", 20.0)])
    assert state.equity({"a": 40.0}) == 100.0 + 40.0 + 20.0  # b falls back to its $20 cost basis


def test_drawdown_zero_at_high_water_mark():
    state = PortfolioState(cash=200.0, high_water_mark=200.0)
    assert state.drawdown() == 0.0


def test_drawdown_positive_below_high_water_mark():
    state = PortfolioState(cash=150.0, high_water_mark=200.0)
    assert abs(state.drawdown() - 0.25) < 1e-9


def test_update_high_water_mark_only_ratchets_up_never_down():
    state = PortfolioState(cash=250.0, high_water_mark=200.0)
    state.update_high_water_mark()
    assert state.high_water_mark == 250.0

    # Equity now below the new high-water mark -- must not pull it back down.
    state.cash = 100.0
    state.update_high_water_mark()
    assert state.high_water_mark == 250.0


def test_save_and_load_roundtrip_including_positions(tmp_path):
    path = tmp_path / "portfolio_state.json"
    original = PortfolioState(
        cash=120.0,
        realized_pnl=15.0,
        high_water_mark=210.0,
        positions=[_position("a", 30.0), _position("b", 50.0)],
    )
    save(original, path)

    reloaded = load(path)
    assert reloaded.cash == 120.0
    assert reloaded.realized_pnl == 15.0
    assert reloaded.high_water_mark == 210.0
    assert len(reloaded.positions) == 2
    assert reloaded.positions[0].market_id == "a"
    assert reloaded.capital_invested == 80.0


def test_load_missing_file_creates_and_persists_default_state(tmp_path):
    path = tmp_path / "does_not_exist.json"
    assert not path.exists()

    state = load(path)
    assert state.cash == state.starting_bankroll
    # load() on a missing file must have created it, not just returned an
    # in-memory default that silently vanishes on the next call.
    assert path.exists()
    reloaded = load(path)
    assert reloaded.cash == state.cash
