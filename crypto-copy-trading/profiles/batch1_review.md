# Candidate batch 1 -- review

8 wallets submitted 2026-08-31. 30-day lookback, up to 150 tx each, public RPC.
Raw output: [`batch1_results.json`](./batch1_results.json).

**Verdict: none of these 8 are recommended for `mofocopytradingbot` right now.**

## Summary

| Wallet | Closed trades | Win% | Median return | Median hold | Verdict |
|---|---|---|---|---|---|
| `JCCHjYkL1hM546GHxqqPM1bc7ych8ErLrLDiCivfAexy` | 6 | 100% | +1,076,560% | 0s | **Sniper bot** |
| `DhY8Ab5cFbZ2VXfiexmCSFkfjqukinVUzFJ514yeAumV` | 13 | 100% | +14,495,599% | 0s | **Sniper bot** |
| `7Dgv6HDjQ8kdgsDRtmgpVwiyfTGjzDaSkWVAZZJ2wiiW` | 7 | 0% | -45% | 0s | **Losing sniper bot** |
| `DAtJJbckkqADvpt7bhCqNHMpitYBVHfFP3ZsisNvbBTC` | 1 | 100% | +26% | 0s | **Sniper bot** + too small a sample to mean anything anyway |
| `12a3vefnfb47xW537swVN777b3woZmvacNjZqGmfM21` | 1 | 100% | +29% | 0s | **Sniper bot** + 1 trade, no signal |
| `2PvubwzjkSwBQ1YyjWedJVuCJ9FTSTEjFYYeyqrMHCGj` | 0 | -- | -- | -- | Active, funded (~165 SOL), no closed SOL-paired trades found -- **inconclusive** |
| `AcVua6Uss59mneonhV5TfBhoyW8kyz7mnTDhtocgez3t` | 0 | -- | -- | -- | Active, funded (~0.25 SOL), no closed SOL-paired trades found -- **inconclusive** |
| `uNksqSWy79L7vPizsU8r56wPmiJwLCtenL5yUk6LM7z` | 0 | -- | -- | -- | Active, funded (~0.006 SOL), no closed SOL-paired trades found -- **inconclusive** |

## What's going on with the 5 "sniper bot" wallets

Same fingerprint as "Early Bird": every buy and sell lands in the same or immediately
adjacent block (median hold time 0 seconds). The returns on the winners are enormous
(one median trade at +14,495,599%) because these are entries at effectively zero cost basis
-- buying at the very instant a token becomes tradeable, before real price discovery -- not
"good calls" in a sense a slower follower can share in. `mofocopytradingbot` cannot execute
in the same block as the leader; copying these wallets means buying after they've already
exited, into whatever's left.

The one *losing* sniper (`7Dgv6...wiiW`, 0% win rate) is worth noting on its own: it proves
the pattern isn't inherently profitable just because it's fast -- this look-alike is what a
less-successful or front-run sniper looks like. Fast execution alone isn't the edge; being
first with good enough odds is, and that's exactly the part a copier can't replicate.

If fomo.app's leaderboard is sorted by raw PnL or "biggest win," expect it to be dominated by
wallets like these -- sniper/insider bots naturally put up the biggest numbers, which is
exactly why they're not automatically the best to copy.

## What's going on with the 3 "inconclusive" wallets

These are real, funded, recently active wallets -- not typos or dead addresses. My backtester
found no *closed* SOL<->token round trips in the 30-day window, which can mean any of:

1. They're currently sitting on open (unsold) positions -- common for someone who bought
   recently and hasn't exited yet. My script only counts realized, closed trades.
2. They trade token-for-token (no SOL leg), which the current script doesn't track.
3. Real closed trades exist further back than the 150-tx / 30-day window pulled here.

Worth re-checking with a longer lookback (`--lookback-days 60 --max-tx 400`) and/or a paid
RPC endpoint before ruling them out -- unlike the sniper-bot wallets, there's no
disqualifying evidence here, just insufficient data yet.

## Update: recheck of the 3 inconclusive wallets (90-day lookback, up to 400 tx)

Raw output: [`inconclusive_recheck.json`](./inconclusive_recheck.json).

| Wallet | Sigs fetched | Closed trades | Outcome |
|---|---|---|---|
| `2PvubwzjkSwBQ1YyjWedJVuCJ9FTSTEjFYYeyqrMHCGj` | 71 (well under cap) | 0 | Low overall activity for a ~165 SOL wallet -- doesn't look like an active memecoin trader by this method. **Drop.** |
| `AcVua6Uss59mneonhV5TfBhoyW8kyz7mnTDhtocgez3t` | 400 (hit cap) | 0 | Heavy on-chain activity but none of it matches a SOL<->token swap shape. Either not a token trader, or trades in a pattern this script's balance-delta heuristic doesn't catch (e.g. no native-SOL leg). **Unresolved** -- would need a labeled data source (Solscan/Birdeye trade history) to confirm either way, not worth more guessing from raw RPC. |
| `uNksqSWy79L7vPizsU8r56wPmiJwLCtenL5yUk6LM7z` | 400 (hit cap) | 2 | Now has a real signal: 0% win rate, -27.8% median return, and the same 0-second hold time as the sniper-bot wallets. **Losing sniper bot -- disqualified.** |

## Bottom line: 9 wallets analyzed, 0 recommended

7 are disqualified outright (sniper-bot pattern, several losing). 1 (`2Pvub...`) doesn't look
like an active trader at all. 1 (`AcVua...`) is a genuine unknown that this backtester can't
resolve with public RPC data alone.

## Next step

Stop pulling from "biggest gainers" style leaderboard views -- that's exactly where sniper
bots cluster and is why 7 of 9 candidates so far were bots. Look for a 30-day win-rate or
consistency sort on fomo.app instead, or a "most followed/copied" list if the app has one.
Send whatever comes out of that and it'll go through the same process.
