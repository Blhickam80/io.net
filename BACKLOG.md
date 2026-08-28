# BACKLOG.md — Prioritized Task List

Scored (informally) by `(Revenue Potential × P(success) × Scalability × Recurring Value) / (Capital × Effort × Time-to-Revenue × Complexity)` per STRATEGY.md/founding brief §22. Ordered highest expected-value first within each status group. Update after every work session.

## Done this session (2026-08-27 to 28, updated after launch)
- ✅ **Highest-intent new long-tails woven into on-page FAQ content**: GoHighLevel review page (`reviews/gohighlevel.html`) gets new FAQPage schema + visible FAQ answers for "Is GoHighLevel worth it?" and "Does GoHighLevel have an affiliate program?"; Lead Response Time Calculator (`tools/lead-response-calculator.html`) gets a new FAQPage schema block + visible FAQ for "Why is lead response time important?" and "What is a good lead response time?" ("speed to lead" terminology folded in). `seo/keywords.csv` updated to add "what is a good lead response time".
- ✅ **SEO keyword list expanded** (`seo/keywords.csv`) — 25 new long-tail keywords added across all 9 published pages (roofing/dental/real-estate industry pages, GoHighLevel/Votel comparison + review, all 3 calculators, Podium and Close/ActiveCampaign comparisons), plus 3 "planned" seeds for the next candidate industry verticals (HVAC, plumbing, law firms) per SEO_PLAN.md's seed list, not yet built into pages. No new page types shipped — deliberately, per this week's CEO review, since the content pipeline should prioritize coverage/internal-linking depth over new formats right now.
- ✅ **First weekly CEO review published** (`reports/weekly-2026-08-28.md`) — honest pre-revenue/zero-traffic status, no SCALE/MODIFY/KILL forced on EXP-001/EXP-002 since their check-in window only starts today; `EXPERIMENTS.md` updated to reflect both are now live with a 2026-08-28 start date.
- ✅ **Close vs ActiveCampaign vs HubSpot comparison page published** (website/public/compare/close-vs-activecampaign-vs-hubspot.html) — CRM money page, completes the pattern of standalone comparisons for every leg of the Customer Monetization Stack
- ✅ **Podium vs Birdeye vs NiceJob comparison page published** (website/public/compare/podium-vs-birdeye-vs-nicejob.html) — reputation-management money page, honest about Birdeye's undisclosed pricing/commission
- ✅ **No-Show / Cancellation Cost Calculator published** (website/public/tools/no-show-calculator.html) — 3rd free tool, targets dental/med-spa/salon segment specifically, math verified in a real browser (400 appts → 48 no-shows → 38 unfilled slots → $6,912/mo → $82,944/yr), cross-sells ActiveCampaign/Calendly/Podium (reminder + rescheduling + two-way texting, the actual fix for this problem)
- ✅ **Reconciled all 15 top-ranked AFFILIATES.md programs onto the rigorous `score_program.py` methodology** (previously only GoHighLevel/MyAIFrontDesk/Votel were rescored, the rest were older holistic estimates). Notable moves: NordLayer 76→55.7 and Seamless.AI/Instantly.ai both fell — all three had strong commission math but a poor TAM fit with our home-service SMB audience that the original pass under-weighted.
- ✅ **Lead Response Time Calculator published** (website/public/tools/lead-response-calculator.html) — 2nd free tool, verified in a real browser (Playwright) that the math is correct, wired into tools/index.html and the homepage, cross-links to the same Customer Monetization Stack (MyAIFrontDesk/Close CRM/ActiveCampaign)
- ✅ **SITE IS LIVE: https://blhickam80.github.io/io.net/** — operator flipped GitHub Pages on, Claude re-ran the deploy and verified the live site by fetching it directly. The Votel.ai affiliate link can now earn a real commission.
- ✅ Merged everything to `main` (PR #2 and #3) and handled the full merge/deploy/diagnose/re-run cycle without further pushes needed.
- ✅ Published "GoHighLevel vs Votel.ai" comparison page
- ✅ Published "Best AI Receptionist for Roofing Companies", "...for Dental Practices", and "...for Real Estate Agents" industry pages (full stack template on all three)
- ✅ Published GoHighLevel Review page + reviews/index.html
- ✅ Missed Call Revenue Calculator live in repo
- ✅ Affiliate-link placeholder system + `automation/apply_affiliate_links.py`
- ✅ `.claude/skills/affiliate-opportunity-scoring/` (with working `score_program.py`) and `.claude/skills/weekly-ceo-review/` project skills
- ✅ SECURITY.md, APPROVAL_POLICY.md
- ✅ Votel.ai referral program verified (real terms, real live link) and wired into AFFILIATES.md, STRATEGY.md, data/*.csv, and the GoHighLevel-vs-Votel comparison page with a transparency note on the commission differential

## In progress / next up (not blocked) — re-ranked per weekly-2026-08-28.md
1. **Continue weaving remaining long-tails into on-page content** — GoHighLevel review and Lead Response Calculator are done; Podium/Birdeye comparison ("podium pricing", "best review management software") and the No-Show Calculator ("appointment no show rate by industry") are the next candidates for the same FAQ-reinforcement treatment.
2. **Check Votel.ai's own referral dashboard for early click/signup data** — doesn't require new tooling, just a login; would be the first real signal on which page/placement is actually driving affiliate interest, even before formal analytics exists.
3. **Draft 5-email lead-magnet nurture sequence** ("AI Automation Checklist for Local Businesses") — Engine G, to run once an ESP exists (ACCESS_NEEDED #7).
4. **Re-score the remaining ~40 surveyed-but-deprioritized programs** if any of them ever become relevant to a new content angle — not worth doing speculatively now since none are referenced in published content.
5. **HVAC / plumbing / law-firm industry pages** — seeded as "planned" keywords in `seo/keywords.csv`; hold until the existing roofing/dental/real-estate pages show some real traffic signal, so we're not building the same page type 6x on pure speculation.

**Flagged again in the weekly review as the highest-leverage item the operator (not Claude) can unblock:** Google Search Console / Analytics access (ACCESS_NEEDED #4) — every Growth/Revenue metric in `reports/weekly-2026-08-28.md` reads "unknown" or "$0" until this exists.

**On hold, not a standing item:** Posting Short 01 (delivered, real rendered video, sitting with the operator — upload whenever) and generating shorts-02/03 the same way — video is on-demand now, not a cadence (STRATEGY.md §5).

**Explicitly deferred, not forgotten** (see DECISIONS.md 2026-08-28 — revisit once there's real traffic/affiliate data to justify them, not before): the remaining ~18 proposed Claude Skills beyond opportunity-scoring/weekly-review, 8 formal subagents, a SQLite database, an attribution pipeline, a dashboard, and any community skill-collection imports.

## Blocked on human (see ACCESS_NEEDED.md for full detail)
- Domain purchase (#2) — not urgent, site is live on GitHub Pages URL in the meantime
- Search Console / Analytics account (#4)
- Actually joining the 5 shortlisted affiliate programs — requires real identity/tax/payment info (#5)
- Social/YouTube account creation (#6)
- Business email + ESP account (#7)

## Backlog (not yet started, lower urgency or waiting on evidence)
- Outreach template set for marketing-agency partnerships (Engine K) — targets the Instantly.ai secondary segment
- Competitor reverse-engineering pass (Section 28) — analyze 3-5 successful "GoHighLevel review" sites/YouTube channels for structure/backlink patterns once we can browse them properly
- Newsletter setup plan (Engine I) — depends on ESP access
- Next weekly CEO review (`reports/weekly-2026-09-04.md`) — due ~1 week after this one (2026-08-28)

## Killed / deprioritized
- Paid advertising of any kind — explicitly against the $0-300 / minimal-paid-spend constraint.
- Commodity hosting affiliate content (Hostinger/Bluehost) — weak one-time-only economics, saturated content space, low fit with target niche.
- Pinterest/Facebook as primary channels — low buyer-intent fit for B2B SMB software audience (may revisit for reputation-management/local-business content specifically).
