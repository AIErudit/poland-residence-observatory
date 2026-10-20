"""Separate verification of curated values against independently read sources.

Reads project artifacts, writes only verification/curated-check.json. This is a
scoped source reconciliation, not certification of every observation or URL.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'data/curated/dataset.json').read_text(encoding='utf-8'))
claims = json.loads((ROOT / 'site/claims.json').read_text(encoding='utf-8'))
base = json.loads((ROOT / 'verification/baseline.json').read_text(encoding='utf-8'))
observations = data['observations']
by_id = {o['id']: o for o in observations}
sources = {s['id']: s for s in data['sources']}
geos = ['PL-DS','PL-KP','PL-LU','PL-LB','PL-LD','PL-MA','PL-MZ','PL-OP',
        'PL-PK','PL-PD','PL-PM','PL-SL','PL-SK','PL-WN','PL-WP','PL-ZP']
issues = []
checks = Counter()
verified_observation_ids = set()

def verify(condition, message):
    if not condition:
        issues.append(message)

def check_value(series, geo, year, indicator, value):
    matches = [o for o in observations if o['series_id'] == series and
               o['geography_id'] == geo and str(o['reference_period'])[:4] == str(year)
               and o['indicator_id'] == indicator]
    verify(len(matches) == 1, f'Cardinality: {series}/{geo}/{year}/{indicator}: {len(matches)}')
    if len(matches) != 1:
        return
    o = matches[0]
    equal = o['value'] == value if value is None or isinstance(value, int) else (
        isinstance(o['value'], (int, float)) and math.isclose(o['value'], value, rel_tol=0, abs_tol=0.000001))
    verify(equal, f"Value: {o['id']} {series}/{geo}/{year}/{indicator}: {o['value']} != {value}")
    checks[series] += 1
    if equal:
        verified_observation_ids.add(o['id'])

for i, row in enumerate(base['tables']['mswia18089_means_days']):
    for year in range(2023, 2027):
        check_value('mswia_18089_concluded_mean_days', geos[i], year,
                    'processing_duration_mean_days', row[str(year)])
    for date, value in base['tables']['udsc_copy_rows'][i]['pending'].items():
        check_value('udsc_20260828_pending_stock', geos[i], date[:4], 'pending_cases', value)
        matching = [o for o in observations if o['series_id'] == 'udsc_20260828_pending_stock'
                    and o['geography_id'] == geos[i] and str(o['reference_period'])[:4] == date[:4]]
        for o in matching:
            verify(o['as_of_date'] == date and o['reference_period'] == date,
                   f"Stock date: {o['id']} differs from {date}")
    for year in range(2023, 2027):
        expected = row[str(year)] if year < 2026 else base['tables']['udsc_copy_rows'][i]['mean2026']
        if year == 2024 and i == 3:
            expected = 406
        if year == 2024 and i == 15:
            expected = 471
        check_value('udsc_20260828_concluded_mean_days', geos[i], year,
                    'processing_duration_mean_days', expected)

for annual in base['tables']['nsa_6272_annual']:
    rows = [('PL', annual['national'])] + [('WSA-' + r['sheet'], r) for r in annual['courts']]
    for geo, r in rows:
        for ind, key in [('court_inflow','incoming'), ('court_resolved','disposed'),
                         ('court_upheld','granted'), ('court_dismissed','dismissed_merits'),
                         ('court_rejected','rejected_procedural'),
                         ('court_upheld_merits_pct','merits_granted_pct')]:
            check_value('nsa_wsa_6272_annual', geo, annual['year'], ind, r[key])
        rejected_share = 100 * r['rejected_procedural'] / r['disposed'] if r['disposed'] else None
        check_value('nsa_wsa_6272_annual', geo, annual['year'], 'court_rejected_resolved_pct', rejected_share)

for annual in base['tables']['warehouse_copy_outcomes']:
    for i, row in enumerate(annual['rows']):
        check_value('warehouse_all_outcomes', geos[i], annual['year'], 'concluded_resolutions', row['outcomes'])
        check_value('warehouse_all_outcomes', geos[i], annual['year'], 'processing_duration_mean_days', row['mean_days'])

# Copy SOC-III.1331.2.2026, 25.08.2026, page2 point2 and page3 point5;
# independently fetched and read during final verification, not taken from pipeline.
for i, year in enumerate(range(2023, 2027)):
    stock = [27179,27016,33979,49844][i]
    workers = [37,38,36,38][i]
    check_value('lodz_pending_stock','PL-LD',year,'pending_cases',stock)
    check_value('lodz_caseworkers','PL-LD',year,'caseworkers',workers)
    check_value('lodz_staff_headcount','PL-LD',year,'staff_headcount',[88,90,82,83][i])
    check_value('lodz_pending_per_caseworker','PL-LD',year,'pending_per_caseworker',stock/workers)

verify(len(by_id) == len(observations), 'Duplicate observation IDs')
verify(len(sources) == len(data['sources']), 'Duplicate source IDs')
for o in observations:
    verify(o['source_id'] in sources, f"Missing source for {o['id']}")
    for ref in (o.get('denominator') or {}).get('observation_ids', []):
        verify(ref in by_id, f"Missing denominator reference {ref}")
for c in claims:
    verify(all(i in by_id for i in c['observation_ids']), f"Claim {c['id']} missing observations")
    verify(set(c['source_ids']) == {by_id[i]['source_id'] for i in c['observation_ids']},
           f"Claim {c['id']} source references inconsistent")
    verify(set(c['observation_ids']) <= verified_observation_ids,
           f"Claim {c['id']} includes values not independently reconciled")

expected_claims = {'silesia-658':658,'fifteen-regions':15,
                   'pending-803223':803223,'courts-merits-2025':29.5}
verify({c['id'] for c in claims} == set(expected_claims), 'Unexpected public claim IDs')
for c in claims:
    verify(c['value'] == expected_claims.get(c['id']), f"Wrong claim value {c['id']}")

result = {
    'checked_at': datetime.now(timezone.utc).isoformat(),
    'status': 'pass_scoped_reconciliation' if not issues else 'blocking_issues',
    'dataset_sha256': hashlib.sha256((ROOT/'data/curated/dataset.json').read_bytes()).hexdigest(),
    'claim_ids': [c['id'] for c in claims],
    'checks_by_series': dict(checks),
    'distinct_observations_reconciled': len(verified_observation_ids),
    'issues': issues,
    'limits': [
        'Copy values reconciled to publicly available copies; original signatures not authenticated.',
        'UdSC regional names are reconstructed; the pending national sum does not depend on names.',
        'Blue Card, maximum-duration, remaining Lodz warehouse and other non-core rows are not all independently reparsed here.',
        'Catalogue URLs are not all fact-verified; structural checks are separate.',
        'This core reconciliation is supplemented by check_remaining.py; overall release scope is recorded separately in release.json.'
    ]
}
(ROOT/'verification/curated-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(result,ensure_ascii=False))
