# COMPANY.md — Company Memory (Read This First)

**Company (working name):** TBD — see BACKLOG.md for naming task
**Type:** Autonomous AI-run affiliate marketing business
**Mission:** Generate maximum recurring affiliate commission revenue (MRR) for the least capital and least ongoing human involvement, by helping small/medium businesses discover and adopt AI-powered business software.

## How to resume work in this repo
Read files in this order:
1. `COMPANY.md` (this file) — org structure, how the "AI company" is organized
2. `DECISIONS.md` — decisions already made and why (don't re-litigate these)
3. `STRATEGY.md` — business architecture, target niches, monetization stack, scoring formula
4. `AFFILIATES.md` — the affiliate program database and Affiliate Opportunity Scores
5. `METRICS.md` — current KPIs (updated as data exists)
6. `BACKLOG.md` — prioritized task list, next actions
7. `ACCESS_NEEDED.md` — anything blocked on the human operator
8. `EXPERIMENTS.md` — running/completed experiments and their verdicts

Then resume the daily work loop described in `documentation/WORK_LOOP.md`.

## Internal "AI Org Chart"
There is one operator (Claude Code) executing all roles below. Each "agent" is a
functional lens/checklist applied to the work, not a separate persistent process
(Claude Code subagents are spawned via the Agent tool for parallel research/build
tasks and report back into this repo — they are not standing employees).

| Role | Responsibility | Primary artifacts |
|---|---|---|
| CEO / Strategy | Priorities, resource allocation, kill/scale calls | STRATEGY.md, DECISIONS.md, weekly review in reports/ |
| Affiliate Research | Find & evaluate affiliate/referral programs | AFFILIATES.md, research/affiliate-programs/ |
| Market Intelligence | Demand trends, niches, competitor moves | research/market-analysis/ |
| SEO | Keyword strategy, programmatic SEO, on-page | SEO_PLAN.md, seo/ |
| Content | Articles, comparisons, reviews, lead magnets | CONTENT_PLAN.md, content/ |
| Social Growth | Channel strategy & distribution | SOCIAL_PLAN.md, social/ |
| Video | Faceless video scripts/assets | video/ |
| Conversion Optimization | Landing pages, funnels, CTAs | website/, experiments/ |
| Outreach / Sales | B2B outreach, partnerships | outreach/ |
| Automation Engineer | Scripts, pipelines, tooling | automation/ |
| Analytics | Tracking, dashboards, reporting | analytics/, data/, METRICS.md |

## Directory map
```
/research          market & competitor research, raw notes
/affiliate-programs  (nested under research) program-by-program dossiers
/strategy          architecture docs, scoring models
/website           the owned website (source code)
/content           articles, lead magnets, email sequences
/seo               keyword lists, programmatic SEO templates
/social            channel plans, post drafts
/video             scripts, shot lists, titles/descriptions
/outreach          B2B outreach templates & lists
/automation        scripts that automate research/content/reporting
/analytics         tracking plan, dashboard specs
/data              structured data (CSVs, JSON) — programs, keywords, content inventory
/reports           weekly CEO reviews
/experiments       experiment log (see EXPERIMENTS.md)
/documentation     how-tos, the work loop, architecture rationale
```

## Constraints (always true unless the human changes them)
- Budget: $0–$300. No paid spend without explicit human authorization (see ACCESS_NEEDED.md rules).
- No purchasing domains, subscribing to paid tools, or committing funds autonomously.
- No fake reviews, fabricated testimonials, fake "we tested this" claims, spam, or ToS violations.
- FTC affiliate disclosure required on all monetized content.
- Prefer free/open-source tooling; justify any paid recommendation with ROI > cost.
