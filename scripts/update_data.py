#!/usr/bin/env python3
"""Snapshot, propose and explicitly review public aggregate updates; never publish."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,subprocess,sys
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from source_pipeline import ROOT,CACHE,discover,fetch_many,manifest,content,jwrite,sid,utcnow

APPROVALS=ROOT/'data/review/approved_sources.json'
def approvals():
 return json.loads(APPROVALS.read_text(encoding='utf-8')) if APPROVALS.exists() else {}
def state():
 snaps=manifest();reviewed=approvals();changes=[]
 for key,r in reviewed.items():
  current=snaps.get(r['url'],{})
  changes.append({'source_id':key,'url':r['url'],'status':current.get('status'),'review':'approved_hash' if current.get('content_sha256')==r['content_sha256'] and current.get('status')==200 else 'review_required'})
 return {'cache':str(CACHE),'snapshots':len(snaps),'approved_sources':len(reviewed),'review_required':sum(r['review']=='review_required' for r in changes),'sources':changes}
def snapshot_all(refresh=False):
 discover(refresh)
 urls=[v['url'] for v in approvals().values()]
 portal='https://glos-migranta.eu/dane/portal-czasowy-rezydent.csv'
 for r in csv.DictReader(io.StringIO(content(portal).decode('utf-8-sig'))):
  u=r['zrodlo_url'];query=parse_qs(urlparse(u).query)
  if int(query['year'][0])>=2023:urls.append(u)
 fetch_many(urls,refresh=refresh)
 return state()
def approve(source_id,expected_sha256,review_note,reviewer):
 if not re.fullmatch(r'[a-f0-9]{64}',expected_sha256):raise ValueError('Expected SHA256 must have64 lowercase hex characters')
 if len(review_note.strip())<20 or not reviewer.strip():raise ValueError('A named reviewer and substantive review note are required')
 candidates=[r for u,r in manifest().items() if sid(u)==source_id]
 if len(candidates)!=1:raise ValueError('Source ID not uniquely present in local snapshot manifest')
 rec=candidates[0]
 if rec.get('status')!=200 or rec.get('content_sha256')!=expected_sha256:raise ValueError('Expected SHA256 does not match the successful current snapshot')
 if hashlib.sha256(content(rec['url'])).hexdigest()!=expected_sha256:raise ValueError('Cached bytes mismatch')
 reviewed=approvals();reviewed[source_id]={'url':rec['url'],'content_sha256':expected_sha256,'reviewed_at':utcnow(),'reviewer':reviewer.strip(),'review_notes':review_note.strip()};jwrite(APPROVALS,reviewed)
 return {'source_id':source_id,'review':'approved_hash','public_dataset_changed':False}
def promote(as_of,version):
 from build_dataset import build
 # Review/hash checks and complete parsing precede any release metadata mutation.
 candidate=CACHE/'promotion-check.json';build(False,candidate)
 date.fromisoformat(as_of)
 if as_of>date.today().isoformat():raise ValueError('Release as_of cannot be in the future')
 if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Version must have major.minor.patch form')
 jwrite(ROOT/'data/review/release.json',{'version':version,'as_of':as_of})
 build()
 subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],cwd=ROOT,check=True)
 return {'reviewed_dataset_built':True,'published':False,'as_of':as_of,'version':version}
def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 sub.add_parser('status',help='Local review status; no network')
 s=sub.add_parser('snapshot',help='Fetch four pages, tabular links and primary sources into external cache');s.add_argument('--refresh',action='store_true')
 s=sub.add_parser('propose',help='Build an unreviewed candidate outside the repository');s.add_argument('--output',type=Path,default=CACHE/'candidate.json')
 s=sub.add_parser('approve-source',help='Record a human review of one exact source hash; does not rebuild/publicize data');s.add_argument('--source-id',required=True);s.add_argument('--expected-sha256',required=True);s.add_argument('--review-note',required=True);s.add_argument('--reviewer',required=True)
 s=sub.add_parser('promote',help='Offline reviewed build plus tests; no git commit, push or publication');s.add_argument('--as-of',required=True);s.add_argument('--version',default='1.0.0')
 a=p.parse_args()
 if a.command=='status':result=state()
 elif a.command=='snapshot':result=snapshot_all(a.refresh)
 elif a.command=='propose':
  from build_dataset import build
  result=build(True,a.output);result={'candidate':str(a.output),'observations':len(result['observations']),'published':False}
 elif a.command=='approve-source':result=approve(a.source_id,a.expected_sha256,a.review_note,a.reviewer)
 else:result=promote(a.as_of,a.version)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
