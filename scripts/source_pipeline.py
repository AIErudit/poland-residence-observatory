"""HTTP snapshots live outside the public repository. No credentials required."""
from __future__ import annotations
import concurrent.futures,hashlib,json,os,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
CACHE=Path(os.environ.get('OBSERVATORY_CACHE',str(ROOT.parent/'source-cache'/'observatory')))
SEED_URLS=[
 'https://glos-migranta.eu/raporty/szesnascie-urzedow-w-liczbach',
 'https://glos-migranta.eu/dane',
 'https://glos-migranta.eu/fakty',
 'https://glos-migranta.eu/raporty/prognoza']
PRIMARY_EXTRA=[
 ('https://www.nsa.gov.pl/dokumenty/statystyki-wsa/','NSA: Statystyki WSA'),
 ('https://www.nik.gov.pl/aktualnosci/sprawy-spoleczne/obsluga-paszportowa-cudzoziemcow-wroclaw.html','NIK: obsługa cudzoziemców we Wrocławiu, 11.12.2025'),
 ('https://www.nik.gov.pl/najnowsze-informacje-o-wynikach-kontroli/obsluga-cudzoziemcow.html','NIK: obsługa cudzoziemców'),
 ('https://www.nik.gov.pl/plik/id,28951,vp,31783.pdf','NIK: informacja LLO.430.2.2023'),
 ('https://bip.brpo.gov.pl/sites/default/files/2026-08/Odpowiedz_MSWiA_cudzoziemcy_legalizacja_pobytu_przewleklosc_30_06_2026.pdf','MSWiA do RPO, 30.06.2026'),
 ('https://bip.brpo.gov.pl/sites/default/files/2026-08/Odpowiedz_MSWiA_cudzoziemcy_legalizacja_pobytu_przewleklosc_12_08_2026.pdf','MSWiA do RPO, 12.08.2026'),
 ('https://www.zus.pl/en/baza-wiedzy/statystyka/opracowania-tematyczne/cudzoziemcy','ZUS: Cudzoziemcy - opracowania tematyczne'),
 ('https://psz.zus.pl/kategorie/ubezpieczeni/ubezpieczenia-emerytalne-i-rentowe','ZUS: ubezpieczeni - dane do pobrania'),
 ('https://orzeczenia.nsa.gov.pl/doc/953FE35D2F','NSA II OSK 2038/25, 09.04.2026'),
]
def utcnow():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def sid(url):return 'src_'+hashlib.sha256(url.encode()).hexdigest()[:12]
def jwrite(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');tmp.replace(path)
def manifest():
 p=CACHE/'manifest.json';return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
def snapshot(url,refresh=False):
 old=manifest().get(url)
 if old and not refresh and old.get('status')==200 and (CACHE/old['file']).exists():return old
 record={'url':url,'retrieved_at':utcnow()}
 try:
  resp=requests.get(url,timeout=(12,50),headers={'User-Agent':'PolandResidenceObservatory/1.0 (+public-interest-research)'})
  record.update(status=resp.status_code,final_url=resp.url,content_type=resp.headers.get('Content-Type',''),etag=resp.headers.get('ETag'),last_modified=resp.headers.get('Last-Modified'))
  data=resp.content;sha=hashlib.sha256(data).hexdigest();path=Path('blobs')/(sha+'.bin');(CACHE/path).parent.mkdir(parents=True,exist_ok=True);(CACHE/path).write_bytes(data)
  record.update(content_sha256=sha,file=path.as_posix(),bytes=len(data))
 except requests.RequestException as e:record.update(status=None,error=str(e))
 return record
def fetch_many(urls,refresh=False):
 urls=sorted(set(urls));CACHE.mkdir(parents=True,exist_ok=True)
 existing=manifest()
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for rec in pool.map(lambda u:snapshot(u,refresh=refresh),urls):existing[rec['url']]=rec
 jwrite(CACHE/'manifest.json',existing)
 return existing
def content(url):
 rec=manifest().get(url)
 if not rec or rec.get('status')!=200:raise ValueError('No successful cached snapshot: '+url)
 data=(CACHE/rec['file']).read_bytes()
 if hashlib.sha256(data).hexdigest()!=rec['content_sha256']:raise ValueError('Cached bytes do not match snapshot SHA256: '+url)
 return data
def links(url):
 soup=BeautifulSoup(content(url),'html.parser')
 return [{'url':urljoin(url,a['href']).split('#')[0],'title':a.get_text(' ',strip=True)} for a in soup.select('a[href]') if not a['href'].startswith(('#','mailto:','tel:'))]
def direct_document(url):return bool(re.search(r'\.(?:pdf|xlsx?|csv|zip|md)(?:\?|$)|api\.sejm\.gov\.pl|InterpelacjaTresc|statystyki-wsa',url,re.I))
def discover(refresh=False):
 fetch_many(SEED_URLS+[x[0] for x in PRIMARY_EXTRA],refresh)
 catalog={}
 for url in SEED_URLS:
  catalog[url]={'url':url,'title':BeautifulSoup(content(url),'html.parser').title.get_text(' ',strip=True),'discovered_on':[],'kind':'editorial_page'}
  for link in links(url):
   external=urlparse(link['url']).netloc not in ['glos-migranta.eu','www.glos-migranta.eu']
   sharing=any(k in link['url'] for k in ['sharer','intent/tweet','wa.me/','t.me/share'])
   if direct_document(link['url']) or (external and not sharing):
    x=catalog.setdefault(link['url'],{**link,'discovered_on':[],'kind':'document_or_data'})
    x['discovered_on'].append(url)
 for url,title in PRIMARY_EXTRA:catalog.setdefault(url,{'url':url,'title':title,'discovered_on':[],'kind':'primary_reference'})
 nsa='https://www.nsa.gov.pl/dokumenty/statystyki-wsa/'
 soup=BeautifulSoup(content(nsa),'html.parser')
 for li in soup.select('li'):
  label=li.get_text(' ',strip=True)
  year=re.search(r'(202[0-5])',label)
  if year and 'Skargi na bezczynność i przewlekłość' in label:
   for a in li.select('a[href]'):
    u=urljoin(nsa,a['href'])
    catalog[u]={'url':u,'title':f'NSA WSA Dział 2 {year.group(1)} - skargi na bezczynność i przewlekłość','discovered_on':[nsa],'kind':'court_workbook','year':year.group(1)}
 # Download HTML, CSVs and the priority primary tables; keep other linked files catalogued.
 priorities=[u for u in catalog if '.csv' in u or 'api.sejm.gov.pl' in u or catalog[u]['kind']=='court_workbook' or any(k in u for k in ['udsc-bsz-waism-0361-16','lodzki-soc-iii-1331-2','lodzki-soc-iv-1331-11-hurtownia','podlaski-ob-ii-1331-16-2026-pt-2026-09-09'])]
 fetch_many(priorities,refresh)
 jwrite(CACHE/'discovered_catalog.json',list(catalog.values()))
 return list(catalog.values())
if __name__=='__main__':
 cs=discover();print(json.dumps({'catalogued':len(cs),'snapshots':len(manifest()),'cache':str(CACHE)},ensure_ascii=False))
