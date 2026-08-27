# DECISIONS.md — Decision Log

Append-only. Newest first. Each entry: date, decision, why, alternatives rejected.

---

### 2026-08-27 (even later) — Brand name corrected: StackFront (overriding the TradeStack decision below)
**Decision:** Reversed the TradeStack pick made minutes earlier and finalized **StackFront** instead.
**Why:** A web search run immediately after picking TradeStack (should have been run before recommending it, and was — for DeskStack/StackFront — the first time, just not for TradeStack itself once the operator expressed a preference) found two live, active competitors already operating under that exact name in our exact niche: TradeStack Limited (UK, incorporated 2025, tradestack.uk, "AI Operators for Trades" — back-office/AI software for contractors) and tradestack.business ("Autonomous Revenue Engine for Service Businesses," AI CRM/marketing for tradespeople). That's not background noise (like BrowserStack/Formstack showing up for any "-Stack" query) — it's the same product category, same buyer, same name, with a UK-incorporated entity behind one of them. Real trademark exposure, permanent SEO/brand confusion, and .com/.uk/.business already gone. Checked StackFront the same way: no dedicated business, no company page, no niche overlap — clean.
**Applied:** Re-rebranded every published page (header logo, footer, homepage title/JSON-LD) from TradeStack to StackFront; updated the domain target (stackfront.com, ACCESS_NEEDED.md #2) and social handle guidance (ACCESS_NEEDED.md #6) to match. Nothing external (domain, accounts) had been created yet, so the correction was free.
**Lesson for future naming decisions:** Run the collision search on the operator's actual final preference before recommending it, not just on the candidates Claude generated up front — the operator picking from a list doesn't mean the list was fully vetted for their pick specifically.

### 2026-08-27 (later still) — Brand name: TradeStack (superseded — see entry above)
**Decision:** Named the company/site **TradeStack**. Operator preferred it directly; final call deferred to Claude, who confirmed it over the other candidates offered (DeskStack, StackFront, OwnerStack, RingReady).
**Why:** Reads as "the software stack a trade/service business owner needs" — ties directly to the Customer Monetization Stack positioning (STRATEGY.md §4) that's the actual economic differentiator, rather than naming after any single product category. "Trade" reads broadly enough ("whatever trade you're in") to not box out the dental/real estate content already published, while still resonating strongest with the primary home-service/trades segment.
**Applied:** Rebranded all published site pages (header logo, footer copyright, homepage `<title>`/JSON-LD `name`) from the "SiteName" placeholder to TradeStack. Domain target set to tradestack.com (fallbacks: .io/.co/gettradestack.com/usetradestack.com) in `ACCESS_NEEDED.md` #2; social handles standardized on `tradestack`/`gettradestack` in `ACCESS_NEEDED.md` #6, not yet created (blocked on operator per usual).
**Not yet done:** Domain availability was not checked before this decision (operator can register before/without a name-collision check since it's a coined compound word, low trademark-collision risk, but this hasn't been formally verified — flagged rather than assumed).
**Alternatives rejected:** DeskStack/StackFront (also fine, but TradeStack was the operator's clear preference and works at least as well); TradeStack was initially flagged as narrower ("less flexible... if we cover dental/real estate/legal too") — resolved by treating "trade" as "line of work" rather than literally construction trades, which the existing content (dental, real estate pages) already supports without contradiction.

### 2026-08-27 (later) — Every money page must sell the full Customer Monetization Stack, not one affiliate link
**Decision:** Made this a hard content rule (CONTENT_PLAN.md) rather than an aspiration: every industry/money page must include a "Complete Software Stack" section pitching AI receptionist + CRM + scheduling + email/SMS + reputation management (STRATEGY.md §4), not just the single product implied by the page's target keyword. Retrofitted the two already-published industry pages (roofing, dental) to comply.
**Why:** Operator feedback pointed out that the strategy already described this ("Customer Monetization Stack," STRATEGY.md §3) but the actual shipped pages didn't practice it — each only pitched one AI-receptionist affiliate link. A single acquired reader converting on all stack legs is worth roughly 4-6x a single-product page (~$1,400+ blended Commission LTV vs. ~$120-234) at zero additional traffic cost, since it's the same visitor. This is a bigger lever than adding more pages.
**Alternatives rejected:** Leaving the stack concept as a strategy-doc aspiration and only applying it "when natural" — too easy to skip under time pressure; making it a template requirement instead removes the judgment call per page.

### 2026-08-27 — Repo structure & company memory established
**Decision:** Adopt the directory structure and memory-file set specified in the founding brief (COMPANY.md, STRATEGY.md, AFFILIATES.md, etc.) at the repo root rather than nesting under a `/company` subfolder.
**Why:** This repo (`blhickam80/io.net`) is dedicated to this venture — no need for an extra nesting level. Keeps root-level docs discoverable to future sessions immediately.
**Alternatives rejected:** Nesting everything under `/company/` as literally suggested — adds a path segment with no benefit since the whole repo is the company.

### 2026-08-27 — Do not treat Votel.ai as the default choice
**Decision:** Run Votel.ai through the same Affiliate Opportunity Score as ~50 competing/complementary programs before committing any content or outreach effort to it.
**Why:** Explicit instruction from the founding brief; also good practice — first-suggested option is rarely optimal without comparison.
**Status:** Research in progress — see AFFILIATES.md.

### 2026-08-27 — Architecture will favor a small number of durable owned assets over many thin sites
**Decision (provisional, to be confirmed after niche research):** Default toward one authority-style site with vertical-specific content clusters (programmatic SEO by industry) rather than many separate niche microsites, because a single site accumulates domain authority faster on a $0 budget and is far less human-effort to maintain (one analytics setup, one CMS, one backlink profile). Will revisit if research shows a specific vertical justifies a dedicated brand.
**Why:** Zero budget means backlinks/authority are scarce; splitting them across many domains dilutes SEO value. A single site with clear URL-path segmentation (`/reviews/`, `/vs/`, `/best-x-for-y/`, `/tools/`) can still target many long-tail keywords.
**Alternatives considered:** Multiple niche microsites (higher relevance per domain, but 0 authority each, more hosting/DNS overhead); SaaS directory (broad but low differentiation, very competitive); local-business automation platform (product business, not affiliate — out of scope for now).

### 2026-08-27 — No autonomous spending, account creation, or domain purchase
**Decision:** All work proceeds on free tooling (GitHub Pages/Cloudflare Pages for hosting, free-tier everything) until the human operator authorizes spend or creates required accounts (affiliate program signups need a real legal/business identity and often a live website + tax info).
**Why:** Explicit financial-control constraint in the founding brief.
