"""Semantic/golden validation of the public release; network/cache not needed."""
import collections,csv,datetime,hashlib,io,json,math,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import source_pipeline
from build_dataset import Builder,num

class DatasetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((ROOT/'data/curated/dataset.json').read_text(encoding='utf-8'))
  cls.rows=cls.data['observations'];cls.byid={r['id']:r for r in cls.rows}
  cls.sources={r['id']:r for r in cls.data['sources']}
  cls.approved=json.loads((ROOT/'data/review/approved_sources.json').read_text(encoding='utf-8'))
 def select(self,**kw):return [r for r in self.rows if all(r[k]==v for k,v in kw.items())]
 def one(self,**kw):
  rows=self.select(**kw);self.assertEqual(len(rows),1,kw);return rows[0]
 def test_schema_references_and_dates(self):
  required={'id','series_id','indicator_id','geography_id','geography_name','geography_level','permit_type','stage','reference_period','as_of_date','unit','value','statistic','denominator','source_id','source_locator','definition_id','quality_status','comparability_group','notes'}
  self.assertEqual(len(self.rows),len(self.byid));self.assertEqual(len(self.sources),len(self.data['sources']))
  definitions={x['id'] for x in self.data['definitions']};geos={x['id'] for x in self.data['geographies']}
  datetime.date.fromisoformat(self.data['as_of'])
  for r in self.rows:
   self.assertEqual(set(r),required);self.assertIn(r['source_id'],self.sources);self.assertIn(r['definition_id'],definitions);self.assertIn(r['geography_id'],geos)
   self.assertTrue(r['source_locator']);self.assertTrue(r['comparability_group']);self.assertFalse(r['quality_status'].startswith('unreviewed'))
   if r['as_of_date'] is None:
    self.assertIn('period_ambiguous',r['quality_status']);self.assertIn('UNKNOWN',r['notes']);self.assertEqual(r['reference_period'],'2026')
   else:datetime.date.fromisoformat(r['as_of_date'])
   if r['value'] is not None:self.assertTrue(math.isfinite(r['value']));self.assertGreaterEqual(r['value'],0)
 def test_published_sources_exactly_reviewed_hashes(self):
  parsed={s['id'] for s in self.sources.values() if s['status']=='parsed'}
  self.assertEqual(parsed,set(self.approved))
  for key in parsed:
   self.assertEqual(self.sources[key]['content_sha256'],self.approved[key]['content_sha256'])
   self.assertEqual(self.sources[key]['url'],self.approved[key]['url'])
   self.assertRegex(self.sources[key]['content_sha256'],r'^[a-f0-9]{64}$')
  for r in self.rows:self.assertIn(r['source_id'],parsed)
  self.assertGreater(sum(s['status']=='catalog_only' for s in self.sources.values()),1000)
 def test_stock_is_not_flow(self):
  for r in self.rows:
   if r['indicator_id']=='pending_cases':self.assertEqual(r['stage'],'pending');self.assertEqual(r['unit'],'cases');self.assertEqual(r['statistic'],'count')
   if r['indicator_id'] in ['applications_received','decisions_issued']:self.assertEqual(r['stage'],r['indicator_id']);self.assertEqual(r['unit'],'cases')
   if r['indicator_id'].startswith('processing_duration_'):self.assertEqual(r['unit'],'days');self.assertIn(r['stage'],['concluded','concluded_positive'])
   if r['unit']=='persons':self.assertEqual(r['stage'],'staff')
   if r['unit']=='percent':self.assertEqual(r['statistic'],'share');self.assertIsNotNone(r['denominator'])
 def test_strict_sixteen_region_coverage(self):
  expected={x['id'] for x in self.data['geographies'] if x['id'].startswith('PL-')}
  self.assertEqual(len(expected),16)
  for series in ['mswia_18089_concluded_mean_days','udsc_20260828_concluded_mean_days','udsc_20260828_blue_card_mean_days','udsc_20260828_pending_stock','warehouse_all_outcomes']:
   groups=collections.defaultdict(list)
   for r in self.select(series_id=series):groups[(r['indicator_id'],r['reference_period'])].append(r)
   for key,rows in groups.items():self.assertEqual(len(rows),16,(series,key));self.assertEqual({r['geography_id'] for r in rows},expected)
 def test_udsc_stock_golden_and_reconstructed_geography(self):
  for period,expected in [('2023-12-31',387312),('2024-12-31',484201),('2025-12-31',646232),('2026-07-01',803223)]:
   rows=self.select(series_id='udsc_20260828_pending_stock',reference_period=period)
   self.assertEqual(sum(r['value'] for r in rows),expected)
  for r in self.rows:
   if r['series_id'].startswith('udsc_20260828_'):
    self.assertIn('geography_reconstructed',r['quality_status']);self.assertIn('not directly legible',r['notes']);self.assertIn('does not depend',r['notes'])
 def test_mswia_cohorts_and_historical_discrepancy_preserved(self):
  self.assertEqual(self.one(series_id='mswia_12584_pending_count',geography_id='PL')['value'],463487)
  self.assertEqual(self.one(series_id='mswia_12584_reported_mean_days',geography_id='PL')['value'],341)
  for r in self.select(series_id='mswia_12584_reported_mean_days'):self.assertEqual(r['definition_id'],'mswia12584_mean_ambiguous');self.assertIn('ambiguous',r['quality_status'])
  self.assertEqual(self.one(series_id='mswia_18089_concluded_mean_days',geography_id='PL-ZP',reference_period='2024')['value'],472)
  self.assertEqual(self.one(series_id='udsc_20260828_concluded_mean_days',geography_id='PL-ZP',reference_period='2024')['value'],471)
 def test_warehouse_counts_not_portal_counts(self):
  for year,total in [('2023',437687),('2024',396808),('2025',398337)]:
   rows=self.select(series_id='warehouse_all_outcomes',indicator_id='concluded_resolutions',reference_period=year)
   self.assertEqual(sum(r['value'] for r in rows),total)
  self.assertEqual(self.one(series_id='udsc_portal_temporary_decisions',reference_period='2025')['value'],445462)
  ambiguous=self.select(series_id='warehouse_all_outcomes',reference_period='2026');self.assertEqual(len(ambiguous),48)
  for r in ambiguous:self.assertIsNone(r['as_of_date']);self.assertIn('period_ambiguous',r['quality_status'])
  self.assertEqual({x['reference_period'] for x in self.data['summary']['warehouse_concluded_totals']},{'2023','2024','2025'})
 def test_warehouse_denominators_match_cohorts(self):
  for r in self.rows:
   if r['series_id'] not in ['warehouse_all_outcomes','lodz_warehouse_all_outcomes','lodz_warehouse_positive_decisions'] or r['unit']!='days':continue
   d=r['denominator'];self.assertEqual(d['unit'],'cases');self.assertEqual(len(d['observation_ids']),1)
   n=self.byid[d['observation_ids'][0]];self.assertEqual(n['value'],d['value']);self.assertEqual(n['indicator_id'],'concluded_resolutions')
   for k in ['series_id','geography_id','permit_type','reference_period','source_id']:self.assertEqual(r[k],n[k])
 def test_lodz_headcounts_and_ratio(self):
  for y,stock,workers,total in [(2023,27179,37,88),(2024,27016,38,90),(2025,33979,36,82),(2026,49844,38,83)]:
   period=f'{y}-12-31' if y<2026 else '2026-08-25'
   self.assertEqual(self.one(series_id='lodz_pending_stock',reference_period=period)['value'],stock)
   self.assertEqual(self.one(series_id='lodz_caseworkers',reference_period=period)['value'],workers)
   self.assertEqual(self.one(series_id='lodz_staff_headcount',reference_period=period)['value'],total)
  for r in self.select(series_id='lodz_pending_per_caseworker'):
   d=r['denominator'];self.assertEqual(d['unit'],'persons');worker=self.byid[d['observation_ids'][0]];stock=self.byid[d['numerator_observation_ids'][0]]
   self.assertEqual(worker['value'],d['value']);self.assertAlmostEqual(r['value'],stock['value']/worker['value'],places=5)
  self.assertEqual(self.one(series_id='lodz_caseworkers',reference_period='2026-08-25')['value'],38)
  self.assertEqual(self.one(series_id='lodz_staff_headcount',reference_period='2026-08-25')['value'],83)
  self.assertEqual(self.one(series_id='lodz_pending_per_caseworker',reference_period='2026-08-25')['value'],1311.684211)
 def test_court_movements_outcomes_and_sixteen_courts(self):
  for year in map(str,range(2020,2026)):
   rows=self.select(series_id='nsa_wsa_6272_annual',reference_period=year);groups=collections.defaultdict(dict)
   for r in rows:groups[r['geography_id']][r['indicator_id']]=r
   self.assertEqual(len(groups),17);self.assertEqual(groups['PL']['court_inflow']['geography_level'],'country')
   for gid,g in groups.items():
    v=lambda k:g[k]['value']
    self.assertEqual(g['court_pending_start']['as_of_date'],year+'-01-01')
    self.assertEqual(g['court_pending_start']['definition_id'],'court_opening_stock')
    self.assertEqual(g['court_pending_end']['as_of_date'],year+'-12-31')
    self.assertEqual(v('court_pending_start')+v('court_inflow'),v('court_resolved_including_closed')+v('court_pending_end'))
    self.assertEqual(v('court_resolved_including_closed'),v('court_resolved')+v('court_closed'))
    self.assertEqual(v('court_resolved'),sum(v(k) for k in ['court_upheld','court_dismissed','court_rejected','court_other_resolved']))
    if gid!='PL':self.assertEqual(g['court_inflow']['geography_level'],'court_jurisdiction')
   for ind,r in groups['PL'].items():
    if r['unit']=='cases':self.assertEqual(r['value'],sum(g[ind]['value'] for gid,g in groups.items() if gid!='PL'))
 def test_court_calculated_shares_and_nulls(self):
  nulls=[]
  for r in self.select(series_id='nsa_wsa_6272_annual'):
   if r['unit']!='percent':continue
   d=r['denominator'];self.assertEqual(d['value'],sum(self.byid[k]['value'] for k in d['observation_ids']))
   expected_indicators={'court_upheld','court_dismissed'} if r['indicator_id']=='court_upheld_merits_pct' else {'court_resolved'}
   self.assertEqual({self.byid[k]['indicator_id'] for k in d['observation_ids']},expected_indicators)
   if d['value']:self.assertAlmostEqual(r['value'],100*d['numerator_value']/d['value'],places=5)
   else:self.assertIsNone(r['value']);self.assertEqual(r['quality_status'],'not_applicable_zero_denominator');nulls.append(r)
  self.assertTrue(nulls)
  self.assertEqual(self.one(series_id='nsa_wsa_6272_annual',geography_id='WSA-KL',reference_period='2025',indicator_id='court_inflow')['value'],0)
  self.assertIsNone(self.one(series_id='nsa_wsa_6272_annual',geography_id='WSA-KL',reference_period='2025',indicator_id='court_upheld_merits_pct')['value'])
 def test_court_golden_layouts(self):
  expected={'2020':{'court_inflow':4329,'court_resolved':3121,'court_upheld':2179,'court_dismissed':126,'court_rejected':527,'court_closed':325,'court_pending_end':1652},'2025':{'court_inflow':3559,'court_resolved':3579,'court_upheld':432,'court_dismissed':1032,'court_rejected':1873,'court_other_resolved':242,'court_closed':11,'court_pending_end':898}}
  for y,indicators in expected.items():
   for ind,val in indicators.items():self.assertEqual(self.one(series_id='nsa_wsa_6272_annual',geography_id='PL',reference_period=y,indicator_id=ind)['value'],val)
  self.assertEqual(self.one(series_id='nsa_wsa_6272_annual',geography_id='WSA-WA',reference_period='2025',indicator_id='court_inflow')['value'],497)
  defs=' '.join(x['description'] for x in self.data['definitions']);self.assertIn('Zamknięto',defs);self.assertNotIn('Zakreślono',defs)
 def test_official_publisher_allowlist_and_readable_titles(self):
  from build_dataset import OFFICIAL_PUBLISHER_HOSTS,URL_18089,URL_12584
  from urllib.parse import urlparse
  for s in self.sources.values():
   if s['access']=='primary_publisher_snapshot':self.assertIn(urlparse(s['url']).netloc,OFFICIAL_PUBLISHER_HOSTS)
   if s['url'] in [URL_18089,URL_12584]:self.assertIn('MSWiA',s['title']);self.assertNotEqual(s['title'],'źródło')
 def test_summary_matches_expected_values(self):
  s=self.data['summary'];self.assertEqual(s['observations'],len(self.rows));self.assertEqual(s['sources'],len(self.sources))
  for c in s['expected_checks']:self.assertEqual(c['actual'],c['expected'],c['check'])
  self.assertTrue(s['no_personal_cases']);self.assertTrue(s['no_forecast_facts'])
 def test_csv_json_parity_and_lf(self):
  for name in ['observations','sources']:
   path=ROOT/f'data/curated/{name}.csv';raw=path.read_bytes();self.assertNotIn(b'\r',raw)
   rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))));self.assertEqual([r['id'] for r in rows],[r['id'] for r in self.data[name]])
  for p in (ROOT/'data/curated').glob('*.json'):
   self.assertNotIn(b'\r',p.read_bytes())
   if p.stem!='dataset':self.assertEqual(json.loads(p.read_text(encoding='utf-8')),self.data[p.stem])
 def test_no_private_material_or_forecasts_in_observations(self):
  for r in self.rows:self.assertNotIn('forecast',r['series_id']);self.assertNotIn('scenario',r['series_id'])
  for p in (ROOT/'data').rglob('*'):
   if p.is_file():self.assertNotIn(p.suffix.lower(),['.html','.pdf','.xls','.xlsx','.jsonl','.bin'])
  text=json.dumps(self.rows,ensure_ascii=False).lower();self.assertNotIn('telegram',text);self.assertNotIn('chats/',text);self.assertNotIn('message anchor',text)

class ReviewGateTests(unittest.TestCase):
 def test_changed_or_missing_primary_hash_rejected(self):
  b=Builder();url='https://example.test/primary';b.ms={url:{'status':200,'content_sha256':'b'*64}};b.approved={source_pipeline.sid(url):{'content_sha256':'a'*64}}
  with self.assertRaisesRegex(ValueError,'REVIEW REQUIRED'):b.require(url)
  b.ms={}
  with self.assertRaisesRegex(ValueError,'unavailable'):b.require(url)
 def test_candidate_preserves_unreviewed_quality(self):
  b=Builder(True);url='https://example.test/primary';b.ms={url:{'status':200,'content_sha256':'b'*64}};b.approved={}
  r=b.add('test','pending_cases','PL','temporary_residence','pending','2026',None,'cases',1,'count',url,'table1','pending_stock','test',quality='period_ambiguous')
  self.assertEqual(r['quality_status'],'unreviewed_candidate__period_ambiguous')
 def test_snapshot_byte_integrity(self):
  with tempfile.TemporaryDirectory() as tmp:
   cache=Path(tmp);(cache/'test.bin').write_bytes(b'modified');rec={'https://example.test/primary':{'status':200,'file':'test.bin','content_sha256':hashlib.sha256(b'original').hexdigest()}}
   with patch.object(source_pipeline,'CACHE',cache),patch.object(source_pipeline,'manifest',return_value=rec):
    with self.assertRaisesRegex(ValueError,'SHA256'):source_pipeline.content('https://example.test/primary')
 def test_missing_numeric_input_not_zero(self):
  with self.assertRaises(ValueError):num('')
  self.assertEqual(num('0'),0)

if __name__=='__main__':unittest.main()
