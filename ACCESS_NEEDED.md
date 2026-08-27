# ACCESS_NEEDED.md — Things Only the Human Operator Can Do

Bundled. Read top-to-bottom; items are ordered by how much they block progress.
For each: What / Why / Where to get it / Cost / Permissions / What happens next.

---

## 1. ~~Approve the business architecture & niche~~ — RESOLVED
Direction confirmed and brand name chosen: **Yardwick** (after TradeStack and StackFront were both ruled out by collision checks — see DECISIONS.md). Site already rebranded (header/footer/schema across all published pages). No longer blocking.

## 2. A domain name
- **What:** Register **yardwick.com** if available; fall back to yardwick.io / yardwick.co / getyardwick.com / useyardwick.com in that order if .com is taken. A web search turned up no dedicated business, trademark, or product currently operating under "Yardwick" in any industry, but registrar-level availability was not checked — confirm before paying for anything.
- **Why:** Needed for a real, indexable, affiliate-program-eligible website. Most affiliate/partner programs require a live business website with real content and a business identity, not a raw GitHub Pages URL, though we can start on a free subdomain.
- **Where:** Any registrar (Cloudflare Registrar has no markup; Namecheap/Porkbun are also cheap, ~$8–12/yr for a .com).
- **Cost:** ~$8–15/year.
- **Permissions:** Payment authorization from the operator.
- **What Claude does next:** Point DNS at the free hosting (Cloudflare Pages/GitHub Pages), finish site branding, and begin submitting to affiliate programs that require a live domain.
- **Interim plan:** Build and deploy the MVP now on a free subdomain (e.g. GitHub Pages) so content and SEO groundwork start accruing immediately; migrate to the paid domain later with 301 redirects — no work is wasted by waiting.

## 3. Free hosting account (Cloudflare Pages or GitHub Pages)
- **What:** Authorize/connect a Cloudflare account (free tier) or confirm GitHub Pages is fine to enable on this repo, so the site can actually be deployed and publicly reachable.
- **Why:** A site that only exists as source code in this repo produces zero traffic, zero SEO, zero affiliate clicks.
- **Where:** GitHub Pages needs only a repo setting toggle (Settings → Pages) — if the operator can do that, no new account is needed at all. Cloudflare Pages needs a free Cloudflare account + connecting this GitHub repo.
- **Cost:** $0.
- **Permissions:** Whoever owns this GitHub repo needs to flip the Pages setting, or create/connect a Cloudflare account.
- **What Claude does next:** Verify the deployed site renders correctly, submit the sitemap to Google Search Console (needs #4), and begin the content publishing cadence.

## 4. Google Search Console + Google Analytics (or a free privacy-friendly alternative like Plausible/Umami self-host, Cloudflare Web Analytics) access
- **What:** A Google account (can be a new free one dedicated to this business) verified against the domain, to get indexing and real keyword/traffic data.
- **Why:** Without this we're flying blind on what's actually ranking/converting — core to the Analytics Agent role and the whole measurement loop.
- **Where:** search.google.com/search-console (free), analytics.google.com (free), or Cloudflare Web Analytics (free, no cookie banner needed) as a simpler alternative.
- **Cost:** $0.
- **Permissions:** Email/account creation, and DNS/HTML verification (Claude can generate the verification file/DNS record; a human needs to add DNS or confirm email ownership).
- **What Claude does next:** Wire up conversion tracking, start the analytics dashboard in `analytics/`, begin reporting real numbers in `METRICS.md`.

## 5. Affiliate/referral program signups (one business identity needed across programs)
- **What:** Actually creating affiliate accounts with the top-scored programs from `AFFILIATES.md` (e.g. via Impact, PartnerStack, Rewardful, or direct signup forms). These require a real name/business, email, tax form (W-9 for US) or payment details (PayPal/bank), and sometimes a live website URL for approval.
- **Why:** Claude cannot pass identity verification, accept program legal terms on the operator's behalf, or receive commission payouts.
- **Where:** Individual program pages — the shortlist and direct links will be maintained in `AFFILIATES.md`.
- **Cost:** $0 to join (most SaaS affiliate programs are free to join).
- **Permissions:** Real name, email, tax/payment info, agreement to program terms — the operator must do this personally.
- **What Claude does next:** Generate the affiliate links, UTM parameters, and disclosure-compliant content immediately once credentials/links are dropped in (they can be pasted into `data/affiliate-links.csv` — see template Claude will create).

## 6. Social media account handles (only for channels we decide to actually run — see SOCIAL_PLAN.md)
- **Status:** YouTube done — https://www.youtube.com/@yardwick is live (confirmed 2026-08-27). TikTok still open (recommended next — see SOCIAL_PLAN.md); Instagram/X remain deprioritized until YouTube/TikTok show traction.
- **What:** Handle/account creation on the 1–2 channels the Market Intelligence + Social Growth analysis recommends starting with (likely YouTube + one short-form platform, not all seven).
- **Brand name to register under:** **Yardwick**. Use `yardwick` as the handle everywhere it's free (YouTube: @yardwick, X: @yardwick, Instagram: @yardwick, TikTok: @yardwick). If a platform's exact handle is taken, use `@getyardwick` or `@yardwickhq` consistently rather than a different handle per platform — cross-platform consistency matters more than winning the shortest handle. Note whichever variant you actually land on so it can be recorded in `SOCIAL_PLAN.md`.
- **Why:** Claude can write scripts/captions/plans but cannot create accounts, verify phone numbers, or upload video from this environment.
- **Where:** Standard signup flows.
- **Cost:** $0.
- **Permissions:** Phone/email verification the operator must complete.
- **What Claude does next:** Deliver ready-to-post scripts, thumbnails concepts, and a publishing calendar the operator (or a scheduling tool) can execute with minimal editing. Also update `SOCIAL_PLAN.md` and `website/public/index.html` (footer/header) with the confirmed handles once created.

## 7. A dedicated email address for the business (e.g. via a free/cheap provider)
- **What:** An inbox for affiliate program correspondence, newsletter sending (e.g. via a free-tier ESP like MailerLite/Brevo), and outreach replies.
- **Why:** Needed before any lead magnet / newsletter signup flow can go live, and most affiliate programs want a real contact email.
- **Where:** A free Gmail/Proton address is enough to start; can attach to the domain later once #2 lands.
- **Cost:** $0.
- **Permissions:** Account creation (phone verification likely required).
- **What Claude does next:** Wire up the lead-magnet delivery and newsletter automation immediately.

---
*Nothing above blocks Claude from continuing to build content, scoring, code, and site structure in the meantime — see BACKLOG.md for what's proceeding in parallel without waiting on the human.*
