# Copy-Trading Strategy: fomo.app Wallets -> mofocopytradingbot

Goal: pick 1-3 fomo.app leaderboard wallets worth copying, and run them through
`mofocopytradingbot` on a small (<$500) account without blowing it up on trade one.

Read the caveats at the bottom before doing anything with real funds.

## 0. What I could and couldn't verify directly

- fomo.app's leaderboard is inside their app, not an indexable webpage, so I can't pull it
  programmatically. You need to pull 5-15 candidate wallet addresses from the app yourself
  (Top Traders / leaderboard screen -> tap a trader -> copy their wallet address).
- `mofocopytradingbot`'s exact settings menu isn't public/documented anywhere I could reach.
  The settings below are the standard set every Solana copy-trading Telegram bot in this
  category (Trojan, BullX, Photon, GMGN, Maestro) exposes in some form — verify the exact
  option names in the bot's own `/start` or settings menu and map them to the principles here.
- `backtest_wallets.py` in this folder pulls **real on-chain data** from Solana RPC and
  computes real closed-trade stats — this part is not hypothetical.

## 1. Shortlisting candidates on fomo.app

Pull candidates that pass ALL of these before you even backtest them:

- **Both 7-day and 30-day leaderboard, not just all-time.** All-time can be one lucky 50x
  that never repeats. You want someone showing up consistently on the short window too.
- **Visible trade count, not just PnL.** A wallet with 3 trades and +400% is a coin flip
  that hit. You want 20+ trades in the window you're judging.
- **Position sizing looks intentional, not degenerate.** If their trade sizes vary 50x
  trade-to-trade relative to their own balance, they're gambling, not trading a repeatable
  edge — bad to copy with a fixed small bankroll.
- **They trade tokens with real liquidity**, not exclusively 5-minute-old pump.fun bonding
  curve tokens with <$20k liquidity. On those, by the time your copy-trade lands a few
  hundred ms to a few seconds after theirs, the price has moved and/or you can't exit —
  their entry price is not available to you as a copier.

Take your shortlist (ideally 5-10 wallets) into the backtester.

## 2. Backtesting candidates (`backtest_wallets.py`)

```bash
python3 backtest_wallets.py --wallets <addr1>,<addr2>,<addr3> --lookback-days 30 --max-tx 200
# or
python3 backtest_wallets.py --wallets-file wallets.txt --json results.json
```

What it does: pulls each wallet's recent transaction history, reconstructs SOL<->token swaps
from balance deltas (chain-agnostic — works whether they routed through Raydium, Pump.fun,
Jupiter, Meteora, etc.), matches buys to sells FIFO per token, and scores each wallet.

What the score rewards: win rate above 50%, enough closed trades to trust that win rate,
recent activity (last trade within a few days), and *median* trade return rather than mean
(so one outlier moon shot doesn't disguise a mediocre wallet). It penalizes:

- **Profit concentration** — if one trade is >60% of total profit, the wallet's "edge" is
  one lucky pump, not a repeatable process. This is the single most important red flag for
  copy-trading: you will very likely miss that exact trade and just eat their losing ones.
- **Inactivity** — >14 days since last closed trade means stale/abandoned.
- **Extreme frequency** — 40+ trades/week will eat a small account alive in fees and
  slippage even if the leader is profitable, because your fills will be worse than theirs.

Important limitation: the PnL numbers are what the leader realized, net of *their* fees —
not what you'd realize copying a few seconds behind them with your own slippage. Treat the
script's numbers as an upper bound and a relative ranking tool, not your expected return.

Use the public RPC endpoint only for a quick look. For anything you're about to commit real
money to, get a free Helius/QuickNode/Triton API key and pass it via `--rpc` — the public
endpoint rate-limits hard and can silently give you a truncated trade history.

## 3. Wallet selection rule

Pick **2-3 wallets, not one.** A single wallet going cold (or getting front-run, or having
their strategy stop working — common with meme-coin traders) takes your whole account with
it. Prefer wallets with different trading cadence (e.g. one fast/high-frequency, one
slower/swing) so their bad weeks don't correlate.

Re-run the backtest weekly. Meme-coin trader edges decay fast — most of it is being early or
plugged into a specific community/callers, and that rotates. A wallet you picked a month ago
can be worth dropping today even if nothing about your process was wrong.

## 4. mofocopytradingbot settings for a small, high-risk-tolerance account

Principles to map onto whatever the bot's actual menu calls them:

| Setting | Recommendation | Why |
|---|---|---|
| Buy sizing mode | **Fixed SOL amount per trade**, not "% of leader's size" or "mirror their size" | The leader may be sizing in the thousands of dollars. Mirroring their size on a <$500 account means one trade can be your whole bankroll. |
| Per-trade size | **3-5% of total bankroll** (e.g. ~$15-25 on a $400-500 account) | Lets you survive 10+ losing trades in a row without being wiped, which will happen with meme coins even on a good wallet. |
| Copy sells | **On, always** | If you only copy buys, you have no exit plan beyond your own reaction time. Copying the leader's sell is your primary exit signal. |
| Slippage tolerance | **10-20%**, higher only for known-illiquid micro-caps | Meme coins move fast; too-tight slippage means missed fills (you never enter, so you also never "lose", but you also never realize the wallet's edge). Too loose bleeds you to MEV/sandwich bots. |
| Priority fee | **Mid-high**, especially during volatile/high-volume periods | Copy-trading is a latency race behind the leader. A cheap priority fee during a hot pump means you land several blocks late, at a much worse price than what the leader's PnL reflects. |
| Max concurrent open positions | **3-5** | Caps total exposure if several copied trades open at once; prevents one busy day from overcommitting the account. |
| Rug/honeypot filter | **On, if the bot offers it** | Blocks copying into tokens that are structurally unsellable, independent of whether the leader is "right" about the trade. |
| Min liquidity filter | **On, ~$20-30k+ if available** | Keeps you out of tokens where you as a late copier can't get a fill or can't exit. |
| Take-profit / stop-loss (bot-native, if offered) | Optional layer on top of copying sells — e.g. auto-sell at -40% regardless of what the leader does | Meme coins can go to zero faster than a leader reacts. A hard stop protects against the case where the wallet you're copying also gets caught. |

## 5. Account-level risk rules (enforce yourself; the bot won't)

- **Daily loss cap: -20 to -25% of account balance.** If hit, stop copying for the day and
  review — don't average down or "make it back."
- **Weekly review**: pull actual results for each copied wallet since you started, compare
  to what the backtest predicted. A wallet whose live win rate is dramatically worse than its
  backtested win rate is either fading or you're getting worse fills than they are — drop it.
- **No leverage, ever**, on this account size and asset class. Spot only.
- **Never let one token be more than one "unit" of your fixed position size** — no adding to
  losers, no revenge-sizing after a loss.

## 6. Caveats / disclaimers

- This is not financial advice. Meme-coin copy-trading is high-variance; total loss of the
  copied balance is a realistic outcome even with a sound process — that's why sizing is
  built around surviving losing streaks, not around a specific expected return.
- `backtest_wallets.py` measures the leader's realized on-chain PnL, not your achievable
  return as a follower. Real slippage, latency, and fees will make your results worse than
  the wallet's own numbers.
- I do not have the ability to execute trades on `mofocopytradingbot` — no Telegram
  integration is available to me in this environment. You configure and run the bot; I can
  help you interpret backtests, refine settings, and review results as you go.
