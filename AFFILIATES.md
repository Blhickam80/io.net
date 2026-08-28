# AFFILIATES.md — Affiliate Program Database & Scoring

Methodology: see `STRATEGY.md` §1 for the Affiliate Opportunity Score (AOS) formula and the Commission LTV formula. Research sources: `research/affiliate-programs/votel-ai.md` and `research/affiliate-programs/market-survey.md` (raw agent research, cited sources inside). This file is the human-readable ranking; `data/affiliate-programs.csv` is the machine-readable version.

**Caveat that applies to every commission % below:** these are the current public terms as of 2026-08-27 per program pages/aggregators cited in the raw research files — affiliate terms change without notice and several programs (Birdeye, Wix, Zapier) don't publish terms at all. Re-verify before relying on a number for a real payout decision. **Update 2026-08-28: Votel.ai's terms are no longer in that "unpublished" category** — the operator joined the program directly and confirmed real terms; see the finding below.

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
| 1 | **GoHighLevel** | Agency/white-label platform | 40% recurring for life + 5% tier-2 | $197 | 24 | **$1,891** | **85.4**¹ |
| 2 | **Instantly.ai** | AI sales/outreach | Up to 40% lifetime recurring (volume-tiered) | $97 | 18 | $698 | 83 |
| 3 | **ClickFunnels** | Funnel/marketing platform | Up to 40% recurring (tiered) | $150 | 18 | $810 | 80 |
| 4 | **Thryv (certified partner)** | Local biz all-in-one | 20-30% recurring for life | $300 | 24 | $1,800 | 78 |
| 5 | **NordLayer** | SMB cybersecurity | 30-40% recurring, lifetime | $45 (5 seats) | 18 | $284 | 76 |
| 6 | **Seamless.AI** | AI sales/lead gen | Up to 40% recurring, yr 1 | $147 | 12 | $706 | 74 |
| 7 | **Votel.ai** | Agency/GHL-style bundle | **50% recurring + 5% tier-2, no cap** (verified, see finding below) | $197 | 18 | $1,773 | 73.3¹ |
| 8 | **ActiveCampaign** | Email/marketing automation | 20-30% recurring, capped 12mo | $60 | 12 | $180 | 71 |
| 9 | **Close CRM** | CRM | 30% recurring, capped 12mo | $50 | 12 | $150 | 70 |
| 10 | **MailerLite** | Email marketing | 30% lifetime recurring | $20 | 24 | $144 | 69 |
| 11 | **Podium** | Reputation management | 30% recurring, full year | $289 | 12 | $867 | 68 |
| 12 | **AI-Receptionist.com** | AI receptionist | 20% recurring | $50 (est.) | 12 | $120 | 65 |
| 13 | **Rosie (heyrosie.com)** | AI receptionist | 20% recurring | $49 | 12 | $118 | 64 |
| 14 | **Smith.ai** | AI receptionist | $1,000 flat/client (one-time) | — | — | $1,000 (one-time) | 62 |
| 15 | **MyAIFrontDesk** | AI receptionist | 30% monthly recurring, uncapped | $65 | 12 | $234 | 57.4¹ |

¹ Re-scored 2026-08-28 via `.claude/skills/affiliate-opportunity-scoring/scripts/score_program.py` (the rigorous version, mechanically-derived Commission LTV bucket + explicit judgment inputs). The other 12 rows are still the original holistic estimates from initial research and haven't been re-run through the script yet — see BACKLOG.md. MyAIFrontDesk's drop (73→57.4) reflects the script's more conservative Commission LTV bucketing at its price point, not new negative information about the program.

AOS methodology note: score = weighted sum per STRATEGY.md §1; Commission LTV and recurring-status dominate, offset by SEO/social demoability, conversion difficulty, cookie duration, credibility, and TAM growth. GoHighLevel still edges out Votel despite Votel's higher raw commission % (50% vs 40%) — the gap is entirely on the product-credibility and TAM axes (GoHighLevel has independently verifiable reviews and a longer track record; Votel's referral *program* is now verified, but its underlying *software's* reputation is not), not on the commission mechanics themselves.

## Key finding: Votel.ai's referral program is now verified — the product-reputation gap is what remains
**Update 2026-08-28:** The operator created a Votel.ai referral account directly and confirmed real terms from the dashboard: **50% recurring commission on $97/$297 plans, no earnings cap, plus a 5% second-tier commission** when a referred business's own referrals convert. This is a working, live link (`data/affiliate-links.csv`) — genuinely better raw commission economics than GoHighLevel's 40%. Cookie/attribution window was not stated in what was confirmed; treat as unknown pending further detail.

What has **not** changed from the original research (`research/affiliate-programs/votel-ai.md`):
- The product is still very likely a **GoHighLevel-based white-label reseller/skin** (identical terminology) — not independently confirmed, but strongly implied.
- The underlying software's reviews/reputation ("5-star on Trustpilot/G2" claims) are still not independently verifiable — that's a claim about the *product*, separate from the *referral program's* now-confirmed economics.
- Votel's referral terms are still not **publicly published** on Votel's own marketing site the way GoHighLevel's are — they only became known because the operator joined the program directly. This matters for how the site frames it editorially: we can honestly say "we joined and confirmed the terms," but we can't claim they're independently verifiable by a reader the way GoHighLevel's public affiliate page is.

**Decision:** Votel.ai is no longer excluded from the monetization stack — it has a real, live, working affiliate link today, unlike GoHighLevel which is still pending signup (ACCESS_NEEDED.md #5). Practically: use Votel's live link now for actual revenue capability, while continuing to recommend GoHighLevel to *readers* as the safer product choice given its independently verifiable track record — these are two separate claims (which program pays better vs. which product we'd tell a reader to buy) and the site should keep them separate rather than let the better commission quietly bias the product recommendation. See the updated `compare/gohighlevel-vs-votel.html` for how this is handled on-page.

## Initial programs to build the business around (Phase 2 decision, updated 2026-08-28)

1. **Votel.ai** — the one program with a real, live, working link right now. Best-in-survey raw commission mechanics (50% + 5% tier-2, no cap). Use its live link immediately; keep the editorial framing honest about the product-reputation gap (above).
2. **GoHighLevel** — highest-scored program overall (85.4) and the safer product recommendation for readers given its verifiable track record; still pending actual signup (ACCESS_NEEDED.md #5) so its link remains a placeholder until then.
3. **MyAIFrontDesk** (or Rosie / AI-Receptionist.com) — the narrow point-solution AI-receptionist option for the missed-call-calculator funnel (Engine H); a different product category from Votel/GHL (point tool vs. all-in-one bundle), so it isn't displaced by Votel's ranking — it's answering a different question for the reader.
4. **ActiveCampaign or Close CRM** — the CRM leg of the Customer Monetization Stack for readers who need more than a bundled CRM or are evaluating standalone options; Close is easier to demo for sales-heavy service businesses.
5. **Podium** — reputation management, natural complementary offer for local/home-service readers (same audience as missed-call calculator), strong 30%/12mo recurring, high price point.
6. **Instantly.ai** (secondary/experimental track) — targets the agency/consultant secondary segment from STRATEGY.md §3; hold as an Experiment (EXPERIMENTS.md) rather than a primary pillar until we confirm the agency-audience segment is worth pursuing.

All but Votel.ai remain **provisional pending actual affiliate account approval** (ACCESS_NEEDED.md #5) — content and comparisons can be built and published now (with disclosure) even before an affiliate link is live; links get inserted once accounts are approved.

## Full data
See `data/affiliate-programs.csv` for the structured version (all 63 surveyed programs with individual fields) used to regenerate this table as new data comes in.
