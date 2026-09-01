#!/usr/bin/env python3
"""
Backtest / score candidate Solana wallets for copy-trading (fomo.app -> mofocopytradingbot).

Pulls each wallet's recent transaction history from a Solana RPC endpoint, reconstructs
SOL <-> SPL-token swaps from balance deltas (works across Raydium/Pump.fun/Jupiter/Meteora
etc. without decoding per-DEX instructions), matches buys to sells FIFO per mint, and scores
each wallet on win rate, expectancy, sample size, recency, and single-trade dependency.

No third-party dependencies (stdlib only).

Usage:
    python3 backtest_wallets.py --wallets <addr1>,<addr2>,... [options]
    python3 backtest_wallets.py --wallets-file wallets.txt [options]

Options:
    --rpc URL           Solana RPC endpoint (default: public mainnet-beta; get a free
                         Helius/QuickNode/Triton endpoint for anything beyond a quick check --
                         the public endpoint is rate-limited and will be slow/flaky).
    --lookback-days N   Only consider transactions from the last N days (default: 30).
    --max-tx N          Max signatures to fetch per wallet (default: 200).
    --json OUT.json     Also write full results to a JSON file.

Caveats (read before trusting the numbers):
    - PnL is computed in SOL terms from balance deltas, so it includes network fees but NOT
      the price impact / slippage YOU would actually get copy-trading a split second later.
      Treat these numbers as an upper bound on what copying this wallet could achieve.
    - Token-for-token swaps (no SOL leg) are skipped, as are airdrops/transfers.
    - Open (unsold) positions are ignored -- only realized, closed trades count.
    - This is a heuristic, not a certified P&L. Use it to rank/filter candidates, not as
      financial advice.
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict, deque

PUBLIC_RPC = "https://api.mainnet-beta.solana.com"
SOL_MINT = "So11111111111111111111111111111111111111112"
# Common stablecoins -- swaps into/out of these look like "SOL trades" balance-wise only if
# paired with SOL itself; we only track the SOL leg, so stables are just ignored as a mint.
LAMPORTS_PER_SOL = 1_000_000_000


def rpc_call(endpoint, method, params, retries=5):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(
        endpoint, data=payload, headers={"Content-Type": "application/json"}
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read())
                if "error" in body:
                    raise RuntimeError(body["error"])
                return body["result"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 2 ** attempt
                time.sleep(wait)
                continue
            raise
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1 + attempt)
    raise RuntimeError(f"rpc_call failed after {retries} retries: {method}")


def get_signatures(endpoint, address, max_tx, cutoff_ts):
    sigs = []
    before = None
    while len(sigs) < max_tx:
        params = [address, {"limit": min(100, max_tx - len(sigs))}]
        if before:
            params[1]["before"] = before
        batch = rpc_call(endpoint, "getSignaturesForAddress", params)
        if not batch:
            break
        for entry in batch:
            if entry.get("err") is not None:
                continue  # skip failed txs
            if cutoff_ts and entry.get("blockTime") and entry["blockTime"] < cutoff_ts:
                return sigs
            sigs.append(entry)
        before = batch[-1]["signature"]
        if len(batch) < 100:
            break
        time.sleep(0.15)
    return sigs


def get_transaction(endpoint, sig):
    params = [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
    return rpc_call(endpoint, "getTransaction", params)


def extract_swap(tx, wallet):
    """Return (mint, sol_delta, token_delta) for the dominant token leg of this tx, or None."""
    if not tx or not tx.get("meta"):
        return None
    meta = tx["meta"]
    msg = tx["transaction"]["message"]
    account_keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg["accountKeys"]]
    if wallet not in account_keys:
        return None
    idx = account_keys.index(wallet)
    pre_bal = meta["preBalances"][idx]
    post_bal = meta["postBalances"][idx]
    sol_delta = (post_bal - pre_bal) / LAMPORTS_PER_SOL

    token_deltas = defaultdict(float)
    for bal in meta.get("preTokenBalances", []):
        if bal.get("owner") == wallet:
            amt = bal["uiTokenAmount"].get("uiAmount") or 0.0
            token_deltas[bal["mint"]] -= amt
    for bal in meta.get("postTokenBalances", []):
        if bal.get("owner") == wallet:
            amt = bal["uiTokenAmount"].get("uiAmount") or 0.0
            token_deltas[bal["mint"]] += amt

    # Drop near-zero noise
    token_deltas = {m: d for m, d in token_deltas.items() if abs(d) > 1e-9}
    if not token_deltas or abs(sol_delta) < 1e-6:
        return None
    # Pick the mint with the largest absolute delta as "the" traded token
    mint, delta = max(token_deltas.items(), key=lambda kv: abs(kv[1]))
    # Require SOL and token to move in opposite directions (buy: SOL down/token up, sell: reverse)
    if (sol_delta < 0 and delta <= 0) or (sol_delta > 0 and delta >= 0):
        return None
    return mint, sol_delta, delta


def analyze_wallet(endpoint, wallet, lookback_days, max_tx, verbose=False):
    cutoff_ts = int(time.time()) - lookback_days * 86400
    sigs = get_signatures(endpoint, wallet, max_tx, cutoff_ts)
    if verbose:
        print(f"  fetched {len(sigs)} signatures", file=sys.stderr)

    # get_signatures returns newest-first (it paginates backward via `before`). FIFO lot
    # matching below requires processing in chronological order -- otherwise a sell can be
    # matched against a buy that happened *after* it in real time (because that buy appeared
    # earlier in the newest-first list), producing a negative hold time that silently gets
    # clamped to 0 by max(0, ...) downstream. That bug previously made every wallet look like
    # a same-block sniper regardless of its real trade timing. Reverse to oldest-first here.
    sigs = list(reversed(sigs))

    open_lots = defaultdict(deque)  # mint -> deque of [remaining_qty, cost_sol_per_unit, ts]
    closed_trades = []
    buy_sizes = []

    for i, entry in enumerate(sigs):
        sig = entry["signature"]
        ts = entry.get("blockTime") or 0
        try:
            tx = get_transaction(endpoint, sig)
        except Exception as e:
            if verbose:
                print(f"  skip {sig[:8]}: {e}", file=sys.stderr)
            continue
        time.sleep(0.12)  # be polite to public RPC

        swap = extract_swap(tx, wallet)
        if not swap:
            continue
        mint, sol_delta, tok_delta = swap

        if sol_delta < 0 and tok_delta > 0:
            # BUY: spent -sol_delta SOL for tok_delta tokens
            cost_per_unit = (-sol_delta) / tok_delta
            open_lots[mint].append([tok_delta, cost_per_unit, ts])
            buy_sizes.append(-sol_delta)
        elif sol_delta > 0 and tok_delta < 0:
            # SELL: received sol_delta SOL for -tok_delta tokens; match FIFO
            qty_to_sell = -tok_delta
            proceeds_per_unit = sol_delta / qty_to_sell if qty_to_sell else 0
            lots = open_lots[mint]
            while qty_to_sell > 1e-9 and lots:
                lot = lots[0]
                take = min(lot[0], qty_to_sell)
                cost = take * lot[1]
                proceeds = take * proceeds_per_unit
                pnl = proceeds - cost
                closed_trades.append({
                    "mint": mint,
                    "buy_ts": lot[2],
                    "sell_ts": ts,
                    "cost_sol": cost,
                    "proceeds_sol": proceeds,
                    "pnl_sol": pnl,
                    "pnl_pct": (pnl / cost * 100) if cost > 1e-12 else 0.0,
                    "hold_seconds": max(0, ts - lot[2]),
                })
                lot[0] -= take
                qty_to_sell -= take
                if lot[0] <= 1e-9:
                    lots.popleft()
            # if qty_to_sell remains, tokens were acquired outside our lookback window; ignore remainder

    return closed_trades, buy_sizes


def compute_metrics(trades, buy_sizes):
    n = len(trades)
    if n == 0:
        return None
    wins = [t for t in trades if t["pnl_sol"] > 0]
    total_pnl = sum(t["pnl_sol"] for t in trades)
    total_pos_pnl = sum(t["pnl_sol"] for t in wins) or 1e-9
    best = max(trades, key=lambda t: t["pnl_sol"])
    worst = min(trades, key=lambda t: t["pnl_sol"])
    now = time.time()
    last_trade_days_ago = min((now - t["sell_ts"]) / 86400 for t in trades)
    trades_last_7d = sum(1 for t in trades if (now - t["sell_ts"]) / 86400 <= 7)
    avg_hold_hr = sum(t["hold_seconds"] for t in trades) / n / 3600
    hold_secs_sorted = sorted(t["hold_seconds"] for t in trades)
    median_hold_seconds = hold_secs_sorted[n // 2]
    pnl_pcts = sorted(t["pnl_pct"] for t in trades)
    median_pct = pnl_pcts[n // 2]

    mean_buy = sum(buy_sizes) / len(buy_sizes) if buy_sizes else 0
    if len(buy_sizes) > 1 and mean_buy > 0:
        var = sum((b - mean_buy) ** 2 for b in buy_sizes) / len(buy_sizes)
        size_cv = (var ** 0.5) / mean_buy  # coefficient of variation: low = consistent sizing
    else:
        size_cv = None

    return {
        "n_trades": n,
        "win_rate": len(wins) / n,
        "total_pnl_sol": total_pnl,
        "avg_pnl_pct": sum(t["pnl_pct"] for t in trades) / n,
        "median_pnl_pct": median_pct,
        "best_trade_pnl_sol": best["pnl_sol"],
        "worst_trade_pnl_sol": worst["pnl_sol"],
        "profit_concentration": (best["pnl_sol"] / total_pos_pnl) if best["pnl_sol"] > 0 else 0,
        "avg_hold_hours": avg_hold_hr,
        "median_hold_seconds": median_hold_seconds,
        "trades_last_7d": trades_last_7d,
        "last_trade_days_ago": last_trade_days_ago,
        "avg_buy_size_sol": mean_buy,
        "position_size_cv": size_cv,
    }


def score_wallet(m):
    """Composite 0-100 score + human-readable warnings. Tuned for small-account copy-trading:
    consistency and capped downside matter more than raw total PnL."""
    warnings = []
    if m is None:
        return 0, ["No closed trades found in lookback window -- cannot score."]

    score = 0.0

    # Sample size: need enough trades to trust win rate at all
    if m["n_trades"] < 10:
        warnings.append(f"Small sample ({m['n_trades']} closed trades) -- win rate is noisy.")
        score += m["n_trades"] * 1.5  # up to +15
    else:
        score += 15

    # Win rate
    score += max(0, (m["win_rate"] - 0.5)) * 100  # 0 at 50%, +50 at 100%
    if m["win_rate"] < 0.45:
        warnings.append(f"Low win rate ({m['win_rate']:.0%}).")

    # Expectancy (median trade %, robust to one huge outlier)
    score += max(-20, min(20, m["median_pnl_pct"] / 5))

    # Recency
    if m["last_trade_days_ago"] > 14:
        warnings.append(f"Inactive: last closed trade {m['last_trade_days_ago']:.1f} days ago.")
        score -= 15
    elif m["last_trade_days_ago"] <= 3:
        score += 10

    # Profit concentration -- red flag if one trade IS the strategy
    if m["profit_concentration"] > 0.6:
        warnings.append(
            f"Profit concentration {m['profit_concentration']:.0%} in a single trade -- "
            "results likely driven by one lucky pump, not repeatable."
        )
        score -= 20

    # Position sizing consistency
    if m["position_size_cv"] is not None and m["position_size_cv"] > 1.5:
        warnings.append("Highly inconsistent position sizing -- harder to copy predictably.")
        score -= 10

    # Hold time floor: block-time resolution is ~1 second, so a median hold under a few blocks
    # means buy-and-sell landed in the same or immediately adjacent block. That is not a
    # "fast trader" -- it's a pattern (sniper bot, atomic bundle, or privileged/MEV execution)
    # that a Telegram-bot copier, which necessarily lags by at least one block plus message and
    # RPC round-trip time, structurally cannot replicate. You would very likely be buying into
    # this wallet's exit, not their entry.
    if m["median_hold_seconds"] <= 3:
        warnings.append(
            f"Median hold time ~{m['median_hold_seconds']:.1f}s -- buys and sells are landing in "
            "the same/adjacent block. Likely a sniper bot, atomic bundle, or privileged execution "
            "(private mempool/Jito bundle) rather than a repeatable read-and-react trade. A "
            "Telegram copy bot cannot match this latency -- copying this wallet means buying "
            "near the top of their flip, not at their entry. Treat as NOT COPYABLE regardless of score."
        )
        score -= 60

    # Frequency sanity: extreme frequency = hard to copy without huge slippage/fees on a small acct
    if m["trades_last_7d"] > 40:
        warnings.append(f"Very high frequency ({m['trades_last_7d']} trades/7d) -- fees/slippage will eat a small account.")
        score -= 10

    return max(0, min(100, round(score, 1))), warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wallets", help="Comma-separated wallet addresses")
    ap.add_argument("--wallets-file", help="File with one wallet address per line")
    ap.add_argument("--rpc", default=PUBLIC_RPC, help="Solana RPC endpoint")
    ap.add_argument("--lookback-days", type=int, default=30)
    ap.add_argument("--max-tx", type=int, default=200)
    ap.add_argument("--json", dest="json_out", help="Write full results to this JSON file")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    wallets = []
    if args.wallets:
        wallets.extend(w.strip() for w in args.wallets.split(",") if w.strip())
    if args.wallets_file:
        with open(args.wallets_file) as f:
            for line in f:
                line = line.split("#", 1)[0].strip()  # drop full-line and inline comments
                if line:
                    wallets.append(line)
    if not wallets:
        ap.error("Provide --wallets or --wallets-file")

    if args.rpc == PUBLIC_RPC:
        print(
            "NOTE: using the public Solana RPC endpoint. It is rate-limited and can be slow "
            "or flaky for more than a couple of wallets. For real use, get a free API key from "
            "Helius, QuickNode, or Triton and pass it via --rpc.\n",
            file=sys.stderr,
        )

    results = []
    for w in wallets:
        print(f"Analyzing {w} ...", file=sys.stderr)
        try:
            trades, buy_sizes = analyze_wallet(args.rpc, w, args.lookback_days, args.max_tx, args.verbose)
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            results.append({"wallet": w, "error": str(e)})
            continue
        metrics = compute_metrics(trades, buy_sizes)
        score, warnings = score_wallet(metrics)
        results.append({
            "wallet": w,
            "score": score,
            "metrics": metrics,
            "warnings": warnings,
            "n_closed_trades": len(trades),
        })

    results.sort(key=lambda r: r.get("score", -1), reverse=True)

    print("\n" + "=" * 100)
    print(f"{'RANK':<5}{'SCORE':<7}{'WALLET':<46}{'TRADES':<8}{'WIN%':<7}{'MED%':<8}{'HOLD':<10}{'LAST TRADE'}")
    print("=" * 100)
    for i, r in enumerate(results, 1):
        if r.get("error"):
            print(f"{i:<5}{'ERR':<7}{r['wallet']:<46} {r['error'][:40]}")
            continue
        m = r["metrics"]
        if m is None:
            print(f"{i:<5}{r['score']:<7}{r['wallet']:<46}{'0':<8}")
            continue
        hold_s = m["median_hold_seconds"]
        hold_str = f"{hold_s:.0f}s" if hold_s < 120 else f"{hold_s/60:.1f}m"
        print(
            f"{i:<5}{r['score']:<7}{r['wallet']:<46}"
            f"{m['n_trades']:<8}{m['win_rate']*100:<7.1f}{m['median_pnl_pct']:<8.1f}{hold_str:<10}"
            f"{m['last_trade_days_ago']:.1f}d ago"
        )
        for w_ in r["warnings"]:
            print(f"      - {w_}")
    print("=" * 100)
    print(
        "Scores are relative ranking aids, not guarantees. Read the warnings -- a high score "
        "with a 'profit concentration' warning is a trap, not a green light.\n"
    )

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Full results written to {args.json_out}", file=sys.stderr)


if __name__ == "__main__":
    main()
