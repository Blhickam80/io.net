---
name: weekly-ceo-review
description: Produce the weekly CEO review report (executive summary, revenue, growth, winners, losers, learnings, opportunities, risks, next actions) per the founding brief section 26 and COMPANY.md's CEO role. Use when ~7 days have elapsed since the last report in reports/, or when explicitly asked for a status/progress review.
---

# Weekly CEO Review

## Purpose
Force a regular, honest look at the whole company state — not just "what did I do this week" but "is this working, and what should change" — so strategy drift (like the video-channel misallocation caught and corrected on 2026-08-27) gets caught on a cadence rather than only when the operator happens to notice.

## Triggers
- ~7 days since the last file in `reports/weekly-*.md`.
- Explicit request: "weekly review," "how are we doing," "status check."

## Workflow
1. Read `METRICS.md`, `EXPERIMENTS.md`, `BACKLOG.md`, `DECISIONS.md` for the period since the last report.
2. Pull real numbers wherever they exist (traffic, clicks, affiliate signups, commissions) — if analytics access doesn't exist yet (see ACCESS_NEEDED.md), say so plainly rather than padding the report with vanity content-count metrics dressed up as progress.
3. For every experiment that's had its check-in window elapse (EXPERIMENTS.md), force a SCALE/CONTINUE/MODIFY/KILL decision — don't let one linger un-decided past its window.
4. Write `reports/weekly-YYYY-MM-DD.md` using the section structure below.
5. Update `BACKLOG.md` with the resulting priority re-ranking.

## Report structure (founding brief section 26)
- Executive Summary
- Revenue (total affiliate revenue, recurring affiliate revenue, projected MRR, active referred customers)
- Growth (traffic, leads, affiliate clicks, conversion rate)
- Winners (what worked)
- Losers (what failed)
- Learnings (what did we learn)
- Opportunities (what new opportunities appeared)
- Risks (what could hurt the company)
- Next Actions (top priorities ranked by expected value)

## Decision rules
- No real traffic/revenue data yet is itself a valid, important finding — report it as "pre-revenue, here's what's blocking measurement" rather than manufacturing a report that implies progress that isn't there.
- A strategic correction this week (a reversed decision, a reprioritization) belongs in "Learnings," cited plainly — see DECISIONS.md for the pattern (the video-channel downgrade, the naming saga). Don't bury corrections to look more consistent than the week actually was.

## Failure conditions
- A report with no real numbers that reads as if things are going well when they aren't measured yet.
- Skipping the SCALE/CONTINUE/MODIFY/KILL call on an experiment past its check-in window because there's "not quite enough data" — that's exactly the sunk-cost pattern the founding brief (section 18) warns against.
