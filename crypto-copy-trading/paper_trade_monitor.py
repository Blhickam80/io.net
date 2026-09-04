#!/usr/bin/env python3
"""
Live paper-trade monitor for candidate copy-trading wallets.

Polls each wallet for new transactions since the monitor started, classifies buys/sells with
the same balance-delta logic as backtest_wallets.py, and simulates what OUR account would have
made copying each trade at a fixed position size -- assuming we get the same fill price as the
leader (no slippage/latency modeled; see caveat below). Prints one line per detected event to
stdout (each line is a Monitor notification) and a running state file so results survive.

Stops and prints a final summary once every wallet has closed TARGET_CLOSED_TRADES trades, or
MAX_RUNTIME_HOURS has elapsed, whichever comes first.

Caveat: this assumes we fill at the exact same price as the wallet we're copying. Real
copy-bot execution lags by seconds, so actual results will be worse than this simulation on
fast trades. This tests "does the wallet's edge hold up out-of-sample" (forward validation),
not "what latency-adjusted return would mofocopytradingbot actually deliver."
"""

import json
import sys
import time
from collections import defaultdict, deque

sys.path.insert(0, "/home/user/io.net/crypto-copy-trading")
from backtest_wallets import PUBLIC_RPC, get_transaction, extract_swap, rpc_call

STATE_FILE = "/home/user/io.net/crypto-copy-trading/paper_trade_state_2pvub.json"
LOG_FILE = "/home/user/io.net/crypto-copy-trading/paper_trades_log_2pvub.md"

WALLETS = [
    {"address": "2PvubwzjkSwBQ1YyjWedJVuCJ9FTSTEjFYYeyqrMHCGj", "label": "2Pvub", "fixed_size_sol": 0.15},
]

TARGET_CLOSED_TRADES = 5
MAX_RUNTIME_HOURS = 168  # 7 days -- open-ended confirmation watch, not a bounded 24h test
POLL_SECONDS = 150


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def log_line(text):
    with open(LOG_FILE, "a") as f:
        f.write(text + "\n")


def init_state():
    now = time.time()
    state = {
        "started_at": now,
        "deadline": now + MAX_RUNTIME_HOURS * 3600,
        "wallets": {},
    }
    for w in WALLETS:
        state["wallets"][w["address"]] = {
            "label": w["label"],
            "fixed_size_sol": w["fixed_size_sol"],
            "last_seen_sig": None,   # newest signature processed
            "open_lots": {},         # mint -> list of [remaining_paper_qty, paper_cost_sol_per_unit]
            "closed_trades": [],
            "seen_opens": 0,
        }
    return state


def get_new_signatures(address, last_seen_sig):
    """Fetch signatures newer than last_seen_sig, oldest-first. If last_seen_sig is None,
    just record the current newest signature and process nothing (establishes the starting
    point so we only react to trades from here forward)."""
    sigs = rpc_call(PUBLIC_RPC, "getSignaturesForAddress", [address, {"limit": 30}])
    sigs = [s for s in sigs if s.get("err") is None]
    if not sigs:
        return [], last_seen_sig
    newest = sigs[0]["signature"]
    if last_seen_sig is None:
        return [], newest
    new_ones = []
    for s in sigs:
        if s["signature"] == last_seen_sig:
            break
        new_ones.append(s)
    new_ones.reverse()  # oldest first
    return new_ones, newest


def process_wallet(address, w_state):
    events = []
    new_sigs, newest = get_new_signatures(address, w_state["last_seen_sig"])
    w_state["last_seen_sig"] = newest

    for entry in new_sigs:
        sig = entry["signature"]
        ts = entry.get("blockTime") or int(time.time())
        try:
            tx = get_transaction(PUBLIC_RPC, sig)
        except Exception as e:
            events.append(f"  (skip {sig[:10]}: {e})")
            continue
        time.sleep(0.15)

        swap = extract_swap(tx, address)
        if not swap:
            continue
        mint, sol_delta, tok_delta = swap
        fixed_size = w_state["fixed_size_sol"]
        when = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(ts))

        if sol_delta < 0 and tok_delta > 0:
            # Real BUY: they spent -sol_delta SOL for tok_delta real tokens at this price.
            # Lot tracks BOTH the real quantity (to FIFO-match against their real sells) and
            # our proportional paper quantity (fixed_size worth at the same price) so partial
            # sells reduce both correctly.
            price_per_unit = (-sol_delta) / tok_delta
            paper_qty = fixed_size / price_per_unit
            w_state["open_lots"].setdefault(mint, []).append(
                {"real_qty": tok_delta, "paper_qty": paper_qty, "cost_per_unit": price_per_unit}
            )
            w_state["seen_opens"] += 1
            events.append(
                f"[{when}] {w_state['label']}: BUY {mint[:8]}... "
                f"(their size {-sol_delta:.3f} SOL -> our paper buy {fixed_size} SOL, "
                f"sig {sig[:10]})"
            )

        elif sol_delta > 0 and tok_delta < 0:
            # Real SELL: FIFO-match against real_qty in our lots; reduce paper_qty by the same
            # proportion so a partial sell closes only the matching paper fraction.
            qty_to_sell = -tok_delta
            proceeds_per_unit = sol_delta / qty_to_sell if qty_to_sell else 0
            lots = w_state["open_lots"].get(mint, [])
            while lots and qty_to_sell > 1e-12:
                lot = lots[0]
                take_real = min(lot["real_qty"], qty_to_sell)
                frac = take_real / lot["real_qty"] if lot["real_qty"] > 1e-12 else 0
                take_paper = lot["paper_qty"] * frac
                cost = take_paper * lot["cost_per_unit"]
                proceeds = take_paper * proceeds_per_unit
                pnl = proceeds - cost
                pnl_pct = (pnl / cost * 100) if cost > 1e-12 else 0
                w_state["closed_trades"].append({
                    "mint": mint, "sig": sig, "ts": ts,
                    "cost_sol": cost, "proceeds_sol": proceeds,
                    "pnl_sol": pnl, "pnl_pct": pnl_pct,
                })
                events.append(
                    f"[{when}] {w_state['label']}: SELL {mint[:8]}... "
                    f"paper PnL {pnl:+.4f} SOL ({pnl_pct:+.1f}%), sig {sig[:10]}"
                )
                lot["real_qty"] -= take_real
                lot["paper_qty"] -= take_paper
                qty_to_sell -= take_real
                if lot["real_qty"] <= 1e-12:
                    lots.pop(0)

    return events


def main():
    state = load_state()
    if state is None:
        state = init_state()
        save_state(state)
        log_line(f"\n# Paper trade session started {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(state['started_at']))}\n")
        for w in WALLETS:
            print(f"Watching {w['label']} ({w['address']}) -- fixed paper size {w['fixed_size_sol']} SOL")
        print(f"Target: {TARGET_CLOSED_TRADES} closed trades per wallet, or {MAX_RUNTIME_HOURS}h, whichever first.\n")

    while True:
        if time.time() > state["deadline"]:
            print("\n=== 24h window elapsed. Final summary: ===")
            break

        all_done = True
        for w in WALLETS:
            addr = w["address"]
            w_state = state["wallets"][addr]
            if len(w_state["closed_trades"]) < TARGET_CLOSED_TRADES:
                all_done = False
            try:
                events = process_wallet(addr, w_state)
            except Exception as e:
                print(f"  ({w['label']} poll error: {e})")
                continue
            for ev in events:
                print(ev)
                log_line(ev)
            save_state(state)

        if all_done:
            print("\n=== All wallets reached target closed-trade count. Final summary: ===")
            break

        time.sleep(POLL_SECONDS)

    for w in WALLETS:
        addr = w["address"]
        w_state = state["wallets"][addr]
        trades = w_state["closed_trades"]
        n = len(trades)
        wins = sum(1 for t in trades if t["pnl_sol"] > 0)
        total_pnl = sum(t["pnl_sol"] for t in trades)
        print(f"\n{w_state['label']}: {n} closed paper trades, {wins}/{n} wins, total paper PnL {total_pnl:+.4f} SOL")
        for t in trades:
            print(f"    {t['mint'][:10]}...  {t['pnl_sol']:+.4f} SOL ({t['pnl_pct']:+.1f}%)")
        log_line(f"\n## {w_state['label']} summary: {n} closed, {wins}/{n} wins, total paper PnL {total_pnl:+.4f} SOL")


if __name__ == "__main__":
    main()
