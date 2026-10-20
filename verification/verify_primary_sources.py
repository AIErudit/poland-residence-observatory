"""Independent read-only primary-source checks. Writes only verification/baseline.json.
No articles, private correspondence, raw PDFs or personal records are stored.
"""
from pathlib import Path
import concurrent.futures, csv, hashlib, io, json, re
import requests, pypdf, xlrd
from bs4 import BeautifulSoup
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parent
sources = []
def fetch(sid, url, tier, note=""):
    r = requests.get(url, timeout=45)
    r.raise_for_status()
    sources.append({"id":sid,"url":url,"tier":tier,"http_status":r.status_code,"sha256":hashlib.sha256(r.content).hexdigest(),"retrieved_at":datetime.now(timezone.utc).isoformat(),"note":note})
    return r.content
API18089="https://api.sejm.gov.pl/sejm/term10/interpellations/18089/reply/DWDJHZ/body"
API12584="https://api.sejm.gov.pl/sejm/term10/interpellations/12584/reply/DMQHGV/body"
soup=BeautifulSoup(fetch("MSWIA-18089",API18089,"official_publication"),"html.parser")
table=next(t for t in soup.find_all("table") if all(x in t.get_text() for x in ["2023","2024","2025","2026"]))
mswia=[]
for tr in table.find_all("tr"):
    cells=[c.get_text(" ",strip=True) for c in tr.find_all(["td","th"])]
    if len(cells)==5 and cells[0].startswith("Wojewoda"):
        mswia.append({"organ":cells[0],**{str(y):int(cells[i+1]) for i,y in enumerate(range(2023,2027))}})
assert len(mswia)==16
s12584=BeautifulSoup(fetch("MSWIA-12584",API12584,"official_publication"),"html.parser")
assert "463 487" in s12584.get_text(" ",strip=True)
UDSC="https://glos-migranta.eu/dokumenty/udsc-bsz-waism-0361-16-2026-08-28.pdf"
raw=fetch("UDSC-COPY",UDSC,"agency_response_copy_on_third_party_site","BSZ.WAiSM.0361.16.2026/DH, 28.08.2026; original signed document and agency-hosted publication not independently verified. Organ labels are blacked out; row mapping is inferred from ordering and historical values, not read directly.")
pdf=pypdf.PdfReader(io.BytesIO(raw))
assert "12 sierpnia 2026" in pdf.pages[2].extract_text()
# Numeric transcription checked visually on the complete public-scan pages 3 and 4.
mean2026=[313,536,386,537,385,244,408,504,305,457,610,668,327,271,341,459]
pending=[
[45648,50901,55049,56687],[16836,18721,20646,23517],
[9774,9430,10198,17177],[14001,22369,27615,36772],
[25843,26342,32908,47194],[15873,20315,35606,49772],
[68121,114903,159872,202187],[14939,17125,19561,22179],
[4928,5841,7737,11420],[4805,8172,16834,21208],
[33022,39937,68806,92054],[49604,65710,75510,86059],
[2572,4184,5395,6296],[4346,5387,7500,9365],
[45884,53328,66790,74752],[31116,21536,36205,46584]]
udsc_rows=[{"row":i+1,"inferred_organ":r["organ"],"mean2026":mean2026[i],"pending":dict(zip(["2023-12-31","2024-12-31","2025-12-31","2026-07-01"],pending[i]))} for i,r in enumerate(mswia)]
pending_totals={k:sum(r["pending"][k] for r in udsc_rows) for k in udsc_rows[0]["pending"]}
assert list(pending_totals.values())==[387312,484201,646232,803223]
# Compare public CSV as a derivative, not as evidence for the primary table.
csvrows=list(csv.DictReader(io.StringIO(fetch("GM-MSWIA-CSV","https://glos-migranta.eu/dane/czas-mswia-18089.csv","derivative_dataset").decode("utf-8-sig"))))
lookup={(r["organ"],str(y)):r[str(y)] for r in mswia for y in range(2023,2027)}
mswia_csv_mismatches=[r for r in csvrows if lookup.get((r["organ"],r["rok"]))!=int(r["sredni_czas_dni"])]
idx=BeautifulSoup(fetch("NSA-INDEX","https://www.nsa.gov.pl/dokumenty/statystyki-wsa/","official_publication"),"html.parser")
courts=[]
for year in range(2020,2026):
    a=next(a for a in idx.find_all("a",href=True) if str(year) in a["href"] and ("7_skargi_na_bezczyn" in a["href"] or "7-skargi-na-bezczyn" in a["href"]))
    url="https://www.nsa.gov.pl"+a["href"]
    book=xlrd.open_workbook(file_contents=fetch(f"NSA-{year}",url,"official_publication"))
    yr={"year":year,"source_id":f"NSA-{year}","symbol":6272,"row_1_based":249,"courts":[]}
    for sh in book.sheets():
        matches=[i for i in range(sh.nrows) if any(str(x).strip() in ["6272","6272.0"] for x in sh.row_values(i))]
        if not matches: continue
        row=sh.row_values(matches[0]); cols={}
        for name,term in [("granted","Uwzględniono"),("dismissed_merits","Oddalono"),("rejected_procedural","Odrzucono")]:
            inds=sorted({j for i in range(10) for j,v in enumerate(sh.row_values(i)) if term in str(v)})
            cols[name]=int(sum(float(row[j] or 0) for j in inds))
        disposed_col=next(j for i in range(10) for j,v in enumerate(sh.row_values(i)) if "suma rubryk" in str(v) and "Łącznie" in str(v))
        cols["disposed"]=int(row[disposed_col] or 0)
        cols["incoming"]=int(row[4] or 0)
        cols["merits_denominator"]=cols["granted"]+cols["dismissed_merits"]
        cols["merits_granted_pct"]=round(100*cols["granted"]/cols["merits_denominator"],6) if cols["merits_denominator"] else None
        if sh.name=="WSA SAB Symbole": yr["national"]=cols
        else: yr["courts"].append({"sheet":sh.name,**cols})
    courts.append(yr)
assert courts[-1]["national"]["granted"]==432 and courts[-1]["national"]["dismissed_merits"]==1032
# Warehouse copies: parse named rows and sum counts; copied DIP response, not independently agency-hosted.
warehouse=[]
for year,annex in [(2023,"04"),(2024,"02"),(2025,"01")]:
    url=f"https://glos-migranta.eu/dokumenty/podlaski-ob-ii-1331-16-2026-pt-2026-09-09-decyzja-zal-{annex}-sredni-czas-postepowania-legalizacja-pod.pdf"
    raw=fetch(f"WAREHOUSE-{year}-COPY",url,"agency_response_copy_on_third_party_site","OB-II.1331.16.2026.PT, 09.09.2026; signed original and authority-hosted publication not verified. Includes positive, negative, discontinued and unexamined outcomes by issue date.")
    text=pypdf.PdfReader(io.BytesIO(raw)).pages[0].extract_text()
    matches=re.findall(r"(WOJEWODA[^\n]+)\n(\d+)\n(\d+)",text)
    rows=[{"organ":m[0],"outcomes":int(m[1]),"mean_days":int(m[2])} for m in matches]
    assert len(rows)==16
    warehouse.append({"year":year,"source_id":f"WAREHOUSE-{year}-COPY","total_outcomes":sum(r["outcomes"] for r in rows),"rows":rows})
portal=[]
for kind,year,ct in [("applications",2020,1),("applications",2021,1),("applications",2022,1),("applications",2023,1),("applications",2025,3),("decisions",2025,1),("decisions",2025,3)]:
    url=f"https://migracje.gov.pl/wp-json/udscmap/v1/{kind}/poland?year={year}&caseType={ct}&groupBy=country&fields=total,country"
    raw=fetch(f"PORTAL-{kind}-{year}-{ct}",url,"official_live_api","Live API snapshot; historical values can be revised. Application counts are not arrival cohorts or counts of unique persons.")
    arr=json.loads(raw)
    portal.append({"measure":kind,"year":year,"case_type":ct,"total":sum(int(r["total"]) for r in arr),"belarus_country_id_241":next((r["total"] for r in arr if r.get("country")==241),None),"ukraine_country_id_215":next((r["total"] for r in arr if r.get("country")==215),None)})
assert [w["total_outcomes"] for w in warehouse]==[437687,396808,398337]
live_portal_decisions=next(r["total"] for r in portal if r["measure"]=="decisions" and r["case_type"]==1)
B=pending_totals["2026-07-01"];g=B-pending_totals["2025-12-31"]
forecast={"type":"conditional_scenario_not_observation","backlog_growth_2026_H1":g,"linear_2026_year_end":B+g,"linear_2027_year_end":B+3*g,"warehouse_clearance_days":B/398337*365,"gm_forecast_text_clearance_days":B/445458*365,"portal_live_clearance_days":B/live_portal_decisions*365,"gm_forecast_text_2025_decisions":445458,"portal_live_2025_decisions":live_portal_decisions,"portal_live_difference":live_portal_decisions-445458,"formula":"snapshot pending / prior annual outcomes * 365; end-2027 = B(1 July 2026) + 3 * H1 growth","resident_ratio_2025_to_2020":33235/261366,"resident_scenario_2026":367751*33235/261366,"resident_scenario_2027":485594*33235/261366,"resident_scenario_2028":566658*33235/261366,"caveats":["Stock/flow arithmetic is not an observed wait, an expected individual wait, or a predictive probability.","Requires comparable scope, constant throughput and counting, no priority effects and a defined queue order. Dynamic arrivals, rework, category changes and MOS can invalidate it.","Calling pending counts an upper bound is not established: a possible counting problem does not prove its direction.","Five-year lag of application totals is not a longitudinal cohort model: repeats, departures, legal-residence periods and eligibility are unobserved.","No confidence interval, probability calibration or validation of forecast accuracy."]}
claims=[
{"id":"C01","status":"confirmed_official","claim":"MSWiA 2026 mean range 242–658 days; Śląskie 658, Pomorskie 598, Lubuskie 555; 15 of 16 exceed 2023.","source_ids":["MSWIA-18089"],"period":"2026 year to 2026-07-06; reply 2026-07-27","caveat":"Arithmetic means for temporary residence proceedings; not maxima, median, live queue waits or plastic-card production times. 2026 is partial; no national mean can be obtained by averaging regional means without weights."},
{"id":"C02","status":"confirmed_in_copy_with_attribution_limit","claim":"UdSC copy gives Śląskie row 668 days at 12.08.2026, a different cut-off from MSWiA's 658.","source_ids":["UDSC-COPY"],"caveat":"Region name is inferred because public scan organ labels are blacked out. Copy not independently matched to signed original or agency website."},
{"id":"C03","status":"confirmed_sum_in_copy","claim":"Sum of 16 pending temporary-residence rows: 387312,484201,646232,803223.","source_ids":["UDSC-COPY"],"periods":["2023-12-31","2024-12-31","2025-12-31","2026-07-01"],"caveat":"Own sum, not printed national total; cases, not unique people. Source does not establish cause of counting changes; MOS/CUKR explanations are hypotheses, not confirmed findings."},
{"id":"C04","status":"confirmed_official_but_article_temporal_error","claim":"463487 pending temporary-residence-and-work cases under art.114; accompanying 341-day mean.","source_ids":["MSWIA-12584"],"period":"2025-10-13; reply 2025-10-22","caveat":"Not current October2026 data, not all temporary residence, not comparable as one time series with803223. TheWarsaw20.10.2026 calls it current; do not repeat that framing."},
{"id":"C05","status":"confirmed_official_calculation","claim":"2025 merits-only grant share29.5%=432/(432+1032);2020=94.5%=2179/(2179+126).","source_ids":["NSA-2020","NSA-2025"],"caveat":"Symbol6272 is broader than temporary residence: includes visas, residence and expulsion. Procedural rejections and other disposals are excluded; not individual win probability or a causal ranking of courts."},
{"id":"C06","status":"confirmed_in_warehouse_copies","claim":"Outcome totals437687(2023),396808(2024),398337(2025).","source_ids":["WAREHOUSE-2023-COPY","WAREHOUSE-2024-COPY","WAREHOUSE-2025-COPY"],"caveat":"All reported outcomes, not just positive permits. Third-party copies of authority-provided reports, not independently agency-published originals. Głos Migranta forecast text445458 differs by4 from both its CSV and the queried API445462; cause unverified. No old CSV snapshot or revision is established. Both differ materially from warehouse scope398337."},
{"id":"C07","status":"arithmetic_confirmed_scenario_only","claim":"Linear extrapolation gives960214 at end2026 and1274196 at end2027; stock/annual-outcomes gives736 or658 days.","source_ids":["UDSC-COPY","WAREHOUSE-2025-COPY","PORTAL-decisions-2025-1"],"caveat":"Conditional stock-clearance scenario, not observed future backlog or individual waiting time. No unique-applicant probability or forecast accuracy claim."},
{"id":"C08","status":"arithmetic_confirmed_eligibility_unverified","claim":"Applying33235/261366 to lagged2021–2023 temporary-residence applications gives approximately47k,62k,72k long-term-resident applications in2026–2028.","source_ids":["PORTAL-applications-2020-1","PORTAL-applications-2021-1","PORTAL-applications-2022-1","PORTAL-applications-2023-1","PORTAL-applications-2025-3"],"caveat":"Illustrative lag scenario only; an application is not date of arrival or start of qualifying residence, and totals contain repeat applicants. UKR eligibility scenarios require separate legal verification."},
{"id":"C09","status":"legal_qualification_required","claim":"Art112a provides60 days for the decision under statutory start conditions; art100d suspends applicable voivode deadlines through4.03.2027; courts may refuse its application.","source_ids":["FOREIGNERS-ACT","UKRAINE-ACT","AMENDMENT-2026-203","NSA-II-OSK-2038-25"],"caveat":"Do not describe every elapsed period beyond60 days from filing as a proven violation. MOS reform changed start conditions; transition depends on filing date/mode. Case-law refusal is not general repeal and outcomes vary; card production is separate."},
{"id":"C10","status":"source_classification_only","claim":"Głos Migranta /dane publishes derivative CSVs and declaresCC0; primary law and agency statistics must remain individually cited.","source_ids":["GM-MSWIA-CSV"],"caveat":"Third-party license declaration is not independent clearance of third-party documents, articles or personal data. No full article/private chat text is included in this audit output."}
]
sources.extend([
{"id":"FOREIGNERS-ACT","url":"https://eli.gov.pl/api/acts/DU/2025/1079/text/U/D20251079Lj.pdf","tier":"official_legal_text","locator":"art112a, PDF p141–142; text updated2026-04-07","note":"Shows MOS-related amendments and commencement by ministerial announcement; precise transitional application not exhaustively audited here."},
{"id":"UKRAINE-ACT","url":"https://eli.gov.pl/api/acts/DU/2025/337/text/U/D20250337Lj.pdf","tier":"official_legal_text","locator":"art100d","note":"Current official consolidation; not a constitutional-validity ruling."},
{"id":"AMENDMENT-2026-203","url":"https://eli.gov.pl/api/acts/DU/2026/203/text/T/D20260203L.pdf","tier":"official_legal_text","locator":"art17(50)","note":"Extends art100d to4March2027."},
{"id":"NSA-II-OSK-2038-25","url":"https://orzeczenia.nsa.gov.pl/doc/953FE35D2F","tier":"official_case_law","date":"2026-04-09","note":"Official indexed text checked; direct requests may fail TLS. Illustrates refusal of extension after30June2024, not general repeal."},
{"id":"THEWARSAW175788","url":"https://www.the-warsaw.pl/175788/v-polshe-reshenija-po-karte-pobytu-zhdut-do-658-dnej-vmesto-dvuh-mesjacev-po-zakonu-v-uzhondah-pochti-polmilliona-del-zhaloba-doshla-do-evropejskoj-komissii/","tier":"secondary_article","date":"2026-10-20","note":"Direct requests403; browser-visible article capture supplied by parent read for verification only, not republished. Claims outside this baseline require separate review."}
])
result={"as_of":"2026-10-20","review_kind":"separate_AI_source_check_not_external_certification","stage":"source_baseline_complete","scope":{"pages":["https://glos-migranta.eu/raporty/szesnascie-urzedow-w-liczbach","https://glos-migranta.eu/dane","https://glos-migranta.eu/fakty","https://glos-migranta.eu/raporty/prognoza"],"article":"THEWARSAW175788","limits":"Key numerical and legal framing checks, not exhaustive audit of every claim in four publications or independent authentication of DIP originals. No legal-service or absolute-lawfulness certification."},"claims":claims,"tables":{"mswia18089_means_days":mswia,"udsc_copy_rows":udsc_rows,"pending_totals":pending_totals,"nsa_6272_annual":courts,"warehouse_copy_outcomes":warehouse,"portal_api_totals":portal,"portal_reconciliation":{"gm_forecast_text_2025_decisions":445458,"gm_csv_2025_decisions":445462,"live_total":live_portal_decisions,"difference":live_portal_decisions-445458,"status":"unresolved_publication_text_vs_csv_api_difference"}},"calculations":{"mswia_csv_rows":len(csvrows),"mswia_csv_mismatches":mswia_csv_mismatches,"regions_slower_than_2023":sum(r['2026']>r['2023'] for r in mswia),"forecast":forecast},"sources":sorted(sources,key=lambda x:x['id'])}
(ROOT/"baseline.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"claims":len(claims),"sources":len(sources),"pending_totals":pending_totals,"csv_mismatches":len(mswia_csv_mismatches),"nsa_rates":{x['year']:x['national']['merits_granted_pct'] for x in courts},"portal_totals":portal,"scenario":forecast},ensure_ascii=False))
