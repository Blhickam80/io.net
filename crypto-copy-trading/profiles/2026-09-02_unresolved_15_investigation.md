# Investigation: the 15 "zero detected trades" wallets

Follow-up to `2026-09-01_corrected_findings.md`. These 15 wallets showed heavy on-chain
activity but zero trades detected by `backtest_wallets.py` even after fixing wrapped-SOL
detection. Rather than keep guessing at the balance-delta level, checked each against
pump.fun's own API (`frontend-api-v3.pump.fun/users/<address>` for profile/identity,
`.../coins?creator=<address>` for tokens created) and manually inspected raw transactions for
the two most notable results.

**Bottom line: none of these 15 yield a new copy-trading candidate.** But several turned out
to be structurally different from trading wallets in ways worth knowing before trusting a
watchlist label again.

## Verified real identities (X-account linked on pump.fun), not showing tradeable activity

| Wallet | pump.fun handle | X link | Followers | On-chain balance | What's actually happening |
|---|---|---|---|---|---|
| `GV6UUmNxz2RpKxmNAPadYKb7uQpszwqQAu3qLJxVdC52` ("real ansem") | ansemconzimp | `blknoiz06` (Ansem's real handle) | 756,129 | 4.15 SOL | Recent txs are unsolicited token airdrops landing in the wallet -- 0 SOL paid, not even paying the transaction fee, meaning this wallet isn't even the signer. Airdrop-magnet noise from fame, not his trading. |
| `CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o` ("Cented") | cented69420 | `Cented7` (matches known handle) | 19,684 | **2,512.76 SOL** (~$350-500k) | Confirms genuine whale status. But every recent transaction shares the exact same block timestamp and touches zero balance/tokens, through unfamiliar programs (`BevFQ2LKT...`, `6EF8rrec...`, `naebaL84...`, `HiGFvqUf...`) -- likely MEV/bundle infrastructure. Not decodable from balance deltas; would need Jito-bundle-aware tooling. |

Both also have a `canonical_evm_wallet` registered (Base/BNB chain, which fomo.app supports) --
their actual spot trading may simply be happening on a different chain than the one this
backtester checks.

## Confirmed pump.fun token creators (fee recipients), not personal trading wallets

- `86xCnPeV69n6t3DnyGvkKobf9FdN2H9oiVDdaMpo2MMY` ("real toly") -- created "Official Toly Coin"
  (parody). Generic username `latefish54822`, no X link, 71 followers. **Not** Anatoly Yakovenko.
- `2fg5QD1eD7rzNNCsvnhmXFm5hqNgwTTG8p7kQ6f3rx6f` ("cupsey2") -- created a self-titled "Cupsey"
  coin, X-linked in the coin's own metadata to `@Cupseyy`. Username `cupseyyyyy`, 16,178
  followers. Circumstantially likely tied to the real Cupsey identity, even without a profile-
  level X link.
- `suqh5sHtr8HyJ7q8scBimULPkPpA557prMG47xCHQfK` ("Cupsey") -- created "CUPDRAINWALLET"
  (`DONTBUY`), a defensive coin explicitly warning people off scam imitators. 2,221 followers --
  suggests some real notability being targeted, though not X-verified.
- `CyaE1VxvBrahnPWkqm5VsdCvyS2QmNht2UFrKJHga54o` (Cented, above) also created a coin called "PNL".
- `5R4RJojpoKNwBcJNgVYGtwXdmhyEHWXGDBQqUnSpLfcW` ("andy") -- on-chain creator of the actual,
  famous **Fartcoin**. Oddly, the wallet's own bio explicitly disclaims creating any coins and
  warns that anything claiming affiliation is a scam -- contradicts the on-chain creator record.
  Not resolved which is right; noted, not pursued further.

Fee-recipient wallets explain the earlier mystery cleanly: DEX program involvement (payouts
from trades on their pool), zero token balance changes (never hold/trade the token itself),
small irregular SOL inflows (creator fee share) -- not trading PnL at all.

## Not the claimed identity

- `73LnJ7G9ffBDjEBGgJDdgvLUhD5APLonKrNiHsKDCw5B` ("waddles") -- pump.fun username `niglet7`, no
  bio, no X link, 141 followers. Nothing ties this to the real Waddles.
- `FxN3VZ4BosL5urG2yoeQ156JSdmavm9K5fdLxjkPmaMR` ("cupsey", lowercase) -- `is_pump_user: false`,
  generic username `funnyshrimp9569`, 12 followers. Not the real Cupsey (that's more likely
  `cupsey2` or `suqh5s...` above).
- `uNksqSWy79L7vPizsU8r56wPmiJwLCtenL5yUk6LM7z`, `BCrTEXmWutwPz8qv6w1S5gDbaLnSLpXKM5kSGVWyyfxu`
  ("rems") -- generic auto-generated usernames, low follower counts, no bio/X.

## Not registered on pump.fun at all

`AcVua6Uss59mneonhV5TfBhoyW8kyz7mnTDhtocgez3t`, `ExyyiTjWfBfcSn6Qu25GdoxxC21dFAd71SiQM2KZRdn6`
("ansem agent"), `4mwxxeq98uyaqmBfeMLZWvHyV55sFbWUacsgEsu62VR1` ("ansem,,"),
`EAov53rG4beBi7bmBVYgCf4yeHxBW7idgbUkCyyVxSCq` ("tjr") -- pump.fun's API returns 404 for these.
Either they trade exclusively through a different platform/UI, or they're genuinely inactive.

## Takeaways for sourcing future candidates

1. **A watchlist label is a guess, not a fact.** Multiple wallets in this list claimed to be
   "ansem" or "cupsey"; per-wallet verification found at most one credible match per name.
   Cross-check against `frontend-api-v3.pump.fun/users/<address>` (profile, X link, followers)
   before trusting a name.
2. **A verified-real famous wallet is not automatically a copyable trading wallet.** It can be
   an airdrop-magnet (attention noise), a token-creator fee address, or run through MEV/bundle
   infrastructure invisible to simple balance-delta analysis -- three different things, none of
   which are "this person's spot trading."
3. If a specific verified identity (e.g. the real Ansem or Cented) matters enough to pursue
   further, the next step is finding their *actual* active trading wallet -- possibly the
   `canonical_evm_wallet` on a different chain, or asking them/checking their own social posts
   for which address they trade from -- rather than assuming the pump.fun profile wallet is it.
