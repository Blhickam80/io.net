# TOP OPPORTUNITIES.md — Phase 1 Discovery Deliverable

Date: 2026-08-27. This is the required Phase 1 output. Full detail lives in `AFFILIATES.md` (scoring), `research/` (raw research), and `STRATEGY.md` (resulting architecture). This file is the executive summary.

## 1. Votel.ai verdict
Likely a GoHighLevel-based white-label agency bundle ($97-$297/mo) targeting local-service agencies. **Its referral program's economics are not publicly documented anywhere** (commission %, recurring status, cookie window, payout terms all unverified — the program page is a login-gated single-page app). Reputation claims are unverifiable. **Conclusion: do not build around it as a lead program.** It remains a watch item — if a human creates an account and reports real terms, we can re-score it (see ACCESS_NEEDED.md).

## 2. Market survey results
63 affiliate/referral programs surveyed across 15 categories (AI receptionist, CRM, scheduling, email marketing, hosting, reputation management, chatbots, workflow automation, accounting, ecommerce, cybersecurity, agency/white-label platforms, field service, AI sales tools, telephony). Full table: `research/affiliate-programs/market-survey.md`.

**Strongest recurring-commission economics:** GoHighLevel (40% for life), Instantly.ai and NordLayer (up to 40% recurring), MailerLite (30% lifetime), Chatfuel/ManyChat/Make.com/n8n (30-40%, 12mo). **Weakest:** commodity hosting and mainstream accounting software — one-time bounties regardless of customer lifetime value.

## 3. Affiliate Opportunity Score — Top 5 (see AFFILIATES.md for all 15 scored + methodology)
| Rank | Program | AOS | Commission LTV | Why |
|---:|---|---:|---:|---|
| 1 | GoHighLevel | 91 | $1,891 | Highest recurring %, lifetime duration, huge/growing agency-reseller TAM, easy to demo, well-documented, strong review base |
| 2 | Instantly.ai | 83 | $698 | Highest raw recurring % surveyed; fits secondary agency/consultant segment |
| 3 | ClickFunnels | 80 | $810 | Strong recurring tiered commission, well-known brand, demoable |
| 4 | Thryv (certified partner) | 78 | $1,800 | High recurring %, high price point; access gated behind partner certification |
| 5 | NordLayer | 76 | $284 | 30-40% recurring lifetime, adjacent SMB-security cross-sell |

Votel.ai scored 31/100 — capped by unverifiable economics and unconfirmed reputation, not by product quality per se.

## 4. Target customer niche
**Primary:** local/home-service SMB owners (roofing, HVAC, plumbing, dental, real estate, auto repair, law firms) — high per-lead revenue, quantifiable pain (missed calls), low technical sophistication but real budget, and a natural need for a *stack* of tools (AI receptionist + CRM + scheduling + reputation management), not just one. One acquired reader → 2-4 plausible affiliate relationships.
**Secondary (hold as experiment):** marketing agencies/consultants who resell software to their own SMB clients — larger deal sizes, more competitive content space, targeted via the Instantly.ai / GoHighLevel angle.

## 5. Business architecture chosen
One authority static website (`website/`) with segmented URL structure (`/tools/`, `/compare/`, `/reviews/`, `/guides/`) rather than many thin microsites — concentrates our zero backlink budget instead of diluting it. Full rationale: `STRATEGY.md` §2, decision logged in `DECISIONS.md`.

## 6. Initial monetization stack (provisional pending real affiliate account approval)
1. GoHighLevel (anchor recurring program)
2. MyAIFrontDesk or best-verified AI-receptionist recurring program (anchor for the missed-call-calculator funnel)
3. Close CRM or ActiveCampaign (CRM leg)
4. Podium (reputation management, complementary local-business offer)
5. Instantly.ai (secondary/experimental — agency segment)

## 7. What's already built (Day 1)
- Full repo scaffolding + company memory files (COMPANY.md, STRATEGY.md, DECISIONS.md, METRICS.md, EXPERIMENTS.md, BACKLOG.md, ACCESS_NEEDED.md, CONTENT_PLAN.md, SEO_PLAN.md, SOCIAL_PLAN.md)
- `AFFILIATES.md` + `data/affiliate-programs.csv` — 63-program database, scored and ranked
- MVP static website: homepage, free-tools index, compare index, about/methodology+disclosure page, and a fully functional **Missed Call Revenue Calculator** (first traffic-magnet asset, Engine H)
- First content assets queued/published — see `CONTENT_PLAN.md`

## 8. What's blocked on the human operator
See `ACCESS_NEEDED.md` — bundled into 7 items (domain, hosting toggle, analytics, affiliate program signups, social account creation, business email/ESP). None of these block continued content/code/research work, which continues per `BACKLOG.md`.
