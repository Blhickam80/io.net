# Wallet profile: "Early Bird"

- **Address:** `3h65MmPZksoKKyEpEjnWU2Yk2iYT5oZDNitGy5cTaxoE`
- **Chain:** Solana
- **Analyzed:** 2026-08-27, 30-day lookback, 23 closed trades (public RPC)
- **Verdict: NOT COPYABLE via mofocopytradingbot, despite strong-looking stats.**

## Raw stats

| Metric | Value |
|---|---|
| Closed trades (30d) | 23 |
| Win rate | 82.6-100% (varied slightly run to run as new trades landed) |
| Median trade return | +104.6% |
| Total realized PnL | ~24.4 SOL |
| Profit concentration | 12% (not one lucky trade -- consistent) |
| Avg buy size | ~1.09 SOL |
| Position sizing consistency | moderate (CV ~0.99) |
| Last trade | same day as analysis |
| **Median hold time** | **~0 seconds** |

Full raw output: [`early_bird_results.json`](./early_bird_results.json).

## Why this disqualifies the wallet

Every single round trip -- buy and matching sell -- lands in the same block or the
immediately adjacent one. That's not "fast trading," it's a structural pattern: a sniper bot,
an atomically bundled buy+sell (e.g. a Jito bundle), or execution with privileged/private
mempool access. The win rate and returns are real, but they depend on getting into a token at
the same instant it's tradeable and out again a fraction of a second later.

`mofocopytradingbot` (like any Telegram-mediated copy bot) has to: receive/parse the leader's
transaction, then submit your own, at minimum one block later plus message and RPC round-trip
time -- realistically low single-digit seconds behind, often more. Copying this wallet doesn't
get you their entry. It gets you the price *after* they've already sold into it, i.e. you
become their exit liquidity. This wallet's edge is unrelated to "picking good trades" in a way
a slower follower can share in -- it's a latency/access edge that doesn't transfer.

## Disposition

Keep on file as a reference example of the "looks perfect, is actually uncopyable" pattern
(see `median_hold_seconds` check added to `backtest_wallets.py`), but do not add to the active
copy list for `mofocopytradingbot`.
