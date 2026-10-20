"""Read-only public deployment checks; never submits a survey response."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
endpoint=json.loads((ROOT/'site/survey-config.json').read_text(encoding='utf8'))['endpoint'].rstrip('/')
cases=[('health','GET','/health',{}),('admin_without_authorization','GET','/admin/export',{}),('disallowed_preflight','OPTIONS','/v1/responses',{'Origin':'https://example.invalid'})]
def run(case):
    name,method,path,headers=case
    try:
        r=requests.request(method,endpoint+path,headers=headers,timeout=15)
        record={'name':name,'status':r.status_code}
        if name=='health':record['public_body']=r.json()
        expected={'health':200,'admin_without_authorization':401,'disallowed_preflight':403}[name]
        record['passed']=r.status_code==expected
        return record
    except Exception as e:return {'name':name,'passed':False,'error_type':type(e).__name__}
with ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,cases))
report={'checked_at':datetime.now(timezone.utc).isoformat(),'endpoint':endpoint,'status':'pass_readonly_scope' if all(x['passed'] for x in results) else 'unresolved','results':results,'no_survey_post_performed':True,'no_database_mutation_requested':True,'limits':['These checks independently confirm only public health and access rejection at this time.','Deployment source bytes, private binding/secret configuration, EU-jurisdiction and synthetic deletion checks are separately reported by the operator in qa/backend-deployment.json and qa/backend-live.json.','A successful real-browser Turnstile-to-insert journey with a real human is not established by this read-only check; no real personal response was submitted.'],'release_approval':False}
(OUT/'deployment-readcheck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'status':report['status'],'checks':results}))
