"""Independent JSON-stat coordinate check for the 15 new context cells."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
CACHE=ROOT.parent/'source-cache'/'round2'/'blobs'
file=ROOT/'research/round2-data/eurostat-context.json'
data=json.loads(file.read_text(encoding='utf8'))
raw={}
records=[]
errors=[]
for s in data['sources']:
    content=(CACHE/(s['content_sha256']+'.bin')).read_bytes()
    assert hashlib.sha256(content).hexdigest()==s['content_sha256']
    d=json.loads(content)
    assert d['class']=='dataset' and d['source']=='ESTAT'
    raw[s['id']]=d
for o in data['observations']:
    d=raw[o['source_id']]
    coordinates={'freq':'A','reason':'TOTAL','citizen':o['citizenship_code'],
                 'duration':'TOTAL','unit':'PER','geo':o['geography_id'],
                 'time':o['reference_period']}
    index=0
    for dimension, size in zip(d['id'],d['size']):
        cats=d['dimension'][dimension]['category']['index']
        position=cats.index(coordinates[dimension]) if isinstance(cats,list) else cats[coordinates[dimension]]
        index=index*size+position
    values=d['value']
    value=values[index] if isinstance(values,list) else values.get(str(index))
    status=d.get('status',{})
    flag=status[index] if isinstance(status,list) else status.get(str(index))
    actual={'id':o['id'],'coordinates':coordinates,'flat_index':index,'source_value':value,
            'source_flag':flag,'value_matches':o['value']==value,'flag_matches':o['flags']==flag,
            'locator_matches':f'value[{index}]' in o['source_locator']}
    records.append(actual)
    if not all(actual[k] for k in ['value_matches','flag_matches','locator_matches']): errors.append(actual)
assert len(records)==15
assert len({r['id'] for r in records})==15
assert {r['coordinates']['time'] for r in records}=={'2021','2022','2023','2024','2025'}
report={'checked_at':datetime.now(timezone.utc).isoformat(),'status':'pass' if not errors else 'mismatch',
        'reviewed_file_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
        'observations_checked':len(records),'source_snapshots_checked':len(raw),'errors':errors,
        'records':records,
        'source_checks':[{'id':s['id'],'url':s['url'],'content_sha256':s['content_sha256'],'dataset_updated':raw[s['id']]['updated']} for s in data['sources']],
        'interpretation_review':{
            'category':'context-not-waiting',
            'scope':'First residence permits under Eurostat collection definitions; not administrative applications, pending stocks, individual waiting times, or the same scope as voivode temporary-residence resolutions.',
            'citizenship':'BY is citizenship, not ethnicity. TOTAL is the total within the non-EU permit collection, not all migrants.',
            'geography':'EU27_2020 includes Poland; do not add EU total to Poland.',
            'dates':'2021–2025 reference years; year-end dates are period endpoints, not a stock date or source retrieval date.',
            'flags':'Checked as returned; no flag does not establish no breaks or revisions.',
            'definition':'Authorisation to stay at least three months; first may follow a gap of at least six months. National long-stay visas/equivalent authorisations may be counted; first does not necessarily mean a first-ever arrival.',
            'metadata_url':'https://ec.europa.eu/eurostat/cache/metadata/en/migr_resval_esms.htm'},
        'release_approval':False}
(OUT/'eurostat-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'status':report['status'],'checked':len(records),'errors':len(errors),'values':[r['source_value'] for r in records]}))
