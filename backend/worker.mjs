// Cloudflare module Worker. No raw responses or contact data are publicly readable.
const ORIGIN='https://aierudit.github.io';
const DAY=86400000;
const REGIONS=['PL-DS','PL-KP','PL-LU','PL-LB','PL-LD','PL-MA','PL-MZ','PL-OP','PL-PK','PL-PD','PL-PM','PL-SL','PL-SK','PL-WN','PL-WP','PL-ZP'];
const ENUMS={permit:['temporary','permanent','eu_long_term'],status:['pending','positive','negative','discontinued','unexamined'],basis:['work','family','study','business','other'],submission:['mos','post','in_person','other'],nationality:['BY','UA','RU','other'],court_outcome:['pending','upheld','dismissed','rejected','other'],bank:['millennium','pko_bp','pekao','other'],bank_issue:['opening','digital','card','termination','other']};
const MULTI={difficulties:['appointment','delivery','documents','no_response','bank','work','travel','other'],actions:['ponaglenie','wsa','lawyer','rpo','bank_complaint']};
const encoder=new TextEncoder();
const b64=bytes=>btoa(String.fromCharCode(...bytes)).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');
const unb64=s=>Uint8Array.from(atob(s.replaceAll('-','+').replaceAll('_','/').padEnd(Math.ceil(s.length/4)*4,'=')),c=>c.charCodeAt(0));
const hex=bytes=>Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
async function sha(s){return hex(new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(s))));}
async function mac(key,value){const k=await crypto.subtle.importKey('raw',encoder.encode(key),{name:'HMAC',hash:'SHA-256'},false,['sign']);return hex(new Uint8Array(await crypto.subtle.sign('HMAC',k,encoder.encode(value))));}
async function constantEqual(a,b){return await sha(a||'')===await sha(b||'');}
function response(data,status=200,origin=ORIGIN){return new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json','Access-Control-Allow-Origin':origin,'Vary':'Origin','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'}});}
function dateValue(s){if(typeof s!=='string'||!/^20\d{2}-\d{2}-\d{2}$/.test(s))return null;const d=new Date(s+'T00:00:00Z');return Number.isFinite(+d)&&d.toISOString().slice(0,10)===s?+d:null;}
export function validateSubmission(input,now=Date.now()){
 if(!input||typeof input!=='object'||Array.isArray(input))throw Error('invalid_input');
 const allowed=new Set(['region','permit','status','applied_date','decision_date','reported_days','basis','submission','nationality','court_outcome','bank','bank_issue','household_size','difficulties','actions','email','contact_consent','consent','privacy_version','turnstile_token','website','request_id','deletion_token']);
 if(Object.keys(input).some(k=>!allowed.has(k)))throw Error('unexpected_field');
 if(typeof input.request_id!=='string'||! /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(input.request_id)||typeof input.deletion_token!=='string'||! /^[A-Za-z0-9_-]{43}$/.test(input.deletion_token))throw Error('invalid_receipt');
 if(!REGIONS.includes(input.region)||!ENUMS.permit.includes(input.permit)||!ENUMS.status.includes(input.status))throw Error('required_fields');
 if(input.consent!==true||input.privacy_version!=='2026-10-20')throw Error('consent_required');
 const applied=dateValue(input.applied_date),decision=input.decision_date?dateValue(input.decision_date):null;
 const today=Math.floor(now/DAY)*DAY;
 if(applied==null||applied< Date.UTC(2014,0,1)||applied>today)throw Error('invalid_dates');
 if(input.status!=='pending'&&(decision==null||decision<applied||decision>today))throw Error('decision_date_required');
 if(input.status==='pending'&&input.decision_date)throw Error('pending_has_decision');
 const out={region:input.region,permit:input.permit,status:input.status,applied_date:input.applied_date,decision_date:input.status==='pending'?null:input.decision_date,observed_date:new Date(today).toISOString().slice(0,10),elapsed_days:Math.round(((input.status==='pending'?today:decision)-applied)/DAY)};
 for(const [key,values] of Object.entries(ENUMS))if(!['permit','status'].includes(key)&&input[key]){if(!values.includes(input[key]))throw Error('invalid_enum');out[key]=input[key];}
 for(const [key,values] of Object.entries(MULTI))if(input[key]!=null){if(!Array.isArray(input[key])||input[key].length>values.length||input[key].some(v=>!values.includes(v)))throw Error('invalid_enum');out[key]=[...new Set(input[key])];}
 if(input.household_size!=null&&input.household_size!==''){if(!Number.isInteger(input.household_size)||input.household_size<1||input.household_size>10)throw Error('invalid_household');out.household_size=input.household_size;}
 if(input.reported_days!=null&&input.reported_days!==''){if(!Number.isInteger(input.reported_days)||input.reported_days<0||input.reported_days>10000)throw Error('invalid_duration');out.reported_days=input.reported_days;}
 let email=null;
 if(input.email){if(typeof input.email!=='string'||input.email.length>254||! /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.email)||input.contact_consent!==true)throw Error('contact_consent_required');email=input.email;}
 return {payload:out,email};
}
async function encryptEmail(email,key){const iv=crypto.getRandomValues(new Uint8Array(12));const k=await crypto.subtle.importKey('raw',unb64(key),'AES-GCM',false,['encrypt']);const ciphertext=await crypto.subtle.encrypt({name:'AES-GCM',iv},k,encoder.encode(email));return b64(iv)+'.'+b64(new Uint8Array(ciphertext));}
async function jsonBody(req,max=8192){if(Number(req.headers.get('Content-Length')||0)>max)throw Error('body_too_large');const reader=req.body?.getReader();if(!reader)throw Error('invalid_input');let size=0,chunks=[];while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>max){await reader.cancel();throw Error('body_too_large');}chunks.push(value);}const all=new Uint8Array(size);let i=0;for(const chunk of chunks){all.set(chunk,i);i+=chunk.length;}try{return JSON.parse(new TextDecoder().decode(all));}catch{throw Error('invalid_json');}}
async function prune(env,now=Date.now()){await env.DB.batch([env.DB.prepare('DELETE FROM contacts WHERE expires_at < ?').bind(now),env.DB.prepare('DELETE FROM responses WHERE expires_at < ?').bind(now),env.DB.prepare('DELETE FROM rate_limits WHERE expires_at < ?').bind(now)]);}
async function rateLimit(req,env,now){const ip=req.headers.get('CF-Connecting-IP')||'unknown';const bucket=await mac(env.RATE_SECRET,Math.floor(now/(10*60000))+':'+ip);const row=await env.DB.prepare('INSERT INTO rate_limits(bucket,attempts,expires_at) VALUES (?,1,?) ON CONFLICT(bucket) DO UPDATE SET attempts=attempts+1 RETURNING attempts').bind(bucket,now+20*60000).first();return row.attempts<=10;}
export default {
 async fetch(req,env){
  const url=new URL(req.url),origin=req.headers.get('Origin');
  if(req.method==='OPTIONS')return new Response(null,{status:origin===ORIGIN?204:403,headers:{'Access-Control-Allow-Origin':ORIGIN,'Access-Control-Allow-Methods':'POST, GET, OPTIONS','Access-Control-Allow-Headers':'Content-Type','Access-Control-Max-Age':'600','Vary':'Origin'}});
  if(url.pathname==='/health'&&req.method==='GET')return response({status:'ok',schema_version:1,collection_enabled:env.COLLECTION_ENABLED==='true',privacy_version:'2026-10-20'});
  // Administration uses a separate secret; no browser client receives it.
  if(url.pathname==='/admin/export'&&req.method==='GET'){
   if(!env.ADMIN_TOKEN||!await constantEqual(req.headers.get('Authorization'),'Bearer '+env.ADMIN_TOKEN))return response({error:'unauthorized'},401);
   await prune(env);const rows=await env.DB.prepare('SELECT id,created_at,payload,review_status FROM responses ORDER BY created_at LIMIT 1000').all();
   return response({schema_version:1,rows:rows.results,limit:1000});
  }
  if(origin!==ORIGIN)return response({error:'origin_not_allowed'},403);
  if(req.method!=='POST'||!['/v1/responses','/v1/delete'].includes(url.pathname))return response({error:'not_found'},404);
  if(!(req.headers.get('Content-Type')||'').startsWith('application/json'))return response({error:'json_required'},415);
  try{
   if(!await rateLimit(req,env,Date.now()))return response({error:'rate_limited'},429);
   const input=await jsonBody(req);
   if(url.pathname==='/v1/delete'){
    if(typeof input.id!=='string'||! /^[0-9a-f-]{36}$/.test(input.id)||typeof input.token!=='string'||input.token.length<32||input.token.length>100)return response({error:'invalid_deletion_receipt'},400);
    const row=await env.DB.prepare('SELECT deletion_hash FROM responses WHERE id=?').bind(input.id).first();
    if(row&&await constantEqual(row.deletion_hash,await sha(input.token)))await env.DB.batch([env.DB.prepare('DELETE FROM contacts WHERE response_id=?').bind(input.id),env.DB.prepare('DELETE FROM responses WHERE id=?').bind(input.id)]);
    else if(row)return response({error:'invalid_deletion_receipt'},403);
    return response({deleted:true});
   }
   if(env.COLLECTION_ENABLED!=='true'||!env.TURNSTILE_SECRET||!env.CONTACT_KEY)return response({error:'collection_unavailable'},503);
   if(input.website)return response({error:'invalid_input'},400);
   const {payload,email}=validateSubmission(input);
   const submissionHash=await mac(env.RATE_SECRET,JSON.stringify({...payload,observed_date:null,elapsed_days:null})+'\n'+(email||''));
   const existing=await env.DB.prepare('SELECT deletion_hash,submission_hash,created_at,expires_at FROM responses WHERE id=?').bind(input.request_id).first();
   if(existing){
    if(!await constantEqual(existing.deletion_hash,await sha(input.deletion_token))||!await constantEqual(existing.submission_hash,submissionHash))return response({error:'receipt_conflict'},409);
    return response({accepted:true,id:input.request_id,deletion_token:input.deletion_token,expires_at:new Date(existing.expires_at).toISOString(),idempotent:true},201);
   }
   if(typeof input.turnstile_token!=='string'||input.turnstile_token.length<5||input.turnstile_token.length>2048)return response({error:'verification_required'},400);
   const check=await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({secret:env.TURNSTILE_SECRET,response:input.turnstile_token})});
   if(!check.ok)return response({error:'verification_unavailable'},503);
   const verified=await check.json();
   if(!verified.success||verified.hostname!=='aierudit.github.io'||verified.action!=='residence_survey')return response({error:'verification_failed'},400);
   const now=Date.now(),id=input.request_id,token=input.deletion_token;
   const statements=[env.DB.prepare('INSERT INTO responses(id,created_at,expires_at,deletion_hash,submission_hash,schema_version,payload,privacy_version,consent_at) VALUES (?,?,?,?,?,1,?,?,?)').bind(id,now,now+730*DAY,await sha(token),submissionHash,JSON.stringify(payload),input.privacy_version,now)];
   if(email)statements.push(env.DB.prepare('INSERT INTO contacts(response_id,encrypted_email,expires_at,privacy_version,consent_at) VALUES (?,?,?,?,?)').bind(id,await encryptEmail(email,env.CONTACT_KEY),now+180*DAY,input.privacy_version,now));
   await env.DB.batch(statements);
   return response({accepted:true,id,deletion_token:token,expires_at:new Date(now+730*DAY).toISOString(),contact_expires_at:email?new Date(now+180*DAY).toISOString():null},201);
  }catch(error){const expected=['invalid_receipt','invalid_input','unexpected_field','required_fields','consent_required','invalid_dates','decision_date_required','pending_has_decision','invalid_enum','invalid_household','invalid_duration','contact_consent_required','body_too_large','invalid_json'];return response({error:expected.includes(error.message)?error.message:'service_unavailable'},expected.includes(error.message)?400:503);}
 },
 async scheduled(_event,env,ctx){ctx.waitUntil(prune(env));}
};
