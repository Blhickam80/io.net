# AFFILIATES.md — Affiliate Program Database & Scoring

Methodology: see `STRATEGY.md` §1 for the Affiliate Opportunity Score (AOS) formula and the Commission LTV formula. Research sources: `research/affiliate-programs/votel-ai.md` and `research/affiliate-programs/market-survey.md` (raw agent research, cited sources inside). This file is the human-readable ranking; `data/affiliate-programs.csv` is the machine-readable version.

**Caveat that applies to every commission % below:** these are the current public terms as of 2026-08-27 per program pages/aggregators cited in the raw research files — affiliate terms change without notice and several programs (Votel, Birdeye, Wix, Zapier) don't publish terms at all. Re-verify before relying on a number for a real payout decision.

## 63 programs surveyed, 15 categories

Full raw tables (AI receptionist, CRM, scheduling, email marketing, hosting, reputation management, chatbots, workflow automation, accounting, ecommerce, cybersecurity, GoHighLevel/agency platforms, field service, AI sales tools, telephony) are preserved in `research/affiliate-programs/market-survey.md`. Summary of where the money is:

- **Best recurring %:** GoHighLevel (40% for life), NordLayer (30-40% recurring), Instantly.ai (up to 40% lifetime), MailerLite (30% lifetime), Chatfuel/ManyChat (30-40%/12mo), Make.com / n8n (30-35%/12mo)
- **Best one-time bounties (for a complementary, lower-effort content track):** Smith.ai ($1,000/client), Thryv ($1,000/sale), Bill.com ($250-350/sale), WP Engine ($200+/sale)
- **AI receptionist category specifically (Votel's direct comp set) skews to either flat bounties (Smith.ai, Ruby, AnswerConnect) or newer 20-30% recurring entrants (MyAIFrontDesk, Rosie, AI-Receptionist.com, Dialzara)** — economics here are weaker than GHL/agency-platform or AI-sales-tool categories.
- **Weakest recurring economics:** commodity hosting (Hostinger, Bluehost) and mainstream accounting (QuickBooks, FreshBooks) — one-time bounties regardless of LTV.

## Top-15 scored (AOS, 0–100)

Commission LTV assumes conservative SMB-software lifetimes (12mo for newer/smaller vendors and lower-price tools, 18mo for established mid-market SaaS, 24mo for sticky agency/platform tools where switching cost is high) — stated per row.

| Rank | Program | Category | Commission | Assumed price/mo | Lifetime (mo) | Commission LTV | AOS |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | **GoHighLevel** | Agency/white-label platform | 40% recurring for life + 5% tier-2 | $197 | 24 | **$1,891** | **91** |
| 2 | **Instantly.ai** | AI sales/outreach | Up to 40% lifetime recurring (volume-tiered) | $97 | 18 | $698 | 83 |
| 3 | **ClickFunnels** | Funnel/marketing platform | Up to 40% recurring (tiered) | $150 | 18 | $810 | 80 |
| 4 | **Thryv (certified partner)** | Local biz all-in-one | 20-30% recurring for life | $300 | 24 | $1,800 | 78 |
| 5 | **NordLayer** | SMB cybersecurity | 30-40% recurring, lifetime | $45 (5 seats) | 18 | $284 | 76 |
| 6 | **Seamless.AI** | AI sales/lead gen | Up to 40% recurring, yr 1 | $147 | 12 | $706 | 74 |
| 7 | **MyAIFrontDesk** | AI receptionist | 30% monthly recurring, uncapped | $65 | 12 | $234 | 73 |
| 8 | **ActiveCampaign** | Email/marketing automation | 20-30% recurring, capped 12mo | $60 | 12 | $180 | 71 |
| 9 | **Close CRM** | CRM | 30% recurring, capped 12mo | $50 | 12 | $150 | 70 |
| 10 | **MailerLite** | Email marketing | 30% lifetime recurring | $20 | 24 | $144 | 69 |
| 11 | **Podium** | Reputation management | 30% recurring, full year | $289 | 12 | $867 | 68 |
| 12 | **AI-Receptionist.com** | AI receptionist | 20% recurring | $50 (est.) | 12 | $120 | 65 |
| 13 | **Rosie (heyrosie.com)** | AI receptionist | 20% recurring | $49 | 12 | $118 | 64 |
| 14 | **Smith.ai** | AI receptionist | $1,000 flat/client (one-time) | — | — | $1,000 (one-time) | 62 (recurring-weighted formula penalizes non-recurring; strong as a complementary bounty program) |
| 15 | **Votel.ai** | Agency/GHL-style bundle | **Unverifiable** — no public terms found | $97-297 | — | Unknown | **31** (capped low: unverifiable economics, no independent reviews, unconfirmed product originality) |

AOS methodology note: score = weighted sum per STRATEGY.md §1; Commission LTV and recurring-status dominate, offset by SEO/social demoability, conversion difficulty, cookie duration, credibility, and TAM growth. GoHighLevel scores highest on nearly every axis: highest recurring %, lifetime duration, huge and growing agency/SMB-reseller TAM, easily demoed on video, well-documented terms, strong review base. Votel scores lowest of the shortlist specifically *because* its referral economics could not be verified even after directly attempting to load its program page — see finding below.

## Key finding: Votel.ai is not yet a defensible bet
Direct research (`research/affiliate-programs/votel-ai.md`) found:
- The product is very likely a **GoHighLevel-based white-label reseller/skin** (identical terminology: sub-accounts, SaaS Mode, rebilling) — not independently confirmed, but strongly implied by feature naming.
- **No commission %, cookie duration, payout terms, or restrictions are publicly documented anywhere** — not on the program page (client-side app, returns only "Loading..." to an unauthenticated fetch), not in any affiliate directory, not in search results.
- Reputation claims ("5-star on Trustpilot/G2") could not be independently verified.
- No Crunchbase profile, no independent customer-count data.

**Decision:** Do not build initial content/traffic around Votel.ai. If we later want to evaluate it seriously, the only path is creating an account and reading the gated terms directly (a human task — see `ACCESS_NEEDED.md`). Meanwhile, **GoHighLevel is the direct, well-documented alternative in the same product category** (arguably the platform Votel is built on) and scores far higher on every axis that matters for a $0-budget content business: proven 40%-for-life recurring commission, mature affiliate infrastructure, huge content precedent (many successful "GoHighLevel review/alternative" sites already exist, proving the SEO opportunity — see `research/market-analysis/`).

## Initial 3–5 programs to build the business around (Phase 2 decision)

1. **GoHighLevel** — anchor recurring-revenue program. Best Commission LTV, huge and growing agency/SMB-reseller TAM, easy to demo on video (screen recordings), well-trodden but not saturated content angle when combined with our specific niche (local/home-service verticals rather than generic "marketing agency" framing).
2. **MyAIFrontDesk** (or the best-verified AI-receptionist recurring program at signup time — Rosie and AI-Receptionist.com are close seconds) — anchor AI-receptionist program for the missed-call-calculator funnel (Engine H), chosen over Votel specifically because its terms are public, recurring, and verifiable.
3. **ActiveCampaign or Close CRM** — the CRM leg of the Customer Monetization Stack for readers who need more than GHL's bundled CRM or are evaluating standalone options; Close is easier to demo for sales-heavy service businesses.
4. **Podium** — reputation management, natural complementary offer for local/home-service readers (same audience as missed-call calculator), strong 30%/12mo recurring, high price point.
5. **Instantly.ai** (secondary/experimental track) — targets the agency/consultant secondary segment from STRATEGY.md §3, highest raw recurring % in the survey; hold as an Experiment (EXPERIMENTS.md) rather than a primary pillar until we confirm the agency-audience segment is worth pursuing.

These are **provisional pending actual affiliate account approval** (ACCESS_NEEDED.md #5) — content and comparisons can be built and published now (with disclosure) even before an affiliate link is live; links get inserted once accounts are approved.

## Full data
See `data/affiliate-programs.csv` for the structured version (all 63 surveyed programs with individual fields) used to regenerate this table as new data comes in.
