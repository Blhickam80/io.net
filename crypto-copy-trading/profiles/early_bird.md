# Wallet profile: "Early Bird"

- **Address:** `3h65MmPZksoKKyEpEjnWU2Yk2iYT5oZDNitGy5cTaxoE`
- **Chain:** Solana
- **Re-analyzed:** 2026-09-01, 30-day lookback, 19 closed trades, corrected script (public RPC)
- **Verdict: NOT RECOMMENDED -- mediocre/marginal, not clearly profitable.**

## ⚠️ Correction (2026-09-01)

The original 2026-08-27 analysis below is **wrong** and is kept only for the record. It was
produced by a version of `backtest_wallets.py` with a chronological-ordering bug: transaction
signatures were processed newest-first instead of oldest-first, which could match a sell
against a buy that happened *after* it in real time, producing impossible negative hold times
that got silently clamped to 0. That bug made this wallet (and every other wallet analyzed
before 2026-09-01) look like a same-block "sniper bot" with a suspiciously perfect track
record. It wasn't real. See the commit fixing this in `backtest_wallets.py` for the technical
detail, verified by manually cross-referencing raw transaction timestamps against script output.

## Corrected stats (post-fix)

| Metric | Value |
|---|---|
| Closed trades (30d) | 19 |
| Win rate | 47.4% |
| Median trade return | -4.8% |
| Median hold time | 3.4 minutes |
| Last trade | same day as analysis |

Roughly a coin flip with a slightly negative median return. Not a sniper bot, not a standout
trader either -- just unremarkable. No reason to copy it.

## Original (incorrect) analysis, 2026-08-27 -- kept for record only

Claimed: 23 closed trades, 82.6-100% win rate, +104.6% median return, ~24.4 SOL total PnL,
~0 second median hold time, disqualified as an uncopyable sniper bot. **The win rate, returns,
and PnL figures were artifacts of the ordering bug, not real.** Full raw output from that run:
[`early_bird_results.json`](./early_bird_results.json) (also stale, kept for reference).

## Disposition

Not on the active copy list. Not because it's a sniper bot (it isn't) -- because a corrected
read shows it isn't actually profitable.
