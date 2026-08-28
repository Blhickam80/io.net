#!/usr/bin/env python3
"""
Compute the Affiliate Opportunity Score (AOS, 0-100) for a program per
STRATEGY.md section 1. stdlib only, no dependencies.

Four sub-scores are derived mechanically from public numbers (50% of the
total weight); six require a human/agent judgment call after actually
researching the program (the other 50%) - this script will not fabricate
those, it requires them as explicit arguments.

Usage:
    python3 score_program.py \
        --price 65 --commission-pct 30 --recurring lifetime \
        --lifetime-months 12 --cookie-days 30 \
        --retention 6 --seo 7 --social 6 --conv-ease 8 --credibility 6 --tam 7

    # One-time bounty example (no --commission-pct/--lifetime-months needed):
    python3 score_program.py --price 285 --one-time-bounty 1000 \
        --cookie-days 0 --retention 5 --seo 6 --social 5 --conv-ease 6 --credibility 7 --tam 6

Run with no arguments for a worked demo using MyAIFrontDesk's public terms.
"""
import argparse
import sys

# Weights per STRATEGY.md section 1 (must sum to 100)
WEIGHTS = {
    "commission_ltv": 25,
    "recurring": 10,
    "payout_pct": 10,
    "retention": 10,
    "seo": 10,
    "social": 8,
    "conv_ease": 8,
    "cookie": 5,
    "credibility": 6,
    "tam": 8,
}
assert sum(WEIGHTS.values()) == 100


def bucket_ltv(ltv):
    """Commission LTV in $ -> 0-10. Calibrated against the surveyed
    programs in data/affiliate-programs.csv (top: GoHighLevel ~$1,891)."""
    if ltv <= 0:
        return 0
    thresholds = [50, 100, 150, 250, 400, 600, 900, 1300, 1800, 2500]
    for i, t in enumerate(thresholds):
        if ltv <= t:
            return i
    return 10


def bucket_payout_pct(pct):
    if pct <= 0:
        return 0
    thresholds = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    for i, t in enumerate(thresholds):
        if pct <= t:
            return i
    return 10


def bucket_cookie(days):
    if days <= 0:
        return 0
    thresholds = [7, 14, 21, 30, 45, 60, 75, 90, 120, 180]
    for i, t in enumerate(thresholds):
        if days <= t:
            return i
    return 10


def recurring_subscore(kind):
    return {
        "lifetime": 10,
        "capped_12mo": 7,
        "capped_other": 6,
        "hybrid": 5,
        "one_time": 3,
        "unknown": 0,
    }.get(kind, 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--price", type=float, help="Est. customer price per month ($)")
    ap.add_argument("--commission-pct", type=float, help="Commission % (for recurring/hybrid)")
    ap.add_argument("--one-time-bounty", type=float, help="Flat one-time bounty $ instead of recurring %")
    ap.add_argument("--recurring", choices=["lifetime", "capped_12mo", "capped_other", "hybrid", "one_time", "unknown"], default="unknown")
    ap.add_argument("--lifetime-months", type=float, default=0, help="Assumed customer lifetime in months (for recurring LTV calc)")
    ap.add_argument("--cookie-days", type=float, default=0)
    ap.add_argument("--retention", type=float, help="0-10 judgment: retention/churn reputation")
    ap.add_argument("--seo", type=float, help="0-10 judgment: SEO opportunity")
    ap.add_argument("--social", type=float, help="0-10 judgment: social/demo-ability")
    ap.add_argument("--conv-ease", type=float, help="0-10 judgment: conversion ease (inverted difficulty)")
    ap.add_argument("--credibility", type=float, help="0-10 judgment: program/reviews credibility")
    ap.add_argument("--tam", type=float, help="0-10 judgment: TAM/demand growth")
    ap.add_argument("--unverified-terms", action="store_true",
                     help="Set if commission terms are not publicly documented anywhere - caps AOS at 35 per policy")
    args = ap.parse_args()

    demo = args.price is None and args.one_time_bounty is None
    if demo:
        print("No arguments given - running worked demo (MyAIFrontDesk public terms):\n")
        args.price, args.commission_pct, args.recurring = 65, 30, "lifetime"
        args.lifetime_months, args.cookie_days = 12, 30
        args.retention, args.seo, args.social = 6, 7, 6
        args.conv_ease, args.credibility, args.tam = 8, 6, 7

    if args.one_time_bounty:
        ltv = args.one_time_bounty
        payout_pct_score = bucket_payout_pct(0)  # one-time bounties aren't a % of price
    else:
        price = args.price or 0
        pct = args.commission_pct or 0
        ltv = price * (pct / 100) * args.lifetime_months
        payout_pct_score = bucket_payout_pct(pct)

    judgment = {"retention": args.retention, "seo": args.seo, "social": args.social,
                "conv_ease": args.conv_ease, "credibility": args.credibility, "tam": args.tam}
    missing = [k for k, v in judgment.items() if v is None]
    if missing and not demo:
        print(f"ERROR: missing required judgment inputs: {', '.join(missing)}", file=sys.stderr)
        print("These cannot be defaulted - research the program and provide them explicitly.", file=sys.stderr)
        sys.exit(1)

    sub = {
        "commission_ltv": bucket_ltv(ltv),
        "recurring": recurring_subscore(args.recurring),
        "payout_pct": payout_pct_score,
        "retention": judgment["retention"],
        "seo": judgment["seo"],
        "social": judgment["social"],
        "conv_ease": judgment["conv_ease"],
        "cookie": bucket_cookie(args.cookie_days),
        "credibility": judgment["credibility"],
        "tam": judgment["tam"],
    }

    total = sum(sub[k] / 10 * WEIGHTS[k] for k in WEIGHTS)
    if args.unverified_terms:
        capped = min(total, 35)
        note = f"  (capped from {total:.1f} - unverified commission terms, see SKILL.md decision rules)" if total > 35 else ""
        total = capped
    else:
        note = ""

    print(f"Commission LTV: ${ltv:,.0f}  (bucket {sub['commission_ltv']}/10)")
    print("Sub-scores (0-10):")
    for k in WEIGHTS:
        print(f"  {k:16s} {sub[k]:>4}/10   x {WEIGHTS[k]}%")
    print(f"\nAOS = {total:.1f}/100{note}")


if __name__ == "__main__":
    main()
