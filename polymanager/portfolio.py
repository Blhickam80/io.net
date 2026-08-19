"""Bankroll and open-position state, persisted to a JSON file so the manager
has memory across trading cycles / process restarts.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .config import STARTING_BANKROLL_USD
from .risk import current_drawdown

DEFAULT_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "portfolio_state.json"


@dataclass
class Position:
    market_id: str
    question: str
    side: str  # "YES" or "NO"
    entry_price: float
    shares: float
    dollars_invested: float
    estimated_probability: float
    catalyst: str
    resolution_date: str
    exit_conditions: str
    strategy: str
    opened_at: str


@dataclass
class PortfolioState:
    starting_bankroll: float = STARTING_BANKROLL_USD
    cash: float = STARTING_BANKROLL_USD
    realized_pnl: float = 0.0
    high_water_mark: float = STARTING_BANKROLL_USD
    positions: list[Position] = field(default_factory=list)

    @property
    def capital_invested(self) -> float:
        return sum(p.dollars_invested for p in self.positions)

    def equity(self, mark_to_market_values: dict[str, float] | None = None) -> float:
        """Cash + current market value of open positions. Without live marks,
        falls back to cost basis (i.e. assumes unrealized P/L of zero)."""
        mtm = mark_to_market_values or {}
        position_value = sum(
            mtm.get(p.market_id, p.dollars_invested) for p in self.positions
        )
        return self.cash + position_value

    def drawdown(self, mark_to_market_values: dict[str, float] | None = None) -> float:
        return current_drawdown(self.equity(mark_to_market_values), self.high_water_mark)

    def update_high_water_mark(self, mark_to_market_values: dict[str, float] | None = None) -> None:
        eq = self.equity(mark_to_market_values)
        if eq > self.high_water_mark:
            self.high_water_mark = eq


def load(path: Path = DEFAULT_STATE_PATH) -> PortfolioState:
    if not path.exists():
        state = PortfolioState()
        save(state, path)
        return state
    raw = json.loads(path.read_text())
    positions = [Position(**p) for p in raw.pop("positions", [])]
    return PortfolioState(positions=positions, **raw)


def save(state: PortfolioState, path: Path = DEFAULT_STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(state)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
