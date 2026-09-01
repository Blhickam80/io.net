# Master watchlist

Imported 2026-09-01 from the user's existing wallet-tracker export (93 entries, all valid
Solana addresses, no duplicates). This is a better source than scraping fomo.app's leaderboard
directly -- several names are recognizable Solana trader/KOL handles (`ansem`, `real ansem`,
`Cented`, `cupsey` / `Cupsey` / `cupsey2`, `real toly`, `waddles`, `tjr`, `Ozark`, `keanu`,
`beanz`...), which means this list is at least partly curated rather than raw leaderboard
output. Two entries appearing twice under different casing/spelling (`ansem` /
`ansem,,` / `ansem agent` / `real ansem`, `cupsey` / `Cupsey` / `cupsey2`) are different
wallet addresses each -- worth treating as separate candidates since we don't know which, if
any, is the "real" one without checking.

**One caveat on the import itself:** the last entry in the pasted export (`igetrugged`,
`C6macjVoEMRtfpupFP4cQtCr49Uws5UFcxLVrGxAKMdr`) was cut off mid-object in the paste (ended at
`"groups": [` with no close). I closed it with an empty `groups` array and dropped the `sound`
field, which weren't needed for our purposes (we only use the address). If there were more
wallets after that one in the original export that got truncated, they're not captured here --
worth checking the original source if the count should be higher than 93.

We already know one of these (`3h65MmPZksoKKyEpEjnWU2Yk2iYT5oZDNitGy5cTaxoE`, named "jidn"
here) as "Early Bird" from earlier analysis -- confirmed NOT COPYABLE (sniper-bot pattern, see
`../profiles/early_bird.md`). It'll get skipped rather than re-analyzed.

## Files

- `tracked_wallets_raw.json` -- full original export, as received.
- `tracked_wallets.json` -- cleaned `{address, name}` pairs, deduplicated and validated.
- `tracked_wallets.txt` -- plain address list (one per line, `# name` comment) for
  `backtest_wallets.py --wallets-file`.

## Plan for processing 93 wallets

Running all 93 through the backtester on the public RPC in one shot isn't practical (roughly
93 x up to a few hundred RPC calls each -- could run well over an hour and hit rate limits
hard). Processing in batches instead:

1. Prioritize named/recognizable wallets (the ones with real handles, not "Rename wallet" /
   "DEFAULT" / "asdsad" placeholder names) first -- higher odds of being real, deliberately
   tracked traders rather than noise.
2. Batch remaining wallets ~10-15 at a time.
3. Already known: `3h65MmP...` (jidn / "Early Bird") -- skip, already disqualified.

Status: not yet started. Next message will kick off batch 1 of the priority group.
