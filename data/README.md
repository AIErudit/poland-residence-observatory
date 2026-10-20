# Public aggregate data

Release1.0.0 was reviewed on2026-10-20. `curated/dataset.json` is the frontend contract. The same observations, source catalog, definitions, geographies and summary are available as separate JSON files. `observations.csv` and `sources.csv` use UTF-8, LF and a header row; nested denominators are JSON strings. CSV empty values mean JSON null, not zero.

The release contains **1780 aggregate observations,18 series and1483 catalogued source URLs**. **32 source snapshots were parsed or used to establish a definition/period**. The remaining1451 source records have `status=catalog_only`; their presence does not claim that all their contents were extracted or fact-checked. The source catalog covers the four requested Głos Migranta pages, their direct documentary/data links, document and external-source indexes, and selected earlier MSWiA/NIK/NSA/ZUS references. Structured-link profiling is documented separately in `coverage/` and is not a numerical fact-check of every secondary row.

No Telegram exports, chat messages, personal cases, private correspondence, raw PDF/XLS/XLSX files, credentials or personal-case texts are included. Public observations contain institution-level counts and statistics only. The downloaded originals remain outside this repository.

## Observation schema

`observation.schema.json` describes one row. References are checked by `tests/test_dataset.py`. Stable IDs are derived from series, indicator, geography, permit type and reference period. A changed value under the same definition keeps its observation ID, while its source hash/review changes.

| Field | Meaning |
|---|---|
| `id` | Unique stable observation identifier |
| `series_id`, `indicator_id` | Series and measure; dictionary in `data/dictionary.json` |
| `geography_id`, `geography_name`, `geography_level` | ISO-style region ID, `PL` country, or `WSA-XX` court jurisdiction; court jurisdictions are not administrative voivodeships |
| `permit_type`, `stage` | Permit/legal-basis cohort and event/stage; do not combine distinct cohorts |
| `reference_period` | Full year, dated point stock, or explicit inclusive interval `YYYY-01-01/YYYY-MM-DD` |
| `as_of_date` | Data cut-off where known. Portal current-year rows use retrieval date with explicit operational-cut-off warning. Unknown warehouse2026 cut-off is null |
| `unit`, `value`, `statistic` | Cases, reported days, persons, cases/person or percent; count, mean, max, ratio or share. Calendar-versus-working-day convention is not independently established for every source |
| `denominator` | Null when unknown/not applicable, otherwise explicit value/unit/definition and source observation IDs; means without a published cohort count have null denominators |
| `source_id`, `source_locator` | Foreign key plus page/table/row/cell or exact calculation |
| `definition_id` | Foreign key to the definition dictionary |
| `quality_status` | Reviewed primary, primary copy, reconstructed geography, ambiguous definition/period, derived, or zero-denominator not applicable |
| `comparability_group` | Explicit cohort that may be compared; not permission to add overlapping rows |
| `notes` | Material reporting, cut-off, calculation and interpretation qualifications |

Null is retained for unknown dates and shares with zero denominators. Zero is a numeric source count. Blank count cells in existing NSA6272 rows are interpreted as zero only after all16 regional rows reproduce each national count and the movement identity balances. Missing rows/sheets or unknown durations are never changed to zero.

## Normalized series and their limits

| Series | Scope and source |
|---|---|
| `mswia_18089_concluded_mean_days` |16 regions x2023–2026, temporary residence, mean concluded duration;2026 through06.07. Native Sejm API HTML, MSWiA reply18089 dated27.07.2026 |
| `mswia_12584_pending_count` |463487 national art.114 pending cases and10807 Opole cases on13.10.2025. Not all-temporary UdSC stock |
| `mswia_12584_reported_mean_days` |341 national/594 Opole days reported beside the stock; cohort is not explicit. Not asserted to be pending-case age or the concluded mean |
| `udsc_20260828_concluded_mean_days` |16 regions x2023–2026 temporary means,2026 through12.08 |
| `udsc_20260828_blue_card_mean_days` |Same structure, Blue Card kept separate |
| `udsc_20260828_pending_stock` |16 regions at each year-end2023–2025 and01.07.2026; four totals computed as sums, not extra overlapping observations |
| `warehouse_all_outcomes` |16 regions x2023–2026, count/mean/max all-outcome temporary-residence resolutions.2025 sum398337.2026 cut-off unknown, excluded from current comparisons and annual scenario baselines |
| `lodz_warehouse_all_outcomes` |Łódź temporary/permanent/EU long-term resident,2024/2025/2026 through31.08, count/mean/max all outcomes |
| `lodz_warehouse_positive_decisions` |Łódź positive decisions only, art.114/127/142/144/158 separately, same three periods. Not interchangeable with all-outcome duration |
| `lodz_pending_stock` |Own-office series2023–2026 through25.08, temporary/Blue Card not separately broken down; do not merge with UdSC series |
| `lodz_caseworkers`, `lodz_staff_headcount` |Direct caseworkers versus total staff in the described units; persons, not FTE |
| `lodz_pending_per_caseworker` |Computed stock/headcount ratio. Not annual productivity or an inspector's measured workload |
| `nsa_wsa_6272_annual` |Official NSA annual XLS2020–2025:16 WSA jurisdictions and national totals; twelve indicators. WSA first instance, not NSA cassation |
| `udsc_portal_temporary_applications`, `udsc_portal_temporary_decisions` |Official API citizenship-group sums; annual flows2023–2026, current year partial |
| `udsc_portal_eu_long_term_applications`, `udsc_portal_eu_long_term_decisions` |Same API, EU long-term resident kept separate |

**Important UdSC geographic limitation:** the public PDF is a redacted copy hosted by Głos Migranta. Several region labels are blacked out or not directly legible. Numeric cells on pages3–4 were visually reviewed, while geographic assignment was reconstructed from row order, the published CSV and unique2023 mean matches to primary MSWiA data. Every regional observation carries `reviewed_primary_copy_geography_reconstructed` and an explicit note. This is not a directly legible geographic label. The sums387312,484201,646232 and803223 do not depend on those geographic assignments. The original signed file has not been independently verified. The2026 stock may also have a reporting-system or scope discontinuity.

The Podlaski warehouse attachments have an explicit report-generation date09.09.2026, but the cover letter says only annual/half-year reports are available. That timestamp does **not** establish the2026 data cut-off. Those48 count/mean/max rows keep `reference_period=2026`, `as_of_date=null` and `quality_status=reviewed_primary_period_ambiguous`. They are not in the annual baseline summary.

Warehouse2025 all-outcome resolutions total398337, while the portal's2025 temporary decisions total445462. Both are retained with separate series and definitions. Do not use these as the same indicator. Likewise MSWiA and UdSC historical mean differences are preserved rather than reconciled by selecting a preferred number.

Court symbol6272 includes visas, residence, settlement and expulsion; it is broader than residence-permit disputes. `court_upheld` is **uwzględniono**, `court_dismissed` is **oddalono**, `court_rejected` is **odrzucono**. `court_resolved` means **Załatwiono** excluding **Zamknięto**; `court_resolved_including_closed` means **Łącznie załatwiono, w tym zamknięto**. Opening stock is dated01.01 of the annual table year; end stock is dated31.12. The2023 column layout change is explicitly mapped. Hearing and non-public-session outcomes are added. `court_other_resolved` is the remainder, not exclusively discontinuance. Upheld merits share uses upheld+dismissed; rejection share uses resolved excluding closure. Annual resolved cases are not a filing cohort and these shares are not personal success probabilities. National totals overlap regional rows and must not be added to them.

No Głos Migranta forecast is imported as a fact. A scenario must be separately labelled with explicit inputs/assumptions. Pending stock divided by yearly output is a workload ratio, not an identified expected wait. Concluded means exclude still-open proceedings and are neither medians nor a legal finding of delay.

## Sources and review gate

`sources.json` records `id,url,title,publisher,authority,document_date,retrieved_at,content_sha256,access,license,notes,status`. `publisher` is the host/publisher and `authority` identifies the issuing institution where known. Glos-hosted primary copies have `primary_document_copy_snapshot`, not official-publisher access. Only an explicit official-host allowlist receives `primary_publisher_snapshot`; other fetched external sites are secondary. `status=catalog_only` means no normalized facts, even if the file was downloaded for inspection. License strings describe source/host declarations, not a transfer of rights to every linked document.

`review/approved_sources.json` pins32 exact SHA256 hashes with review notes. A new or changed primary hash cannot enter a normal build. Cached bytes are themselves hash-verified. The UdSC transcription additionally pins its PDF hash and requires a fresh visual review/transcription if that PDF changes. A candidate is visibly unreviewed and must be outside the public repository. Approving a hash requires an explicit source ID, full expected hash, substantive review note and reviewer; the command does not rebuild or publish anything. Promotion builds locally and runs the tests; it does not commit, push or publish.

```powershell
python -m pip install -r scripts/requirements.txt
# Default cache: sibling source-cache/observatory, outside this repository.
# OBSERVATORY_CACHE may point to a different external directory.
python scripts/update_data.py snapshot
python scripts/update_data.py status
python scripts/update_data.py propose
# Inspect source changes and candidate, then approve each reviewed changed source:
python scripts/update_data.py approve-source --source-id src_ID --expected-sha256 FULL_SHA256 --review-note "What was checked and why the definition remains valid" --reviewer "Reviewer"
python scripts/update_data.py promote --as-of 2026-10-20 --version 1.0.0
```

Use `snapshot --refresh` to check remote changes. A network failure does not overwrite reviewed facts or silently approve a source. Upstream files can change or disappear; fetching newer bytes may require review before reproducing the release. The exact cached blobs used for this release are content-addressed outside Git. For an offline build from those retained snapshots, run `python scripts/build_dataset.py`, then `python -m unittest discover -s tests -v`. No application credentials are required.

`summary.json` contains reproducible totals and explicit expected/actual checks, not synthetic facts. Tests verify row IDs/references/dates, strict16-region coverage, units, stock-versus-flow stages, source hashes/review states, all court movement/outcome identities, calculated denominators, null versus zero, warehouse baseline, preserved primary discrepancies, CSV/JSON parity and LF serialization.
