---
name: residence-editorial-release
description: Turn verified residence data into citable fact pages, charts and a reviewed GitHub Pages release. Use for editorial updates, new public claims and publication.
---

Read `AGENTS.md`, `research/` and the independent verification. Choose a headline whose number, population and date fit in the title or immediate subtitle. Use institutional, factual language. State when the evidence cannot establish a trend or causal claim.

Every fact page must include a permanent URL, observation IDs, source links + locator, extraction date, definition, calculation and limitations. Keep numeric claims in `site/claims.json` so the build and verifier can inspect them. Give downloadable normalized data and a correction route. Do not turn filings with EU institutions into findings of illegality.

Build `docs/` with `python scripts/build_site.py`. Run data tests, site validation and desktop/mobile browser checks. Test table sorting/filtering, date changes, scenario calculations, source links, downloads and copied citations. Inspect social metadata and previews.

If no blocking finding remains and publication is authorized in the session, publish to GitHub Pages and verify the deployed URL and dataset version. Otherwise prepare a concrete reviewable result. Record corrections in `CHANGELOG.md`; do not claim a live feed or automated monitoring when updates are manual.
