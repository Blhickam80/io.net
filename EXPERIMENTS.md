# EXPERIMENTS.md — Experiment Log

Template per experiment:
```
## EXP-000: <name>
- Hypothesis:
- Channel:
- Target customer:
- Offer:
- Content/asset:
- CTA:
- Started:
- Traffic / Clicks / Leads / Trials / Sales / Revenue / Recurring revenue:
- Cost:
- Time invested:
- Result:
- Decision: SCALE | CONTINUE | MODIFY | KILL
```

No experiments have concluded yet (Day 1). Planned first experiments (to launch once the MVP site + at least one live affiliate link exist):

## EXP-001: Missed Call Revenue Calculator as a lead magnet + affiliate CTA
- Hypothesis: A free, useful calculator showing $ lost to missed calls will attract organic search traffic ("missed call calculator", "how much revenue am I losing from missed calls") and convert a meaningful % of visitors into affiliate clicks on an AI receptionist program, because it makes an abstract pain point concrete and personal.
- Channel: Organic SEO (Engine H + A)
- Target customer: Home-service/local business owners
- Offer: Free calculator, no email gate initially (to maximize top-of-funnel reach and indexability), soft CTA to top-scored AI receptionist affiliate program
- Content/asset: `website/public/tools/missed-call-calculator.html` (built Day 1, live since site launch)
- CTA: "See how [Product] fixes this" → affiliate link with UTM
- Started: 2026-08-28 (site went live; hosting blocker from ACCESS_NEEDED #3 is resolved)
- Traffic / Clicks / Leads / Trials / Sales / Revenue / Recurring revenue: no data yet — analytics not wired up (ACCESS_NEEDED #4); zero on all measured figures as of this report
- Cost: $0
- Time invested: ~1 session to build
- Result: Too early to call — check-in window (2 weeks or 100 sessions from 2026-08-28) has not elapsed
- Decision: CONTINUE (evidence pending — see weekly-2026-08-28.md; do not force SCALE/MODIFY/KILL before the window elapses)

## EXP-002: "Best AI Receptionist for {Industry}" programmatic cluster
- Hypothesis: Industry-specific comparison content outranks generic "best AI receptionist" pages because competition is lower and buyer intent is higher.
- Channel: Engine A/C
- Target customer: Home-service/local business owners in roofing, dental, and real estate specifically
- Offer: Full industry comparison pages with Customer Monetization Stack cross-sell
- Content/asset: `website/public/compare/best-ai-receptionist-{roofing,dental,real-estate}.html` — all 3 published and live since site launch
- Started: 2026-08-28 (site went live)
- Traffic / Clicks / Leads / Trials / Sales / Revenue / Recurring revenue: no data yet — analytics not wired up (ACCESS_NEEDED #4); zero on all measured figures as of this report
- Cost: $0
- Time invested: ~1 session to build all 3 pages
- Result: Too early to call — check-in window (2 weeks or 100 sessions from 2026-08-28) has not elapsed
- Decision: CONTINUE (evidence pending — see weekly-2026-08-28.md; do not force SCALE/MODIFY/KILL before the window elapses)

Update this file every time an experiment starts, changes state, or concludes. Do not let a strategy linger in "CONTINUE" indefinitely without new evidence — force a SCALE/MODIFY/KILL decision within a defined check-in window (default: 2 weeks or 100 sessions, whichever first).
