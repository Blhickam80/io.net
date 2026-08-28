# APPROVAL_POLICY.md — What Claude Does Autonomously vs. What Needs the Operator

## Autonomous — no approval needed
- Research public information (market, competitors, affiliate programs, keywords)
- Write and publish website content, comparisons, reviews, free tools (subject to the content quality rules in CONTENT_PLAN.md — no fabricated testing claims, disclosure required)
- Create/edit code, scripts, automation, local files
- Score and rank affiliate opportunities (AFFILIATES.md, data/affiliate-programs.csv)
- Update internal documentation, tracking, and reports
- Commit and push to the designated working branch
- Generate draft outreach, email, or social copy for the operator's review before it goes out anywhere requiring an account Claude doesn't have

## Requires operator approval before proceeding
- Spending any money (domain purchase, paid software subscription, paid advertising) — the $0-300 constraint in COMPANY.md already forbids most of this outright; this is the process for the rare case something is worth proposing.
- Creating accounts that require identity/phone/payment verification (affiliate programs, social platforms, hosting, analytics) — Claude cannot complete these regardless, so this is naturally enforced, not just policy.
- Sending outbound campaigns at any real volume (more than a small number of individually-considered, personalized messages) — see the anti-spam principle in COMPANY.md.
- Changing DNS, billing, or payment information on any account.
- Accepting any contract or terms-of-service on the operator's behalf.
- Publishing a claim that's legally or reputationally sensitive (a specific negative claim about a named competitor beyond what's directly sourced, a health/legal/financial claim beyond general business-software context).
- Destructive git operations beyond normal practice (force-push, history rewrite, deleting a branch) — standard git safety practice already covers this.

## How this gets applied day to day
Most of what Claude does in this business falls in the autonomous column, by design — the whole point of the founding brief is minimizing operator involvement. The approval-needed list is short and mostly self-enforcing (Claude structurally cannot create an account or spend money from this environment). Where judgment is genuinely needed — is a piece of content borderline on a sensitive claim, is an outreach message personalized enough to not read as spam — default to asking rather than guessing, but don't pad this list with routine publishing decisions that were already delegated by the founding brief.
