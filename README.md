# Polymarket Portfolio Manager

An autonomous quantitative-trading framework for Polymarket: market
screening, edge/expected-value analysis, fractional-Kelly position sizing,
tiered risk buckets, drawdown throttling, copy-trader quality scoring, and a
trading journal — implementing the portfolio-manager mandate this repo was
built from.

## Important: this environment cannot reach Polymarket

The sandbox this code was authored in has **no outbound network access** to
`gamma-api.polymarket.com`, `clob.polymarket.com`, or `data-api.polymarket.com`
(egress is blocked at the proxy level — confirmed directly, not assumed). That
means:

- No live market prices, order books, or wallet/leaderboard data could be
  fetched from this session.
- No real trades were or could be made. **Nothing in this repo has touched
  real money.**
- Every number in this README's example output is either a unit test
  assertion or clearly-labeled synthetic `[DEMO]` data — never presented as a
  real market or a real recommendation.

Run `python -m polymanager.cli` from a machine/environment with normal
internet access to get real data and real recommendations.

## What's actually implemented vs. what still needs research judgment

Implemented as real, tested code (`tests/` passes with no network needed):

- **Market Selection Filter** (`polymanager/scanner.py`) — rejects markets on
  liquidity, 24h volume, spread, time-to-resolution, and disputed-resolution
  status before any probability analysis runs.
- **Kelly-criterion sizing** (`polymanager/kelly.py`) — `f* = (p_true -
  price) / (1 - price)` for a YES share, scaled by a confidence-based
  fractional-Kelly multiplier (1/4, 1/3, 1/2), then capped by risk tier and a
  hard per-position ceiling.
- **Risk tiers and drawdown throttle** (`polymanager/config.py`,
  `polymanager/risk.py`) — Tier 1/2/3 allocation bands, and automatic size
  reduction at 10%/20%/30% drawdown from the bankroll's high-water mark.
- **Correlation limits** (`polymanager/risk.py`) — caps aggregate exposure to
  a group of correlated markets (e.g. multiple contracts on the same
  election) even if each position individually looks fine.
- **Copy-trading quality score** (`polymanager/copytrading.py`) — weights
  sample size, win rate, ROI, drawdown, and (critically) *penalizes* traders
  whose P/L is concentrated in one lucky trade, rather than just ranking by
  raw realized profit.
- **Portfolio state & trading journal** (`polymanager/portfolio.py`,
  `polymanager/journal.py`) — persisted bankroll/position state in
  `data/portfolio_state.json`, append-only decision log in
  `data/trading_journal.csv`.
- **Dashboard renderer** (`polymanager/dashboard.py`) — produces the exact
  Bankroll / Best Opportunities / Existing Positions / Actions format from
  the mandate.
- **Cycle orchestrator** (`polymanager/cli.py`) — runs the 14-step cycle:
  load state → scan markets → screen → estimate probability → compute edge →
  size position → check correlation → journal → render dashboard.

Deliberately **not** faked: **Step 5/6, "research the event and estimate its
true probability,"** is the one step this codebase refuses to automate with a
stub. `estimate_true_probability()` in `polymanager/cli.py` returns `None`
for every market by default — which correctly routes everything to `NO
TRADE` — because a real probability estimate requires actually reading news,
polling data, court filings, official sources, etc. per market, which needs
live tools this sandbox doesn't have. **Wire real research into that
function** (an LLM session with live web search + this codebase's data, or a
human analyst) before using this for real capital allocation. Treating a
placeholder 50/50 or the market's own price as your "estimate" would silently
defeat the entire point of the system (you can't have edge against a price by
copying that same price).

## Running it

```bash
pip install -r requirements.txt

# Offline pipeline walkthrough against synthetic, clearly-labeled sample markets:
python -m polymanager.cli --demo

# Real cycle (requires network access to Polymarket's APIs + a wired-up
# estimate_true_probability implementation to produce any opportunities):
python -m polymanager.cli

# Test suite (no network required):
pip install pytest
pytest tests/ -q
```

## Going live (real order execution)

`polymanager/execution.py` intentionally does **not** ship a working
live-order path. To enable it:

1. Install `py-clob-client`.
2. Fund a Polygon wallet with USDC and set `POLYMARKET_PRIVATE_KEY` as an
   environment variable — **never commit it, never put it in this repo**.
3. Implement and review the actual order-building/signing call in
   `live_execute()` before using it. It currently raises
   `LiveExecutionUnavailable` on purpose rather than silently no-opping or
   falling back to a paper trade.

Only the operator can supply that wallet key and take on that legal/
financial responsibility — this is the one input the mandate correctly
identifies as something only a human can authorize.

## Risk framework at a glance

| | |
|---|---|
| Starting bankroll | $200 |
| Tier 1 (high confidence) | 5-12% per position, edge ≥ 10pp, confidence ≥ 8/10 |
| Tier 2 (medium confidence) | 2-6% per position, edge ≥ 6pp, confidence ≥ 6/10 |
| Tier 3 (experimental) | 0.5-3% per position, edge ≥ 3pp, confidence ≥ 4/10 |
| Drawdown ≥ 10% | Position sizing × 0.5 |
| Drawdown ≥ 20% | Position sizing × 0.25 |
| Drawdown ≥ 30% | Position sizing × 0 (stop; diagnose before resuming) |
| Max single position | 12% of bankroll (hard cap, overrides Kelly) |
| Max correlated group | 20% of bankroll |

All defaults live in `polymanager/config.py` and are meant to be tuned, not
treated as immutable law.

## Legal / disclaimer

This is a decision-support and execution-scaffolding tool, not investment
advice. Prediction-market trading may not be legal or available in every
jurisdiction or for every account; confirm you're eligible under Polymarket's
terms and your local law before funding a wallet or placing real orders. No
trade is ever certain; capital preservation takes priority over upside in
every default in this codebase.
