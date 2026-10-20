# Residence Observatory: working agreement

This repository publishes aggregate evidence about residence proceedings in Poland. The public site is generated into `docs/`; source code is in `site/`. Do not import private chat exports, individual case files, signatures, telephone numbers or personal letters.

## Roles

For a new evidence release, assign source researcher, data engineer, editorial maintainer and an independent verifier. Parallel agent work is explicitly authorized for these roles. The verifier must be a separate agent or person from the author of the claims under review. This is a research check, not legal certification. Small visual fixes need no new evidence review.

* Researcher: follow each claim to the original publisher; inventory cited material and additional official sources. Record inaccessible and catalogued-only sources honestly.
* Data engineer: preserve acquisition hashes outside the repository, normalize observations without losing dates or definitions, write meaningful reconciliation tests. Never manufacture a national mean from regional means without weights.
* Editor/maintainer: select defensible headlines, preserve uncertainty beside each number, maintain accessible tables and permanent citations. Distinguish permits, plastic cards, applications and people.
* Verifier: independently reproduce source numbers and calculations; challenge coverage, denominator, period, comparability and legal wording; report blocking issues in `verification/`. Do not edit the observations being verified. An editor fixes them and requests re-review.

## Evidence and release rules

1. Read `.agents/skills/residence-source-research/SKILL.md` for collection, `residence-data-refresh` for normalization, `residence-verification` for review, or `residence-editorial-release` for publication.
2. Every published numeric claim needs observation IDs, source URL + locator, unit, population, date/period and definition. A copy of an official letter is labelled as a copy; it is not called an independently authenticated original.
3. Keep pending stocks, incoming applications, concluded cases, persons and issued cards separate. Keep different cutoffs and permit types in separate series. A missing value is null or absent, never zero.
4. Means of concluded proceedings do not describe the waiting time of everyone currently waiting. Court success rates among merit rulings are not individual success probabilities. Forecasts are scenarios with explicit assumptions, never observations.
5. Legal claims need current primary law and judgments. State conditions and scope of the 60-day rule, art. 100d, and the individual nature of court rulings. Never promise a permit, damages or a court outcome.
6. No raw personal records, full third-party articles, credentials or private source caches in Git. Publish derived aggregates and source references. Retain upstream licence restrictions and attribution.
7. New evidence is staged and reviewed before updating published observations or claims. No unattended ingestion-to-publication workflow. Record corrections with the date and affected claim IDs.
8. Before release: run the dataset tests, verifier check, site build and site validation. Review desktop/mobile, source links, filters, citations and downloads. Publish only after blocking findings are resolved. Record exact scope of verification.

## Commands

See `README.md` for acquisition, validation, build and preview commands. Source caches belong outside this repository. GitHub Pages serves `main:/docs`.
