# Website

Static site, zero build step, in `public/`. Deploy target: GitHub Pages (free) or Cloudflare Pages (free) — see `ACCESS_NEEDED.md` #3.

## Local preview
```
cd website/public
python3 -m http.server 8080
# open http://localhost:8080
```

## Deploying to GitHub Pages
1. Repo Settings → Pages → Source: Deploy from a branch → branch: this branch (or `main` after merge), folder: `/website/public` (GitHub Pages requires `/root` or `/docs`; if `/website/public` isn't selectable, add a workflow that copies `website/public` to `docs/` or `gh-pages` — see `automation/` once built).
2. Once live, add the URL to `ACCESS_NEEDED.md` follow-ups (Search Console verification, etc.).

## Structure
- `index.html` — homepage
- `tools/` — free calculators (traffic magnets, Engine H)
- `compare/` — comparison / "best X for Y" / "X vs Y" pages (Engine B/C)
- `reviews/` — single-product review pages
- `about.html` — methodology + affiliate disclosure (linked from every monetized page)
- `styles.css` — shared stylesheet, dark theme, no external dependencies/CDNs

## Content rules (enforced by Content Agent — see CONTENT_PLAN.md)
- Every page with an affiliate link includes/links the disclosure.
- No fabricated "we tested" claims.
- Every new page gets JSON-LD structured data appropriate to its type (Article/Review/FAQPage/WebApplication).
- No page ships until it has genuine differentiated value (no keyword-stuffed thin pages).
