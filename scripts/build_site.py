"""Build dependency-free GitHub Pages output from curated observations.

No network calls and no private source paths in the generated site.
"""
from __future__ import annotations
import csv
import hashlib
import html
import json
import re
from pathlib import Path
import shutil
from build_round2 import fact_html, translate_claims, build_pages, review_html

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs'
BASE = 'https://aierudit.github.io/poland-residence-observatory'

def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

def esc(value):
    return html.escape(str(value), quote=True)

def fmt(value):
    return f'{value:,}'.replace(',', ' ')

def build_claims(data):
    observations = data['observations']
    select = lambda sid: [o for o in observations if o['series_id'] == sid]
    year = lambda o: str(o['reference_period'])[:4]
    mswia = select('mswia_18089_concluded_mean_days')
    current = [o for o in mswia if year(o) == '2026']
    previous = {o['geography_id']: o for o in mswia if year(o) == '2023'}
    assert len(current) == len(previous) == 16, 'Expected all 16 regions in the primary comparison'
    worst = max(current, key=lambda o: o['value'])
    assert worst['value'] == 658
    increased = sum(o['value'] > previous[o['geography_id']]['value'] for o in current)
    assert increased == 15
    stocks = [o for o in select('udsc_20260828_pending_stock') if year(o) == '2026' and o.get('geography_level') != 'country']
    assert len(stocks) == 16, 'Stock total must be the sum of 16 regions, not a sum including a national aggregate'
    stock = sum(o['value'] for o in stocks)
    assert stock == 803223
    concluded_2025=[o for o in select('warehouse_all_outcomes') if year(o)=='2025' and o['indicator_id']=='concluded_resolutions']
    assert len(concluded_2025)==16 and sum(o['value'] for o in concluded_2025)==398337, 'Scenario baseline must match the 16-region 2025 source table'
    courts = [o for o in select('nsa_wsa_6272_annual') if year(o) == '2025' and (o.get('geography_level') == 'country' or o.get('geography_id') == 'PL' or o.get('geography_name') == 'Polska')]
    def court(ind):
        return next(o for o in courts if o['indicator_id'] == ind)
    up, down, rejected, resolved = [court(i) for i in ['court_upheld', 'court_dismissed', 'court_rejected', 'court_resolved']]
    assert up['value'] == 432 and down['value'] == 1032
    rate = up['value'] / (up['value'] + down['value']) * 100
    ids = lambda rows: [o['id'] for o in rows]
    claims = [
      {
        'id':'silesia-658', 'value':658, 'unit':'days', 'observation_ids':ids([worst]),
        'title_pl':'658 dni: średnia zakończonych postępowań na Śląsku',
        'title_ru':'658 дней: среднее по завершённым производствам в Силезии',
        'body_pl':'MSWiA podaje 658 dni dla pobytu czasowego w województwie śląskim w części 2026 roku, do 6 lipca. To najwyższa średnia w zestawieniu 16 województw.',
        'body_ru':'MSWiA указывает 658 дней для временного проживания в Силезском воеводстве за часть 2026 года, до 6 июля. Это наибольшее среднее среди 16 воеводств в этой таблице.',
        'caveat_pl':'Średnia zakończonych postępowań, nie maksimum ani przewidywany czas nowego wniosku. Źródło nie publikuje liczebności kohort ani szczegółowego sposobu liczenia dni.',
        'caveat_ru':'Среднее по завершённым производствам, не максимум и не прогноз для нового заявления. Источник не раскрывает размер когорт и подробный способ подсчёта дней.',
        'calculation':'max(mean_days_2026 for 16 voivodeships) = 658; MSWiA 18089, table 1, Śląski / 2026.',
        'metric_label_pl':'ŚLĄSKIE · DO 06.07.2026','metric_label_ru':'СИЛЕЗИЯ · ДО 06.07.2026',
        'metric_copy_pl':'Średni czas zakończonych postępowań o pobyt czasowy. Najwyższy w tym zestawieniu.',
        'metric_copy_ru':'Среднее по завершённым производствам о временном проживании. Наибольшее в этой таблице.',
        'preview_value':'658 dni', 'preview_context':'Pobyt czasowy · Śląskie · średnia zakończonych spraw · do 06.07.2026'
      },
      {
        'id':'fifteen-regions','value':15,'unit':'voivodeships','observation_ids':ids(current + list(previous.values())),
        'title_pl':'W 15 z 16 województw średnia za 2026 jest wyższa niż za 2023',
        'title_ru':'В 15 из 16 воеводств среднее за 2026 год выше, чем за 2023',
        'body_pl':'Porównanie tabeli MSWiA: średni czas zakończonych postępowań o pobyt czasowy wzrósł w 15 regionach. Wyjątkiem jest dolnośląskie: 401 dni w 2023 i 303 w części 2026.',
        'body_ru':'Сравнение таблицы MSWiA: среднее по завершённым производствам о временном проживании выросло в 15 регионах. Исключение — Нижняя Силезия: 401 день в 2023 году и 303 за часть 2026 года.',
        'caveat_pl':'Pełny rok 2023 porównano z okresem 2026 do 6 lipca. To nie dowód wydłużenia każdego indywidualnego postępowania ani miara wieku spraw w toku. Zmiana składu zakończonych spraw może zmieniać średnią.',
        'caveat_ru':'Полный 2023 год сравнивается с 2026 годом до 6 июля. Это не доказательство удлинения каждого дела и не возраст текущей очереди. Изменение состава завершённых дел может менять среднее.',
        'calculation':'count(mean_days_2026 > mean_days_2023) = 15 of 16, paired by geography_id. No national average calculated.',
        'preview_value':'15 / 16', 'preview_context':'Pobyt czasowy · województwa z wyższą średnią: 2023 vs 2026 do 6 lipca · MSWiA'
      },
      {
        'id':'pending-803223','value':stock,'unit':'cases','observation_ids':ids(stocks),
        'title_pl':'803 223 sprawy o pobyt czasowy w toku na 1 lipca 2026',
        'title_ru':'803 223 дела о временном проживании в работе на 1 июля 2026',
        'body_pl':'Suma 16 wierszy tabeli UdSC w piśmie z 28 sierpnia 2026: 803 223 niezakończone sprawy na 01.07.2026.',
        'body_ru':'Сумма 16 строк таблицы UdSC в письме от 28 августа 2026 года: 803 223 незавершённых дела на 01.07.2026.',
        'caveat_pl':'Sprawy, nie unikalne osoby. Dokument to kopia opublikowana przez Głos Migranta, bez niezależnego potwierdzenia oryginału u organu. Nazwy regionów zasłonięto; suma ich nie wymaga. Możliwa zmiana porównywalności MOS/CUKR w 2026.',
        'caveat_ru':'Дела, не уникальные люди. Документ — копия у Głos Migranta, без независимого подтверждения оригинала у органа. Названия регионов скрыты; для общей суммы они не нужны. Возможен разрыв сопоставимости MOS/CUKR в 2026 году.',
        'calculation':'sum(pending cases on 2026-07-01 over 16 rows) = 803223. UdSC BSZ.WAiSM.0361.16.2026/DH, table of pending cases.',
        'metric_label_pl':'POBYT CZASOWY · 01.07.2026','metric_label_ru':'ВРЕМЕННОЕ ПРОЖИВАНИЕ · 01.07.2026',
        'metric_copy_pl':'spraw w toku — suma tabeli w kopii pisma UdSC. To nie liczba migrantów.',
        'metric_copy_ru':'дел в работе — сумма таблицы в копии письма UdSC. Это не число мигрантов.',
        'preview_value':'803 223', 'preview_context':'Pobyt czasowy · sprawy w toku, nie osoby · 01.07.2026 · kopia pisma UdSC'
      },
      {
        'id':'courts-merits-2025','value':round(rate,1),'unit':'percent','observation_ids':ids([up,down,rejected,resolved]),
        'title_pl':'29,5% uwzględnionych — tylko wśród rozstrzygnięć merytorycznych',
        'title_ru':'29,5% удовлетворённых — только среди решений по существу',
        'body_pl':'WSA, 2025, bezczynność i przewlekłość, symbol 6272: 432 uwzględnienia i 1 032 oddalenia. 432 / (432 + 1 032) = 29,5%. Kategoria obejmuje wizy, pobyt, wydalenie i inne sprawy cudzoziemców.',
        'body_ru':'WSA, 2025 год, бездействие и затягивание, символ 6272: 432 удовлетворения и 1 032 отказа по существу. 432 / (432 + 1 032) = 29,5%. Категория включает визы, проживание, выдворение и другие дела иностранцев.',
        'caveat_pl':f'Poza tym mianownikiem są m.in. {fmt(rejected["value"])} odrzucenia procesowe. Nie jest to udział w nowych skargach ani szansa wygranej konkretnej osoby.',
        'caveat_ru':f'За пределами этого знаменателя — в том числе {fmt(rejected["value"])} процессуальных отклонения. Это не доля новых жалоб и не вероятность выигрыша конкретного человека.',
        'calculation':f'432 / (432 + 1032) × 100 = {rate:.6f}%. Rejected/resolved = {rejected["value"]}/{resolved["value"]}. Different cohorts: inflow is not used as denominator.',
        'metric_label_pl':'WSA · SYMBOL 6272 · 2025','metric_label_ru':'WSA · СИМВОЛ 6272 · 2025',
        'metric_copy_pl':'uwzględnionych wśród rozstrzygnięć merytorycznych. Szersza kategoria niż sam pobyt.',
        'metric_copy_ru':'удовлетворённых среди решений по существу. Категория шире дел о проживании.',
        'preview_value':'29,5%', 'preview_context':'432 / (432 + 1032) · tylko rozstrzygnięcia merytoryczne. Wizy, pobyt, wydalenie · WSA 6272 · 2025'
      }
    ]
    by_id = {o['id']:o for o in observations}
    for c in claims:
        c['source_ids'] = sorted({by_id[i]['source_id'] for i in c['observation_ids']})
        c['as_of_release'] = data['as_of']
        c['review_scope'] = 'Independent AI source review; see verification/round2/review.md. Not external certification.'
    return translate_claims(claims)

def main():
    data = read('data/curated/dataset.json')
    claims = build_claims(data)
    OUT.mkdir(exist_ok=True)
    (OUT/'assets').mkdir(exist_ok=True)
    (OUT/'data').mkdir(exist_ok=True)
    (OUT/'.nojekyll').write_text('',encoding='utf-8', newline='\n')
    for name in ['style.css','app.js','icon.svg','i18n.js','page.js','analytics.js','survey.js','flag-en.svg']:
        shutil.copyfile(ROOT/'site'/name, OUT/'assets'/name)
    for p in (ROOT/'site/vendor').glob('*'):
        shutil.copyfile(p,OUT/'assets'/p.name)
    for original,name in [('research/round2-data/offices.json','offices'),('research/round2-data/provenance-audit.json','provenance-audit'),('research/round2-data/eurostat-context.json','eurostat-context'),('research/round2-law/banking.json','banking'),('research/round2-law/actions.json','actions'),('site/survey-config.json','survey-config')]:
        shutil.copyfile(ROOT/original,OUT/'data'/f'{name}.json')
    for p in (ROOT/'data/curated').glob('*'):
        if p.suffix in ('.json','.csv'):
            shutil.copyfile(p,OUT/'data'/p.name)
    write_json(OUT/'data/claims.json', claims)
    write_json(ROOT/'site/claims.json', claims)
    (OUT/'coverage').mkdir(exist_ok=True)
    coverage=ROOT/'coverage/structured-sources.json'
    if coverage.exists():shutil.copyfile(coverage,OUT/'coverage/structured-sources.json')
    metrics = []
    cards = []
    for c in claims:
        if 'metric_label_pl' in c:
            value=c['preview_value']
            if c['unit']=='days': value='658 <small>dni</small>'
            metrics.append(f'<article class="metric" data-claim="{c["id"]}"><span class="metric-label">{esc(c["metric_label_pl"])}</span><strong>{value}</strong><p class="metric-copy">{esc(c["metric_copy_pl"])}</p><a data-i18n="definitionLink" data-keep-lang href="facts/{c["id"]}/">Definicja i źródło ↗</a></article>')
        cards.append(f'<article class="fact-card" data-claim="{c["id"]}" id="fact-{c["id"]}"><div class="fact-top"><span>DATA / {esc(c["id"].upper())}</span><span>{esc(data["version"])}</span></div><h3 data-field="title">{esc(c["title_pl"])}</h3><p data-field="body">{esc(c["body_pl"])}</p><p class="fact-caveat" data-field="caveat">{esc(c["caveat_pl"])}</p><div class="fact-actions"><a data-i18n="definitionLink" data-keep-lang href="facts/{c["id"]}/">Źródło ↗</a><button data-i18n="copy" data-copy="{c["id"]}">Cytuj</button></div></article>')
        folder=OUT/'facts'/c['id']
        folder.mkdir(parents=True,exist_ok=True)
        (folder/'index.html').write_text(fact_html(c,data,{s['id']:s for s in data['sources']}),encoding='utf-8', newline='\n')
    page=(ROOT/'site/index.html').read_text(encoding='utf-8').replace('__METRICS__',''.join(metrics)).replace('__FACTS__',''.join(cards))
    (OUT/'index.html').write_text(page,encoding='utf-8', newline='\n')
    (OUT/'404.html').write_text('<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>404 · Residence Observatory</title><h1>Nie znaleziono strony</h1><a href="/poland-residence-observatory/">Residence Observatory →</a></html>',encoding='utf-8', newline='\n')
    (OUT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n',encoding='utf-8', newline='\n')
    urls=[BASE+'/',BASE+'/survey/',BASE+'/privacy/',BASE+'/verification/']+[f'{BASE}/facts/{c["id"]}/' for c in claims]
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{u}</loc><lastmod>{data["as_of"]}</lastmod></url>' for u in urls)+'</urlset>',encoding='utf-8', newline='\n')
    (OUT/'verification').mkdir(exist_ok=True)
    for name in ['review.md','baseline.json','research-review.json','release.json','verify_primary_sources.py']:
        p=ROOT/'verification'/name
        if p.exists(): shutil.copyfile(p, OUT/'verification'/name)
    review=ROOT/'verification/review.md'
    if review.exists():
        (OUT/'verification/index.html').write_text(review_html(),encoding='utf-8', newline='\n')
    (OUT/'verification/round2').mkdir(exist_ok=True)
    for p in (ROOT/'verification/round2').glob('*'):
        if p.suffix in ['.json','.md']:shutil.copyfile(p,OUT/'verification/round2'/p.name)
    build_pages(OUT)
    # File hashes prevent mixed old/new JavaScript and CSS after a Pages update.
    def asset_version(match):
        prefix,url=match.groups();asset=OUT/'assets'/Path(url).name
        if not asset.exists():return match.group(0)
        digest=hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        return prefix+'="'+url+'?v='+digest+'"'
    for page_file in OUT.rglob('*.html'):
        text=page_file.read_text(encoding='utf-8')
        text=re.sub(r'(src|href)="([^"?#]*assets/[^"?#]+)"',asset_version,text)
        page_file.write_text(text,encoding='utf-8',newline='\n')
    manifest={'site_version':'1.1.0','languages':['pl','be','en'],'context_observations':15,'version':data['version'],'as_of':data['as_of'],'dataset_sha256':hashlib.sha256((OUT/'data/dataset.json').read_bytes()).hexdigest(),'claim_ids':[c['id'] for c in claims],'observations':len(data['observations']),'sources':len(data['sources'])}
    write_json(OUT/'manifest.json',manifest)
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
