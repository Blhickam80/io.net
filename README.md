# Polymarket Portfolio Manager

An autonomous quantitative-trading framework for Polymarket: market
screening, edge/expected-value analysis, fractional-Kelly position sizing,
tiered risk buckets, drawdown throttling, copy-trader quality scoring, and a
trading journal — implementing the portfolio-manager mandate this repo was
built from.

## Status: live data works; no capital has moved

This started in a sandbox with no outbound network access to Polymarket at
all. That's since been fixed by switching the Claude Code cloud environment's
network access level to **Full** (see [Cloud environments](https://code.claude.com/docs/en/cloud-environments#access-levels) —
the alternative is **Custom** with `gamma-api.polymarket.com`,
`clob.polymarket.com`, `data-api.polymarket.com`, and `api.coingecko.com`
explicitly allowlisted). `polymanager/api.py`'s endpoints and
`polymanager/coingecko.py` are now verified live, not just written against
docs. Still true:

- **No real trades have been made and no wallet is configured.** Nothing in
  this repo has touched real money. `polymanager/execution.py` still refuses
  to place live orders (see "Going live" below).
- Recommendations the live cycle produces are real model output, not
  fabricated numbers — but they reflect exactly one automated strategy
  (`polymanager/btc_touch.py`) with a documented, imperfect calibration (see
  "Backtesting" below). Everything else still correctly falls through to
  `NO TRADE`.

Run `python -m polymanager.cli` to execute a real cycle.

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

- **Live strategy #1: BTC barrier-touch** (`polymanager/btc_touch.py`,
  `polymanager/models.py`, `polymanager/coingecko.py`) — prices "Will Bitcoin
  reach $X in \<month\>?" markets (a textbook barrier option: resolves YES if
  BTC ever trades at/above $X during the window) against live spot price and
  realized volatility using a driftless-GBM touch-probability formula, and
  compares that to the market's own price.
- **Live strategy #2: nested-outcome monotonicity** (`polymanager/monotonicity.py`)
  — Polymarket's "ladder" events (e.g. "What price will Bitcoin hit in
  \<month\>?") contain many nested markets ("reach $72,500," "reach $75,000,"
  …) where a harder outcome can never legitimately be priced above an easier
  one. This is a model-free, no-research-needed consistency check — pure
  logic, not probability estimation. Run `python -m polymanager.monotonicity`
  to scan live. **Real finding (2026-08-20):** a naive scan initially flagged
  12 "violations" across 50 active events, but every one was 0.1–0.3
  percentage points on deep out-of-the-money tail markets — smaller than
  Polymarket's own tick size and typical spread, i.e. noise, not tradeable
  arbitrage. Added `MIN_VIOLATION_MAGNITUDE_PP` (2.0) and a liquidity floor
  on both legs; after filtering, **zero real violations** across the top 50
  events by volume. Efficient-market result, not a bug — this check is
  well-known enough that market makers actively enforce it, so don't expect
  frequent hits. Cross-market inconsistency also produces *pair* trades
  (short the overpriced leg, long the underpriced one), not a single-side
  probability estimate, so it deliberately isn't forced into
  `polymanager.cli`'s per-market Kelly-sizing pipeline — it's a separate
  scan with its own entry point.
- **Live strategy #3: mutually-exclusive outcome sum** (`polymanager/sum_consistency.py`)
  — the classic complement to monotonicity: for a "negRisk" event where
  exactly one outcome resolves YES (elections, championships, "who wins"
  markets), summed YES prices across every outcome should sit near 100%.
  Materially below 100% = a YES basket across all outcomes is underpriced;
  materially above = a NO basket is. Run `python -m polymanager.sum_consistency`
  to scan live. **Real findings (2026-08-20):** an initial scan of 50 active
  negRisk events flagged 9, including two presidential-primary events
  (Democratic Nominee 2028, Presidential Winner 2028) apparently underpriced
  by 5-9pp — but investigation showed only 51-52 of each event's 128 total
  candidate markets have ever traded; the other ~77 are real outcome slots
  with zero price history, and summing *every priced* market (ignoring
  liquidity entirely) still landed under 100%, meaning the "missing"
  probability is genuinely sitting on those untradeable long-shot legs, not
  capturable as a basket trade. Added `has_unpriced_outcomes()` to suppress
  a below-100% finding whenever an event has any untraded outcome (the
  opposite direction isn't suppressed, since missing mass only pushes an
  already-above-100% sum higher). After that fix: **7 remaining findings**,
  all "buy the NO basket" on long-duration tournament/range-bucket markets
  (2-9pp), each printed with an explicit capital-lock-up/execution-slippage
  caveat rather than presented as clean free money — 12-32 legs held until
  a championship resolves months out is a real cost, not a rounding error.
- **Backtesting** (`polymanager/backtest.py`) — walk-forward calibration test
  for the touch-probability model against real historical BTC data. **Real
  finding from the 2026-08-20 run** (trailing 365 days, the longest history
  CoinGecko's free tier allows): mean predicted touch probability was 44.0%
  against an actual realized rate of 24.7%. That's not necessarily a bug in
  the math — that backtest year saw BTC fall ~37% peak-to-trough, and a
  zero-drift model *will* overstate upside-barrier touches in a sustained
  downtrend (symmetrically, it understates them in an uptrend, which is what
  happened during this repo's first live cycle the same day — see the
  trading journal). Because there's no reliable way to know in advance which
  regime the next few weeks will look like, `btc_touch.py` hard-caps its own
  confidence output at 4/10 (`CONFIDENCE_CAP`) until this is re-validated —
  which keeps it out of Tier 1/2 sizing entirely regardless of nominal edge.
  Run `python -m polymanager.backtest` to reproduce or re-run this.

Still deliberately **not** faked: for every other market shape,
`estimate_true_probability()` in `polymanager/cli.py` returns `None` — which
correctly routes to `NO TRADE` — because a real probability estimate requires
actually reading news, polling data, official sources, etc. per market and
per cycle. **Add more strategies the same way `btc_touch.py` was built**:
real data source, real (ideally backtested) model, honest confidence:
never a guess dressed up as a number.

## Running it

```bash
pip install -r requirements.txt

# Offline pipeline walkthrough against synthetic, clearly-labeled sample markets:
python -m polymanager.cli --demo

# Run everything live in one go (main cycle + both cross-market scans):
python -m polymanager.scan_all

# Or individually:

# Real cycle (requires network access to Polymarket's + CoinGecko's APIs):
python -m polymanager.cli

# Re-run the BTC touch-probability model's calibration backtest:
python -m polymanager.backtest

# Scan live events for nested-outcome (ladder) pricing violations:
python -m polymanager.monotonicity

# Scan live events for mutually-exclusive-outcome sum inconsistencies:
python -m polymanager.sum_consistency

# Test suite (no network required -- all network calls are mocked/avoided):
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
