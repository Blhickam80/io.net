# STRATEGY.md — Business Architecture

Status: **Phase 1 (Discovery) → Phase 2 (Architecture) in progress.** Affiliate scoring in `AFFILIATES.md` is being populated from live research; the architecture below is the working plan and will be revised as data comes in (see DECISIONS.md for the log of changes).

## 1. Affiliate Opportunity Score (AOS)

Every program is scored 0–100 as a weighted sum of normalized (0–10) sub-scores:

| Factor | Weight | What it measures |
|---|---:|---|
| Commission LTV | 25% | See formula below — the single best predictor of $ per conversion |
| Recurring vs one-time | 10% | Recurring commission = 10, one-time flat = 3–5 depending on size |
| Payout % | 10% | Higher % = more resilient to price changes, easier to explain to readers |
| Retention / churn reputation | 10% | Sticky products protect Commission LTV from decaying |
| SEO opportunity | 10% | Search volume vs current SERP competition for money keywords |
| Social/demo-ability | 8% | Can we show it working on video/screenshot? Drives content engine D/E/H |
| Conversion difficulty (inverse) | 8% | Self-serve free trial = easy; enterprise sales call = hard, scored lower |
| Cookie duration | 5% | 30+ days = 10, 7 days = 3 |
| Program credibility/reviews | 6% | G2/Capterra/Trustpilot sentiment, longevity, payment reliability reports |
| TAM / demand growth | 8% | Rising category (AI voice, automation) scores higher than flat/declining |

**Commission LTV formula** (used as the core input to the Commission LTV sub-score):
```
Commission LTV = Avg Monthly Customer Price × Commission % × Expected Customer Lifetime (months)
```
Expected lifetime is estimated from published churn/retention data when available, else a conservative default by category (SMB SaaS default: 18 months; enterprise: 30 months; low-switching-cost tools: 12 months) — always stated explicitly per program so the assumption is auditable.

Scores and their inputs live in `data/affiliate-programs.csv` (machine-readable) and are summarized in `AFFILIATES.md` (human-readable, ranked).

## 2. Website architecture decision

**Decision: one authority site, not a directory or many microsites**, built as a fast static site (see `website/`) with clear URL segmentation:
- `/best/{category}-for-{industry}/` — programmatic, but hand-curated per page (no thin auto-spam)
- `/vs/{product-a}-vs-{product-b}/` — comparison pages
- `/reviews/{product}/` — single-product reviews (clearly labeled as researched, not "tested," unless we get hands-on trial access)
- `/tools/` — free calculators (traffic magnets + natural affiliate CTAs)
- `/guides/` — evergreen how-to and buyer-intent educational content
- `/blog/` — supporting/awareness content, internal-links into money pages

Rationale: zero backlink budget means authority must be concentrated on one domain; segmentation still lets us rank many long-tail terms. Revisit only if a single vertical proves so strong it deserves a dedicated brand (tracked as an experiment, not a default).

**Stack:** plain static HTML/CSS + minimal vanilla JS (no build step required, zero hosting cost, trivial to deploy to GitHub Pages/Cloudflare Pages, fast Core Web Vitals by default, easy for Claude to generate/maintain programmatically). JSON-LD structured data (Product/Review/FAQ/Article schema) on every page for SEO + AI-search/AEO/GEO visibility. Revisit only if interactivity needs (e.g. a quiz engine) outgrow vanilla JS.

## 3. Target customer segment (initial hypothesis — to confirm against Market Intelligence research)

**Primary:** local/home-service SMBs with high call volume and real revenue-per-lead (roofing, HVAC, plumbing, electricians, dental/med-spa, real estate, auto shops, law firms, property managers). These businesses:
- Lose real, quantifiable money to missed calls/slow lead response (easy to make vivid with a calculator — Engine H)
- Have low technical sophistication but real budget (owner decides fast, no procurement committee)
- Are underserved by content (most SaaS content targets tech-savvy startups, not a roofing company owner)
- Naturally need a **stack**, not one tool: AI receptionist/voice agent + CRM + scheduling + reputation management + payments — i.e., one acquired reader can plausibly generate 2–4 affiliate relationships (the "Customer Monetization Stack" from the brief), which is the single biggest lever on Commission LTV per visitor.

**Secondary (evaluate after MVP traction):** marketing agencies and consultants who resell/recommend software to their own SMB clients (e.g., GoHighLevel's audience) — higher LTV per referred account, more competitive content space.

## 4. The Customer Monetization Stack (default content template — not optional)

Every industry/money page must sell the *stack*, not a single product. One acquired reader is worth 4-6x more if the page monetizes every complementary need in the buying journey instead of stopping at the first affiliate link. This is now a hard content rule (see `CONTENT_PLAN.md` "Content quality rules") — a published industry page without a stack section is incomplete, not just an SEO opportunity left on the table.

**Default stack (swap per vertical only when a category genuinely doesn't apply — e.g., skip reputation management for a business that is pre-revenue):**

| Leg | Default program | Commission | Placeholder |
|---|---|---|---|
| AI receptionist / phone | MyAIFrontDesk (Rosie / AI-Receptionist.com as alternates) | 30% recurring, uncapped | `#affiliate:myaifrontdesk` |
| CRM | Close CRM | 30% recurring, capped 12mo | `#affiliate:close-crm` |
| Scheduling | Calendly | 10-30% recurring (varies) | `#affiliate:calendly` |
| Email/SMS marketing | ActiveCampaign | 20-30% recurring, capped 12mo | `#affiliate:activecampaign` |
| Reputation management | Podium | 30% recurring, full year | `#affiliate:podium` |
| Website/hosting (lower priority, include only if page has room) | Cloudways | $30 + 7% lifetime recurring | `#affiliate:cloudways` |

**Illustrative stack economics** (per referred customer, all 5 core legs converting — an upper bound, not an expectation): $234 (AI receptionist) + $150 (CRM) + ~$180 (email/SMS) + $867 (reputation) + a scheduling commission ≈ **$1,400+ in blended Commission LTV from one acquired customer**, versus ~$120-$234 from a single-product page. Even a 20-30% stack-wide conversion rate on the secondary legs meaningfully changes unit economics — this is the single biggest lever available at zero additional traffic cost, since it's the same visitor.

**Anchor program (highest individual AOS, leads the agency/reseller segment separately from the stack above):** GoHighLevel — 40% recurring for life, `#affiliate:gohighlevel`. GHL substitutes for several stack legs at once (it bundles CRM + scheduling + some marketing automation) for readers who want one platform instead of best-of-breed tools; present it as an alternative path, not an additional stack leg, to avoid double-pitching the same buying decision.

## 5. Acquisition engine priority (80/20 allocation for Phase 1–3)

**Revised 2026-08-27 after a real production constraint surfaced (see DECISIONS.md): video requires either the operator's voice/face or a much more elaborate no-voiceover edit to be watchable as actual content — Claude has no camera or speech synthesis available in this environment, so a "faceless video channel" isn't actually faceless-and-autonomous, it's operator-time-gated. Written/SEO content, by contrast, is fully executable end-to-end with zero ongoing operator time. Reweighted accordingly: SEO content is no longer "80% alongside video at 20%" — it is effectively the whole of the autonomous 80%, and video moves to opportunistic/operator-gated rather than a standing allocation.**

**~90% of effort — high-confidence, compounding, fully autonomous:**
- Engine A (high-intent SEO) — money keywords: "best AI receptionist for {industry}", "{product} pricing", "{product} vs {competitor}"
- Engine C (alternative/comparison pages) — low competition, high intent, fast to produce well
- Engine G/H (lead magnets & free tools) — missed-call revenue calculator ships in the MVP; more calculators queued (see BACKLOG.md)
- Every published page carries the full Customer Monetization Stack (§4) — this is the actual compounding lever, not additional channels

**~10% of effort — operator-gated experiments, not a standing channel:**
- Engine D/E (video) — downgraded from a planned channel to an on-demand asset: Claude can produce a real screen-recording of a tool with computed numbers and burned-in captions (see `automation/record_calculator_short.py`) on request, but treating this as a content pipeline without the operator's voice or face overstates what it actually is. Revisit as a real channel only if/when the operator wants to record voiceover regularly, or a genuinely voice-free format (e.g., pure data/animation) proves out — track as an experiment in EXPERIMENTS.md, don't assume it into the plan.
- Engine J (direct outreach) — to marketing agencies/consultants as a distribution partner test, not spam

Explicitly deprioritized for now (revisit at scale): paid ads (violates $0–300 constraint and instructions to minimize paid spend), Pinterest/Facebook (low buyer-intent fit for B2B SMB software), cold email at volume (compliance risk without a properly warmed domain/mailbox — start small and personalized only).

## 6. Revenue milestones tracking
See `METRICS.md` for current status against Milestone 1 ($ first commission) → Milestone 8 ($25k+/mo). Strategy above is calibrated for $0→$1,000/mo; will be revisited explicitly at each milestone per the founding brief (Section 27).
