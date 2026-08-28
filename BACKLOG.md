# BACKLOG.md — Prioritized Task List

Scored (informally) by `(Revenue Potential × P(success) × Scalability × Recurring Value) / (Capital × Effort × Time-to-Revenue × Complexity)` per STRATEGY.md/founding brief §22. Ordered highest expected-value first within each status group. Update after every work session.

## Done this session (2026-08-27 to 28, updated after merge)
- ✅ Merged everything to `main` (PR #2) and ran the deploy workflow myself — it failed at the one step that requires the repo owner to flip GitHub Pages on in Settings (see ACCESS_NEEDED.md #3 for the exact status). Will re-run the moment that's done; no further push needed.
- ✅ Published "GoHighLevel vs Votel.ai" comparison page
- ✅ Published "Best AI Receptionist for Roofing Companies", "...for Dental Practices", and "...for Real Estate Agents" industry pages (full stack template on all three)
- ✅ Published GoHighLevel Review page + reviews/index.html
- ✅ Missed Call Revenue Calculator live in repo
- ✅ Affiliate-link placeholder system + `automation/apply_affiliate_links.py`
- ✅ `.claude/skills/affiliate-opportunity-scoring/` (with working `score_program.py`) and `.claude/skills/weekly-ceo-review/` project skills
- ✅ SECURITY.md, APPROVAL_POLICY.md
- ✅ Votel.ai referral program verified (real terms, real live link) and wired into AFFILIATES.md, STRATEGY.md, data/*.csv, and the GoHighLevel-vs-Votel comparison page with a transparency note on the commission differential

## In progress / next up (not blocked)
1. **Reconcile the remaining AFFILIATES.md scores against `score_program.py`** — GoHighLevel, MyAIFrontDesk, and Votel.ai are now rescored with the rigorous script; the other ~12 rows are still the original holistic estimates. Re-run them with real judgment inputs before relying on the full ranking for a decision.
2. **Build 2nd free tool: Lead Response Time Calculator** (Engine H) — same pattern as the missed-call calculator, pairs with CRM/AI-receptionist content.
3. **SEO keyword list build-out** — expand `seo/keywords.csv` beyond the seed list (see SEO_PLAN.md) using free tools (Google autosuggest, AlsoAsked-style manual research, competitor sitemaps).
4. **Draft 5-email lead-magnet nurture sequence** ("AI Automation Checklist for Local Businesses") — Engine G, to run once an ESP exists (ACCESS_NEEDED #7).

**Elevated priority note:** Votel's live link means ACCESS_NEEDED.md #3 (enabling GitHub Pages / hosting) is now the actual binding constraint on Milestone 1 (first affiliate commission) — not affiliate approval, which was true until today. Everything else on this list keeps compounding SEO value regardless, but getting the site publicly reachable is the one blocker standing directly between "real live affiliate link exists" and "real live affiliate link can earn something."

**On hold, not a standing item:** Posting Short 01 (delivered, real rendered video, sitting with the operator — upload whenever) and generating shorts-02/03 the same way — video is on-demand now, not a cadence (STRATEGY.md §5).

**Explicitly deferred, not forgotten** (see DECISIONS.md 2026-08-28 — revisit once there's real traffic/affiliate data to justify them, not before): the remaining ~18 proposed Claude Skills beyond opportunity-scoring/weekly-review, 8 formal subagents, a SQLite database, an attribution pipeline, a dashboard, and any community skill-collection imports.

## Blocked on human (see ACCESS_NEEDED.md for full detail)
- Domain purchase (#2)
- Enabling GitHub Pages / connecting Cloudflare Pages (#3)
- Search Console / Analytics account (#4)
- Actually joining the 5 shortlisted affiliate programs — requires real identity/tax/payment info (#5)
- Social/YouTube account creation (#6)
- Business email + ESP account (#7)

## Backlog (not yet started, lower urgency or waiting on evidence)
- Reputation-management comparison page (Podium vs Birdeye vs NiceJob)
- CRM comparison cluster (Close vs ActiveCampaign vs HubSpot for service businesses)
- No-show / cancellation cost calculator (3rd free tool)
- Outreach template set for marketing-agency partnerships (Engine K) — targets the Instantly.ai secondary segment
- Competitor reverse-engineering pass (Section 28) — analyze 3-5 successful "GoHighLevel review" sites/YouTube channels for structure/backlink patterns once we can browse them properly
- Newsletter setup plan (Engine I) — depends on ESP access
- First weekly CEO review (`reports/weekly-2026-09-03.md`) — due ~1 week after launch

## Killed / deprioritized
- Paid advertising of any kind — explicitly against the $0-300 / minimal-paid-spend constraint.
- Commodity hosting affiliate content (Hostinger/Bluehost) — weak one-time-only economics, saturated content space, low fit with target niche.
- Pinterest/Facebook as primary channels — low buyer-intent fit for B2B SMB software audience (may revisit for reputation-management/local-business content specifically).
