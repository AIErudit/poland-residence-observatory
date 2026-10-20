"""Profile every linked /dane CSV without redistributing its rows or personal text."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
CACHE=Path(os.environ.get('OBSERVATORY_CACHE',str(ROOT.parent/'source-cache'/'observatory')))
ROLES={
 'sprawy.csv':'Campaign public-information requests; not a representative sample of all proceedings.',
 'sprawy-kroki.csv':'Campaign procedural steps; request-level observations, not residence applicants.',
 'ranking.csv':'Campaign-derived response ranking; inspect coding and request selection before comparisons.',
 'ranking-kody.csv':'Coding dictionary for the campaign ranking.',
 'dokumenty.csv':'Document catalogue; source discovery, not administrative case counts.',
 'cytaty.csv':'Selected quotations; qualitative selection, not prevalence data. Text not republished.',
 'wojewodztwa.csv':'Regional summary with heterogeneous dates and definitions; primary sources normalized separately.',
 'fami.csv':'Funding/project summary; commitments and applications are not expenditures. Reviewed separately in research/.',
 'sady-skargi-2026.csv':'Partial-year court/registry extracts; not pooled with full-year NSA disposition statistics.',
 'orzeczenia-powolane.csv':'Judgment catalogue; cited cases are not a representative sample of all judgments.',
 'orzeczenia-powolania.csv':'Citation edges between documents and judgments; not case outcomes.',
 'arkusze-katalog.csv':'Workbook/sheet catalogue; extraction inventory, not a homogeneous data series.',
 'czas-mswia-18089.csv':'Derivative cross-check of primary MSWiA 18089; primary table normalized.',
 'hurtownia-wojewodowie.csv':'Warehouse aggregates; primary attachments normalized with source-period qualifications.',
 'niebieska-karta-czas.csv':'Blue Card duration derivative; primary copy normalized separately from temporary residence.',
 'pdf-tabele-katalog.csv':'PDF table extraction catalogue; table presence is not verification of its contents.',
 'portal-czasowy-rezydent.csv':'API-derived applications/decisions; live snapshots normalized, historical revisions recorded.',
 'skany-tabele-katalog.csv':'Scan/OCR extraction catalogue; human checks required before treating OCR cells as facts.',
 'sprawy-w-toku.csv':'Derivative UdSC stock table; primary numeric transcription normalized with regional-label caveat.',
 'teksty-indeks.csv':'Full-text extraction index; document coverage, not a statistical series.',
 'zrodla-zewnetrzne-katalog.csv':'External source catalogue; a link does not establish authority or comparability.'
}

def main():
    manifest=json.loads((CACHE/'manifest.json').read_text(encoding='utf-8'))
    catalog=json.loads((CACHE/'discovered_catalog.json').read_text(encoding='utf-8'))
    urls=sorted({r['url'] for r in catalog if r['url'].startswith('https://glos-migranta.eu/dane/') and r['url'].endswith('.csv')})
    result=[]
    for url in urls:
        name=Path(urlparse(url).path).name;rec=manifest.get(url,{})
        if rec.get('status')!=200:
            result.append({'url':url,'status':'unavailable','notes':ROLES.get(name,'Needs classification.')});continue
        raw=(CACHE/rec['file']).read_bytes();rows=list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
        header=rows[0] if rows else [];values=rows[1:];width=len(header)
        blanks={k:sum(len(row)<=i or not row[i].strip() for row in values) for i,k in enumerate(header)}
        result.append({'url':url,'status':'profiled_not_all_rows_fact_verified','sha256':hashlib.sha256(raw).hexdigest(),'retrieved_at':rec.get('retrieved_at'),'rows':len(values),'columns':header,'width_mismatch_rows':sum(len(r)!=width for r in values),'duplicate_full_rows':len(values)-len(set(tuple(r) for r in values)),'blank_cells_by_column':blanks,'purpose_and_limit':ROLES.get(name,'Needs classification.'),'redistributed_rows':False})
    out={'as_of':'2026-10-20','scope':'All CSV download links found on /dane. Structure/completeness profile, not independent verification of every record. Raw rows remain in the external cache. ZIPs are derivative packages and are catalogued, not asserted to be independently parsed here.','tables':result,'summary':{'csv_links':len(urls),'profiled':sum(r['status']=='profiled_not_all_rows_fact_verified' for r in result),'total_rows_profiled':sum(r.get('rows',0) for r in result),'width_mismatches':sum(r.get('width_mismatch_rows',0) for r in result)}}
    target=ROOT/'coverage/structured-sources.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(out['summary'],indent=2))

if __name__=='__main__':main()
