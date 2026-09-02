# Corrected findings, 2026-09-01

## What happened

Every wallet analyzed in this session before 2026-09-01 was scored by a version of
`backtest_wallets.py` with a chronological-ordering bug (see the fix commit and
`early_bird.md` for detail). `getSignaturesForAddress` returns transactions newest-first;
the script processed them in that order without reversing, so FIFO buy/sell matching could
pair a sell with a buy that happened *after* it in real time. That produced impossible
negative hold times clamped to 0, and in wallets with overlapping positions, corrupted win
rates and trade counts too -- not just hold time. Every "sniper bot, NOT COPYABLE" verdict
from before this date was built on that broken measurement.

Fixed and verified (manually cross-checked raw transaction timestamps against script output
for two different wallets before trusting it again), then re-ran all 29 previously-analyzed
wallets. Full corrected output: [`full_reverify_results.json`](./full_reverify_results.json).

A second, smaller gap was also found and fixed while investigating why several heavily-active
named wallets showed zero detected trades: wallets that route swaps through a persistent
wrapped-SOL token account (instead of wrapping/unwrapping native SOL per trade) had their
SOL-side balance change invisible to the original detector. Fixed, but did not resolve most of
the zero-trade wallets -- see "Unresolved" below for why.

## Corrected results, ranked

| Wallet | Name | Trades | Win% | Median return | Profit conc. | Hold | Verdict |
|---|---|---|---|---|---|---|---|
| `2PvubwzjkSwBQ1YyjWedJVuCJ9FTSTEjFYYeyqrMHCGj` | (unnamed) | 35 | 80.0% | +79.3% | 9.2% | 4.2 min | **Best candidate found this session -- see below** |
| `DhY8Ab5cFbZ2VXfiexmCSFkfjqukinVUzFJ514yeAumV` | (unnamed) | 11 | 81.8% | astronomical (near-zero cost basis) | 19.2% | 4.3 hr | Real but likely sniping brand-new tokens at ~0 cost; inconsistent sizing (CV 3.16) |
| `12a3vefnfb47xW537swVN777b3woZmvacNjZqGmfM21` | (unnamed) | 37 | 86.5% | astronomical | 11.5% | 10.4 min | Same pattern as above, inconsistent sizing (CV 1.56) |
| `JCCHjYkL1hM546GHxqqPM1bc7ych8ErLrLDiCivfAexy` | (unnamed) | 6 | 100% | astronomical | 73% | 12.1 hr | Small sample + profit concentration -- one trade drove most of it |
| `DZAa55HwXgv5hStwaTEJGXZz1DhHejvpb7Yr762urXam` | Ozark | 15 | 66.7% | +8.1% | 29.1% | 82s | Decent secondary candidate -- realistic numbers, no red flags |
| `3h65MmPZksoKKyEpEjnWU2Yk2iYT5oZDNitGy5cTaxoE` | Early Bird / jidn | 19 | 47.4% | -4.8% | -- | 3.4 min | Mediocre, not a sniper bot after all -- just not profitable |
| `F3aJ28RrFAceShmtG1wJPmwgPZqQhVabzonsSao7qjEo` | keanu | 65 | 52.3% | +2.0% | -- | 17s | Thin edge, very high frequency -- fees/slippage would eat it on a small account |
| `7Dgv6HDjQ8kdgsDRtmgpVwiyfTGjzDaSkWVAZZJ2wiiW` | (unnamed) | 27 | 14.8% | -58.2% | -- | 23.9 hr | Genuinely bad trader |
| `GZVSEAajExLJEvACHHQcujBw7nJq98GWUEZtood9LM9b` | washy | 54 | 31.5% | -15.8% | -- | 35s | Genuinely bad trader, high frequency |
| `DAtJJbckkqADvpt7bhCqNHMpitYBVHfFP3ZsisNvbBTC` | (unnamed) | 21 | 0% | -41.1% | -- | 61s | Bad |
| `Bf4zji6S979QySiGNjPJ2VMZ5i2SRVtAzfx8QUBScJm6` | solcrow | 3 | 0% | -1.2% | -- | 25.1 hr | Bad, tiny sample |
| `G6fUXjMKPJzCY1rveAE6Qm7wy5U3vZgKDJmN1VPAdiZC` | cluckz | 17 | 5.9% | -5.2% | 100% | 6s | Bad |
| `BbdWnFY3jyBvvX5HBSjN6p9CQEn6VZNnzStRykcL6GwM` | on a tear | 2 | 0% | -9.1% | -- | 42.3 min | Bad, tiny sample |
| `AVAZvHLR2PcWpDf8BXY4rVxNHYRBytycHkcB5z5QNXYm` | ansem | 10 | 10% | -53.2% | 100% | 3.5 hr | Bad -- one lucky trade covering losses elsewhere |

## Best candidate: `2PvubwzjkSwBQ1YyjWedJVuCJ9FTSTEjFYYeyqrMHCGj`

The strongest, cleanest read of the whole session. 35 closed trades over 30 days, 80% win
rate, +79.3% median return, **9.2% profit concentration** (meaning the gains are spread across
many trades, not one lucky pump -- this is the opposite of the profit-concentration trap seen
elsewhere), 4.17 SOL average position size (real money, not dust), moderate position-sizing
consistency (CV 0.55), 18 trades in the last 7 days, last trade under a day ago, no warnings
from the scorer.

Independently spot-checked against raw transactions (not just the script's output): traced a
losing trade (-1.14 SOL on a 256-second hold), a near-breakeven trade (+0.002 SOL, 178s), and
a multi-lot position that correctly FIFO-splits across three partial sells with consistent
quantities. The numbers hold up.

**Caveat:** median hold time is ~4 minutes. That's dramatically more copyable than the fake
0-second numbers from before the bug fix, but it's still fast -- a Telegram copy bot's
execution lag (parsing the leader's transaction, submitting your own, RPC confirmation) will
cost some of this edge on the fastest trades, especially the ones under a minute. This wallet
is a genuine find, not a guaranteed result once you're copying with real latency behind it.

## Secondary candidate: `DZAa55HwXgv5hStwaTEJGXZz1DhHejvpb7Yr762urXam` (Ozark)

More modest, realistic numbers rather than astronomical percentages -- which is itself a good
sign (astronomical median returns on the other wallets above indicate buying tokens at
effectively zero cost basis in the first moments of trading, which is a different, harder
pattern to copy). 66.7% win rate over 15 trades, +8.1% median return, no warnings. Hold time
82 seconds is fast but the return profile doesn't depend on it the way the astronomical-return
wallets do. Worth considering as the second wallet in a 2-3 wallet copy set per the strategy
doc, since its profile (fast, modest, consistent) differs from `2Pvub...`'s (few-minute hold,
larger swings).

## Unresolved: ~15 wallets show heavy activity but zero detected trades

Includes: `AcVua...`, `uNksq...`, `real ansem`, `ansem agent`, `ansem,,`, `cupsey`, `Cupsey`,
`cupsey2`, `Cented`, `real toly`, `waddles`, `beanz`, `rems`. Investigated one (`real toly`) in
detail: its transactions invoke Pump.fun's AMM and the SPL Token program, but the wallet's own
native SOL balance and token balances never change in the transaction record -- meaning this
address isn't acting as the economic counterparty in these swaps the way a normal trading
wallet would. It may be a passive/authority account referenced in the instruction rather than
the actual trader, or use a custody structure (a program-derived vault) this balance-delta
heuristic structurally can't unwind.

This is a real limit of RPC-only analysis without labeled transaction data. Solscan's or
Birdeye's own "DeFi Activities" views decode swap instructions directly rather than inferring
them from balance deltas, and would very likely resolve these in a couple of minutes each --
not worth more engineering time chasing here. If any of these wallets matter enough to resolve
(particularly the recognizable KOL-name ones), check them there directly.

## Bottom line

One strong candidate (`2Pvub...`), one decent secondary (`Ozark`), everything else in this
watchlist either mediocre, bad, or currently unreadable by this method.
