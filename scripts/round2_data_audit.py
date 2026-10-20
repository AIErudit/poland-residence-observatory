#!/usr/bin/env python3
"""Second-pass read-only audit. Does not import the production parser or approve data."""
from __future__ import annotations
import argparse,collections,concurrent.futures,csv,datetime,hashlib,io,json,re,unicodedata
from pathlib import Path
from urllib.parse import urljoin,urlparse,parse_qs
import requests,pdfplumber,xlrd,openpyxl
from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'source-cache/observatory';CACHE=ROOT.parent/'source-cache/round2';OUT=ROOT/'research/round2-data'
PAGES=['https://glos-migranta.eu/dane','https://glos-migranta.eu/fakty','https://glos-migranta.eu/raporty/szesnascie-urzedow-w-liczbach','https://glos-migranta.eu/raporty/prognoza']
REGIONS=[('DS','Dolnośląski'),('KP','Kujawsko-Pomorski'),('LU','Lubelski'),('LB','Lubuski'),('LD','Łódzki'),('MA','Małopolski'),('MZ','Mazowiecki'),('OP','Opolski'),('PK','Podkarpacki'),('PD','Podlaski'),('PM','Pomorski'),('SL','Śląski'),('SK','Świętokrzyski'),('WN','Warmińsko-Mazurski'),('WP','Wielkopolski'),('ZP','Zachodniopomorski')]
def jwrite(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def folded(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.lower().replace('ł','l')) if not unicodedata.combining(c))
def integer(s):return int(s) if isinstance(s,(int,float)) else int(re.sub(r'[^0-9]','',str(s)))
def geo(s):return next('PL-'+g for g,a in REGIONS if folded(a)==folded(s.replace('WOJEWODA','').replace('Wojewoda','').strip()))
def acquire(url,refresh=False):
 meta=CACHE/'http'/f'{hashlib.sha256(url.encode()).hexdigest()}.json'
 if meta.exists() and not refresh:return json.loads(meta.read_text(encoding='utf-8'))
 rec={'url':url,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}
 try:
  r=requests.get(url,headers={'User-Agent':'PolandResidenceObservatory/round2-source-audit'},timeout=(12,45));blob=r.content;sha=hashlib.sha256(blob).hexdigest();p=CACHE/'blobs'/f'{sha}.bin';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob)
  rec.update(status=r.status_code,final_url=r.url,content_type=r.headers.get('Content-Type'),sha256=sha,bytes=len(blob),file=p.relative_to(CACHE).as_posix())
 except requests.RequestException as e:rec.update(status=None,error=str(e))
 jwrite(meta,rec);return rec
def snap_bytes(rec):return (CACHE/rec['file']).read_bytes()
def snapshots(refresh=False):
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:pages=list(pool.map(lambda u:acquire(u,refresh),PAGES))
 links={};summaries=[]
 for r in pages:
  if r.get('status')!=200:continue
  soup=BeautifulSoup(snap_bytes(r),'html.parser');text=soup.get_text(' ',strip=True);csvs=[]
  for a in soup.select('a[href]'):
   u=urljoin(r['url'],a['href']).split('#')[0]
   links.setdefault(u,[]).append(r['url'])
   if re.search(r'\.csv(?:\?|$)',u):csvs.append(u)
  summaries.append({**{k:r.get(k) for k in ['url','status','retrieved_at','sha256','bytes']},'title':soup.title.get_text(' ',strip=True) if soup.title else '', 'text_characters':len(text),'csv_links':sorted(set(csvs))})
 csvurls=sorted({u for x in summaries for u in x['csv_links']})
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:tables=list(pool.map(lambda u:acquire(u,refresh),csvurls))
 for r in tables:
  if r.get('status')!=200:continue
  for row in csv.DictReader(io.StringIO(snap_bytes(r).decode('utf-8-sig'))):
   for val in row.values():
    if isinstance(val,str) and val.startswith(('https://','http://')):links.setdefault(val,[]).append(r['url'])
 jwrite(CACHE/'current-pages.json',summaries);jwrite(CACHE/'current-tables.json',tables);jwrite(CACHE/'link-paths.json',links)
 return summaries,tables,links

class Audit:
 def __init__(self):
  self.dataset_path=ROOT/'data/curated/dataset.json';self.d=json.loads(self.dataset_path.read_text(encoding='utf-8'));self.ms=json.loads((OLD/'manifest.json').read_text(encoding='utf-8'));self.sources={s['id']:s for s in self.d['sources']};self.expected={};self.parsers={};self.byte_checks=[];self.notes=[]
 def raw(self,url):
  r=self.ms[url];data=(OLD/r['file']).read_bytes();sha=hashlib.sha256(data).hexdigest();assert sha==r['content_sha256'],url
  self.byte_checks.append({'url':url,'sha256':sha});return data
 def remember(self,row,value,method):
  assert row['id'] not in self.expected,row['id'];self.expected[row['id']]=value;self.parsers[row['id']]=method
 def byseries(self,series):return [r for r in self.d['observations'] if r['series_id']==series]
 def url(self,r):return self.sources[r['source_id']]['url']
 def audit_sejm(self):
  for series in ['mswia_18089_concluded_mean_days','mswia_12584_pending_count','mswia_12584_reported_mean_days']:
   rows=self.byseries(series);url=self.url(rows[0]);soup=BeautifulSoup(self.raw(url),'html.parser');table=soup.find('table');values={}
   for tr in table.find_all('tr')[1:]:
    cs=[x.get_text(' ',strip=True) for x in tr.find_all(['td','th'])]
    if not cs:continue
    g='PL' if cs[0]=='Wszyscy wojewodowie' else geo(cs[0]);values[g]=[integer(x) for x in cs[1:]]
   for row in rows:
    col=int(row['reference_period'][:4])-2023 if series=='mswia_18089_concluded_mean_days' else 0 if series.endswith('pending_count') else 1
    self.remember(row,values[row['geography_id']][col],'native_sejm_html_table')
 def udsc_grid(self,page,y0,y1,bounds):
  words=[w for w in page.extract_words() if y0<w['top']<y1 and bounds[0]<w['x0']<bounds[-1]];groups=[]
  for w in sorted(words,key=lambda w:(w['top'],w['x0'])):
   if not groups or abs(w['top']-groups[-1][0]['top'])>3:groups.append([w])
   else:groups[-1].append(w)
  assert len(groups)==16,len(groups)
  result=[]
  for g in groups:
   row=[]
   for lo,hi in zip(bounds,bounds[1:]):
    text=''.join(w['text'] for w in sorted(g,key=lambda x:x['x0']) if lo<w['x0']<hi);digits=re.sub(r'\D','',text);row.append(int(digits) if digits else None)
   result.append(row)
  return result
 def audit_udsc(self):
  rows=[r for r in self.d['observations'] if r['series_id'].startswith('udsc_20260828_')];raw=self.raw(self.url(rows[0]))
  with pdfplumber.open(io.BytesIO(raw)) as pdf:
   temp=self.udsc_grid(pdf.pages[2],497,720,[365,420,466,513,560]);blue=self.udsc_grid(pdf.pages[3],136,330,[365,420,466,513,560]);stock=self.udsc_grid(pdf.pages[3],458,655,[330,395,450,508,560])
  # Independent visual reinspection of the freshly rendered PDF page3:
  # OCR omits row1/2024 and reads row6/2024 as445. The image reads472/145.
  temp[0][1]=472;temp[5][1]=145
  for row in rows:
   grid=stock if row['indicator_id']=='pending_cases' else blue if row['permit_type']=='blue_card' else temp
   rn=int(re.search(r'numeric row(\d+)',row['source_locator']).group(1))-1;year=int(row['reference_period'][:4])-2023
   self.remember(row,grid[rn][year],'pdf_coordinate_grid_plus_two_visual_OCR_corrections')
  self.notes.append('UdSC192 numeric cells checked against the PDF independently of verified transcription;2OCR cells visually corrected. All regional identities remain reconstructed, because the ORGAN column is redacted. This pass does not independently authenticate those geographic labels.')
 def audit_lodz(self):
  rows=[r for r in self.d['observations'] if r['series_id'] in ['lodz_pending_stock','lodz_caseworkers','lodz_staff_headcount','lodz_pending_per_caseworker']];pdf=PdfReader(io.BytesIO(self.raw(self.url(rows[0]))));stock={};staff={};workers={}
  for line in pdf.pages[1].extract_text().splitlines():
   pieces=re.fullmatch(r'\s*(202[3-6])r\.\s*[—–-]\s*([0-9.]+),?\s*',line)
   if pieces:stock[int(pieces[1])]=integer(pieces[2])
  for line in pdf.pages[2].extract_text().splitlines():
   m=re.match(r'\s*(202[3-6])\s+r\.\s*[—–-]\s*(\d+)\s+os\S+\s+w tym\s+(\d+)',line)
   if m:staff[int(m[1])]=int(m[2]);workers[int(m[1])]=int(m[3])
  assert [stock[y] for y in sorted(stock)]==[27179,27016,33979,49844]
  assert [workers[y] for y in sorted(workers)]==[37,38,36,38] and [staff[y] for y in sorted(staff)]==[88,90,82,83]
  for r in rows:
   y=int(r['reference_period'][:4]);value=stock[y] if r['series_id']=='lodz_pending_stock' else workers[y] if r['series_id']=='lodz_caseworkers' else staff[y] if r['series_id']=='lodz_staff_headcount' else round(stock[y]/workers[y],6)
   self.remember(r,value,'independent_full_line_letter_extraction_with_golden_series')
 def audit_warehouse(self):
  rows=self.byseries('warehouse_all_outcomes');byurl=collections.defaultdict(list)
  for r in rows:byurl[self.url(r)].append(r)
  for url,rs in byurl.items():
   pdf=PdfReader(io.BytesIO(self.raw(url)));lines=pdf.pages[0].extract_text().splitlines();records={}
   for i,line in enumerate(lines):
    if not line.startswith('WOJEWODA'):continue
    # Separate line parser rather than the production multi-line regular expression.
    nums=re.findall(r'\d+',line)+re.findall(r'\d+',lines[i+1])+re.findall(r'\d+',lines[i+2])
    records[geo(re.sub(r'\d.*','',line).strip())]=list(map(int,nums[:2]))
   maximum=[int(line.strip()) for line in pdf.pages[1].extract_text().splitlines() if line.strip().isdigit()];assert len(records)==len(maximum)==16
   for (g,v),mx in zip(records.items(),maximum):v.append(mx)
   for r in rs:self.remember(r,records[r['geography_id']][{'concluded_resolutions':0,'processing_duration_mean_days':1,'processing_duration_max_days':2}[r['indicator_id']]],'native_warehouse_PDF_independent_line_parser')
  rows=self.byseries('lodz_warehouse_all_outcomes')+self.byseries('lodz_warehouse_positive_decisions');book=openpyxl.load_workbook(io.BytesIO(self.raw(self.url(rows[0]))),read_only=True,data_only=True)
  for r in rows:
   name=re.search(r'sheet=(.*?);',r['source_locator'])[1];sheet=book[name];candidates=[v for v in sheet.iter_rows(values_only=True) if v[0] and folded(str(v[0]))==folded('WOJEWODA ŁÓDZKI')];assert len(candidates)==1
   v=candidates[0][{'concluded_resolutions':1,'processing_duration_mean_days':2,'processing_duration_max_days':3}[r['indicator_id']]];self.remember(r,integer(v),'source_XLSX_labelled_row_and_indicator_column')
 def audit_courts(self):
  byurl=collections.defaultdict(list)
  for r in self.byseries('nsa_wsa_6272_annual'):byurl[self.url(r)].append(r)
  for url,rows in byurl.items():
   book=xlrd.open_workbook(file_contents=self.raw(url));y=int(rows[0]['reference_period']);native={}
   for sheet in book.sheets():
    gid='PL' if sheet.name=='WSA SAB Symbole' else 'WSA-'+sheet.name
    if gid not in {r['geography_id'] for r in rows}:continue
    data=[sheet.row_values(i) for i in range(sheet.nrows) if sheet.ncols>1 and str(sheet.cell_value(i,1)) in ['6272','6272.0']];assert len(data)==1
    a=[int(v or 0) if isinstance(v,(int,float)) or not v else v for v in data[0]]
    if y<2023:up=a[9]+a[14];dismiss=a[10]+a[15];reject=a[11]+a[16];resolved=a[7];closed=a[17];total=a[6];end=a[18]
    else:up=a[8]+a[13];dismiss=a[9]+a[14];reject=a[10]+a[15];resolved=a[6];closed=a[17];total=a[18];end=a[19]
    assert a[3]+a[4]==total+end and total==resolved+closed
    native[gid]={'court_inflow':a[4],'court_pending_start':a[3],'court_pending_end':end,'court_resolved':resolved,'court_upheld':up,'court_dismissed':dismiss,'court_rejected':reject,'court_other_resolved':resolved-up-dismiss-reject,'court_closed':closed,'court_resolved_including_closed':total,'court_upheld_merits_pct':round(100*up/(up+dismiss),6) if up+dismiss else None,'court_rejected_resolved_pct':round(100*reject/resolved,6) if resolved else None}
   assert len(native)==17
   for k,v in native['PL'].items():
    if not k.endswith('_pct'):assert v==sum(g[k] for gid,g in native.items() if gid!='PL')
   for r in rows:self.remember(r,native[r['geography_id']][r['indicator_id']],'official_XLS_6272_native_outcome_partition_and_regional_reconciliation')
 def audit_portal(self):
  dictionary=acquire('https://migracje.gov.pl/wp-json/udscmap/v1/caseType');assert dictionary.get('status')==200
  types={r['id']:r['type'] for r in json.loads(snap_bytes(dictionary))}
  assert types[1]=='Pobyt czasowy' and types[3]=='Pobyt rezydenta dlugoterminowego UE'
  for r in self.d['observations']:
   if not r['series_id'].startswith('udsc_portal_'):continue
   url=self.url(r);q=parse_qs(urlparse(url).query);assert q['year'][0]==r['reference_period'][:4];assert (q['caseType'][0]=='1')==(r['permit_type']=='temporary_residence')
   records=json.loads(self.raw(url));value=sum(int(v['total']) for v in records);self.remember(r,value,'direct_official_API_sum_citizenship_total')
 def run(self):
  self.audit_sejm();self.audit_udsc();self.audit_lodz();self.audit_warehouse();self.audit_courts();self.audit_portal()
  mismatches=[]
  for r in self.d['observations']:
   if r['id'] not in self.expected:mismatches.append({'observation_id':r['id'],'issue':'not_reproduced'})
   elif self.expected[r['id']]!=r['value']:mismatches.append({'observation_id':r['id'],'published':r['value'],'recomputed':self.expected[r['id']]})
  bymethod=collections.Counter(self.parsers.values());unique={r['url']:r for r in self.byte_checks};parsed={s['url']:s for s in self.sources.values() if s['status']=='parsed'}
  for u,s in parsed.items():assert hashlib.sha256(self.raw(u)).hexdigest()==s['content_sha256']
  result={'audit_date':datetime.date.today().isoformat(),'dataset_sha256':hashlib.sha256(self.dataset_path.read_bytes()).hexdigest(),'dataset_version':self.d['version'],'observations':len(self.d['observations']),'recomputed':len(self.expected),'numeric_mismatches':mismatches,'methods':dict(bymethod),'source_snapshots_hash_checked':len(parsed),'reviewer_independence':'Independent audit code, but same engineer authored original pipeline; not an independent-person sign-off. Separate verifier required.','geographic_limit':'192 UdSC numeric cells match source; regional labels are reconstructed, not independently legible.','notes':self.notes,'status':'numeric_reproduction_pass_with_provenance_and_definition_limits' if not mismatches else 'blocking_mismatch'}
  jwrite(ROOT/'qa/round2-data.json',result);jwrite(CACHE/'numeric-reproduction.json',self.expected);return result

def provenance(a,pages,tables,paths):
 records=[]
 for s in a.d['sources']:
  if s['status']!='parsed':continue
  via=sorted(set(paths.get(s['url'],[])));url=s['url']
  if via:route='explicit_Glos_page_or_download_index_link'
  elif 'www.nsa.gov.pl/media/' in url:route='official_workbook_retrieved_via_NSA_index_linked_by_Glos'
  else:route='route_not_independently_reconstructed'
  relevant=[r for r in a.d['observations'] if r['source_id']==s['id']];derived=[r for r in relevant if r['statistic'] in ['share','ratio'] or r['indicator_id']=='court_other_resolved']
  records.append({'source_id':s['id'],'url':url,'authority':s['authority'],'access':s['access'],'observations':len(relevant),'derived_observations':len(derived),'acquisition_route':route,'link_evidence':via,'new_primary_data_collected_by_this_project':False})
 out={'as_of':datetime.date.today().isoformat(),'dataset_sha256':hashlib.sha256(a.dataset_path.read_bytes()).hexdigest(),'counts':{'observations':len(a.d['observations']),'catalog_urls':len(a.d['sources']),'parsed_or_definition_supporting_sources':len(records),'catalog_only_sources':sum(s['status']=='catalog_only' for s in a.d['sources']),'current_Glos_pages_fetched':len(pages),'current_Glos_CSVs_fetched':len(tables),'new_primary_observations_claimed':0,'explicitly_derived_observations':sum(r['derived_observations'] for r in records)},'credit':{'pl':'Podstawowy zbiór powstał dzięki dokumentom i odnośnikom zebranym przez Głos Migranta. Nasz wkład to weryfikacja, normalizacja, definicje, odtwarzalny kod i wizualizacja; nie nowy niezależny zbiór spraw.','be':'Аснову складаюць дакументы і спасылкі, сабраныя Głos Migranta. Наш унёсак — праверка, нармалізацыя, азначэнні, аднаўляльны код і візуалізацыя; гэта не новы незалежны збор спраў.','en':'The core dataset builds on documents and links collected by Głos Migranta. Our contribution is verification, normalization, definitions, reproducible code and visualization, not a new independent collection of cases.'},'source_routes':records,'current_page_snapshots':pages,'limits':['1483 URLs are a catalog, not1483 independently verified datasets.','Primary official API downloads can still have been discovered through a secondary collector; publisher and discovery credit are different fields.','An independent HTTP retrieval is not an independent administrative measurement.','This audit was coded separately but not performed by a different person/agent from the original data engineer.','No survey or chat sample supports national representativeness.']}
 jwrite(OUT/'provenance-audit.json',out);return out

def offices():
 """Verify public official institution profiles; no officeholder personal data."""
 slugs=['dolnoslaski-uw','uw-kujawsko-pomorski','uw-lubelski','uw-lubuski','uw-lodzki','uw-malopolski','uw-mazowiecki','uw-opolski','uw-podkarpacki','uw-podlaski','uw-pomorski','uw-slaski','uw-swietokrzyski','uw-warminsko-mazurski','uw-wielkopolski','uw-zachodniopomorski']
 index_url='https://www.gov.pl/web/mswia/urzedy-wojewodzkie';directory=acquire(index_url);soup=BeautifulSoup(snap_bytes(directory),'html.parser');headings=[h for h in soup.find_all('h3') if 'Urząd Wojewódzki' in h.get_text()];assert len(headings)==16
 geo_dict=json.loads((ROOT/'data/curated/geographies.json').read_text(encoding='utf-8'));geos={g['id']:g for g in geo_dict}
 urls=['https://www.gov.pl/web/'+slug for slug in slugs]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:profiles=list(pool.map(acquire,urls))
 result=[]
 for (code,adjective),h,r in zip(REGIONS,headings,profiles):
  gid='PL-'+code;title=h.get_text(' ',strip=True);profile_title='';contact=None
  if r.get('status')==200:
   page=BeautifulSoup(snap_bytes(r),'html.parser');profile_title=page.title.get_text(' ',strip=True) if page.title else ''
   valid=folded(adjective[:5]) in folded(profile_title)
   if valid:
    candidates=[urljoin(r['url'],a['href']) for a in page.select('a[href]') if re.search(r'^(Kontakt|Dane kontaktowe|Wydział.*Cudzoziem|Cudzoziemcy)$',a.get_text(' ',strip=True),re.I) and not a['href'].startswith('#')]
    for u in list(dict.fromkeys(candidates))[:2]:
     c=acquire(u)
     if c.get('status')==200 and urlparse(c['final_url']).netloc.endswith(('gov.pl','uw.gov.pl')):contact=c['final_url'];break
   else:r['status']='wrong_institution_title'
  valid=r.get('status')==200
  cities=[x.strip() for x in geos[gid]['capital'].split('/')]
  result.append({'geography_id':gid,'geography_name':geos[gid]['name'],'office_name':title,'authority_name':'Wojewoda '+adjective,'cities':cities,'cities_definition':'Project capital labels, not a verified list of all foreigner-service branches. For two-capital regions the provincial office seat is specified by office_name.','official_url':r['final_url'] if valid else index_url,'contact_or_foreigners_url':contact,'verification_status':'official_profile_and_contact_verified' if contact else 'official_general_profile_verified' if valid else 'official_MSWiA_directory_verified_profile_not_confirmed','retrieved_at':r['retrieved_at'] if valid else directory['retrieved_at'],'content_sha256':r['sha256'] if valid else directory['sha256'],'official_profile_title':profile_title if valid else None,'directory_source_url':index_url})
 assert len(result)==16 and len({r['geography_id'] for r in result})==16
 jwrite(OUT/'offices.json',{'as_of':datetime.date.today().isoformat(),'offices':result,'limitation':'Directory and contact references only; not appointment availability or confirmation of competent office for a personal case.'});return result

def eurostat_context():
 base='https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/migr_resfirst?lang=EN&'
 urls=[base+'geo=PL&geo=EU27_2020&citizen=TOTAL&reason=TOTAL&duration=TOTAL&unit=PER',base+'geo=PL&citizen=BY&reason=TOTAL&duration=TOTAL&unit=PER']
 metadata_urls=['https://ec.europa.eu/eurostat/cache/metadata/en/migr_resval_esms.htm','https://ec.europa.eu/eurostat/web/migration-asylum/managed-migration/information-data','https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction']
 records=[acquire(u) for u in urls];metas=[acquire(u) for u in metadata_urls]
 if any(r.get('status')!=200 for r in records):
  out={'status':'unavailable_no_values_invented','category':'context-not-waiting','sources':records};jwrite(OUT/'eurostat-context.json',out);return out
 data=[json.loads(snap_bytes(r)) for r in records];definitions=[];observations=[];sources=[]
 def cell(js,codes):
  idx=0
  for dim,size in zip(js['id'],js['size']):idx=idx*size+js['dimension'][dim]['category']['index'][codes[dim]]
  values=js.get('value',{});flags=js.get('status',{});value=values.get(str(idx)) if isinstance(values,dict) else values[idx]
  flag=flags.get(str(idx)) if isinstance(flags,dict) else flags[idx] if flags else None
  return value,flag,idx
 assert data[0]['dimension']['geo']['category']['label']['PL']=='Poland'
 assert data[0]['dimension']['geo']['category']['label']['EU27_2020']=='European Union - 27 countries (from 2020)'
 assert data[0]['dimension']['unit']['category']['label']['PER']=='Person'
 assert data[1]['dimension']['citizen']['category']['label']['BY']=='Belarus'
 years=sorted(data[0]['dimension']['time']['category']['index']);basecodes={'freq':'A','reason':'TOTAL','citizen':'TOTAL','duration':'TOTAL','unit':'PER'}
 years=[y for y in years if int(y)<datetime.date.today().year and all(cell(data[0],{**basecodes,'geo':g,'time':y})[0] is not None for g in ['PL','EU27_2020'])][-5:]
 assert len(years)==5
 for n,(js,source) in enumerate(zip(data,records)):
  source_id='round2_eurostat_'+hashlib.sha256(source['url'].encode()).hexdigest()[:12]
  sources.append({'id':source_id,'url':source['url'],'publisher':'Eurostat','retrieved_at':source['retrieved_at'],'content_sha256':source['sha256'],'dataset_updated':js.get('updated'),'dimensions':js['dimension'],'access':'direct_official_API','discovery_route':'new_round2_official_Eurostat_research_not_the_old_Glos_core'})
  for g in (['PL','EU27_2020'] if n==0 else ['PL']):
   for y in years:
    codes={**basecodes,'geo':g,'time':y,'citizen':'TOTAL' if n==0 else 'BY'};value,flag,index=cell(js,codes)
    observations.append({'id':'es_migr_resfirst_'+g+'_'+codes['citizen']+'_'+y,'series_id':'eurostat_first_residence_permits_context','indicator_id':'first_residence_permits','category':'context-not-waiting','geography_id':g,'geography_name':js['dimension']['geo']['category']['label'][g],'reference_period':y,'as_of_date':y+'-12-31','citizenship_code':codes['citizen'],'citizenship_label':js['dimension']['citizen']['category']['label'][codes['citizen']],'reason_code':'TOTAL','duration_code':'TOTAL','frequency':'A','unit_code':'PER','unit_label':'Person','value':value,'flags':flag,'statistical_break':True if flag and 'b' in flag else None,'source_id':source_id,'source_locator':'JSON-stat value['+str(index)+']; '+json.dumps(codes,sort_keys=True),'definition_id':'eurostat_first_permit_context','quality_status':'official_context_pending_independent_review','notes':'Administrative first-permit flow for non-EU citizens in this collection; TOTAL does not mean all migrants. Not a waiting-time, pending-case, unique-new-arrival or voivode-only decision count. Absence of a break flag does not certify full comparability.'})
 definitions=[{'id':'eurostat_first_permit_context','label':'Eurostat first residence permits: context only','description':'Annual authorisations for non-EU citizens to stay at least3months. A first permit can also follow a gap of at least6months after an earlier permit. National long-stay visas/status grants may be included under the statistical definition. TOTAL aggregates citizenship within this collection; BY means Belarus citizenship, not ethnic origin. Reported PER/Person unit is preserved. These are not applications, waiting times, the resident stock, or the same scope as Polish temporary-residence case resolutions.'}]
 out={'status':'official_context_pending_independent_review','category':'context-not-waiting','as_of':datetime.date.today().isoformat(),'dataset':'migr_resfirst','selected_full_years':years,'observations':observations,'definitions':definitions,'sources':sources,'metadata_sources':[{k:r.get(k) for k in ['url','retrieved_at','sha256','status']} for r in metas],'limitations':['EU27 includes Poland and must not be added to Poland.','A first residence permit is not necessarily a first-ever migration event.','No time-to-decision can be inferred from these annual counts.','Absence of flags is preserved as null, not proof of no statistical breaks.','Eurostat revisions can change historical values; snapshots must be retained.','This additional context layer does not replace or mutate the frozen1780-observation core.']}
 assert len(observations)==15 and all(r['value'] is None or isinstance(r['value'],(int,float)) for r in observations)
 jwrite(OUT/'eurostat-context.json',out);return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--refresh-pages',action='store_true');p.add_argument('--offline',action='store_true');p.add_argument('--offices',action='store_true');p.add_argument('--eurostat',action='store_true');args=p.parse_args()
 if args.offices:print(json.dumps({'offices':len(offices())}));return
 if args.eurostat:out=eurostat_context();print(json.dumps({'status':out['status'],'years':out.get('selected_full_years'),'observations':len(out.get('observations',[]))}));return
 a=Audit();result=a.run()
 if args.offline:pages=json.loads((CACHE/'current-pages.json').read_text(encoding='utf-8'));paths=json.loads((CACHE/'link-paths.json').read_text(encoding='utf-8'));tables=json.loads((CACHE/'current-tables.json').read_text(encoding='utf-8'))
 else:pages,tables,paths=snapshots(args.refresh_pages)
 prov=provenance(a,pages,tables,paths);print(json.dumps({'numeric_status':result['status'],'recomputed':result['recomputed'],'mismatches':result['numeric_mismatches'],'provenance_counts':prov['counts']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
