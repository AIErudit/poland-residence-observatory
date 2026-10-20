"""Read-only checks of generated static HTML and downloadable aggregates.

This does not replace browser/UI review or approve publication.
"""
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import csv
import io
import json
import re
import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8766/'
data = json.loads((ROOT/'data/curated/dataset.json').read_text(encoding='utf-8'))
claims = json.loads((ROOT/'site/claims.json').read_text(encoding='utf-8'))
issues = []
http_checks = []

def verify(ok, description):
    if not ok:
        issues.append(description)

for route in ['', 'data/dataset.json', 'data/observations.csv'] + ['facts/'+c['id']+'/' for c in claims]:
    r = requests.get(BASE+route, timeout=20)
    verify(r.status_code == 200, f'HTTP {r.status_code}: {route}')
    entry = {'route':route, 'status':r.status_code}
    if route.startswith('facts/'):
        c = next(c for c in claims if c['id'] in route)
        soup = BeautifulSoup(r.content, 'html.parser')
        text = soup.get_text(' ', strip=True)
        for key in ['body_pl','caveat_pl','body_ru','caveat_ru']:
            entry[key+'_present'] = c[key] in text
            verify(entry[key+'_present'], f'Missing {key} in fact {c["id"]}')
        for key, field in [('og:title','title_pl'),('og:description','caveat_pl')]:
            meta = soup.find('meta',property=key)
            verify(bool(meta) and meta.get('content') == c[field], f'Wrong {key}: {c["id"]}')
    elif route == 'data/dataset.json':
        verify(r.json() == data, 'Served dataset differs from curated dataset')
    elif route.endswith('.csv'):
        records = list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig'))))
        entry['rows'] = len(records)
        verify(len(records) == len(data['observations']), 'CSV/JSON row counts differ')
        verify({o['id'] for o in records} == {o['id'] for o in data['observations']}, 'CSV/JSON observation IDs differ')
        by_id = {o['id']:o for o in data['observations']}
        for record in records:
            o = by_id[record['id']]
            for key in ['source_id','reference_period','unit','indicator_id']:
                verify(record[key] == str(o[key]), f'CSV {key} differs for {o["id"]}')
            verify((record['value'] == '' and o['value'] is None) or
                   (o['value'] is not None and float(record['value']) == o['value']),
                   f'CSV value differs for {o["id"]}')
    else:
        verify(not re.search(r'__(?:METRICS|FACTS)__',r.text), 'Template markers remain')
        verify('AI' in BeautifulSoup(r.content,'html.parser').get_text(' ',strip=True), 'AI review disclosure absent')
    http_checks.append(entry)

for name, expected in [('observations.json', data['observations']),('sources.json',data['sources']),
                       ('definitions.json',data['definitions']),('geographies.json',data['geographies']),
                       ('claims.json',claims)]:
    actual = json.loads((ROOT/'docs/data'/name).read_text(encoding='utf-8'))
    verify(actual == expected, f'Public {name} differs from curated source')

patterns = [r'[A-Z]:\\',r'file://',r'ChatExport_',r'messages[0-9]+\.html',
            r'BEGIN (?:RSA |OPENSSH )?PRIVATE KEY']
public_files = []
for path in (ROOT/'docs').rglob('*'):
    if not path.is_file():
        continue
    public_files.append(path.relative_to(ROOT).as_posix())
    if path.suffix in ['.pdf','.xlsx','.xls','.zip','.docx']:
        issues.append(f'Raw binary document unexpectedly in public docs: {path.name}')
    if path.suffix in ['.json','.html','.csv','.md','.py','.js','.css']:
        text = path.read_text(encoding='utf-8',errors='replace')
        for pattern in patterns:
            verify(not re.search(pattern,text), f'Private-path/secret marker in {path.relative_to(ROOT)}: {pattern}')

result = {
    'checked_at': datetime.now(timezone.utc).isoformat(),
    'status':'pass_static_artifact_checks' if not issues else 'blocking_issues',
    'claim_ids':[c['id'] for c in claims],
    'http_checks':http_checks,
    'public_files':sorted(public_files),
    'issues':issues,
    'limits':['No browser interaction/visual viewport checks in this script; editor performs UI QA.',
              'Marker scan is not a comprehensive security or personal-data certification.',
              'Numbers are source-reconciled separately; catalogue entries are not all fact-verified.',
              'Overall release scope and immutable file hashes are recorded separately in release.json.']
}
(ROOT/'verification/public-artifact-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(result,ensure_ascii=False))
