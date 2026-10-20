"""Seal the explicit scoped review only after the maintainer's freeze signal.

Never builds or edits audited data, frontend, backend, research or Git state.
Generated docs/verification files and release.json itself are excluded to avoid
recursive/self-referential hashes when the maintainer copies this review.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
EXPECTED_DATASET='8d1f0c6b081b75ebfa24aebbfaccf234f0c51755a7f1faa11c40f6010bd1b995'
EXPECTED_BACKEND='60bb06396b710bd3eb97191a6213f2986c42b3cd84c3767323d6d93d2b407837'
CLAIMS=['silesia-658','fifteen-regions','pending-803223','courts-merits-2025']

def read(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze-confirmed',action='store_true');a=ap.parse_args()
    if not a.freeze_confirmed:raise SystemExit('A maintainer freeze signal is required; no approval written.')
    now=datetime.now(timezone.utc).isoformat()
    assert sha('data/curated/dataset.json')==EXPECTED_DATASET
    assert sha('backend/worker.mjs')==EXPECTED_BACKEND
    d=read('data/curated/dataset.json');assert d['version']=='1.1.0'
    numeric=read('verification/round2/numeric-recheck.json')
    public=read('verification/round2/public-check.json')
    backend=read('verification/round2/backend-check.json')
    eurostat=read('verification/round2/eurostat-check.json')
    assert numeric['dataset_sha256']==public['dataset_sha256']==EXPECTED_DATASET
    assert numeric['total_numeric_observations_reconciled']==1780 and not numeric['issues']
    assert public['status']=='pass' and not public['errors']
    assert backend['status']=='pass_synthetic_scope' and backend['checks']==14
    assert backend['file_sha256']['backend/worker.mjs']==EXPECTED_BACKEND
    assert eurostat['status']=='pass' and eurostat['observations_checked']==15
    assert set(CLAIMS)=={x['id'] for x in read('site/claims.json')}
    survey=(ROOT/'site/survey.js').read_text(encoding='utf8')
    assert "state.phase === 'restored' && !state.attempt" in survey
    assert 'without identifying details' not in survey
    assert "['unexamined'" in survey
    privacy=read('site/privacy-content.json')
    for lang in ['pl','be','en']:
        text=json.dumps(privacy[lang],ensure_ascii=False)
        assert '2021/914' in text and '12' in text
    assert 'зыры IP' not in json.dumps(privacy,ensure_ascii=False)

    critique=read('verification/round2/critique.json')
    critique.update(status='completed_scoped_review_v1.1.0',checked_at=now,dataset_sha256=EXPECTED_DATASET,
                    release_approval=True,phase_3_status='completed_scoped_source_content_and_behavior_review',
                    final_scope_file='verification/round2/release.json')
    for f in critique['findings']:
        if f['id']=='R2-N08':
            f['status']='resolved_primary_dictionary_checked'
            f['final_disposition']='Official caseType dictionary independently read and hash-checked; see phase3-review.json.'
        elif f['id'] in ['R2-B01','R2-B02']:
            f['final_disposition']='New published banking copy preserves the stated limits; the upstream-overstatement risk is avoided.'
        elif f['id']=='R2-B03':
            f['final_disposition']='Full official judgment paragraphs34–56 independently reviewed; new copy remains calibrated. See phase3-review.json.'
        else:f['final_disposition']='Confirmed within its stated scope or retained as a disclosed source/inference limitation.'
    critique['resolved_additional_findings']=[
        {'id':'R2-N09','resolution':'General duration metadata no longer asserts a submission start-event for MSWiA18089; endpoints are source-specific.'},
        {'id':'R2-P03','resolution':'445458 is described as forecast prose;445462 as inspected CSV/API; no historical snapshot/revision cause is asserted.'},
        {'id':'R2-S01','resolution':'Idempotent receipts and stable fingerprints tested, including a lost response and midnight retry.'},
        {'id':'R2-S02','resolution':'Versioned response/contact consent and timestamps retained and tested.'}
    ]
    write('critique.json',critique)
    part=read('verification/round2/phase3-review.json')
    part.update(status='completed_scoped_phase_3_review',checked_at=now,release_approval=True,
                final_scope_file='verification/round2/release.json')
    for f in part['findings_pending_or_to_recheck']:
        f['status']='resolved_or_scoped_in_final_review'
    part['not_yet_reviewed']=['Positive production browser Turnstile-to-insert journey; this remains explicitly unobserved.',
                             'Actual future operator handling of real responses, correspondence, disclosure review and provider logs/backups.',
                             'Administrative database truth/completeness, original signatures, catalogued-only URLs and every upstream CSV/research claim.']
    part['backend']['independent_synthetic_checks']=14
    part['backend']['tested_file_sha256']=backend['file_sha256']
    part['reviewed_research_file_sha256']={p:sha(p) for p in part['reviewed_research_file_sha256']}
    part['final_public_content_check']='verification/round2/public-check.json'
    part['independence_and_limits']='Separate AI reviewer from the authors of audited data/code. Source/content and synthetic behavior checks, supplemented by operator browser/deployment evidence; not external certification, a legal opinion, penetration test or administrative database audit. Exact scope and remaining limits are in release.json.'
    write('phase3-review.json',part)
    ui=read('verification/round2/ui-privacy-findings.json')
    ui.update(status='completed_recheck_no_blocking_findings',checked_at=now,release_approval=True,
              final_scope_file='verification/round2/release.json')
    for f in ui['findings']:
        if f['id']=='R2-U04':
            f['status']='accepted_nonblocking_lifecycle_limit'
            f['resolution']='Static config enables the form; the reviewed deployment is enabled. Later availability is still checked by the actual submission result, not a continuous health monitor. Errors never claim successful acceptance.'
        elif f['id']=='R2-U07':f['status']='accepted_disclosed_limitation'
        else:f['status']='resolved_rechecked'
    ui['file_sha256_at_final_recheck']={p:sha(p) for p in ui['file_sha256_at_recording']}
    ui['limits']=['Exact scope is in release.json. Earlier evidence describes the initial ready-for-review copy; resolved findings are retained for traceability.',
                  'Belarusian substantive equivalence was checked by an AI reviewer; no native-human editorial certification is claimed.']
    write('ui-privacy-findings.json',ui)

    review='''# Round 2 — scoped approval of v1.1.0

As of 20 October 2026. A separate AI reviewer found no unresolved blocking finding in the frozen v1.1.0 snapshot. [release.json](release.json) records the exact file hashes, four claim IDs and scope. This is a source/content and functional review, not external certification, a legal opinion, a security audit or authentication of signed originals.

The core dataset contains **1,780 normalized indicator cells**; all were independently reconciled to the original **32 acquired/supporting snapshots** or stated formulas. A separate Eurostat context layer contains **15 cells**, independently checked through JSON-stat coordinates, values, flags and locators in two official API snapshots. Public JSON/CSV and all four permanent fact pages preserve the checked values and PL/BE/EN limitations. The reviewed core is v1.1.0, SHA-256 `8d1f0c6b081b75ebfa24aebbfaccf234f0c51755a7f1faa11c40f6010bd1b995`.

## Meaning and provenance

The original core builds on Głos Migranta's source collection: 24 official-publisher snapshots and eight public copies. Our normalization and calculations are not new primary fieldwork. The 1,483-entry register includes 1,451 catalogued-only records; 6,625 structurally profiled upstream CSV rows were not all fact-verified. Neither links nor normalized cells are counts of independently sampled people.

Concluded means exclude ongoing cases and are not personal forecasts; regional means do not create a weighted national mean. MSWiA's exact starting event remains unspecified. UdSC regional labels remain reconstructed because the copy hides them; the national sum does not require names. The 48 warehouse2026 cells retain unknown cut-offs and are excluded from annual scenario baselines. Staff ratios, stocks and flows have different units/cohorts. Court6272 is broader than residence permits; merits shares exclude procedural dispositions and do not predict individual success. Adjacent NSA stocks differ by one case twice, for an unknown reason. Scenarios remain conditional arithmetic. Eurostat is context, not waiting time, and EU27 includes Poland.

The corrected 445,458 attribution concerns forecast prose; inspected CSV/API values are 445,462. An old CSV, revision or cause for the four-case difference has not been established. [Structured critique](critique.json), [numeric reconciliation](numeric-recheck.json), [Eurostat check](eurostat-check.json), [public artifact check](public-check.json).

## Banking, survey and privacy

PL/BE/EN banking/actions wording preserves basic-account versus commercial-account scope, AML/sanctions exceptions, exact document types, separate complaint deadlines and institutional roles. TZTC is not an ordinary application receipt. Jenec is used within its specific holding, not as a guarantee against every existing-account restriction. Published bank policies are not findings that every restriction is lawful. Residence/travel wording preserves statutory conditions and case-specific remedies. [Phase3 evidence](phase3-review.json).

The voluntary survey distinguishes completed durations from ongoing elapsed ages, does not promise representativeness or anonymity, collects no unrestricted narratives/files, and keeps optional encrypted contact separate. The notice identifies the confirmed controller, purpose, consent, safeguards, retention, provider recovery history, rights and manual correspondence duties. Receipt clearing and restored-state behavior were corrected; clearing a local receipt is separate from server deletion. Canonical crawler/social metadata remains Polish; PL/BE/EN article content renders in the browser. Belarusian meaning was reviewed by AI; no native-human certification is claimed.

The independent backend harness passed **14 synthetic checks**, including retry idempotency, date/consent/field validation, contact encryption, wrong Turnstile hostname/action, database failure, access rejection, deletion, expiry and the unexamined outcome. Default test execution does not rewrite its report. Public read-only health/401/403 checks were reproduced. The operator separately supplied real D1 synthetic insertion/deletion back to zero, EU-jurisdiction/configuration and browser QA evidence. No real personal response was used in this review. The private aggregate helper separates pending/concluded cases and requires reviewed rows, minimum cells and a further human disclosure/consent review; no survey aggregates are published in this release.

## Remaining limits

A positive production browser Turnstile→insert journey was **not observed**; mocked Siteverify and a real D1 fixture/deletion test are different evidence. Provider settings/secret bindings, EU jurisdiction and browser screenshots were supplied by the operator, rather than independently accessed with private credentials. Requested observability=false is distinguished from the API's unconfigured/null readback; application code does not log payloads. No penetration test, provider log/backup audit, cryptographic signature authentication or administrative database audit was performed.

Future operator access, consent withdrawals, correspondence deletion, recovery handling and aggregate disclosure require the documented manual duties. Ten responses per group do not establish anonymity or representativeness. Approval applies to the exact hashed files and the stated scope, not every catalogue URL, historical research memo, upstream CSV row, future response or later amendment. Changed evidence or code requires a new review. Generated `docs/verification/` copies and this approval JSON are excluded from its hash map to avoid recursive hashes.
'''
    (OUT/'review.md').write_text(review,encoding='utf8',newline='\n')

    tops=['.agents','.github','backend','data/curated','docs','docs-research','research','coverage','site','scripts','tests','qa','verification/round2']
    files=set()
    for top in tops:
        for p in (ROOT/top).rglob('*'):
            rel=p.relative_to(ROOT).as_posix()
            if not p.is_file() or '__pycache__' in p.parts:continue
            if rel.startswith('docs/verification/') or rel in {'verification/round2/release.json','docs/manifest.json'}:continue
            if rel=='backend/wrangler.jsonc' or p.name.startswith('.dev.vars'):continue
            if p.suffix.lower() in {'.json','.jsonc','.md','.py','.mjs','.js','.html','.css','.csv','.sql','.svg','.png','.txt','.yml','.yaml','.xml'} or p.name=='.nojekyll':files.add(rel)
    for name in ['README.md','AGENTS.md','CHANGELOG.md','DATA-LICENSE.md','LICENSE','.gitignore']:
        if (ROOT/name).is_file():files.add(name)
    hashes={p:sha(p) for p in sorted(files)}
    release={'status':'approved','version':'1.1.0','as_of':'2026-10-20','checked_at':now,
             'claim_ids':CLAIMS,'file_sha256':hashes,'release_approval':True,
             'core_dataset_sha256':EXPECTED_DATASET,'backend_sha256':EXPECTED_BACKEND,
             'scope':{'core_numeric_observations':1780,'core_acquired_or_supporting_snapshots':32,
                      'core_source_provenance':{'official_publisher':24,'public_official_document_copy':8},
                      'separate_eurostat_context_cells':15,'eurostat_api_snapshots':2,
                      'official_udsc_case_type_dictionary':'checked',
                      'public_claim_pages':CLAIMS,'public_languages':['pl','be','en'],
                      'backend_independent_synthetic_checks':14,
                      'privacy_and_legal':'Calibrated public wording and actual processing flow checked; not certification.',
                      'survey_aggregates_published':False},
             'blocking_findings':[],
             'evidence_files':['verification/round2/numeric-recheck.json','verification/round2/eurostat-check.json',
                               'verification/round2/public-check.json','verification/round2/backend-check.json',
                               'verification/round2/deployment-readcheck.json','verification/round2/phase3-review.json',
                               'verification/round2/ui-privacy-findings.json','verification/round2/final-checks.json',
                               'qa/round2-browser.json','qa/backend-deployment.json','qa/backend-live.json','qa/backend-launch.json'],
             'remaining_unverified_scope':[
                 'All catalogued-only URLs, every upstream CSV row and every historical research-memo claim were not independently fact-verified in this round.',
                 'Administrative-source completeness/truth, original signatures and direct regional labels hidden in the UdSC copy were not established.',
                 'Positive production browser Turnstile-to-insert journey not observed; no real personal response submitted.',
                 'Private deployment settings, binding values/EU jurisdiction and browser QA are operator-supplied evidence; public health/access rejection and code behavior were separately checked.',
                 'No external legal certification, penetration test, provider log/backup audit or native-human Belarusian review.',
                 'Operator browser QA checked citation DOM/success; actual cross-application clipboard paste was not independently established.',
                 'Future manual privacy duties, actual respondent accuracy/uniqueness, representativeness and safety of future aggregates require further review.'],
             'hash_boundary':'Hash identity freezes the listed bytes; it does not expand factual endorsement beyond scope. Excludes release.json itself, generated docs/verification/ copies/index and the generated docs/manifest.json. Manifest stable dataset/version/claim fields were checked separately; generated review copies are built afterward.',
             'review_file':'verification/round2/review.md'}
    write('release.json',release)
    print(json.dumps({'status':'approved','version':'1.1.0','hashed_files':len(hashes),'core_cells':1780,'eurostat_cells':15,'backend_checks':14,'blocking_findings':0}))

if __name__=='__main__':main()
