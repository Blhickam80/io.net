# fomo.app -> mofocopytradingbot Copy-Trading Strategy

Read [STRATEGY.md](./STRATEGY.md) first — it covers wallet selection criteria, how to use
the backtester below, recommended bot settings, and risk rules for a small account.

## Quick start

1. Pull 5-15 candidate wallet addresses from the fomo.app leaderboard/Top Traders screen
   into `wallets.txt` (one per line).
2. Run the backtester:

   ```bash
   python3 backtest_wallets.py --wallets-file wallets.txt --lookback-days 30 --json results.json
   ```

   No dependencies beyond Python 3's standard library. Uses the public Solana RPC endpoint
   by default (fine for a quick look; get a free Helius/QuickNode/Triton key and pass it via
   `--rpc` for anything you're about to trade on — the public endpoint rate-limits hard).

3. Read the ranked output and the warnings under each wallet — a high score with a "profit
   concentration" or "inactive" warning is a trap, not a green light.
4. Pick 2-3 wallets per STRATEGY.md section 3, configure `mofocopytradingbot` per section 4,
   and enforce the account-level risk rules in section 5 yourself (the bot won't).
5. Re-run the backtest weekly and drop wallets that are fading.
