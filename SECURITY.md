# SECURITY.md

## Credentials
- **Never** store plaintext passwords, API keys, tokens, cookies, or affiliate payment details in this repository — not in a file named `credentials.md`, not in a comment, not in a "temporary" scratch file that gets committed by accident.
- Real credentials (affiliate dashboard logins, ESP API keys, analytics tokens, once they exist) belong in environment variables or the hosting platform's secret manager (GitHub Actions secrets, Cloudflare environment variables, etc.) — never in tracked files.
- `data/affiliate-links.csv` stores the *destination URLs* for approved affiliate links once an account is joined, not login credentials for those accounts. If a program's dashboard requires a login to generate/regenerate links, that login itself is never written to this repo.
- `.gitignore` already excludes `__pycache__/`, `*.pyc`, and generated media (`*.mp4`, `*.webm`). Extend it immediately if any credential-bearing file type is introduced (`.env`, `*.pem`, etc.) — don't wait for an accidental commit to notice.

## Before every commit
- Run `git status` after a broad `git add` and actually look at what's staged before committing — this is already standing practice in this repo, not a new rule.
- If a file looks like it could contain a secret (even with an innocuous name), read its contents before staging.

## Third-party code
- Do not install or execute code from an unverified source (a community "skill," an npm/pip package, a GitHub Action) without inspecting it first: look for shell-out commands, network calls to unfamiliar hosts, credential/env-var access, and destructive filesystem operations.
- Prefer packages/skills with a clear maintainer and no unusual permission requests. When in doubt, don't install it silently — flag it in `ACCESS_NEEDED.md` or ask, rather than running unreviewed code against a repo that will eventually hold real credentials.

## MCP servers and browser automation
- Any MCP server or browser-automation tool added to this project should come from the tool's official publisher (e.g., Microsoft's own Playwright MCP, not a third-party fork) — see `ACCESS_NEEDED.md` for the current status of that request.
- Browser automation is for public research, our own site, and dashboards the operator has explicitly authorized — never for bypassing CAPTCHAs, rate limits, or access controls on a third-party site.

## Scope discipline
- This repo currently holds no real secrets because no affiliate account, analytics account, or paid service has been connected yet (see ACCESS_NEEDED.md). Revisit this file's provisions for real enforcement (pre-commit hooks scanning for secret patterns, etc.) once real credentials actually exist to protect — building a secret-scanning pipeline for a repo with zero secrets in it would be effort spent on the wrong problem right now.
