# 24-hour paper trade verdict: 2Pvub and Ozark

Window: 2026-09-02 01:16 UTC -> 2026-09-03 01:16 UTC. Full trade-by-trade log:
[`../paper_trades_log.md`](../paper_trades_log.md).

## 2Pvub: zero data

Not a single transaction in 24 hours, despite a 30-day backtest showing ~2.5 trades/day
(18 trades in the last 7 days of that window). Completely unproven either way. Worth
questioning whether the backtest window caught a temporarily active stretch that has since
cooled off, rather than assuming this is normal variance. **Do not deploy real money on this
wallet without more live confirmation.**

## Ozark: bad realized results, masked by one huge unresolved bet

**Realized (closed trades): 10 closed, 3 wins (30%), -0.2484 SOL net.** Backtested win rate
was 66.7% -- a 30% live win rate on 10 trades is a real, statistically meaningful divergence,
not noise. By trade *count* this looks even worse than by trading *decision*: 6 of the 10
"losses" came from a single bad call (Gv9fjtT9, a 6-buy-then-single-dump loss recorded as 6
separate closed lots). Counting by decision rather than by lot: roughly 4 independent calls in
24h -- 2 profitable (659xrvMd +11.6%, 6zSqTexg +27.8%/+8.3%), 1 clearly bad (Gv9fjtT9, -49%
average across its lots), 1 still partially open (4oFcrU1i).

**Two positions never closed in the window:**
- **Marketplier (DUZN7M6e...)** -- the 40.28 SOL, 13-buy accumulation into a thin-liquidity,
  bot-swarmed token flagged as reckless when it happened. As of window close: **unrealized
  +2.9377 SOL (+226%)** on the 1.3 SOL paper position. Ozark's real stake would be worth
  roughly 131 SOL if sold at the current price. **Not realized. Not sold. Could still reverse
  hard** -- this token was up +6340% in 24h when bought and is thin enough that Ozark's own
  exit would move the price against them.
- **4oFcrU1i (UNCHILL) remainder** -- the ~52% left over from the very first trade of the
  session. Small unrealized loss (-0.0055 SOL, -10.7%). Token has gone completely dead (zero
  buys/sells in the last 6 hours) -- looks like a stuck bag, not a position anyone is likely to
  exit favorably.

**Mark-to-market total (realized + unrealized): roughly +2.68 SOL.** Driven almost entirely by
one open, unresolved, extremely volatile bet. This is the profit-concentration trap this whole
session has been warning about, now visible inside the test itself: if that one position had
gone to zero instead of up 226%, the honest read would be "Ozark lost badly in live paper
trading, confirming the backtest doesn't hold up." Nothing about *how* that trade was made
changes based on its outcome -- aping 40 SOL into a bot-swarmed pump was exactly as reckless
whether it happened to work out or not.

## Verdict

**Neither wallet is confirmed ready for real money right now.**

- 2Pvub: no data, needs more live observation.
- Ozark: realized performance is bad and doesn't match the backtest. The positive
  mark-to-market total is not a green light -- it's one outstanding coin-flip-scale bet away
  from looking like exactly what the realized numbers already show: a wallet whose edge isn't
  holding up out-of-sample.

If Ozark's Marketplier position gets sold, that resolves the ambiguity one way or the other and
is worth watching for specifically. Until then, the responsible read is the realized number
(-0.2484 SOL, 30% win rate), not the mark-to-market one.
