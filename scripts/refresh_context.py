"""Snapshot Eurostat and prepare an external candidate, without promotion."""
import argparse
import datetime
import hashlib
import itertools
import json
from pathlib import Path
from urllib.parse import urlparse
import requests

ROOT=Path(__file__).resolve().parents[1]

def rows_from_jsonstat(data):
    dimensions=data['id'];sizes=data['size'];labels=[]
    for name,size in zip(dimensions,sizes):
        index=data['dimension'][name]['category']['index']
        order=index if isinstance(index,list) else sorted(index,key=index.get)
        if len(order)!=size:raise ValueError('Dimension size mismatch')
        labels.append(order)
    for flat,coordinates in enumerate(itertools.product(*labels)):
        value=data.get('value',{})
        value=value[flat] if isinstance(value,list) and flat<len(value) else value.get(str(flat)) if isinstance(value,dict) else None
        if value is None:continue
        status=data.get('status',{})
        flag=status[flat] if isinstance(status,list) and flat<len(status) else status.get(str(flat)) if isinstance(status,dict) else None
        yield flat,dict(zip(dimensions,coordinates)),value,flag

def outside(path):
    path=path.resolve()
    if path==ROOT or ROOT in path.parents:raise ValueError('Snapshots and candidates must remain outside the public repository')
    return path

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    cache=outside(args.cache);target=outside(args.output);cache.mkdir(parents=True,exist_ok=True)
    template=json.loads((ROOT/'research/round2-data/eurostat-context.json').read_text(encoding='utf-8'))
    now=datetime.datetime.now(datetime.timezone.utc);records=[];observations=[]
    for source in template['sources']:
        url=source['url']
        if urlparse(url).hostname!='ec.europa.eu':raise ValueError('Expected official Eurostat source')
        response=requests.get(url,timeout=(15,60),headers={'User-Agent':'ResidenceObservatory-reviewed-candidate/1.1'})
        response.raise_for_status();raw=response.content;sha=hashlib.sha256(raw).hexdigest()
        blobs=cache/'blobs';blobs.mkdir(exist_ok=True);(blobs/(sha+'.bin')).write_bytes(raw)
        data=response.json();record={**source,'retrieved_at':now.isoformat(timespec='seconds'),'content_sha256':sha,'dataset_updated':data.get('updated'),'dimensions':data['id']}
        records.append(record)
        for flat,coords,value,flag in rows_from_jsonstat(data):
            if coords.get('freq')!='A' or coords.get('unit')!='PER' or any(coords.get(k)!='TOTAL' for k in ['duration','reason']):continue
            year=coords['time'];geo=coords['geo'];citizen=coords['citizen']
            if not year.isdigit() or int(year)>=now.year:continue
            if (geo,citizen) not in [('PL','TOTAL'),('EU27_2020','TOTAL'),('PL','BY')]:continue
            if isinstance(value,bool) or not isinstance(value,(int,float)):raise ValueError('Non-numeric observation')
            observations.append({'id':f'es_migr_resfirst_{geo}_{citizen}_{year}','series_id':'eurostat_first_residence_permits_context','indicator_id':'first_residence_permits','category':'context-not-waiting','geography_id':geo,'geography_name':data['dimension']['geo']['category']['label'][geo],'reference_period':year,'as_of_date':year+'-12-31','citizenship_code':citizen,'citizenship_label':data['dimension']['citizen']['category']['label'][citizen],'reason_code':'TOTAL','duration_code':'TOTAL','frequency':coords.get('freq'),'unit_code':'PER','unit_label':data['dimension']['unit']['category']['label']['PER'],'value':value,'flags':flag,'source_id':source['id'],'source_locator':f'JSON-stat value[{flat}]; '+json.dumps(coords,sort_keys=True),'definition_id':'eurostat_first_permit_context','quality_status':'candidate_not_reviewed'})
    yearsets=[{o['reference_period'] for o in observations if (o['geography_id'],o['citizenship_code'])==pair} for pair in [('PL','TOTAL'),('EU27_2020','TOTAL'),('PL','BY')]]
    years=sorted(set.intersection(*yearsets))[-5:]
    if len(years)!=5:raise ValueError('Five common complete years are unavailable; review source coverage')
    selected=[o for o in observations if o['reference_period'] in years]
    if len(selected)!=15:raise ValueError('Expected 3 distinct series × 5 years')
    result={**template,'status':'candidate_not_reviewed','as_of':now.date().isoformat(),'selected_full_years':years,'observations':selected,'sources':records}
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (cache/(now.strftime('%Y%m%dT%H%M%SZ')+'-manifest.json')).write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('15-observation external candidate prepared; independent review and explicit promotion remain required.')
