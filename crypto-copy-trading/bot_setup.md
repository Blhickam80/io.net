# mofocopytradingbot setup: 2026-09-02

Concrete settings for the two verified candidates from this session. Numbers assume a ~$400
account (mid-point of the <$500 range) at SOL = $99.69 (2026-09-02) -- scale the SOL amounts
proportionally if your actual balance differs, keep the percentages the same.

## Recommended rollout: start with one wallet, not two

This session corrected itself twice already (a chronological-ordering bug that inflated then
deflated multiple wallets' apparent quality). That's exactly the kind of error real-money
copying should have a chance to catch before it's compounded across two wallets at once.
**Start with `2Pvub...` alone for the first ~10 copied trades or one week, whichever comes
first.** Add `Ozark` only after confirming `2Pvub...`'s live results are roughly in line with
the backtest (positive median return, no unexplained string of losses).

## Wallet 1 (start here): `2PvubwzjkSwBQ1YyjWedJVuCJ9FTSTEjFYYeyqrMHCGj`

Backtest: 35 trades/30d, 80% win rate, +79.3% median return, 9.2% profit concentration
(spread across many trades, not one lucky pump), ~4.2 min median hold, 18 trades in the last
7 days (~2.5/day).

| Setting | Value | Why |
|---|---|---|
| Copy amount | **Fixed 0.15 SOL (~$15) per trade** | ~3.7% of a $400 account -- inside the 3-5% band from STRATEGY.md. Not proportional to the leader's ~4.17 SOL average size, which would be 100%+ of a small account on one trade. |
| Copy sells | **On** | Your primary exit signal. |
| Slippage | **15%** | Matches STRATEGY.md's mid-range; hold times here (minutes, not seconds) give some room, but memecoins still move fast. |
| Priority fee | **Medium-high** | ~2.5 trades/day isn't extreme frequency, so this doesn't need to be maxed, but the ~4min median hold means late entries eat directly into the edge. |
| Max concurrent positions | **3** | Caps exposure if multiple signals fire close together. |
| Rug/honeypot filter | **On** | If the bot offers it. |
| Min liquidity filter | **On, ~$20-30k+** | If the bot offers it. |

## Wallet 2 (add later): `DZAa55HwXgv5hStwaTEJGXZz1DhHejvpb7Yr762urXam` (Ozark)

Backtest: 15 trades/30d, 66.7% win rate, +8.1% median return, no warnings, ~82s median hold,
~15 trades in the last 7 days (~2.1/day).

| Setting | Value | Why |
|---|---|---|
| Copy amount | **Fixed 0.10 SOL (~$10) per trade** | ~2.5% of a $400 account. Smaller than Wallet 1's allocation since its edge (+8.1% median) is thinner and its 82s hold gives less room for bot latency. |
| Copy sells | **On** | |
| Slippage | **15-20%** | Faster hold time (82s vs 4min) means slightly more tolerance needed to actually get filled before the move is over. |
| Priority fee | **Medium-high** | |
| Rug/honeypot + liquidity filters | **On** | Same as Wallet 1. |

## Combined account-level rules (once both are live)

- **Max 4 total concurrent positions** across both wallets (3 + adjust down, not 3+3=6 --
  don't let two wallets firing at once double your intended exposure).
- **Daily loss cap: -20% of account (~$80 on $400).** Hit it → stop copying for the day,
  don't average down.
- **Weekly re-check:** re-run `backtest_wallets.py` against both wallets. If live results
  diverge badly from the backtest (win rate meaningfully worse, or a wallet goes quiet),
  drop it -- per STRATEGY.md, meme-coin trader edges decay fast.
- No leverage. Spot only. This was already the plan, restating it because it's the rule most
  worth not breaking on a "sure thing" trade.

## What I can't verify from here

I don't have access to `mofocopytradingbot`'s actual settings menu, so the option names above
(copy amount, slippage, priority fee, filters) are the standard set this category of bot
exposes -- map them onto whatever the real menu calls them. If a setting listed here doesn't
exist in the bot, the closest equivalent is fine; the fixed-dollar-sizing and daily-loss-cap
rules matter more than hitting these exact knobs.
