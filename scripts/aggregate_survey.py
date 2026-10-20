"""Prepare a private review candidate; never publish volunteered personal records."""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parents[1]

def aggregate(rows,min_n=10):
    if min_n<10:raise ValueError('Disclosure threshold must be at least 10')
    seen=set();groups=collections.defaultdict(list);excluded=collections.Counter()
    for row in rows:
        if row.get('review_status')!='accepted':excluded['not_operator_accepted']+=1;continue
        if not row.get('id') or row['id'] in seen:excluded['duplicate_or_missing_id']+=1;continue
        seen.add(row['id'])
        p=row['payload'];p=json.loads(p) if isinstance(p,str) else p
        if p.get('status') not in ['pending','positive','negative','discontinued','unexamined'] or not isinstance(p.get('elapsed_days'),int):excluded['invalid_payload']+=1;continue
        # No dates, citizenship, bank or household cross-tabs. Pending is not completed wait.
        endpoint='pending_elapsed_age' if p['status']=='pending' else 'concluded_duration'
        groups[(p['region'],p['permit'],endpoint)].append(p['elapsed_days'])
    cells=[];suppressed=0
    for (region,permit,endpoint),values in sorted(groups.items()):
        if len(values)<min_n:suppressed+=1;continue
        cells.append({'region':region,'permit':permit,'measure':endpoint,'n':len(values),'median_days':statistics.median(values)})
    return {'status':'private_candidate_requires_disclosure_and_evidence_review','sample':'self_selected_not_population_representative','minimum_group_size':min_n,'cells':cells,'suppressed_groups':suppressed,'exclusions':dict(excluded),'limitations':['Pending age is right-censored and subject to length/selection bias; it is not final waiting time.','Concluded median describes accepted participating cases only, not new applicants.','No totals or marginal tables are emitted; complementary suppression and linkage risk still require human review.','No automatic publication or public endpoint exists.']}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    target=args.output.resolve()
    if target==ROOT or ROOT in target.parents:raise SystemExit('Survey candidates must remain outside the public repository')
    raw=args.input.read_bytes();source=json.loads(raw);rows=source['rows'] if isinstance(source,dict) else source
    result=aggregate(rows);result['input_sha256']=hashlib.sha256(raw).hexdigest();result['prepared_at']=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print('Private candidate prepared; no publication performed.')
