"""Renders the REQUIRED OUTPUT dashboard format: bankroll summary, ranked
opportunities, existing positions, and the action list.
"""

from __future__ import annotations

from .portfolio import PortfolioState


def render_bankroll(state: PortfolioState, mark_to_market_values: dict[str, float] | None = None) -> str:
    equity = state.equity(mark_to_market_values)
    invested = state.capital_invested
    if mark_to_market_values:
        unrealized = sum(
            mark_to_market_values.get(p.market_id, p.dollars_invested) - p.dollars_invested
            for p in state.positions
        )
    else:
        unrealized = 0.0
    total_return_pct = (
        (equity - state.starting_bankroll) / state.starting_bankroll * 100
        if state.starting_bankroll
        else 0.0
    )
    dd = state.drawdown(mark_to_market_values) * 100

    lines = [
        "BANKROLL",
        f"Starting Bankroll: ${state.starting_bankroll:,.2f}",
        f"Current Bankroll: ${equity:,.2f}",
        f"Cash Available: ${state.cash:,.2f}",
        f"Capital Invested: ${invested:,.2f}",
        f"Realized P/L: ${state.realized_pnl:,.2f}",
        f"Unrealized P/L: ${unrealized:,.2f}",
        f"Total Return: {total_return_pct:.2f}%",
        f"Maximum Drawdown: {dd:.2f}%",
    ]
    return "\n".join(lines)


def render_opportunity(rank: int, opp: dict) -> str:
    return "\n".join(
        [
            f"{rank}. Market: {opp['market']}",
            f"Position: {opp['side']}",
            f"Current Price: ${opp['current_price']:.3f}",
            f"Target Entry: ${opp['target_entry']:.3f}",
            f"Estimated True Probability: {opp['estimated_probability']:.1%}",
            f"Estimated Edge: {opp['edge_pp']:+.1f} pp",
            f"Recommended Investment: ${opp['recommended_investment']:.2f}",
            f"Confidence: {opp['confidence']}/10",
            f"Strategy: {opp['strategy']}",
            f"Reason: {opp['reason']}",
        ]
    )


def render_opportunities(opportunities: list[dict]) -> str:
    if not opportunities:
        return "BEST OPPORTUNITIES\nNone met the expected-value / edge bar this cycle."
    body = "\n\n".join(render_opportunity(i + 1, o) for i, o in enumerate(opportunities))
    return f"BEST OPPORTUNITIES\n{body}"


def render_position(p, current_price: float | None, recommendation: str, reason: str) -> str:
    price_str = f"${current_price:.3f}" if current_price is not None else "unknown (no live mark)"
    pnl_str = (
        f"${(current_price - p.entry_price) * p.shares:+.2f}"
        if current_price is not None
        else "n/a"
    )
    return "\n".join(
        [
            f"Market: {p.question}",
            f"Entry: ${p.entry_price:.3f} ({p.side})",
            f"Current: {price_str}",
            f"P/L: {pnl_str}",
            f"Current Estimated Probability: {p.estimated_probability:.1%}",
            f"Recommendation: {recommendation}",
            f"Reason: {reason}",
        ]
    )


def render_positions(entries: list[str]) -> str:
    if not entries:
        return "EXISTING POSITIONS\nNone."
    return "EXISTING POSITIONS\n" + "\n\n".join(entries)


def render_actions(actions: list[str]) -> str:
    if not actions:
        return "ACTIONS\nNO TRADE\nNo opportunities currently clear the expected-value bar. Preserve the bankroll and continue searching."
    return "ACTIONS\n" + "\n\n".join(actions)


def render_full_dashboard(
    state: PortfolioState,
    opportunities: list[dict],
    position_entries: list[str],
    actions: list[str],
    mark_to_market_values: dict[str, float] | None = None,
) -> str:
    sections = [
        render_bankroll(state, mark_to_market_values),
        render_opportunities(opportunities),
        render_positions(position_entries),
        render_actions(actions),
    ]
    return "\n\n".join(sections)
