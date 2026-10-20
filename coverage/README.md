# Coverage of the supplied data hub

All **21 CSV download links** on `glos-migranta.eu/dane` were downloaded and structurally profiled: **6,625 rows**, no inconsistent row widths and no completely identical rows within individual files. These checks do **not** establish that all rows are factually correct, that records across files are unique, or that the campaign's samples are representative.

[structured-sources.json](structured-sources.json) records each table's URL, acquisition hash, retrieval time, row count, fields, missing-cell counts, duplicates and analytical use/limits. Raw rows, quotations and correspondence remain outside the repository. Reproduce the profile with `python scripts/audit_structured.py` after acquisition.

The hub mixes administrative aggregates, campaign request histories, rankings, selected quotations, court registries, citation edges and document/extraction indexes. They have different units of analysis. A catalogue of 1,264 documents is not 1,264 residence cases; a count of extracted tables is not a count of verified facts. Do not pool these rows into one statistical population.

The quantitative core is normalized from selected primary tables and API responses in `data/curated/`; the qualitative checks and further source-finding plan are in `research/`. The source register explicitly labels documents that are only catalogued. ZIP links package derivative extractions; their existence is inventoried, not represented as independent verification of every enclosed table, OCR result or letter.

Priority for further work: reconcile pending stock against incoming and completed cases; obtain p50/p90 and age bands for pending cases; establish a consistent definition of headcount/FTE; verify partial 2026 court registries; link FAMI output indicators to dated project commitments and actual expenditure. See the proposed public-information requests before collecting any additional data.
