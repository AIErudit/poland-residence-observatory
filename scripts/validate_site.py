"""Check generated public output, provenance and local URL targets."""
from __future__ import annotations
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'

class Page(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set();self.meta={};self.lang=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html':self.lang=a.get('lang')
        if 'id' in a:self.ids.add(a['id'])
        if tag in ('a','link','script','img'):
            value=a.get('href') or a.get('src')
            if value:self.links.append(value)
        if tag=='meta':self.meta[a.get('property') or a.get('name')]=a.get('content')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--release',action='store_true');args=parser.parse_args()
    failures=[]
    data=json.loads((OUT/'data/dataset.json').read_text(encoding='utf-8'))
    claims=json.loads((OUT/'data/claims.json').read_text(encoding='utf-8'))
    known={o['id'] for o in data['observations']}
    sources={s['id'] for s in data['sources']}
    for c in claims:
        if not c['observation_ids'] or not set(c['observation_ids'])<=known:failures.append('Invalid observation references: '+c['id'])
        if not set(c['source_ids'])<=sources:failures.append('Invalid source references: '+c['id'])
        for lang in ['pl','be','en']:
            for key in ['title','body','caveat']:
                if not c.get(key+'_'+lang):failures.append('Missing claim copy: '+c['id'])
    pages=list(OUT.rglob('*.html'))
    for path in pages:
        content=path.read_text(encoding='utf-8');page=Page();page.feed(content)
        if '__METRICS__' in content or '__FACTS__' in content:failures.append('Unfilled template: '+str(path))
        if not page.lang:failures.append('Missing page language: '+str(path))
        for link in page.links:
            parsed=urlparse(link)
            if parsed.scheme or link.startswith('//') or not parsed.path:continue
            target=(OUT/parsed.path.removeprefix('/poland-residence-observatory/')) if parsed.path.startswith('/poland-residence-observatory/') else path.parent/unquote(parsed.path)
            if target.is_dir():target=target/'index.html'
            if not target.exists():failures.append(f'Broken local link: {path.relative_to(OUT)} -> {link}')
        if path.name=='index.html':
            for key in ['description','og:title','og:description','og:image','twitter:card']:
                if not page.meta.get(key):failures.append(f'Missing {key}: {path}')
            image=page.meta.get('og:image','').split('/assets/')[-1]
            if not (OUT/'assets'/image).exists():failures.append('Missing social preview: '+image)
    forbidden_suffixes={'.pdf','.xlsx','.xls','.zip','.jsonl','.env'}
    for path in OUT.rglob('*'):
        if not path.is_file():continue
        if path.suffix in forbidden_suffixes:failures.append('Unapproved raw artifact: '+str(path))
        if path.suffix in {'.html','.js','.json','.md','.csv','.py'}:
            text=path.read_text(encoding='utf-8')
            if any(token in text for token in ['C:\\Users\\','D:\\residence permit\\Chats','ghp_','github_pat_']):failures.append('Private path/credential marker in '+str(path))
    if args.release:
        release_path=ROOT/'verification/round2/release.json'
        if not release_path.exists():failures.append('Independent release review is missing')
        else:
            release=json.loads(release_path.read_text(encoding='utf-8'))
            if release.get('status')!='approved':failures.append('Release review has not approved this snapshot')
            hashes=release.get('file_sha256',{})
            if not hashes:failures.append('Release review has no reviewed file hashes')
            for relative,expected in hashes.items():
                p=ROOT/relative
                if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:failures.append('Changed since verification: '+relative)
            if set(release.get('claim_ids',[]))!={c['id'] for c in claims}:failures.append('Claim IDs do not match release review')
    if failures:
        raise SystemExit('\n'.join(failures))
    print(json.dumps({'status':'passed','html_pages':len(pages),'claims':len(claims),'observations':len(data['observations']),'sources':len(data['sources']),'release_gate':args.release},indent=2))

if __name__=='__main__':main()
