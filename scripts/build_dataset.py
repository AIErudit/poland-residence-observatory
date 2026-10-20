#!/usr/bin/env python3
"""Build reviewed public aggregates from pinned primary snapshots, offline.

No Telegram exports, personal cases, letters or PDF binaries are copied into data/.
See data/README.md for the review gate and the meanings of stocks and flows.
"""
from __future__ import annotations
import argparse,collections,csv,hashlib,io,json,re,unicodedata
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import xlrd
import openpyxl
from bs4 import BeautifulSoup
from pypdf import PdfReader
from source_pipeline import ROOT,CACHE,SEED_URLS,PRIMARY_EXTRA,manifest,content,links,direct_document,sid,jwrite

DATA=ROOT/'data';CURATED=DATA/'curated';REVIEW=DATA/'review';AS_OF='2026-10-20'
URL_18089='https://api.sejm.gov.pl/sejm/term10/interpellations/18089/reply/DWDJHZ/body'
URL_12584='https://api.sejm.gov.pl/sejm/term10/interpellations/12584/reply/DMQHGV/body'
URL_UDSC='https://glos-migranta.eu/dokumenty/udsc-bsz-waism-0361-16-2026-08-28.pdf'
URL_LODZ='https://glos-migranta.eu/dokumenty/lodzki-soc-iii-1331-2-2026-08-25.pdf'
URL_LODZ_WAREHOUSE='https://glos-migranta.eu/dokumenty/lodzki-soc-iv-1331-11-hurtownia-raporty.xlsx'
URL_PODLASKI_COVER='https://glos-migranta.eu/dokumenty/podlaski-ob-ii-1331-16-2026-pt-2026-09-09-decyzja.pdf'
OFFICIAL_PUBLISHER_HOSTS={'api.sejm.gov.pl','sejm.gov.pl','www.sejm.gov.pl','nsa.gov.pl','www.nsa.gov.pl','orzeczenia.nsa.gov.pl','nik.gov.pl','www.nik.gov.pl','bip.brpo.gov.pl','brpo.gov.pl','www.brpo.gov.pl','zus.pl','www.zus.pl','psz.zus.pl','migracje.gov.pl','udsc.gov.pl','www.udsc.gov.pl','gov.pl','www.gov.pl','dane.gov.pl','stat.gov.pl','www.stat.gov.pl','bdl.stat.gov.pl','eur-lex.europa.eu','curia.europa.eu'}
GEOGRAPHIES=[
 ('PL-DS','Dolnośląskie','Wrocław','Dolnośląski','WR'),('PL-KP','Kujawsko-pomorskie','Bydgoszcz / Toruń','Kujawsko-Pomorski','BD'),
 ('PL-LU','Lubelskie','Lublin','Lubelski','LU'),('PL-LB','Lubuskie','Gorzów Wielkopolski / Zielona Góra','Lubuski','GW'),
 ('PL-LD','Łódzkie','Łódź','Łódzki','LD'),('PL-MA','Małopolskie','Kraków','Małopolski','KR'),
 ('PL-MZ','Mazowieckie','Warszawa','Mazowiecki','WA'),('PL-OP','Opolskie','Opole','Opolski','OP'),
 ('PL-PK','Podkarpackie','Rzeszów','Podkarpacki','RZ'),('PL-PD','Podlaskie','Białystok','Podlaski','BK'),
 ('PL-PM','Pomorskie','Gdańsk','Pomorski','GD'),('PL-SL','Śląskie','Katowice','Śląski','GL'),
 ('PL-SK','Świętokrzyskie','Kielce','Świętokrzyski','KL'),('PL-WN','Warmińsko-mazurskie','Olsztyn','Warmińsko-Mazurski','OL'),
 ('PL-WP','Wielkopolskie','Poznań','Wielkopolski','PO'),('PL-ZP','Zachodniopomorskie','Szczecin','Zachodniopomorski','SZ')]
COURT_CITIES={'BK':'Białystok','BD':'Bydgoszcz','GD':'Gdańsk','GL':'Gliwice','GW':'Gorzów Wielkopolski','KL':'Kielce','KR':'Kraków','LU':'Lublin','LD':'Łódź','OL':'Olsztyn','OP':'Opole','PO':'Poznań','RZ':'Rzeszów','SZ':'Szczecin','WA':'Warszawa','WR':'Wrocław'}
geographies=[{'id':g,'name':n,'capital':c} for g,n,c,_,_ in GEOGRAPHIES]+[{'id':'PL','name':'Polska','capital':'Warszawa'},{'id':'WSA-PL','name':'Wszystkie WSA','capital':None}]+[{'id':'WSA-'+k,'name':'WSA: '+v,'capital':v} for k,v in COURT_CITIES.items()]
GEO={g['id']:g for g in geographies}
def fold(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.replace('ł','l').replace('Ł','L')).casefold() if not unicodedata.combining(c))
ORG={fold('Wojewoda '+adjective):gid for gid,_,_,adjective,_ in GEOGRAPHIES}
def organ_id(t):return ORG[fold(' '.join(t.split()))]
def num(x):
 if isinstance(x,(int,float)):return int(x) if int(x)==x else x
 x=str(x).strip().replace('\u00a0','').replace(' ','').replace('.','')
 if not x:raise ValueError('Missing value must not be silently replaced with zero')
 return int(x)
def csv_rows(url):return list(csv.DictReader(io.StringIO(content(url).decode('utf-8-sig'))))
def annual_period(year,cutoff):return str(year) if year<int(cutoff[:4]) else f'{year}-01-01/{cutoff}'
def annual_end(year,cutoff):return f'{year}-12-31' if year<int(cutoff[:4]) else cutoff

DEFS=[
 ('concluded_duration','Reported mean duration of concluded proceedings','Reported administrative duration of concluded proceedings, grouped by year of resolution. Endpoints are submission to first-instance resolution only where expressly defined by the source (including the UdSC letter of28.08.2026); the exact starting event is not established for MSWiA18089. Calendar-versus-working-day convention is not independently established for every source. Unfinished applications do not enter this average; a legal deadline or median is not being measured. Source reporting may include discontinuance and leaving an application unexamined. A reported mean does not establish a legal violation.'),
 ('pending_stock','Pending proceedings at a point in time','Stock of unfinished proceedings on the explicitly stated reference date. Not applications received or decisions issued during a year. The 2026 UdSC count may have a reporting-system/scope discontinuity; source cohorts must not be spliced.'),
 ('mswia12584_mean_ambiguous','Reported mean alongside pending stock, cohort not explicit','MSWiA12584 reports art.114 temporary-residence-and-work cases pending on13.10.2025 and a mean processing time. It does not explicitly establish whether this mean is elapsed age of the open stock or a mean of concluded proceedings. Kept separate from concluded-duration and waiting-age measures.'),
 ('lodz_scope','Łódź office own series, scope not separately broken down','Letter SOC-III.1331.2.2026 answers temporary-residence and BlueCard questions without a separate breakdown. Its own pending counts differ from the UdSC national extraction. Keep both series; do not merge or describe the difference as an error.'),
 ('caseworkers','Caseworkers headcount','Persons directly conducting residence-permit proceedings in the Łódź units described in the letter. Headcount, not funded FTE, not all department staff, and not annual output.'),
 ('staff_headcount','Reported staff headcount in the Łódź units','Persons in the relevant Łódź residence/residence-and-work units. Headcount rather than FTE; includes workers not directly deciding cases.'),
 ('stock_per_caseworker','Pending stock divided by caseworker headcount','Computed ratio of the office own pending stock to persons directly conducting proceedings at the matching cut-off. Not productivity, annual caseload or number of unique applicants.'),
 ('court_6272','WSA inactivity/delay cases, subject symbol6272','Annual statistical movements and dispositions of inactivity/protracted-proceedings complaints under NSA subject6272 (visas, residence, settlement and expulsion in the source classification). WSA first-instance court statistics published by NSA, not NSA cassation outcomes and not a sample limited to one permit type.'),
 ('court_opening_stock','Opening court stock: Pozostało z poprzedniego okresu','Cases carried over from the previous period, represented as opening stock on01.01 of the stated annual table year. Not31.12 of that year, not annual inflow. The end stock is separately dated31.12.'),
 ('court_resolved','Załatwiono, excluding administratively closed cases','Sum of hearing and non-public-session dispositions. Distinct from Zamknięto and from Łącznie załatwiono including Zamknięto. Table layout changes in2023; the parser explicitly maps both layouts.'),
 ('court_other','Resolved in other ways','Remainder of Załatwiono minus upheld, dismissed and rejected, matching W inny sposób where separately reported. It must not be relabelled as exclusively discontinued proceedings.'),
 ('court_merits_denominator','Upheld plus dismissed complaints','Only uwzględniono+oddalono. Rejected complaints, other dispositions and administrative closure are excluded. This is not the share of all filed complaints that ultimately succeed.'),
 ('court_rejection_denominator','Resolved complaints excluding administrative closure','Odrzucono divided by Załatwiono, excluding Zamknięto. Annual disposed cases may have been filed in earlier years; this is not a filing-cohort outcome probability.'),
 ('court_blank_zero','Blank numeric count in an existing official statistical row','Blank count cells in existing6272 rows are treated as zero only after all16 courts sum exactly to the published national row and stock-flow identities hold. A missing sheet, row or unknown duration is never converted to zero. Shares with zero denominators are null, not0percent.'),
 ('portal_flow','UdSC portal annual applications and decisions','Direct migracje.gov.pl API snapshot, national totals summed across the returned citizenship groups for caseType1(temporary residence) or3(EU long-term resident). Applications and decisions are flows in a reference year, not the pending stock; subtracting them does not reconstruct the stock without other movements.2026 is partial; API does not state a separate operational cut-off.'),
 ('warehouse_resolutions','Data warehouse all-outcome resolutions','Count, mean and reported maximum of positive and negative decisions, discontinuance and leaving an application unexamined, grouped by resolution date. Different scope from portal decisions flow. Report generation date is not automatically the data cut-off.2026 Podlaski attachment cut-off is unknown because the letter says only annual/half-year reports are available.'),
 ('positive_resolution_duration','Łódź positive-decisions-only warehouse cohort','Duration and count for positive decisions under the stated legal basis only. Do not compare as identical to all-outcome mean. Source validation note says duplicate application IDs were removed and certain pre01.05.2014 submission dates were replaced by registration dates.'),
 ('scenario','Scenario only, not an observed or official forecast','No forecast values from Głos Migranta are imported as facts. Any scenario must carry explicit inputs and assumptions, data cut-offs and a separate scenario label. Pending/annual decisions is a workload ratio, not an identified expected waiting time.')]
definitions=[{'id':i,'label':l,'description':d} for i,l,d in DEFS]
SERIES={
 'mswia_18089_concluded_mean_days':['processing_duration_mean_days','days','concluded'],
 'mswia_12584_pending_count':['pending_cases','cases','pending'],
 'mswia_12584_reported_mean_days':['reported_processing_mean_days_ambiguous_cohort','days','reported_with_pending_stock'],
 'udsc_20260828_concluded_mean_days':['processing_duration_mean_days','days','concluded'],
 'udsc_20260828_blue_card_mean_days':['processing_duration_mean_days','days','concluded'],
 'udsc_20260828_pending_stock':['pending_cases','cases','pending'],
 'lodz_pending_stock':['pending_cases','cases','pending'],
 'lodz_caseworkers':['caseworkers','persons','staff'],
 'lodz_staff_headcount':['staff_headcount','persons','staff'],
 'lodz_pending_per_caseworker':['pending_per_caseworker','cases_per_person','pending'],
 'warehouse_all_outcomes':['concluded_resolutions / processing_duration_mean_days / processing_duration_max_days','cases or days','concluded'],
 'lodz_warehouse_all_outcomes':['concluded_resolutions / processing_duration_mean_days / processing_duration_max_days','cases or days','concluded'],
 'lodz_warehouse_positive_decisions':['concluded_resolutions / processing_duration_mean_days / processing_duration_max_days','cases or days','concluded_positive'],
 'nsa_wsa_6272_annual':['multiple court indicators','cases or percent','court_inflow/court_resolved/court_stock'],
 'udsc_portal_temporary_applications':['applications_received','cases','applications_received'],
 'udsc_portal_temporary_decisions':['decisions_issued','cases','decisions_issued'],
 'udsc_portal_eu_long_term_applications':['applications_received','cases','applications_received'],
 'udsc_portal_eu_long_term_decisions':['decisions_issued','cases','decisions_issued']}

class Builder:
 def __init__(self,allow_unreviewed=False):
  self.rows=[];self.used=set();self.allow_unreviewed=allow_unreviewed;self.ms=manifest()
  p=REVIEW/'approved_sources.json';self.approved=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
 def require(self,url):
  r=self.ms.get(url)
  if not r or r.get('status')!=200:raise ValueError('Primary source unavailable: '+url)
  self.used.add(url);approval=self.approved.get(sid(url),{})
  if not self.allow_unreviewed and approval.get('content_sha256')!=r['content_sha256']:raise ValueError('REVIEW REQUIRED for source '+sid(url)+' '+url)
  return r
 def add(self,series,indicator,gid,permit,stage,period,cutoff,unit,value,statistic,url,locator,definition,group,notes='',quality=None,denominator=None):
  r=self.require(url);approved=self.approved.get(sid(url),{}).get('content_sha256')==r['content_sha256']
  if quality is None:quality='reviewed_primary_copy' if url.startswith('https://glos-migranta.eu/dokumenty/') else 'reviewed_primary'
  if not approved:quality='unreviewed_candidate__'+quality
  identity='|'.join([series,indicator,gid,permit,period])
  level='country' if gid=='PL' else 'country_courts' if gid=='WSA-PL' else 'court_jurisdiction' if gid.startswith('WSA-') else 'voivodeship'
  row={'id':'obs_'+hashlib.sha256(identity.encode()).hexdigest()[:18],'series_id':series,'indicator_id':indicator,'geography_id':gid,'geography_name':GEO[gid]['name'],'geography_level':level,'permit_type':permit,'stage':stage,'reference_period':period,'as_of_date':cutoff,'unit':unit,'value':value,'statistic':statistic,'denominator':denominator,'source_id':sid(url),'source_locator':locator,'definition_id':definition,'quality_status':quality,'comparability_group':group,'notes':notes}
  self.rows.append(row);return row
 def parse_mswia(self):
  self.require(URL_18089);s=BeautifulSoup(content(URL_18089),'html.parser');table=s.select('table')[0]
  for rn,tr in enumerate(table.select('tr')[1:],2):
   cells=[c.get_text(' ',strip=True) for c in tr.find_all(['td','th'])]
   if not cells:continue
   assert len(cells)==5,cells;gid=organ_id(cells[0])
   for y,val in zip(range(2023,2027),cells[1:]):
    self.add('mswia_18089_concluded_mean_days','processing_duration_mean_days',gid,'temporary_residence','concluded',annual_period(y,'2026-07-06'),annual_end(y,'2026-07-06'),'days',num(val),'mean',URL_18089,f'HTML table1 row{rn} column{y-2021} ({y})','concluded_duration','mswia18089_temporary_first_instance','MSWiA answer dated27.07.2026; table footnote cut-off06.07.2026. Rounded regional means; no national weighted mean or median inferred.')
  self.require(URL_12584);s=BeautifulSoup(content(URL_12584),'html.parser')
  for rn,tr in enumerate(s.select('table')[0].select('tr')[1:],2):
   cs=[c.get_text(' ',strip=True) for c in tr.find_all(['td','th'])]
   if not cs:continue
   gid='PL' if cs[0]=='Wszyscy wojewodowie' else organ_id(cs[0])
   self.add('mswia_12584_pending_count','pending_cases',gid,'temporary_residence_and_work_art114','pending','2025-10-13','2025-10-13','cases',num(cs[1]),'count',URL_12584,f'HTML table1 row{rn} column2','pending_stock','mswia12584_art114_stock','All art.114 pending cases; national and Opole-only rows, not16 regional rows. Do not splice into UdSC all-temporary stock.')
   self.add('mswia_12584_reported_mean_days','reported_processing_mean_days_ambiguous_cohort',gid,'temporary_residence_and_work_art114','reported_with_pending_stock','2025-10-13','2025-10-13','days',num(cs[2]),'mean',URL_12584,f'HTML table1 row{rn} column3','mswia12584_mean_ambiguous','mswia12584_ambiguous_mean','The response does not establish that the reported mean is elapsed age of pending cases. No claimed equivalence to18089 concluded duration.',quality='reviewed_primary_definition_ambiguous')
 def parse_udsc(self):
  r=self.require(URL_UDSC);x=json.loads((DATA/'verified'/'udsc_20260828_tables.json').read_text(encoding='utf-8'))
  if r['content_sha256']!=x['content_sha256']:raise ValueError('UdSC scanned PDF changed: update and visually review the transcription before use')
  for key,series,permit,page,table in [('temporary_mean_days','udsc_20260828_concluded_mean_days','temporary_residence',3,'Ad.pkt1 Table1'),('blue_card_mean_days','udsc_20260828_blue_card_mean_days','blue_card',4,'Ad.pkt1 Table2'),('pending_cases','udsc_20260828_pending_stock','temporary_residence',4,'Ad.pkt2 Table1')]:
   for i,gid in enumerate(x['geography_order']):
    for j,y in enumerate(x['years']):
     pending=key=='pending_cases';cut=annual_end(y,'2026-07-01' if pending else '2026-08-12');period=cut if pending else annual_period(y,'2026-08-12')
     self.add(series,'pending_cases' if pending else 'processing_duration_mean_days',gid,permit,'pending' if pending else 'concluded',period,cut,'cases' if pending else 'days',x[key][i][j],'count' if pending else 'mean',URL_UDSC,f'PDF page{page}, {table}, numeric row{i+1}, year{y}','pending_stock' if pending else 'concluded_duration',series,'Primary document in a redacted third-party copy. Numeric cells visually reviewed. Geographic assignment reconstructed: regional labels are not directly legible in the public PDF; row order corroborated with published CSV and unique2023 primaryMSWiA means. Regional assignment is not independently legible, while the sum of16 numeric rows does not depend on the geographic labels. Original signed file not independently verified.'+(' 2026 stock scope/system comparability may have changed; not a flow.' if pending else ' Unfinished cases excluded; no median available.'),quality='reviewed_primary_copy_geography_reconstructed')
 def parse_lodz(self):
  self.require(URL_LODZ);reader=PdfReader(io.BytesIO(content(URL_LODZ)));p2=reader.pages[1].extract_text();p3=reader.pages[2].extract_text()
  # The source uses spaces/dots inconsistently. Restrict the extraction to4 labelled lines.
  # Whole-line anchors and a real dash prevent the full stop after a prose
  # year from being mistaken for the separator and the next year for a count.
  matches=re.findall(r'(?m)^[ \t]*(202[3-6])[ \t]*r\.[ \t]*[—–-][ \t]*([0-9][0-9. \t]*)[,]?[ \t]*$',p2)
  assert len(matches)==4 and {int(y) for y,_ in matches}==set(range(2023,2027)),matches
  counts={int(y):num(n) for y,n in matches}
  for y in range(2023,2027):
   m=re.search(r'(?m)^[ \t]*'+str(y)+r'[ \t]*r\.[ \t]*[—–-][ \t]*(\d+)\s+os[oó]b\w*\s+w\s+tym\s+(\d+)',p3,re.I);assert m,(y,p3)
   total,workers=map(int,m.groups());cut=annual_end(y,'2026-08-25');period=cut
   stock=self.add('lodz_pending_stock','pending_cases','PL-LD','temporary_and_blue_card_undifferentiated','pending',period,cut,'cases',counts[y],'count',URL_LODZ,f'PDF page2 point2 year{y}','lodz_scope','lodz_office_own_stock','Own office series;2026 is answer-date25.08.2026, not UdSC01.07.2026. Temporary/BlueCard not separately broken down.')
   worker=self.add('lodz_caseworkers','caseworkers','PL-LD','residence_all_reported','staff',period,cut,'persons',workers,'count',URL_LODZ,f'PDF page3 point5 year{y}, direct caseworkers','caseworkers','lodz_headcount','Persons, not FTE.')
   self.add('lodz_staff_headcount','staff_headcount','PL-LD','residence_all_reported','staff',period,cut,'persons',total,'count',URL_LODZ,f'PDF page3 point5 year{y}, total headcount','staff_headcount','lodz_headcount','Persons in the described units, not all provincial government employees and not FTE.')
   self.add('lodz_pending_per_caseworker','pending_per_caseworker','PL-LD','temporary_and_blue_card_undifferentiated','pending',period,cut,'cases_per_person',round(counts[y]/workers,6),'ratio',URL_LODZ,f'Computed: page2 point2 / page3 point5 year{y}','stock_per_caseworker','lodz_stock_headcount_ratio','Arithmetic stock/headcount ratio, not productivity or individual inspector workload.',quality='reviewed_derived',denominator={'value':workers,'unit':'persons','definition_id':'caseworkers','observation_ids':[worker['id']],'numerator_observation_ids':[stock['id']]})
 def parse_warehouse(self):
  self.require(URL_PODLASKI_COVER)
  # Reviewed attachment-to-year mapping; do not let a mutable secondary CSV
  # silently relabel unchanged primary snapshots.
  byyear={y:'https://glos-migranta.eu/dokumenty/podlaski-ob-ii-1331-16-2026-pt-2026-09-09-decyzja-zal-'+ann+'-sredni-czas-postepowania-legalizacja-pod.pdf' for y,ann in [(2023,'04'),(2024,'02'),(2025,'01'),(2026,'03')]}
  assert set(byyear)=={2023,2024,2025,2026}
  for year,url in sorted(byyear.items()):
   self.require(url);reader=PdfReader(io.BytesIO(content(url)));p1=reader.pages[0].extract_text();p2=reader.pages[1].extract_text()
   found=re.findall(r'(WOJEWODA[^\r\n]+)\s+(\d+)\s+(\d+)',p1)
   maxima=[int(x.strip()) for x in p2.splitlines() if re.fullmatch(r'\d+',x.strip())]
   assert len(found)==len(maxima)==16,(year,len(found),len(maxima))
   for i,((org,count,mean),maximum) in enumerate(zip(found,maxima)):
    gid=organ_id(org);count,mean=int(count),int(mean);quality='reviewed_primary_period_ambiguous' if year==2026 else 'reviewed_primary_copy'
    cutoff=None if year==2026 else f'{year}-12-31'
    note='Data warehouse all resolutions, including positive/negative decisions, discontinuance and leaving unexamined. Not the portal decisions scope. Period year assigned from the released attachment index and corroborated against historical MSWiA/Łódź tables. '+('2026 cut-off UNKNOWN.09.09.2026 is report generation date, not data as_of_date. Cover letter page2 says only annual/half-year reports are available; do not use this partial-year count in current comparisons or annual scenarios.' if year==2026 else 'Full calendar year; generator timestamp09.09.2026 is not the data period.')
    n=self.add('warehouse_all_outcomes','concluded_resolutions',gid,'temporary_residence','concluded',str(year),cutoff,'cases',count,'count',url,f'PDF page1 numeric row{i+1}, Liczba decyzji; generated09.09.2026','warehouse_resolutions','warehouse_temporary_all_outcomes' if year<2026 else 'warehouse_temporary_2026_period_unknown',note,quality=quality)
    for ind,value,stat,page in [('processing_duration_mean_days',mean,'mean',1),('processing_duration_max_days',maximum,'max',2)]:
     self.add('warehouse_all_outcomes',ind,gid,'temporary_residence','concluded',str(year),cutoff,'days',value,stat,url,f'PDF page{page} numeric row{i+1}; generated09.09.2026','warehouse_resolutions','warehouse_temporary_all_outcomes' if year<2026 else 'warehouse_temporary_2026_period_unknown',note,quality=quality,denominator={'value':count,'unit':'cases','definition_id':'warehouse_resolutions','observation_ids':[n['id']]})
  self.require(URL_LODZ_WAREHOUSE);book=openpyxl.load_workbook(io.BytesIO(content(URL_LODZ_WAREHOUSE)),read_only=True,data_only=True)
  for sh in book:
   title=str(sh['A1'].value);positive='pozytywnej' in title;years=re.findall(r'202[4-6]',sh.title+' '+title);assert years,sh.title;year=int(years[-1])
   if not positive:permit='eu_long_term_resident' if sh.title.startswith('Rezydent') else 'permanent_residence' if sh.title.startswith('Pobyt stały') else 'temporary_residence'
   else:
    basis=re.search(r'art\.?\s*(\d+)',title);assert basis;permit={'114':'temporary_work_art114','127':'blue_card_art127','142':'temporary_business_art142','144':'temporary_study_art144','158':'temporary_family_art158'}[basis.group(1)]
   data=[(i,row) for i,row in enumerate(sh.iter_rows(values_only=True),1) if row[0] and fold(str(row[0]))==fold('WOJEWODA ŁÓDZKI')];assert len(data)==1
   rownum,row=data[0];count,mean,maximum=map(num,row[1:4]);series='lodz_warehouse_positive_decisions' if positive else 'lodz_warehouse_all_outcomes';definition='positive_resolution_duration' if positive else 'warehouse_resolutions';cutoff=annual_end(year,'2026-08-31');period=annual_period(year,'2026-08-31');stage='concluded_positive' if positive else 'concluded'
   note='Łódź source workbook; A1 explicitly defines '+('positive decisions only under the stated legal basis. Duplicate IDs and certain legacy dates treated as described in sheetG3.' if positive else 'positive/negative decisions, discontinuance and leaving unexamined.')+'2026 period through31.08 is explicit in source sheet title/header. Reported maximum is a database statistic, not an independently checked individual history.'
   n=self.add(series,'concluded_resolutions','PL-LD',permit,stage,period,cutoff,'cases',count,'count',URL_LODZ_WAREHOUSE,f'XLSX sheet={sh.title}; B{rownum}; definitionA1',definition,series+'_'+permit,note)
   for ind,value,stat,col in [('processing_duration_mean_days',mean,'mean','C'),('processing_duration_max_days',maximum,'max','D')]:self.add(series,ind,'PL-LD',permit,stage,period,cutoff,'days',value,stat,URL_LODZ_WAREHOUSE,f'XLSX sheet={sh.title}; {col}{rownum}; definitionA1',definition,series+'_'+permit,note,denominator={'value':count,'unit':'cases','definition_id':definition,'observation_ids':[n['id']]})
 def parse_courts(self,catalog):
  for source in catalog:
   if source.get('kind')!='court_workbook':continue
   url=source['url'];self.require(url);year=int(source['year']);book=xlrd.open_workbook(file_contents=content(url));raw={}
   for sh in book.sheets():
    if sh.name not in COURT_CITIES and sh.name!='WSA SAB Symbole':continue
    rows=[(r,sh.row_values(r)) for r in range(sh.nrows) if sh.ncols>1 and sh.cell_value(r,1) in [6272,'6272']]
    assert len(rows)==1,(year,sh.name,len(rows));raw[sh.name]=rows[0]
   assert len(raw)==17 and len([k for k in raw if k in COURT_CITIES])==16
   nat=raw['WSA SAB Symbole'][1]
   for c in range(3,19 if year<=2022 else 20):assert (nat[c] or 0)==sum(v[1][c] or 0 for k,v in raw.items() if k!='WSA SAB Symbole'),(year,c)
   for sheet,(rn,vs) in raw.items():
    v=lambda i:int(vs[i] or 0)
    gid='PL' if sheet=='WSA SAB Symbole' else 'WSA-'+sheet
    if year<=2022:resolved=v(7);closed=v(17);up=v(9)+v(14);dismiss=v(10)+v(15);reject=v(11)+v(16);pending_end=v(18);including=v(6);cols={'court_resolved':'H','court_closed':'R','court_upheld':'J+O','court_dismissed':'K+P','court_rejected':'L+Q','court_pending_end':'S','court_resolved_including_closed':'G'}
    else:resolved=v(6);closed=v(17);up=v(8)+v(13);dismiss=v(9)+v(14);reject=v(10)+v(15);pending_end=v(19);including=v(18);cols={'court_resolved':'G','court_closed':'R','court_upheld':'I+N','court_dismissed':'J+O','court_rejected':'K+P','court_pending_end':'T','court_resolved_including_closed':'S'}
    assert including==resolved+closed and v(3)+v(4)==including+pending_end,(year,sheet)
    other=resolved-up-dismiss-reject;assert other>=0
    counts={'court_inflow':v(4),'court_pending_start':v(3),'court_resolved':resolved,'court_upheld':up,'court_dismissed':dismiss,'court_rejected':reject,'court_other_resolved':other,'court_closed':closed,'court_resolved_including_closed':including,'court_pending_end':pending_end}
    cols.update(court_inflow='E',court_pending_start='D',court_other_resolved='resolved-upheld-dismissed-rejected')
    obs={}
    for ind,value in counts.items():
     stage='court_inflow' if ind=='court_inflow' else 'court_stock' if 'pending_' in ind else 'court_resolved'
     definition='court_opening_stock' if ind=='court_pending_start' else 'court_resolved' if ind=='court_resolved' else 'court_other' if ind=='court_other_resolved' else 'court_6272'
     cutoff=f'{year}-01-01' if ind=='court_pending_start' else f'{year}-12-31'
     obs[ind]=self.add('nsa_wsa_6272_annual',ind,gid,'immigration_symbol_6272',stage,str(year),cutoff,'cases',value,'count',url,f'XLS sheet={sheet}; symbol6272; Excel row{rn+1}; column(s){cols[ind]}',definition,'wsa_6272_annual','WSA first-instance statistics published by NSA. Subject6272 is broader than temporary residence. Empty numeric cells in existing rows interpreted as0 only with16-court sum and movement identity checks. Table layout mapped explicitly for2020-2022 vs2023-2025.'+(' Opening stock carried from the previous period, dated01.01 of the table year.' if ind=='court_pending_start' else ''))
    for ind,numerator,den,denids,definition in [('court_upheld_merits_pct',up,up+dismiss,[obs['court_upheld']['id'],obs['court_dismissed']['id']],'court_merits_denominator'),('court_rejected_resolved_pct',reject,resolved,[obs['court_resolved']['id']],'court_rejection_denominator')]:
     self.add('nsa_wsa_6272_annual',ind,gid,'immigration_symbol_6272','court_resolved',str(year),f'{year}-12-31','percent',round(numerator/den*100,6) if den else None,'share',url,f'Computed from XLS sheet={sheet}; symbol6272; row{rn+1}',definition,'wsa_6272_annual','Annual disposition share, not a personal success probability or a filing-cohort result. Zero denominator =>null.',quality='reviewed_derived' if den else 'not_applicable_zero_denominator',denominator={'value':den,'unit':'cases','definition_id':definition,'observation_ids':denids,'numerator_value':numerator})
 def parse_portal(self):
  url='https://glos-migranta.eu/dane/portal-czasowy-rezydent.csv'
  for r in csv_rows(url):
   query=parse_qs(urlparse(r['zrodlo_url']).query);y=int(query['year'][0]);assert y==int(r['rok'])
   if y<2023:continue
   primary=r['zrodlo_url'];snap=self.require(primary);snapshot_date=snap['retrieved_at'][:10];js=json.loads(content(primary));assert isinstance(js,list) and all(set(x)>={'country','total'} for x in js)
   value=sum(int(x['total']) for x in js);temporary=query['caseType'][0]=='1';assert query['caseType'][0] in ['1','3'];application='/applications/' in urlparse(primary).path
   assert temporary==(r['rodzaj_sprawy']=='pobyt czasowy') and application==(r['miara']=='wnioski')
   permit='temporary_residence' if temporary else 'eu_long_term_resident';series='udsc_portal_'+('temporary' if temporary else 'eu_long_term')+('_applications' if application else '_decisions');ind='applications_received' if application else 'decisions_issued'
   self.add(series,ind,'PL',permit,ind,annual_period(y,snapshot_date),annual_end(y,snapshot_date),'cases',value,'count',primary,'JSON array, sum(total) over all returned country groups','portal_flow','udsc_portal_national_flow_snapshot','Direct API snapshot'+snapshot_date+'; as_of_date for the current year denotes retrieval date, not an independently stated operational cut-off. Current year partial. Secondary CSV comparison total='+r['wszyscy']+'. No stock reconstruction or forecast inferred.')

def catalog_sources(builder,catalog):
 records={x['url']:dict(x) for x in catalog}
 for u,title in PRIMARY_EXTRA:records.setdefault(u,{'url':u,'title':title,'discovered_on':[],'kind':'primary_reference'})
 # Catalog all primary document URLs represented by the linked documents index,
 # without publishing the actual letters or indexing private case narratives.
 for row in csv_rows('https://glos-migranta.eu/dane/dokumenty.csv'):
  u=row['url'];r=records.setdefault(u,{'url':u,'discovered_on':['https://glos-migranta.eu/dane/dokumenty.csv'],'kind':'primary_document_copy'})
  r.update(title='; '.join(x for x in [row['organ'],row['znak'],row['data']] if x),authority=row['organ'],document_date_raw=row['data'])
 for filename in ['zrodla-zewnetrzne-katalog.csv','portal-czasowy-rezydent.csv']:
  for row in csv_rows('https://glos-migranta.eu/dane/'+filename):
   for key in ['zrodlo_url','csv_url']:
    if row.get(key):records.setdefault(row[key],{'url':row[key],'title':row.get('zrodlo',row.get('rodzaj_sprawy','Linked tabular source')),'discovered_on':['https://glos-migranta.eu/dane/'+filename],'kind':'primary_reference' if key=='zrodlo_url' else 'secondary_table'})
 for u in builder.used:records.setdefault(u,{'url':u,'title':u,'discovered_on':[],'kind':'primary_reference'})
 out=[]
 for u,r in sorted(records.items()):
  host=urlparse(u).netloc;doccopy=host=='glos-migranta.eu' and '/dokumenty/' in u;secondary=host=='glos-migranta.eu' and not doccopy
  publisher='Głos Migranta (copy host)' if doccopy else 'Głos Migranta' if secondary else 'Sejm RP' if 'sejm.gov.pl' in host else 'Naczelny Sąd Administracyjny' if 'nsa.gov.pl' in host else 'Zakład Ubezpieczeń Społecznych' if 'zus.pl' in host else 'Urząd do Spraw Cudzoziemców' if 'migracje.gov.pl' in host else 'Najwyższa Izba Kontroli' if 'nik.gov.pl' in host else 'Rzecznik Praw Obywatelskich' if 'brpo.gov.pl' in host else host
  authority=r.get('authority') or ('MSWiA' if u in [URL_18089,URL_12584] else 'Urząd do Spraw Cudzoziemców' if 'udsc-' in u or 'migracje.gov.pl' in host else 'Wojewoda Łódzki' if 'lodzki-' in u else publisher)
  snap=builder.ms.get(u,{});ok=snap.get('status')==200
  access=('primary_document_copy_snapshot' if doccopy else 'secondary_dataset_snapshot' if secondary else 'primary_publisher_snapshot' if host in OFFICIAL_PUBLISHER_HOSTS else 'other_secondary_publisher_snapshot') if ok else 'catalog_only'
  docdate={'https://api.sejm.gov.pl/sejm/term10/interpellations/18089/reply/DWDJHZ/body':'2026-07-27',URL_12584:'2025-10-22',URL_UDSC:'2026-08-28',URL_LODZ:'2026-08-25'}.get(u)
  raw=r.get('document_date_raw','')
  if not docdate and re.fullmatch(r'\d{2}\.\d{2}\.\d{4}',raw):docdate=raw[6:]+'-'+raw[3:5]+'-'+raw[:2]
  notes=('Primary official document hosted as a redacted copy by a third party; original electronic signature not verified. ' if doccopy else '')+('Metadata catalog only; no observations extracted. ' if u not in builder.used else 'Used in normalized observations. ')
  if not ok:notes+='No successful snapshot retained; retrieval status='+str(snap.get('status','not_requested'))+'. '
  if r.get('discovered_on'):notes+='Discovered on: '+'; '.join(sorted(set(r['discovered_on'])))
  title={URL_18089:'MSWiA — odpowiedź na interpelację18089: średni czas zakończonych postępowań2023–2026 (27.07.2026)',URL_12584:'MSWiA — odpowiedź na interpelację12584: sprawy art.114 w toku13.10.2025 (22.10.2025)'}.get(u,r.get('title') or u)
  if host=='migracje.gov.pl' and '/wp-json/udscmap/' in u:
   q=parse_qs(urlparse(u).query);title='UdSC portal API — '+('wnioski' if '/applications/' in u else 'decyzje')+' — '+('pobyt czasowy' if q.get('caseType')==['1'] else 'rezydent długoterminowy UE')+' — '+q.get('year',['?'])[0]
  license_note='CC0 1.0 as declared by host' if secondary else 'Official document; copy host declares CC0' if doccopy else 'Not specified in snapshot; official public source' if host in OFFICIAL_PUBLISHER_HOSTS else 'Not specified in snapshot'
  out.append({'id':sid(u),'url':u,'title':title,'publisher':publisher,'authority':authority,'document_date':docdate,'retrieved_at':snap.get('retrieved_at'),'content_sha256':snap.get('content_sha256') if ok else None,'access':access,'license':license_note,'status':'parsed' if u in builder.used else 'catalog_only','notes':notes.strip()})
 return out
def summarize(rows,sources):
 s={'observations':len(rows),'sources':len(sources),'sources_parsed':sum(x['status']=='parsed' for x in sources),'sources_catalog_only':sum(x['status']=='catalog_only' for x in sources),'series_counts':dict(collections.Counter(r['series_id'] for r in rows)),'no_personal_cases':True,'no_forecast_facts':True,'expected_checks':[]}
 s['udsc_pending_totals']=[{'as_of_date':p,'value':sum(r['value'] for r in rows if r['series_id']=='udsc_20260828_pending_stock' and r['reference_period']==p),'unit':'cases','calculation':'sum of16 voivodeships; own calculation, not a published national total','source_id':sid(URL_UDSC)} for p in ['2023-12-31','2024-12-31','2025-12-31','2026-07-01']]
 s['court_national_annual']=[{'year':str(y),**{r['indicator_id']:r['value'] for r in rows if r['series_id']=='nsa_wsa_6272_annual' and r['geography_id']=='PL' and r['reference_period']==str(y)}} for y in range(2020,2026)]
 s['warehouse_concluded_totals']=[{'reference_period':str(y),'value':sum(r['value'] for r in rows if r['series_id']=='warehouse_all_outcomes' and r['indicator_id']=='concluded_resolutions' and r['reference_period']==str(y)),'unit':'cases','calculation':'sum of16 all-outcome counts, not portal decisions'} for y in range(2023,2026)]
 s['mswia_2023_2026_change']=[{'geography_id':gid,'days_2023':next(r['value'] for r in rows if r['series_id']=='mswia_18089_concluded_mean_days' and r['geography_id']==gid and r['reference_period']=='2023'),'days_2026':next(r['value'] for r in rows if r['series_id']=='mswia_18089_concluded_mean_days' and r['geography_id']==gid and r['reference_period'].startswith('2026'))} for gid,*_ in GEOGRAPHIES]
 for r in s['mswia_2023_2026_change']:r['change_days']=r['days_2026']-r['days_2023']
 s['expected_checks']=[{'check':'MSWiA18089:16voivodeships*4periods','expected':64,'actual':sum(r['series_id']=='mswia_18089_concluded_mean_days' for r in rows)}, {'check':'UdSC pending2026 sum16','expected':803223,'actual':s['udsc_pending_totals'][-1]['value']},{'check':'WSA6272 inflow2025','expected':3559,'actual':s['court_national_annual'][-1]['court_inflow']},{'check':'WSA6272 upheld2025','expected':432,'actual':s['court_national_annual'][-1]['court_upheld']},{'check':'Warehouse all-outcome concluded2025 sum16','expected':398337,'actual':s['warehouse_concluded_totals'][-1]['value']}]
 s['limitations']=['Concluded-duration means exclude ongoing cases; means are not medians or individual forecasts.','Administrative regions and WSA court jurisdictions are different geography levels.','Stock, flow, staff headcount and disposition shares must not be plotted as one interchangeable series.','MSWiA12584 mean has an ambiguous cohort; no pending-age interpretation is asserted.','UdSC regional labels are redacted or not directly legible: geographic assignment is reconstructed, while the sum of16 numeric rows is independent of those labels.','UdSC2026 pending stocks may have a reporting/scope discontinuity; Łódź own-office counts have a different cut-off and incompletely specified scope.','All2026 periods are partial; full-year2025 is not a like-for-like annual flow comparator.','Warehouse2026 cut-off is unknown: as_of_date=null, period_ambiguous; excluded from annual scenario baselines.','NSA symbol6272 includes visas/residence/settlement/expulsion; WSA disposition outcomes are not NSA cassation outcomes.','No forecast from the secondary reports is treated as fact. No chat messages, personal cases, raw correspondence, PDF/XLS binaries or secrets are published.']
 return s
def write_csv(path,rows):
 if not rows:return
 with path.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else '' if v is None else v for k,v in r.items()})
def build(allow_unreviewed=False,output=None):
 catalog=json.loads((CACHE/'discovered_catalog.json').read_text(encoding='utf-8'));b=Builder(allow_unreviewed)
 b.parse_mswia();b.parse_udsc();b.parse_lodz();b.parse_warehouse();b.parse_courts(catalog);b.parse_portal()
 sources=catalog_sources(b,catalog);summary=summarize(b.rows,sources)
 release_file=REVIEW/'release.json';release=json.loads(release_file.read_text(encoding='utf-8')) if release_file.exists() else {'version':'1.0.0','as_of':AS_OF}
 result={'version':release['version'],'as_of':release['as_of'],'observations':b.rows,'sources':sources,'definitions':definitions,'geographies':geographies,'summary':summary}
 target=Path(output) if output else CURATED/'dataset.json'
 if allow_unreviewed and not output:raise ValueError('Unreviewed candidates require an explicit output outside public data/')
 if allow_unreviewed and target.resolve().is_relative_to(ROOT.resolve()):raise ValueError('Unreviewed candidates must be written outside the public repository')
 jwrite(target,result)
 if not output:
  for name,value in [('observations',b.rows),('sources',sources),('definitions',definitions),('geographies',geographies),('summary',summary)]:jwrite(CURATED/(name+'.json'),value)
  write_csv(CURATED/'observations.csv',b.rows);write_csv(CURATED/'sources.csv',sources)
  series_dictionary=[]
  for k,v in SERIES.items():
   matched=[r for r in b.rows if r['series_id']==k]
   series_dictionary.append({'id':k,'indicator_id':v[0],'unit':v[1],'stage':v[2],'indicator_ids':sorted({r['indicator_id'] for r in matched}),'units':sorted({r['unit'] for r in matched}),'permit_types':sorted({r['permit_type'] for r in matched}),'geography_levels':sorted({r['geography_level'] for r in matched})})
  jwrite(DATA/'dictionary.json',{'series':series_dictionary,'indicators':[{'id':i,'units':sorted({r['unit'] for r in b.rows if r['indicator_id']==i}),'statistics':sorted({r['statistic'] for r in b.rows if r['indicator_id']==i})} for i in sorted({r['indicator_id'] for r in b.rows})],'court_indicators':['court_inflow','court_pending_start','court_pending_end','court_resolved','court_upheld','court_dismissed','court_rejected','court_other_resolved','court_closed','court_resolved_including_closed','court_upheld_merits_pct','court_rejected_resolved_pct'],'source_keys':{'mswia18089':sid(URL_18089),'mswia12584':sid(URL_12584),'udsc20260828':sid(URL_UDSC),'lodz20260825':sid(URL_LODZ),'lodzWarehouse':sid(URL_LODZ_WAREHOUSE),'warehouseCover':sid(URL_PODLASKI_COVER)}})
 print(json.dumps({'observations':len(b.rows),'sources':len(sources),'used_primary_snapshots':len(b.used),'output':str(target)},ensure_ascii=False))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--candidate',action='store_true');p.add_argument('--output');a=p.parse_args();build(a.candidate,a.output)
