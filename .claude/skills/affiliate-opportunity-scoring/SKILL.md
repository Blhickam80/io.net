---
name: affiliate-opportunity-scoring
description: Score and rank an affiliate/referral program on the 0-100 Affiliate Opportunity Score (AOS) defined in STRATEGY.md, using Commission LTV as the dominant factor. Use whenever a new affiliate program is discovered and needs to be compared against the existing shortlist in AFFILIATES.md/data/affiliate-programs.csv, or when re-scoring an existing program after its terms change.
---

# Affiliate Opportunity Scoring

## Purpose
Give every affiliate/referral program a single, comparable 0-100 score so prioritization decisions (which programs to lead content with, which to drop) are made consistently across sessions, not re-derived from vibes each time. This is the formalization of `STRATEGY.md` §1 — read that section for the authoritative formula and weights; this skill is the repeatable procedure for applying it.

## Triggers
- A new affiliate program surfaces in research and needs a score before it can be compared to the shortlist.
- An existing program's terms change (commission %, cookie duration, pricing) and needs re-scoring.
- Periodic re-validation of the top-ranked programs (their public terms can change without notice).

## Inputs required
From the program's public affiliate/partner page (never guess these — mark "unverified" if not publicly stated, per the credibility rule below):
- `commission_type`: recurring_lifetime / recurring_capped_Nmo / one_time / hybrid / unknown
- `commission_pct_or_amount`
- `cookie_days`
- `est_customer_price_monthly`
- Category (to pick a default lifetime assumption: 12mo newer/lower-price, 18mo established mid-market, 24mo sticky/high-switching-cost)

Judgment inputs (0-10 each, the qualitative sub-scores STRATEGY.md §1 defines — these require actually looking at the program, not defaulting to a mid score):
- Retention/churn reputation (does the underlying product retain customers, based on reviews/public churn signals?)
- SEO opportunity (search volume vs. current SERP competition for its money keywords)
- Social/demo-ability (can it be shown working on video/screenshot?)
- Conversion difficulty, inverted (self-serve trial = 10, enterprise sales call = 2-3)
- Program credibility (reviews, longevity, payout-reliability reports)
- TAM/demand growth (rising category vs. flat/declining)

These six judgment factors and the four mechanically-derived ones (Commission LTV, recurring-vs-one-time, payout %, cookie duration) split the 100 points roughly 50/50 — see `scripts/score_program.py --help` for the exact weights.

## Workflow
1. Compute Commission LTV: `Avg Monthly Price × Commission % × Assumed Lifetime (months)`. State the lifetime assumption explicitly — it's the single most consequential unstated assumption in this whole model.
2. Run `scripts/score_program.py` with the numeric inputs to get the mechanically-derivable sub-scores (Commission LTV bucket, recurring-vs-one-time, payout %, cookie duration) plus a placeholder for the five judgment sub-scores.
3. Fill in the five judgment sub-scores yourself, based on what you actually found in research — do not default them to 5/10 out of laziness; an unscored judgment factor should be flagged, not guessed.
4. Re-run the script with `--judgment` flags to get the final weighted AOS.
5. Add/update the row in `data/affiliate-programs.csv` and the ranked table in `AFFILIATES.md`.

## Decision rules
- If commission terms are **not publicly documented anywhere** (no program page states them, no affiliate directory lists them), cap the program at AOS ≤ 35 regardless of how good the product looks — see the Votel.ai precedent in `AFFILIATES.md`. Unverifiable economics is disqualifying for content-building purposes, not a minor deduction.
- Never let a single very high sub-score (e.g., a huge commission %) overcome a fundamentally weak Commission LTV — the weighted formula exists specifically to prevent flashy-percentage / weak-actual-value programs from ranking above quietly-strong ones (see STRATEGY.md's Program A/B example: 50% commission on a $50/mo, 5-month-retention product loses to 20% on a $300/mo, 30-month product).
- Re-verify terms before relying on a score for a real decision (joining a program, leading content with it) if the score is more than ~30 days old — affiliate terms change without notice.

## Quality standards
- Every score must cite where each input came from (URL or "unverified, inferred from category norms").
- Lifetime-month assumptions must be stated, not buried.
- A program that scores high partly on unverified/optimistic inputs should be flagged as provisional, not presented with the same confidence as one with fully public terms.

## Expected output
An updated row in `data/affiliate-programs.csv` (see its header for the schema) and, for anything entering the top-10, an updated entry in `AFFILIATES.md`'s ranked table with the one-line rationale for its placement.

## Failure conditions
- Scoring a program without checking whether its terms are even public (this is exactly the mistake avoided with Votel.ai — check publication status first, before any other input).
- Letting the judgment sub-scores default to a flat mid-value across every program (defeats the purpose of having them be judgment calls at all).
- Treating a 30+ day old score as current without re-checking.
