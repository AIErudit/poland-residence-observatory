"""Check actual public artifacts against the reviewed cells and claim texts."""
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
def read(p):return (ROOT/p).read_text(encoding='utf8')
def js(p):return json.loads(read(p))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
errors=[]
def expect(ok,reason):
    if not ok:errors.append(reason)
data=js('data/curated/dataset.json')
public=js('docs/data/dataset.json')
expect(data==public,'Public dataset differs from curated dataset')
rows=list(csv.DictReader(read('docs/data/observations.csv').splitlines()))
expect(len(rows)==len(data['observations']),'CSV observation count')
by_id={r['id']:r for r in rows}
expect(len(by_id)==len(rows),'CSV duplicate observation IDs')
for o in data['observations']:
    r=by_id.get(o['id'])
    if r is None:errors.append('Missing CSV ID '+o['id']);continue
    if o['value'] is None:ok=r['value']==''
    else:
        try:ok=math.isclose(float(r['value']),o['value'],rel_tol=0,abs_tol=1e-6)
        except ValueError:ok=False
    expect(ok,'CSV numeric cell '+o['id'])
    for key in ['series_id','indicator_id','geography_id','unit','source_id','source_locator','definition_id','quality_status']:
        expect(r[key]==str(o[key]),'CSV metadata '+key+' '+o['id'])
claims=js('site/claims.json')
expect(claims==js('docs/data/claims.json'),'Public claims differ from site claims')
expect(len(claims)==4,'Expected original four public claims')
facts=[]
for c in claims:
    path='docs/facts/'+c['id']+'/index.html'
    html=BeautifulSoup(read(path),'html.parser')
    actual_langs=[x['data-locale'] for x in html.select('[data-locale]')]
    expect(set(actual_langs)=={'pl','be','en'} and len(actual_langs)==3,'Fact locales '+c['id'])
    for lang in ['pl','be','en']:
        block=html.select_one('[data-locale='+lang+']')
        expect(block is not None,'Missing locale '+c['id']+' '+lang)
        if block is None:continue
        text=block.get_text(' ',strip=True)
        citation=block.select_one('.citation').get_text(' ',strip=True)
        for field in ['title','body','caveat']:
            expect(c[field+'_'+lang] in text,'Fact '+field+' '+c['id']+' '+lang)
            expect(c[field+'_'+lang] in citation,'Citation '+field+' '+c['id']+' '+lang)
        expect('?lang='+lang in citation,'Citation locale URL '+c['id']+' '+lang)
        expect(data['version'] in citation,'Citation version '+c['id']+' '+lang)
    for key in ['description','og:description']:
        tag=html.find('meta',attrs={'name':key}) if key=='description' else html.find('meta',attrs={'property':key})
        expect(bool(tag) and c['caveat_pl'] in tag.get('content',''),'Canonical metadata preserves caveat '+c['id']+' '+key)
    facts.append({'claim_id':c['id'],'languages':['pl','be','en'],'file_sha256':sha(path)})
for p in ['docs/index.html','docs/survey/index.html','docs/privacy/index.html']:
    soup=BeautifulSoup(read(p),'html.parser')
    expect({x['data-lang'] for x in soup.select('[data-lang]')}=={'pl','be','en'},'Language controls '+p)
    expect(not soup.select('[data-locale=ru]'),'Russian public locale block '+p)
    for s in soup.select('script[src]'):
        expect(not s['src'].startswith(('http:','https:','//')),'Initial external script '+p)
context=js('docs/data/eurostat-context.json')
expect(context['observations']==js('research/round2-data/eurostat-context.json')['observations'],'Public Eurostat observations differ')
expect(len(context['observations'])==15,'Public Eurostat count')
for name,folder in [('banking','round2-law'),('actions','round2-law'),('offices','round2-data'),('provenance-audit','round2-data')]:
    expect(js('docs/data/'+name+'.json')==js('research/'+folder+'/'+name+'.json'),'Public research content differs: '+name)
privacy=js('site/privacy-content.json')
html=BeautifulSoup(read('docs/privacy/index.html'),'html.parser')
for lang in ['pl','be','en']:
    block=html.select_one('[data-locale='+lang+']')
    expect(block is not None,'Privacy language '+lang)
    if block:
        text=block.get_text(' ',strip=True)
        for heading,body in privacy[lang]['sections']:
            expect(heading in text and body in text,'Privacy section '+lang+' '+heading)
for name in ['app.js','analytics.js','i18n.js','page.js','survey.js','style.css']:
    expect(sha('site/'+name)==sha('docs/assets/'+name),'Public asset differs from reviewed source: '+name)
result={'checked_at':datetime.now(timezone.utc).isoformat(),'status':'pass' if not errors else 'fail','errors':errors,
        'dataset_version':data['version'],'dataset_sha256':sha('data/curated/dataset.json'),
        'public_observations_checked':len(rows),'eurostat_cells_checked':len(context['observations']),
        'facts_checked':facts,'claim_ids':[c['id'] for c in claims],
        'public_numeric_files_identical_to_reviewed_inputs':not errors,
        'limits':['This is an artifact/content check, not browser interaction or a production survey submission.','Dynamic PL/BE/EN wording was separately read; this script checks the server-rendered fact blocks and public downloads.','Canonical HTML/social metadata is Polish; query-parameter localization renders after JavaScript. This is not a promise of localized crawler previews.'],
        'release_approval':False}
(OUT/'public-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'status':result['status'],'csv_cells':len(rows),'facts':len(facts),'errors':errors}))
