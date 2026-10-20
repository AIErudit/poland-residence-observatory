# Residence Observatory / Polska

A reproducible, independently checked research workspace on residence proceedings in Poland. Public site: **[aierudit.github.io/poland-residence-observatory](https://aierudit.github.io/poland-residence-observatory/)**. Interface: Polish and Russian. Each fact has a permanent page, source, date, definition, calculation and share preview.

This is an independent AIErudit project, using materials collected by **[Głos Migranta](https://glos-migranta.eu/dane)** and official publications. It is not affiliated with that initiative or with public authorities. The first release is a historical snapshot as of **20 October 2026**, not a live feed or legal advice.

## What is published

* Normalized aggregate observations: processing-time means, pending stocks, incoming applications and decisions, WSA complaint outcomes, and a separately defined Łódź staffing series.
* A source register distinguishing original agency publications, third-party copies and catalogued-only material. A catalogued link is not a claim that its contents have been extracted or verified.
* A structure/completeness profile of **all 21 linked CSV files** on the data hub: **6,625 rows**. See [coverage](coverage/). This is distinct from verification of the contents of every record.
* A comparison of the four Głos Migranta pages and the [The Warsaw article](https://www.the-warsaw.pl/175788/v-polshe-reshenija-po-karte-pobytu-zhdut-do-658-dnej-vmesto-dvuh-mesjacev-po-zakonu-v-uzhondah-pochti-polmilliona-del-zhaloba-doshla-do-evropejskoj-komissii/), research gaps, additional official sources and a plan for obtaining better data: see [research](research/).
* An independent AI review of specified sources and release claims, with limitations: [verification/review.md](verification/review.md). This is not external certification or a guarantee of legal correctness.
* A simple stock-flow scenario calculator. It deliberately does not predict an individual applicant's waiting time.

The private chat research that preceded this project is **not** part of the public repository. No chat exports, individual case narratives, raw letters, PDFs, XLS workbooks or personal records are published.

## The distinctions that matter

**658 and 668 days** refer to different source cutoffs. They are regional means for concluded proceedings, not maximum waits. **463,487** is the MSWiA snapshot of temporary-residence-and-work cases on **13 October 2025**, not a current October 2026 total. **803,223** is the sum of a different UdSC stock table on **1 July 2026**, published as a copy by Głos Migranta; it counts cases, not people. Its regional labels were reconstructed because the public scan obscures them.

**29.5%** in WSA category 6272 in 2025 is `432 / (432 + 1032)`: upheld complaints among merit dispositions only. It excludes procedural rejections and other outcomes. The category covers visas, residence, settlement and expulsion; it is broader than residence permits. It is not an individual success probability.

The 60-day rule in art.112a has conditions for the start of the clock, with transitional issues after the MOS reform. Art.100d and individual court judgments require context. No table proves that every case over 60 days was unlawful.

## Reproduce the site

Python 3.12+ and Node (only for the syntax check) are sufficient. Install extraction dependencies for the full pipeline:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/build_site.py
python scripts/validate_site.py --release
node --check site/app.js
python -m http.server 8766 --directory docs --bind 127.0.0.1
```

Open `http://127.0.0.1:8766/`. Do not open `index.html` through `file://`: browser fetch restrictions prevent loading the data. PNG share cards are committed; regenerate them after changing claims with `python scripts/generate_social.py` and inspect them before release.

## Add new evidence

1. Read [AGENTS.md](AGENTS.md), the source metadata and data definitions. Assign researcher, engineer, editor and a separate verifier. Reusable skills live in [.agents/skills](.agents/skills/).
2. Acquire into an external source cache and stage a candidate with `scripts/update_data.py`. See its `--help` and [data documentation](data/) for the review gate. Never point the source cache into the public repository.
3. Review new bytes, source definitions and scope before accepting a snapshot. `python scripts/build_dataset.py` rebuilds from approved snapshots; an unapproved candidate must have an explicit output outside `data/`.
4. Run reconciliation tests; inspect the diff. Add source locators, dates, populations and denominator references. Keep incompatible series separate.
5. Have the separate verifier check the changed observations and public wording, then update `verification/release.json` with the reviewed file hashes and claim IDs. Fix blocking findings before publication.
6. Build and inspect the desktop/mobile site, copied citations and share cards. Run `validate_site.py --release`, commit generated `docs/` and record the correction in [CHANGELOG.md](CHANGELOG.md).

Updates are **reviewed and manual**. There is no scheduled ingestion, monitoring, or automatic promotion of new facts. A change in source bytes is a review trigger, not proof of an error or a licence to replace a public number.

## Data layout

| Path | Purpose |
|---|---|
| `data/curated/dataset.json` | Version, observations, sources, definitions, geographies and summary |
| `data/curated/observations.csv` | Flat export; nested denominator fields are JSON strings |
| `data/curated/sources.json` | Source register with provenance, hashes and extraction status |
| `data/verified/` | Reviewed transcriptions and acquisition acceptance metadata |
| `scripts/` | Acquisition, normalization, checks and static-site build |
| `research/` | Claims audit, source-finding strategy and editorial brief |
| `verification/` | Independent review, reproducible checks and release scope |
| `site/` | Source HTML/CSS/JS and generated claim register |
| `docs/` | Public GitHub Pages output |

An observation preserves series/indicator, geography, permit type, stage, reference period, as-of date, unit, value, statistic, denominator, source + locator, definition, quality status, comparability group and notes. These fields are part of the evidence, not optional display decoration.

## Publication and corrections

GitHub Pages is configured for `main:/docs`, with `.nojekyll`. CI reconciles the data, checks JavaScript, rebuilds the site and checks the independent-review hashes. Commit only a verified snapshot to `main`; deployment from the branch can begin before a separate CI run completes.

Use [issues](https://github.com/AIErudit/poland-residence-observatory/issues/new/choose) for a new source or a correction, including its exact locator. Do not upload personal case files. Git history and the changelog retain corrections. Code: [MIT](LICENSE). Original database arrangement and derived work: [CC BY 4.0, with source-specific limits](DATA-LICENSE.md).
