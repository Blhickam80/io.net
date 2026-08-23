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
- **The CLOB order-book client is written but never used.** `polymanager/api.py`
  implements `get_order_book()` and `get_price()` against `clob.polymarket.com`
  — real, correct code, now with its own test coverage — but a repo-wide
  grep (2026-08-21) confirms neither is called from anywhere else in the
  codebase. Every strategy prices markets from Gamma's static `outcomePrices`
  snapshot field instead, never the live order book. That's a real gap for
  execution quality (a snapshot price isn't the same as confirmed tradeable
  depth at that price), separate from and in addition to the no-wallet
  limitation above — worth wiring in before `execution.py` ever places a
  real order, not before.
- **`polymanager/risk.py` had a real zero-bankroll edge case, fixed
  2026-08-21.** `check_correlation_limit()`'s old divide-by-zero guard
  made `resulting_pct` fall back to `0.0` whenever `bankroll <= 0`, so any
  proposed dollar amount — even $1,000 — was reported as "0% exposure"
  and always allowed. Exactly backwards: zero or negative capital should
  block any *new* correlated exposure, not wave it through. Currently
  unreachable in this deployment (`state.cash` never actually decreases —
  same root cause as the drawdown-throttle finding), but a genuine
  correctness bug regardless, fixed the same way as `crypto_touch.py`'s
  pre-emptive decimal fix: before it can ever fire, not after.

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
  `data/trading_journal.csv`. **Audited (2026-08-21)**: `portfolio.py`
  itself had zero test coverage despite underlying several of the drawdown
  findings above; a close read plus 10 new tests (`equity()`/`drawdown()`
  math, high-water-mark ratcheting, save/load round-trip) found no
  independent bug in the module's own logic — its only real issue is the
  already-documented one (nothing ever populates `state.positions`, not a
  flaw in how `equity()`/`drawdown()` compute from whatever state they're
  given).
- **Dashboard renderer** (`polymanager/dashboard.py`) — produces the exact
  Bankroll / Best Opportunities / Existing Positions / Actions format from
  the mandate.
- **Cycle orchestrator** (`polymanager/cli.py`) — runs the 14-step cycle:
  load state → scan markets → screen → estimate probability → compute edge →
  size position → check correlation → journal → render dashboard.

  **Three real gaps found and fixed by actually running this end-to-end
  (2026-08-20), not just building it:**
  1. **YES-only blind spot.** The opportunity loop only ever evaluated the
     YES side of a market. A probability estimate below the market's YES
     price is exactly a positive edge on NO (`p_true_NO = 1-p_true`,
     `price_NO = 1-price_YES`) — the loop was silently discarding every
     NO-side opportunity. Live: with BTC having rallied further, several
     "reach $X" markets showed a real 3-5pp edge on NO that never
     surfaced. Added `_best_side()` to evaluate both sides and take
     whichever has the better edge.
  2. **Confidence-4 opportunities always sized to $0.** `T3_EXPERIMENTAL`
     accepts `confidence >= 4`, but `KELLY_FRACTION_BY_CONFIDENCE`'s floor
     was 5 — any confidence-4 opportunity got a 0.0 Kelly multiplier no
     matter its edge. This silently neutered `btc_touch.py`'s own
     `CONFIDENCE_CAP=4`: an entire strategy could never produce a trade
     regardless of edge size. Fixed by adding an explicit, deliberately
     conservative 1/8-Kelly bucket at confidence 4 in `config.py`.
  3. **ACTIONS section and journal entries were dead code for real
     opportunities.** `actions` was hardcoded to `[]` and only `NO TRADE`
     ever got journaled — a cycle with 5 real opportunities in "BEST
     OPPORTUNITIES" still printed "ACTIONS: NO TRADE" underneath them, and
     nothing was ever recorded for an actual recommendation. Also:
     `polymanager/risk.py`'s correlation-exposure check was fully built and
     unit-tested but never actually called from the cycle — multiple
     correlated BTC opportunities in one cycle could in principle have
     summed past `MAX_CORRELATED_GROUP_PCT` with nothing stopping it (today's
     numbers stayed under it by coincidence, not enforcement). Fixed all
     three together: opportunities are now accepted in ranked order against
     `check_correlation_limit`, rendered as real `BUY` actions
     (`dashboard.render_buy_action`, matching the mandate's exact format
     including a "do not chase above" ceiling), and journaled via
     `journal.append_entry` — not just `NO TRADE`.

  After these fixes, the same live BTC rally that closed the earlier
  edges opened new ones on the downside: the system's first-ever real
  output was 6 ranked NO-side opportunities on "reach $X" markets (BTC has
  overshot several thresholds; the barrier-touch model says the market is
  now overpricing further upside), sized $1.25-$6.00 each, all Tier 3
  given the model's confidence cap. See the trading journal for the exact
  entries.

- **Live strategy #1: crypto barrier-touch** (`polymanager/crypto_touch.py`
  is the shared engine; `polymanager/btc_touch.py` and
  `polymanager/eth_touch.py` are thin per-asset wrappers, each with its own
  `CONFIDENCE_CAP`; `polymanager/models.py`, `polymanager/coingecko.py`) —
  prices "Will Bitcoin/Ethereum reach $X in \<month\>?" markets (a textbook
  barrier option: resolves YES if the asset ever trades at/above $X during
  the window) against live spot price and realized volatility using a
  driftless-GBM touch-probability formula, and compares that to the
  market's own price. **Each asset's confidence cap comes from that
  asset's own backtest — one never transfers to the other.** BTC's capped
  at 4/10 (see below). Ran the identical backtest against ETH's own price
  history (2026-08-20): ETH fell ~46% over the window (steeper than BTC's
  ~37%), and the model's Brier score (0.2359) came out *worse* than a
  naive always-predict-the-base-rate baseline (0.2320) — it doesn't
  currently beat a coin flip for ETH. `eth_touch.py`'s `CONFIDENCE_CAP` is
  set to 2, below every risk tier's `min_confidence` floor (Tier 3's is 4)
  — deliberately wired into the live pipeline for visibility rather than
  disabled outright, but structurally incapable of sizing a trade.
  Confirmed live: real ETH "reach $X" markets get evaluated and produce
  real model estimates each cycle, but never qualify for a sized
  recommendation.
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
  **Real bug found live (2026-08-21):** after a full day of correctly
  finding zero violations (every ladder scanned had been BTC, always
  whole-dollar thresholds), the first decimal-priced ladder swept in
  ("What price will XRP hit in August?", $1.40/$1.60/$1.80) immediately
  produced 3 "violations." Cause: the threshold-parsing regex's capture
  group was `[\d,]+`, which doesn't include `.` — every XRP threshold
  silently truncated to `1.0`, so three genuinely different, correctly
  monotonic prices got compared as if they were three copies of the same
  market. Fixed by extending the capture group to `[\d,]+(?:\.\d+)?`;
  re-ran the live scan after the fix — back to 0 violations, confirming the
  "finding" was purely a parsing bug, not a real inconsistency. This had
  been silently wrong since the module was written; nothing decimal-priced
  had ever been scanned before to trigger it.
  **Follow-up spot-check (2026-08-21):** grepped the rest of `polymanager/`
  for the same `[\d,]+`-without-decimal pattern. Found one more instance —
  `polymanager/crypto_touch.py`'s `make_pattern()`/`extract_barrier()`, the
  shared engine behind `btc_touch.py`/`eth_touch.py`'s real probability
  estimates. This one is more consequential than the monotonicity
  false-positive: a truncated barrier there wouldn't just produce a benign
  duplicate-market flag, it would silently feed the wrong barrier into
  `touch_probability_upper_barrier()` and corrupt the resulting edge/sizing
  recommendation. No live BTC/ETH "reach $X" market has used a decimal
  threshold yet (same reason the monotonicity bug went undetected all day),
  so this hadn't fired live — fixed pre-emptively with the identical regex
  change rather than waiting for it to. No other `re.compile`/`_PATTERN`
  definitions in the package use this shape.
  **First genuine violation, confirmed live (2026-08-21, later the same
  day):** "Will Bitcoin reach $87,500 in August?" (harder, higher
  threshold) priced at 28.5% YES, above "Will Bitcoin reach $85,000 in
  August?" (easier) at 19.8% — an 8.7pp inconsistency, both whole-dollar
  thresholds (no decimal-parsing involvement). Checked both legs directly
  against Gamma: both open, `acceptingOrders: true`, not closed, and both
  clear `MIN_LIQUIDITY_USD` ($52,107 and $2,645 respectively, floor is
  $2,000). Unlike every earlier "violation" this module ever reported,
  this one is real — not a parsing bug, not a stale-instance artifact, not
  sub-threshold noise. First actual confirmation, after a full day of
  either zero violations or bugs, that the mechanism catches a genuine
  live inconsistency when one exists. **Closed the loop roughly an hour
  later (2026-08-21):** re-scanned and the violation was gone — not
  because the market closed, but because it self-corrected: $85,000 moved
  to 17.6% and $87,500 to 9.0%, correctly monotonic again. A real,
  briefly-mispriced inefficiency that the market itself arbitraged away —
  further confirmation the original finding was genuine, not a data
  artifact, and a small demonstration of exactly the efficient-market
  self-correction this module's docstring predicted from day one.
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
  **Follow-up work, same day:** three more real issues found and fixed by
  actually using the tool, not just building it:
  1. **Feasibility check.** Added `minimum_basket_cost_usd()`, using each
     leg's real `orderMinSize`, to compute the cheapest a basket could
     possibly be executed for. Result: all 6 remaining tournament findings
     require 22-77% of a $200 bankroll just to place the *minimum* order on
     every leg — every one exceeds the portfolio's own 20% correlated-
     exposure cap before any sizing decision happens. The nominal edge is
     real; it is not accessible at this bankroll size. `main()` now prints
     this and an explicit "NOT PRACTICALLY TRADEABLE" flag per finding.
  2. **Liquidity-masked mass (a second completeness bug).** Live scan
     surfaced "Highest temperature in London on August 20?" at sum=0.6%,
     deviation=-99.4pp, minimum cost $0.03 — absurd on its face. Cause: the
     correct answer (24C) was priced at 99.75% but had only $1,740
     liquidity, just under the $2,000 floor, so `parse_legs` silently
     dropped it along with essentially all the real probability mass.
     `has_unpriced_outcomes` didn't catch this because the market *was*
     priced, just excluded for being thin. Added `has_liquidity_masked_mass()`,
     which compares the liquid-only sum against the sum of every *priced*
     market regardless of liquidity; a gap bigger than the noise threshold
     now suppresses the finding the same way an unpriced outcome does.
  3. **In-play timing risk.** A real, liquid, well-formed finding appeared
     on a live soccer match (Mjallby vs. Salzburg) with a genuine 3.5pp
     deviation and feasible execution cost — but its `endDate` was already
     ~35 minutes in the past, meaning the match was in-play or just
     finished. A periodic REST-poll scan cannot compete with a fast-moving
     in-play order book; that gap is far more likely stale-by-the-time-you-
     see-it than real. Added `MIN_HOURS_TO_RESOLUTION_FOR_ARB` (24h): any
     event with a leg resolving sooner than that is skipped for this
     strategy entirely, independent of how good the number looks.

  After all three fixes: **6 real findings remain, and all 6 are flagged
  NOT PRACTICALLY TRADEABLE** at a $200 bankroll (last checked 2026-08-20) —
  the honest end state is that this strategy currently has zero *actionable*
  edge for this account size, not that it found nothing.
  **Persistence check (2026-08-21):** a stable finding *count* across scans
  (5-7 findings, repeatedly, over 9+ hours) doesn't by itself prove it's the
  same mispricing recurring rather than a different rotating set of events
  landing on a similar count by coincidence — `scan_history.jsonl` only
  logged counts until this was fixed to also log event titles (see
  `polymanager.scan_history.persistent_sum_consistency_titles()`). First
  real check against two tagged scans 78 minutes apart: **all 6 events found
  in the first scan reappeared identically in the second** (UEFA Champions
  League, EPL, NBA, and Pro Football 2027 champions; Brazil Presidential
  Election; 2026 Men's US Open) — genuine persistence, not coincidence.
  **Refined with a 3rd tagged scan (2026-08-21, ~2h36m span):** the picture
  sharpens rather than just repeating — 5 events (UEFA, EPL, NBA, Pro
  Football, Brazil) held across *all three* scans and are the real signal,
  while the 2026 Men's US Open and a later-appearing EWC 2026 CS2 finding
  each showed up in only 2 of 3 scans. Checking their actual deviations
  explains why: both sat right at the 2.0pp `MIN_SUM_DEVIATION_PP` threshold
  (US Open was +2.1pp when it appeared), so small odds movements between
  scans flip them in and out of the finding set — boundary noise, not a
  real mispricing coming and going. The 5 that persisted every time were
  never close to the threshold (2.6-5.1pp). Still NOT PRACTICALLY TRADEABLE
  per the capital-lock-up finding
  above.
  **Output gap found and fixed (2026-08-23):** `main()` only printed the
  multi-leg execution-risk CAVEAT (near-simultaneous fills across every leg,
  capital locked until resolution) for `buy_no_basket` findings, never for
  `buy_yes_basket` ones — even though the same execution risk applies
  identically to buying YES across N legs. This asymmetry went unnoticed
  because every live finding through 2026-08-22 happened to be
  `buy_no_basket` (baskets running *over* 100%, the far more common case on
  Polymarket). The first live `buy_yes_basket` finding (2026-08-23, an Elon
  Musk tweet-count-range event, sum(YES)=97.6%) surfaced it: the caveat was
  silently missing from that finding's printed output. Fixed to print
  regardless of direction, naming the correct side (YES vs NO).
- **Real copy-trading analysis** (`polymanager/wallet_research.py`) — bridges
  `polymanager/copytrading.py`'s scoring logic (previously only unit-tested
  against synthetic data) to Polymarket's actual public API. **Correction
  worth flagging on its own:** an earlier version of this repo and its
  `polymanager/api.py` docstring claimed no public leaderboard endpoint
  exists — that was wrong, caused by guessing plausible-looking unversioned
  paths (`/leaderboard`) instead of checking `docs.polymarket.com`. The real
  path is `/v1/leaderboard`, found via the official OpenAPI spec and now
  wired up correctly. Also found: `/closed-positions` returns Polymarket's
  own already-computed per-market `realizedPnl` — no manual P/L
  reconstruction from raw trades needed. **Real findings (2026-08-20)**,
  pulling closed-position history for the top 10 all-time-PNL traders:
  confirmed authentic data (Theo4's top positions are exactly the famous
  2024 Trump-popular-vote / Kamala-NO bets reported in the press). Built
  real, verifiable stats — win rate, capital-weighted ROI, concentration
  (largest win as % of realized gains), and a "trade-order drawdown."
  That last one exposed its own bug in testing: normalizing by a running
  cumulative-P/L peak can report >1000% "drawdown" when the peak itself was
  small (confirmed live: swisstony showed 1646%, which is mathematically
  correct but means little as a percentage) — fixed by reporting the dollar
  drawdown alongside the percentage rather than hiding or clamping it.
  Explicitly NOT computed, and documented as such rather than guessed: true
  mark-to-market drawdown, "how early they enter," and any signal from
  currently-open (not yet resolved) positions — see the module docstring's
  full list. Run `python -m polymanager.wallet_research` to reproduce.
  **Bigger correction (2026-08-21, researching a real user-watchlisted
  wallet):** `/closed-positions` alone is survivorship-biased. A resolved
  loss never needs to be "redeemed" (there's nothing to claim), so it can
  sit indefinitely in `/positions` looking "open" (`curPrice=0`,
  `endDate` already past) and never appear in `/closed-positions` — only
  wins reliably show up there, since redeeming is how you collect the
  payout. Confirmed on a real wallet: `/closed-positions` alone showed a
  94.7% win rate; once the 10 genuinely-resolved-but-unredeemed losses
  sitting in `/positions` were folded in, the real figure was 62.1%, with
  a real $106,992 (62.3%) trade-order drawdown that the closed-positions-
  only view completely hid. `fetch_wallet_stats()` now scans `/positions`
  too and treats anything with `curPrice <= 0.001` as a settled loss,
  using its `cashPnl`. This retroactively affects every wallet this module
  has ever scored, including the original top-10-leaderboard numbers
  above — treat pre-fix win rates as an upper bound, not fact.
- **User-sourced trader watchlist** (`polymanager/watchlist.py`,
  `data/trader_watchlist.csv`) — the leaderboard-based scan above only
  finds top-50-by-PNL whales; it can't see a smaller, specialized trader
  someone spots on Twitter or in an article. `add_entry()` logs an address
  (upserted, so a second mention of the same wallet adds context rather
  than duplicating a row) with its source and claim; `research_watchlist()`
  runs every logged wallet through the *identical* real-data pipeline as
  `wallet_research.py` (same `fetch_wallet_stats`, same quality scoring) —
  a claim that someone is a good trader is a lead, never itself evidence,
  and a wallet with no closed-position history is reported as an
  unverified claim, not quietly dropped. Run `python -m polymanager.watchlist`
  once entries exist. Starts empty — no addresses fabricated to seed it.
  **Real finding (2026-08-21), running the 5 wallets logged so far**: the
  quality-score ranking alone is not a copy recommendation, and running it
  against real data proved why. BTC1UPDOWN — the *only* one of the 5 with
  negative real capital-weighted ROI (-2.19%) — scored **highest** (60.3),
  ahead of all four wallets with genuine positive edge. Cause: `roi_component`
  in `trader_quality_score()` tops out at 20 of 100 points (and a modest
  +7.46% ROI earns under 1.5 of those), while sample size, win rate, and low
  concentration are scored independently of whether the trader is actually
  profitable — so a large-sample, low-concentration net *loser* still racks
  up 60+ points on style alone. Added `meets_copy_target_bar()` to
  `copytrading.py` — a hard pass/fail gate (positive ROI, ≥30 sampled
  positions, ≥55% win rate, ≤50% trade-order drawdown) reported alongside,
  never instead of, the score — and wired it into `research_watchlist()`'s
  output. Real result against the current 5: **zero pass**. Four fail purely
  on drawdown (58.2%–114.7%, all well past 50%), one (BTC1UPDOWN) fails on
  negative ROI. So the honest answer to "is any of these 5 a good copy
  target" is no — not because they're bad traders (four of five have real,
  positive lifetime PNL on the leaderboard) but because copying any of them
  1:1 today would mean living through a real 58%+ peak-to-trough swing along
  the way. See `tests/test_copytrading.py` (new file — this module had zero
  test coverage before this audit) for the regression test reproducing the
  exact BTC1UPDOWN-outranks-a-real-winner paradox.
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
- **Journal reconciliation** (`polymanager/reconcile.py`) — the mandate's
  journal spec calls for filling in exit price, P/L, and "was the thesis
  correct?" once a recommendation's market resolves; that update-after-the-
  fact step didn't exist until this was built. Checks every journaled
  recommendation with a captured `market_id` against Gamma's per-market
  endpoint (`GET /markets/{id}` — confirmed live 2026-08-20 that the
  `?id=` query-param form silently returns an empty list; use the path
  form), and for any that have genuinely settled (price at/near 0 or 1,
  not just `closed`), fills in the outcome. **Real validation the same
  day**: one BTC "reach $X" market included in this repo's own live runs
  resolved (YES, touched $72,500) within hours — confirming short-duration
  recommendations really can resolve inside a single day's check-in
  cadence, not just in theory. Every reconciled row is stamped
  `HYPOTHETICAL` in `lesson_learned` and nothing here touches
  `polymanager.portfolio`'s cash or realized P/L — no wallet is configured,
  so this computes what a recommendation *would have* returned, strictly
  for calibration, never as a record of real capital. `python -m
  polymanager.scan_all` runs this first, before generating new
  recommendations; run `python -m polymanager.reconcile` standalone too.
- **Performance analysis** (`polymanager/performance.py`) — the mandate's
  PERFORMANCE ANALYSIS section (win rate, average win/loss, profit factor,
  strategy-specific breakdown) had nowhere to be computed from:
  `polymanager/dashboard.py` only ever renders one cycle's snapshot, never
  the accumulated history. This aggregates every *reconciled* journal row
  (see above) into those metrics, split out per strategy. Same
  hypothetical caveat as reconciliation — it answers "would following this
  system's recommendations have made money," not "did it." Was empty for
  the first day (`python -m polymanager.scan_all` confirmed: 0 reconciled,
  28 pending). **First real data (2026-08-21):** 4 recommendations
  reconciled — all Tier 3 `btc_touch` "reach $X" markets from the same
  underlying BTC move (2 wins, 2 losses, 50% win rate, profit factor 1.46,
  net hypothetical P/L +$1.40). n=4 is nowhere near enough to say anything
  about the model's real calibration (see the backtest section above for
  that, which used a full year of history) — this is the pipeline's first
  live out-of-sample data point, not a verdict.
  **A 5th reconciled outcome, same day, shows a real, coherent pattern
  worth flagging even at this tiny sample:** all 5 resolved markets are
  "reach $X" bets on the same "August 17-23" window at $74k/$75k/$76k —
  and BTC visibly trended up through all three levels (spot is $76,428 as
  of this scan). Both wins were `YES` bets on touching $74k (correct — it
  got touched). All 3 losses were `NO` bets against touching $74k/$75k/$76k
  (wrong — each got touched anyway as price climbed). Win rate is now 40%
  (2/5), profit factor 1.04, net still barely positive (+$0.18), and
  hypothetical max drawdown widened to 93.5% ($2.60). This is exactly the
  directional risk the backtest section above already flagged
  theoretically (zero-drift model *understates* upside-touch probability
  in a sustained uptrend) — here it's a live, concrete instance of it,
  not a new finding, but real confirmation rather than just theory. Still
  n=5: not remotely enough to revisit `CONFIDENCE_CAP`, which already
  exists because of this exact risk. This fills in automatically as
  `reconcile.py` closes more rows out over time. Run `python -m
  polymanager.performance` standalone too.
  **Real bug found live (2026-08-21), when n jumped from 5 to 14 in one
  cycle:** win rate crashed to 14.3% and hypothetical P/L to -$24.64 —
  but inspecting the newly-resolved rows showed this wasn't 9 fresh
  independent trials. `polymanager/cli.py` journals every opportunity
  that clears the edge bar on *every* cycle, with nothing checking
  whether that same market/side is already an open, unresolved
  recommendation from an earlier cycle — because `state.positions` is
  never actually written (see the drawdown-throttle finding above), a
  still-open opportunity never moves out of "opportunity" and into
  "existing position," so it just keeps getting re-journaled every cycle
  it stays open. One real market ("Will Bitcoin reach $77,500 in August?"
  NO) got journaled **8 separate times** this way before it finally
  resolved, and all 8 rows reconciled as losses simultaneously — one
  wrong prediction weighted 8x as if it were 8 independent tests of the
  model. The 14 "reconciled recommendations" were really only **6
  distinct market/side bets** (1 win, 5 losses — a true 16.7% win rate,
  not the reported 14.3%, though close by coincidence here; the dollar
  P/L was overstated far more, since the repeated $77,500 loss alone was
  counted 8x). Fixed with `journal.has_open_unresolved_entry()`, checked
  in `cli.py` before journaling — confirmed live immediately after: the
  next cycle correctly skipped re-journaling every still-open opportunity
  and fell through to `NO TRADE` instead of manufacturing more
  duplicates. **This does not retroactively fix the 14 already-recorded
  rows** (the journal is intentionally append-only outside of
  `reconcile.py`'s resolution rewrite) — treat every performance number
  computed before this fix as overstating both sample size and loss
  severity, not as fact. Going forward, `n` in the per-strategy breakdown
  now means what it says.
  **Follow-up audit (2026-08-21): even the very first "n=4"/"n=5"
  checkpoints above already had one undetected duplicate baked in.**
  Grepping the journal's `(market_id, side)` pairs by actual resolution
  order shows the "first real data" batch that resolved together
  (2026-08-21T02:36) was `$74,000 NO` (loss), `$74,000 YES` (win),
  `$74,000 YES` (the *same* win, journaled and counted twice), and
  `$75,000 NO` (loss) — 3 distinct bets, not 4: 1 win + 2 losses (a true
  33% win rate), not the reported "2 wins, 2 losses, 50%." The n=5
  checkpoint added one genuinely new distinct bet (`$76,000 NO`, a real
  loss), making it 4 distinct bets, 1 win + 3 losses (25% true), not the
  reported 40%. So this bug wasn't a one-time spike introduced right
  before the n=14 batch — it was present from this system's very first
  reconciled outcome, just small enough (2x on one market) to not stand
  out until the $77,500 market's 8x repeat made it impossible to miss.
  Not worth rewriting the historical rows over (same append-only
  reasoning as above), but worth knowing the true distinct-bet picture
  was always more loss-weighted than what was reported live, at every
  checkpoint, not just the last one.
  **A second, subtler bug surfaced immediately while verifying the fix
  above:** re-running `scan_all` on a cycle where *every* opportunity was
  already an open recommendation correctly wrote zero duplicate BUY
  rows — but wrote nothing else either, not even a `NO TRADE` marker, so
  the journal had no record that cycle had run at all. A silent gap is
  better than a silent duplicate, but still not honest bookkeeping.
  Fixed by having `cli.py` record an explicit `NO TRADE`-style trace row
  ("N opportunities identified, all already open") whenever every
  opportunity is a duplicate — confirmed live immediately after: the next
  cycle correctly appended exactly one such row instead of leaving a gap.
  **Real bug found live (2026-08-21), in `performance.py` this time:**
  close-read `reconcile.py` (nothing in the mandate matters more than
  trusting what "resolved" means) and found it permanently skips any
  journal row with no `market_id` (`skipped_no_market_id`, rows recorded
  before that field was captured) — those rows can never be checked
  against a real market again. But `performance.py`'s "Still pending"
  count didn't know that: it counted every unreconciled recommendation
  row the same way, `market_id` or not. 11 real rows from this project's
  very first hour (2026-08-20T16:51-16:52, before `market_id` capture
  existed) were sitting in "Still pending," implying they were just
  waiting on a market to settle, when `reconcile.py` will never look at
  them again. Split `n_pending` (has a `market_id`, genuinely awaiting
  resolution) from a new `n_unreconcilable` (no `market_id`, permanently
  stuck) in `PerformanceReport`, surfaced as a distinct line in
  `render_report()` only when nonzero. Confirmed live: "Still pending"
  dropped from 71 to the true 60, with the 11 now honestly labeled
  separately instead of silently inflating a count that implied they'd
  eventually resolve.

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

# Run everything live in one go (main cycle + both cross-market scans),
# logging a summary row to data/scan_history.jsonl each time:
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

# Real copy-trading analysis of the top all-time-PNL leaderboard traders:
python -m polymanager.wallet_research

# Research every wallet logged in data/trader_watchlist.csv (user-sourced leads):
python -m polymanager.watchlist

# Check past recommendations against resolved markets and fill in outcomes:
python -m polymanager.reconcile

# Win rate / profit factor / strategy breakdown from reconciled journal rows:
python -m polymanager.performance

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

**Audited live 2026-08-20**: does the correlated-group cap actually bind, or
is it dead code given today's small Tier-3-only position sizes ($6 max
each, since `btc_touch.py`'s `CONFIDENCE_CAP=4` structurally limits it to
Tier 3)? A real cycle that day produced 4 simultaneous BTC opportunities
totaling 10.3% of the bankroll — under the cap, nothing rejected. Replaying
the real accept-in-ranked-order logic with 8 opportunities at that same
real $6 size confirmed the mechanism itself is not dead: it accepts the
first 6 (18%) and correctly rejects the 7th and 8th (would reach 21%) —
see `tests/test_risk.py::test_correlation_cap_binds_under_realistic_btc_opportunity_counts`.
Real and reachable; that day's specific market conditions just hadn't
produced enough simultaneous correlated opportunities to trigger it.

**A materially different finding from the same day's audit pass**: is the
drawdown throttle (`DRAWDOWN_RULES` above; 10%/20%/30% cuts) similarly
reachable-but-unexercised, or is it structurally dead? Confirmed the
latter by reading `polymanager/portfolio.py` and grepping `polymanager/cli.py`
for writes to `state.positions`/`state.cash`: there aren't any.
`cli.py` only ever *reads* `state.positions` (for correlation accounting)
and never appends a `Position` or spends `cash` — because no wallet is
configured, nothing ever actually executes. So `equity()` is permanently
`cash` ($200, untouched) plus zero open positions, exactly equal to
`high_water_mark` forever, and `drawdown()` is always precisely `0.0`. Not
"hasn't triggered yet" like the correlation cap — genuinely unreachable
given the current no-wallet architecture, and it will stay that way until
`polymanager/execution.py` is wired to a real wallet and actually spends
`state.cash`. Since the mandate's "Maximum Drawdown" metric can't be
satisfied by a value permanently pinned at 0%, `polymanager/performance.py`
now computes `hypothetical_max_drawdown_pct/usd` instead: a real
peak-to-trough curve over this system's own *reconciled recommendation
outcomes* (see `polymanager/pnl_stats.py`, the same math already built for
`wallet_research.py`'s real-trader drawdown, extracted so both share it).
It's not a substitute for real portfolio drawdown, but it's not nothing
either — and it's honestly labeled as hypothetical throughout.

**Third audit in the same series (2026-08-20)**: does `MAX_SINGLE_POSITION_PCT`
(12%, the "hard cap" row above) ever bind distinctly from the tier system, or
is it redundant given `tier_capped = min(f_fractional, tier_max_pct)` already
happens first? Under the *live config* it's redundant: every `TIERS[*].max_pct`
is ≤ 0.12 (Tier 1's own max_pct **is** 0.12) and every `DRAWDOWN_RULES`
multiplier is ≤ 1.0, so `tier_capped * drawdown_multiplier` can never exceed
12% in the first place — confirmed by running each tier's real max through
`recommended_position_size` with a deliberately enormous edge and showing
`hard_cap_pct=0.12` vs. effectively no cap produce identical output (see
`tests/test_kelly.py::test_hard_cap_is_redundant_under_current_live_config`).
Unlike the drawdown throttle, though, this one is *not* dead code — it's live
defense-in-depth that would immediately start binding the moment a tier's
`max_pct` is ever widened past 12% (e.g. loosening Tier 1), confirmed by
feeding the function a hypothetical `tier_max_pct=0.20` directly and watching
the hard cap clamp the result back to 12% (see
`test_hard_cap_does_bind_if_a_tier_max_ever_exceeds_it`). Leave it in place —
it's cheap insurance against a future config change, just not currently doing
any work.

## Legal / disclaimer

This is a decision-support and execution-scaffolding tool, not investment
advice. Prediction-market trading may not be legal or available in every
jurisdiction or for every account; confirm you're eligible under Polymarket's
terms and your local law before funding a wallet or placing real orders. No
trade is ever certain; capital preservation takes priority over upside in
every default in this codebase.
