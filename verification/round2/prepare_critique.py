"""Prepare a scoped round-2 critique; never changes audited inputs."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
dataset_file = ROOT / "data/curated/dataset.json"
data = json.loads(dataset_file.read_text(encoding="utf-8"))
numeric = json.loads((OUT / "numeric-recheck.json").read_text(encoding="utf-8"))
sources = {s["id"]: s for s in data["sources"]}
parsed = [s for s in data["sources"] if s["status"] == "parsed"]
sha = hashlib.sha256(dataset_file.read_bytes()).hexdigest()
assert sha == numeric["dataset_sha256"]
assert numeric["total_numeric_observations_reconciled"] == len(data["observations"])

source_access = Counter(s["access"] for s in parsed)
observation_access = Counter(sources[o["source_id"]]["access"] for o in data["observations"])
annual = sorted(data["summary"]["court_national_annual"], key=lambda x: x["year"])
boundaries = [
    {"end_year": a["year"], "end_stock": a["court_pending_end"],
     "next_year": b["year"], "next_opening_stock": b["court_pending_start"],
     "difference_next_opening_minus_previous_end": b["court_pending_start"] - a["court_pending_end"]}
    for a, b in zip(annual, annual[1:])
]

def ev(url, locator):
    return {"url": url, "locator": locator}

mswia = "https://api.sejm.gov.pl/sejm/term10/interpellations/18089/reply/DWDJHZ/body"
udsc = "https://glos-migranta.eu/dokumenty/udsc-bsz-waism-0361-16-2026-08-28.pdf"
nsa = "https://www.nsa.gov.pl/dokumenty/statystyki-wsa/"
pad = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014L0092"
aml = "https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32015L0849"
knf = "https://bip.brpo.gov.pl/sites/default/files/2026-03/Odpowiedz_KNF_Bialorusini_konta_05_03_2026.pdf"
giif = "https://www.gov.pl/web/finanse/komunikat-nr-73-w-sprawie-wykluczania-niektorych-kategorii-klientow-z-nawiazywania-stosunkow-gospodarczych-derisking-oraz-skarg-wnoszonych-do-generalnego-inspektora-informacji-finansowej-przez-klientow-instytucji-obowiazanych"
jenec = "https://infocuria.curia.europa.eu/tabs/affair?lang=en&publishedId=C-81%2F24"
rf = "https://rf.gov.pl/dla-klientow/postepowania-interwencyjne/"

findings = [
 {"id":"R2-N01", "phase":1, "severity":"info", "status":"confirmed",
  "title":"All 1,780 numeric cells reconcile to the acquired sources or stated formulas",
  "body":"The verifier reran its own source-reading helpers against the frozen dataset: 1,018 core cells plus 762 remaining cells, with no numeric mismatch or unverified numeric row. This checks transcription and calculations, not the administrative databases, source signatures, or every source-register URL.",
  "affected_series":sorted({o["series_id"] for o in data["observations"]}), "evidence":[{"file":"verification/round2/numeric-recheck.json"}],
  "recommendation":"Describe the result as a scoped numeric and source review, not certification or 1,780 independently observed people/cases."},
 {"id":"R2-N02", "phase":1, "severity":"medium", "status":"retain_existing_qualification",
  "title":"Concluded-case averages do not estimate the wait of current or new applicants",
  "body":"MSWiA regional means concern concluded proceedings; unfinished cases are absent. Rounded regional means have no supplied regional weights for a national mean. Full-year 2023 and partial 2026 differ in period and case mix. Their arithmetic comparison does not identify a causal change in administrative efficiency. Calendar-versus-working-day conventions are not independently established for every reporting system.",
  "affected_series":["mswia_18089_concluded_mean_days","udsc_20260828_concluded_mean_days","udsc_20260828_blue_card_mean_days"],
  "evidence":[ev(mswia,"table 1; footnote cut-off 06.07.2026"),ev(udsc,"duration tables, cut-off 12.08.2026; public document copy")],
  "recommendation":"Keep 'reported mean of concluded proceedings', exact cut-off, partial-year notice and no individual-wait forecast beside the chart and shared cards."},
 {"id":"R2-N03", "phase":1, "severity":"medium", "status":"retain_existing_qualification",
  "title":"UdSC regional attribution is reconstruction rather than direct authentication",
  "body":"The public copy hides regional names. The 16 numeric rows are legible, and their national sums do not depend on names. Regional mapping relies on row-order reconstruction and the 2023 match to MSWiA; Blue Card inherits the row-order assumption. A unique numeric match supports the reconstruction but does not reveal a redacted label or authenticate the original letter.",
  "affected_series":["udsc_20260828_pending_stock","udsc_20260828_concluded_mean_days","udsc_20260828_blue_card_mean_days"],
  "evidence":[ev(udsc,"pp. 3–4, hidden region labels; source-access class primary_document_copy_snapshot")],
  "recommendation":"Retain the reconstructed-geography quality flag and visible caveat. Avoid calling a regional value directly read from a named original row."},
 {"id":"R2-N04", "phase":1, "severity":"low", "status":"new_source_limitation",
  "title":"NSA annual stock boundaries differ by one case twice",
  "body":"The national 6272 end stock is 820 in 2023 while the 2024 opening stock is 821; the 2024 end stock is 930 while the 2025 opening stock is 929. Each dataset cell agrees with the corresponding official annual workbook and each annual movement identity reconciles. No cause for the cross-year differences has been established.",
  "affected_series":["nsa_wsa_6272_annual"],
  "evidence":[ev(nsa,"2023, 2024, 2025 annual XLS; sheet WSA SAB Symbole; national symbol 6272, Excel row 249"),{"computed_boundaries":boundaries}],
  "recommendation":"Do not silently correct source figures, claim exact interyear stock continuity, or attribute the differences to revisions without evidence. Add a short note if stock movement across years is visualized."},
 {"id":"R2-N05", "phase":1, "severity":"medium", "status":"retain_existing_qualification",
  "title":"Court denominator, subject scope and disposed-case cohort matter",
  "body":"Symbol 6272 includes visas, residence, settlement and expulsion, not residence permits alone. 432/(432+1032)=29.508197% in 2025 is the upheld share among merits dispositions. Rejected complaints, other dispositions and administrative closures have different categories. Annual disposed cases are not the cohort filed that year. These shares do not identify a new claimant's success probability or causal court performance.",
  "affected_series":["nsa_wsa_6272_annual"], "evidence":[ev(nsa,"2025 XLS, WSA SAB Symbole, symbol 6272; disposition columns and Załatwiono/Zamknięto distinction")],
  "recommendation":"Keep all outcome categories and the actual denominator visible; use blank-count-as-zero only under the documented existing-row reconciliation rule."},
 {"id":"R2-N06", "phase":1, "severity":"medium", "status":"retain_existing_qualification",
  "title":"Warehouse periods and outcome cohorts cannot be interchanged",
  "body":"The 48 Podlaski warehouse cells for 2026 have an unknown operational cut-off; the report generation date does not establish it. All-outcome resolutions include positive and negative decisions, discontinuance and leaving an application unexamined. Łódź positive-only legal-basis cohorts and maximum durations are separate statistics; the latter are reported database maxima, not independently authenticated individual case histories. Source validation also removed duplicate IDs and substituted registration dates for specified old submission dates.",
  "affected_series":["warehouse_all_outcomes","lodz_warehouse_all_outcomes","lodz_warehouse_positive_decisions"],
  "evidence":[{"file":"data/curated/dataset.json","locator":"definitions warehouse_resolutions / positive_resolution_duration and 48 period_ambiguous observations"}],
  "recommendation":"Preserve null 2026 cut-offs and exclude these partial/ambiguous cells from an annual scenario baseline. Keep outcome cohorts and duration maxima separately labelled."},
 {"id":"R2-N07", "phase":1, "severity":"medium", "status":"retain_existing_qualification",
  "title":"Stocks, portal flows and staff ratios do not form a single cohort model",
  "body":"UdSC stock and Łódź office stock have different cut-offs and incompletely matched scopes. Headcount is a snapshot of people, not annual FTE. Pending/headcount is a workload proxy, not productivity. Portal applications and decisions are counts by event year, not unique persons or the same filing cohort. Acquisition time is not an independently known operational cut-off. A stock divided by annual output is a conditional workload ratio, not an expected wait; stock-flow reconciliation also needs other movements.",
  "affected_series":["lodz_pending_stock","lodz_caseworkers","lodz_staff_headcount","lodz_pending_per_caseworker","udsc_portal_temporary_applications","udsc_portal_temporary_decisions","udsc_portal_eu_long_term_applications","udsc_portal_eu_long_term_decisions"],
  "evidence":[{"file":"data/curated/dataset.json","locator":"definitions lodz_scope, caseworkers, stock_per_caseworker, portal_flow, scenario"}],
  "recommendation":"Keep source/scope differences and scenario assumptions beside the values; do not infer missing cases, productivity, future LTR eligibility or a representative migrant wait distribution."},
 {"id":"R2-N08", "phase":1, "severity":"low", "status":"evidence_gap_no_error_identified",
  "title":"API identifier semantics need a separately cited dictionary",
  "body":"The 16 preserved API response bodies allow country totals to be reconciled but expose only country and total. They do not themselves explain caseType=1 and caseType=3. The current labels agree with the portal/CSV discovery context; no incorrect mapping has been demonstrated. A preserved official dictionary or exact official UI configuration would make that attribution independently reproducible.",
  "affected_series":["udsc_portal_temporary_applications","udsc_portal_temporary_decisions","udsc_portal_eu_long_term_applications","udsc_portal_eu_long_term_decisions"],
  "evidence":[{"file":"verification/round2/numeric-recheck.json","locator":"16 migracje.gov.pl API snapshots; numeric country totals"}],
  "recommendation":"Add the official identifier dictionary/locator if available. Do not describe the absence as proof of a wrong mapping."},
 {"id":"R2-P01", "phase":2, "severity":"medium", "status":"confirmed_origin_boundary",
  "title":"The original core reuses the source collection discovered through Głos Migranta",
  "body":"All 32 parsed/supporting source acquisitions were discovered through Głos Migranta pages/downloads or its cited official NSA index. Directly fetching 24 official-publisher snapshots improves provenance and reproducibility but does not, by itself, create newly collected empirical cases. Eight acquisitions are public copies of official documents. The current README and footer credit Głos Migranta and do not claim affiliation; that attribution is fair and must survive the expanded comparison.",
  "affected_files":["README.md","site/index.html","research/round2-data/provenance-audit.json"],
  "evidence":[{"file":"data/curated/dataset.json","locator":"sources[].notes / access / status"},{"file":"research/round2-data/provenance-audit.json","locator":"acquisition routes; independently compared with the original source register"}],
  "recommendation":"Credit the collection, documents, datasets and prior calculations. State our contribution as selected source rechecking, normalization, explicit definitions, reproducible code and visualization. Do not call Głos Migranta only a link list or claim new primary fieldwork for these 32 sources."},
 {"id":"R2-P02", "phase":2, "severity":"medium", "status":"confirmed_coverage_boundary",
  "title":"Source links, profiled rows and normalized cells are different coverage units",
  "body":"The source register contains 1,483 records, with 32 parsed/supporting acquisitions and 1,451 catalogued-only entries. The normalized 1,780 observations are indicator cells, including derived shares and repeated fields, not 1,780 people or independent cases. Profiling 6,625 upstream CSV rows is a structural inventory, not a full factual audit of all their claims. Neither this administrative selection nor a future volunteer questionnaire is a representative sample of all migrants.",
  "evidence":[{"file":"data/curated/dataset.json","locator":"summary"},{"file":"coverage/structured-sources.json","locator":"structural profiling scope, separate from source-value verification"}],
  "recommendation":"Publish these units separately. Do not give catalogue entries reviewed status or infer survey prevalence/population averages from voluntary responses."},
 {"id":"R2-B01", "phase":1, "severity":"high_if_reproduced_in_new_site", "status":"prevent_upstream_overstatement",
  "title":"Do not transfer the TZTC identity rule to an ordinary application certificate",
  "body":"The official UKNF response concerns Belarusian international-protection applicants and expressly recognizes the Tymczasowe Zaświadczenie Tożsamości Cudzoziemca (TZTC). That statutory identity document is not the same document as an ordinary residence-application receipt, MOS confirmation or passport stamp. A statement that every 'zaświadczenie' proves identity would overextend this source. The letter also preserves other customer-due-diligence duties.",
  "evidence":[ev(knf,"letter dated 05.03.2026, pp. 1–3; prior sector letter 10.06.2025, DML-DMLZNA.071.1.2025.KK"),ev("https://glos-migranta.eu/fakty","section 7, banking discussion; inspected as a secondary assertion")],
  "recommendation":"Name the document precisely. Present ordinary filing proof as possible evidence of a legal position, not automatically as an identity document or proof of lawful residence in every case."},
 {"id":"R2-B02", "phase":1, "severity":"high_if_reproduced_in_new_site", "status":"prevent_unconditional_account_guarantee",
  "title":"A basic-account right and AML safeguards coexist",
  "body":"Directive 2014/92 arts. 2, 15 and 16 protect qualifying consumers' basic-payment-account access; lawful residence is a legal entitlement, not a requirement to hold a plastic permit. This is not a guarantee for every commercial/business account. Article 16(4) preserves AML refusal, while Directive 2015/849 art. 14(4) requires action where relevant due diligence cannot be completed. Identity, lawful status and remaining due diligence are distinct questions.",
  "evidence":[ev(pad,"arts. 2(1)–(2), 15, 16(2), 16(4), 19"),ev(aml,"arts. 13–14; current version link shown as 30.12.2024")],
  "recommendation":"Distinguish opening refusal, account restrictions, payment-card expiry and termination. Do not promise that a valid passport or pending application makes every restriction unlawful. Check current Polish implementation separately."},
 {"id":"R2-B03", "phase":1, "severity":"info", "status":"new_relevant_primary_authority",
  "title":"Jenec supports individual assessment, within a specific basic-account case",
  "body":"CJEU C-81/24 Jenec, judgment 11.06.2026, ECLI:EU:C:2026:470, rejects automatic basic-account refusal solely because of inclusion on a third-country sanctions list, requiring an individual AML assessment. It strengthens the argument against blanket exclusion; it does not decide every migrant document-expiry restriction or remove EU sanctions and AML duties. The official case record, operative part and official abstract were checked; a full-judgment paragraph review remains with the legal workstream.",
  "evidence":[ev(jenec,"judgment/operative part, 11.06.2026; official abstract ECLI:EU:C:2026:470"),ev("https://juris.curia.europa.eu/juris/document/document.jsf?docid=312451&doclang=PL","official abstract")],
  "recommendation":"Use the narrow holding, then clearly label any extension to expiry-related restrictions as an argument rather than an adjudicated conclusion."},
 {"id":"R2-B04", "phase":1, "severity":"medium", "status":"retain_remedy_limits",
  "title":"Supervisory reporting and individual complaint remedies differ",
  "body":"GIIF communication 73 rejects category-only de-risking but says GIIF cannot change an individual bank decision. Rzecznik Finansowy intervention normally follows a rejected, partially met or unanswered bank complaint; it assists natural persons, including entrepreneurs, but does not issue a binding decision or interrupt the claim limitation period. These are separate banking routes, not ways to accelerate a residence permit.",
  "evidence":[ev(giif,"individual assessment and competence paragraphs"),ev(rf,"conditions, persons assisted, limits of intervention")],
  "recommendation":"Ask for the bank's stated reasons and a formal complaint; route systemic information to the proper supervisor without promising an immediate unfreeze or requiring public disclosure of private records."}
]

report = {
 "as_of":"2026-10-20", "checked_at":datetime.now(timezone.utc).isoformat(),
 "status":"phases_1_2_completed_phase_3_pending", "release_approval":False,
 "dataset_sha256":sha,
 "role":"Separate AI source and claim review; not external certification, authentication of signatures, or legal advice",
 "ownership":"verification/round2/ only; audited inputs were not edited",
 "numeric_recheck":{"status":numeric["status"],"reconciled":len(data["observations"]),"total":len(data["observations"]),"mismatches":0,"unverified_numeric_rows":0,"evidence_file":"verification/round2/numeric-recheck.json"},
 "source_coverage":{"registered":len(sources),"parsed_or_supporting_snapshots":len(parsed),"catalogued_only":len(sources)-len(parsed),"snapshots_by_access":dict(source_access),"numeric_cells_by_source_access":dict(observation_access),"all_32_discovery_routes":"Głos Migranta links/downloads or official NSA index already cited there","new_primary_fieldwork_in_original_32":False},
 "new_numeric_data_errors":[],
 "findings":findings,
 "glos_comparison":{"fair_contribution":"Selected source rechecking, provenance distinctions, normalized indicator cells, definitions, reproducible calculations, citations and visualization built on the Głos Migranta source collection and official publishers.","not_established":["New independently collected case-level empirical dataset in the original 32 acquisitions","Verification of all 1,483 source-register URLs or all 6,625 upstream CSV rows","Representativeness of the administrative selection or voluntary questionnaire","Cause of text/API differences, including the 445458 versus 445462 distinction; an old CSV or revision has not been established"]},
 "phase_3_pending_checks":[
  "Review the finished PL/BE/EN pages, fallback text, fact pages, metadata and social cards for equivalent statistical/legal qualifications and removal of Russian public copy as requested.",
  "Verify finished banking/actions/scenarios against current Polish law and primary EU authority, including exact document types, court scope, conditional remedy claims and new sources.",
  "Review questionnaire wording: voluntary selection, one submission versus one person/case, duplicate handling, completed versus right-censored ongoing waits, denominator/missing-answer rules and no representative-population inference.",
  "Review controller/contact/purpose/legal basis/retention/deletion information before submission; distinguish lack of names from anonymity and Cloudflare's operational IP processing.",
  "Inspect server validation, allowed fields and lengths, size limits, duplicate retry handling, abuse controls, error/success behavior, database commit evidence, admin/export authorization and logs; CORS is not authentication.",
  "Check no passport/card/case numbers or identifying free text is required, no row-level responses are published, and aggregate disclosure controls and access/retention practices match public promises.",
  "Check backend tests and deployment evidence supplied by the author; a passing local test is not proof of deployed configuration or production data deletion.",
  "Reconcile new datasets separately; record any unverified series rather than silently extending approval from the original 1,780 cells.",
  "Only after an explicit final freeze: record exact reviewed claim IDs, file hashes and the remaining unverified scope. No round-2 release approval is issued here."
 ],
 "limits":["The source register is much larger than the 32 acquired snapshots reviewed numerically.","Public copies were reconciled to their published bytes; agency-hosted original signatures were not authenticated.","Reconciliation does not establish completeness/correctness of the original administrative databases or representativeness.","The expanded public site, questionnaire and Cloudflare backend were not ready for this phase and have not yet been approved.","No private chat, case file, credential, complete third-party article, or raw source binary was copied into these reports."]
}

(OUT / "critique.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
md = """# Round 2 review — interim, no release approval

As of 20 October 2026. Phases 1–2 are complete for the original statistical snapshot. Phase 3 (the expanded PL/BE/EN public site, questionnaire, banking/actions pages and backend) remains pending. This is a separate AI source/claim review, not external certification or legal advice. Audited inputs were not changed.

The dataset reviewed is `a3609775dc2a5e8fb85b50838f3d65faa5e938c74f98bf028931a45be625fb76`. The verifier's own readers reconcile **1,780/1,780 numeric cells** to the acquired source snapshots and stated calculations, with **no new numeric mismatch**. [Numeric evidence](numeric-recheck.json) and [structured critique](critique.json) distinguish that result from the meaning and reliability of the underlying statistics.

## Statistical meaning and genuine limits

* Regional duration means describe concluded proceedings, excluding those still pending. Full 2023 versus partial 2026 differs in exposure and case mix; no causal efficiency claim or national weighted mean follows. A legal deadline, a median and a new applicant's predicted wait are different measures.
* The UdSC copy's regional names are hidden. The reconstructed mapping has supporting evidence but is not direct reading of named rows; Blue Card inherits its order assumption. National sums are independent of region labels. The published quality flag and caveat must remain visible.
* A real cross-year source discontinuity occurs in NSA 6272: **2023 end 820 → 2024 opening 821**, and **2024 end 930 → 2025 opening 929**. Each source table and annual identity reconciles. The cause is unknown; neither revision nor error is proved. Preserve source figures and disclose the discrepancy if presenting a continuous stock history. [Official NSA annual workbooks](https://www.nsa.gov.pl/dokumenty/statystyki-wsa/).
* Court symbol 6272 also covers visas, settlement and expulsion. The 2025 **29.5%** is 432/(432+1,032), among merits dispositions. Annual disposed cases are not that year's filing cohort. Rejections, other dispositions and closures stay separate; none supplies personal success odds.
* The 48 warehouse cells for 2026 have no established operational cut-off. Keep null dates and exclude them from annual scenario baselines. All-outcome reports, positive-only Łódź cohorts and database maxima have different definitions. Some historical dates were replaced by registration dates by the source's stated validation process.
* Staff headcount is not annual FTE; pending/headcount is not productivity. Office and UdSC stock scopes/cut-offs differ. Portal flows are event-year applications/decisions, not unique people or matched filing cohorts; retrieval time does not prove operational cut-off. Stock/output is only a conditional workload ratio.
* The API arrays reproduce country totals but do not explain the `caseType` identifier dictionary. No incorrect mapping was found; adding a separately cited official dictionary/UI locator would close this provenance gap.

These are limits of inference, mostly already preserved in the dataset. They should not be relabelled as newly discovered transcription errors.

## Fair comparison with Głos Migranta

The original 32 parsed/supporting acquisitions were discovered through its pages/downloads or its cited official NSA index. **24** snapshots were acquired from official publishers and **8** are public copies of official documents. They support **1,308** and **472** normalized cells respectively. Re-fetching an official source gives a fresh version and a reproducible chain; it does not alone constitute new case-level evidence or new primary fieldwork.

The current README/footer give fair credit and disclaim affiliation. Preserve that credit in the new comparison: Głos Migranta supplies actual documents, datasets, analysis and scenarios, not merely a list of links. Our defensible contribution is selected source rechecking, normalization, explicit definitions, reproducible calculations, citations and visualization. New primary acquisitions, if any, need a separate provenance statement.

**1,483 source records ≠ 1,483 verified documents; 6,625 structurally profiled CSV rows ≠ 6,625 fact-checked rows; 1,780 indicator cells ≠ 1,780 cases or respondents.** A future voluntary survey must not be described as representative or used to estimate population prevalence without an appropriate design. The original administrative selection is not a representative survey either.

The 445,458 value belongs to the forecast's text; inspected CSV/API values are 445,462. An old CSV, API revision or historical snapshot explaining the four-case difference has not been established.

## Banking guardrails for the new copy

The [official UKNF response of 5 March 2026](https://bip.brpo.gov.pl/sites/default/files/2026-03/Odpowiedz_KNF_Bialorusini_konta_05_03_2026.pdf) recognizes **TZTC**, the statutory temporary identity certificate used in international-protection proceedings. It does not turn every ordinary residence-application receipt, MOS confirmation or passport stamp into an identity document. Keep identity, lawful residence and other due-diligence requirements separate.

[Directive 2014/92](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014L0092), arts. 2, 15–16, gives qualifying consumers basic-account rights; a plastic residence permit is not the definition of lawful residence. This is not unconditional access to all business/commercial accounts. Its AML exception and [Directive 2015/849 art. 14(4)](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=CELEX:32015L0849) preclude promising that every restriction is unlawful or that a passport alone satisfies all checks.

[CJEU C-81/24 Jenec, 11 June 2026](https://infocuria.curia.europa.eu/tabs/affair?lang=en&publishedId=C-81%2F24), supports individual assessment: inclusion solely on a third-country sanctions list does not justify automatic refusal of a basic account. Its specific holding is not a judgment about all migrant document-expiry restrictions. The full-judgment paragraph check remains with the legal workstream.

[GIIF communication 73](https://www.gov.pl/web/finanse/komunikat-nr-73-w-sprawie-wykluczania-niektorych-kategorii-klientow-z-nawiazywania-stosunkow-gospodarczych-derisking-oraz-skarg-wnoszonych-do-generalnego-inspektora-informacji-finansowej-przez-klientow-instytucji-obowiazanych) opposes category-only exclusion but does not empower GIIF to reverse an individual's bank decision. [Rzecznik Finansowy intervention](https://rf.gov.pl/dla-klientow/postepowania-interwencyjne/) follows the complaint route and is not binding or a guarantee of unfreezing; it does not interrupt limitation. Account restrictions, termination and payment-card expiry are different. Banking complaints do not accelerate residence proceedings.

## Release boundary

No blocker was found in the original 1,780 numeric transcriptions. The new publication is **not approved**: finished translations, legal text, survey selection/denominators/privacy, backend behavior, deployment configuration and tests remain to be reviewed. Requirements are listed in `critique.json`; they are pending checks, not asserted implementation defects. No final release hashes or approval have been issued.

Source signatures were not authenticated; the administrative databases were not audited; catalogued-only URLs and all upstream CSV claims were not fact-verified. No private chat, case file, credential, full third-party article or raw source binary is published with this review.
"""
(OUT / "review.md").write_text(md,encoding="utf-8",newline="\n")
print(json.dumps({"status":report["status"],"dataset_sha256":sha,"numeric_cells":len(data["observations"]),"snapshots":len(parsed),"findings":len(findings),"release_approval":False}))
