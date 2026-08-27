# DECISIONS.md — Decision Log

Append-only. Newest first. Each entry: date, decision, why, alternatives rejected.

---

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
