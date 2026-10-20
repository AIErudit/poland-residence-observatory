"""Render the three-language static research pages, without network access."""
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE='https://aierudit.github.io/poland-residence-observatory'
e=lambda s:html.escape(str(s),quote=True)

def language_bar():
    return '<div class="lang" aria-label="Language"><button data-lang="pl" aria-pressed="true" title="Polski"><span class="flag-pl" aria-hidden="true"></span> PL</button><button data-lang="be" aria-pressed="false" title="Беларуская"><span class="flag-be" aria-hidden="true"></span> BE</button><button data-lang="en" aria-pressed="false" title="English"><span class="flag-en" aria-hidden="true"></span> EN</button></div>'

def shell(title,description,body,depth=1,path='',image='social.png'):
    prefix='../'*depth
    return f'''<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)} · Residence Observatory</title><meta name="description" content="{e(description)}"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(description)}"><meta property="og:type" content="article"><meta property="og:url" content="{BASE}/{path}"><meta property="og:image" content="{BASE}/assets/{image}"><meta name="twitter:card" content="summary_large_image"><link rel="canonical" href="{BASE}/{path}"><link rel="icon" href="{prefix}assets/icon.svg"><link rel="stylesheet" href="{prefix}assets/style.css"><script src="{prefix}assets/i18n.js" defer></script><script src="{prefix}assets/page.js" defer></script></head><body><main class="fact-page legal-document"><div class="locale-tools"><a href="{prefix}" data-keep-lang>← Residence Observatory</a>{language_bar()}</div>{body}</main></body></html>'''

def translate_claims(claims):
    translations=json.loads((ROOT/'site/claim-translations.json').read_text(encoding='utf-8'))
    for c in claims:
        c.update(translations[c['id']])
        for key in list(c):
            if key.endswith('_ru'):del c[key]
        if c['id']=='silesia-658':
            c['caveat_pl']='Średnia zakończonych postępowań, nie maksimum ani przewidywany czas nowego wniosku. Źródło nie podaje liczebności kohort ani dokładnego zdarzenia rozpoczynającego liczenie dni.'
    return claims

def fact_html(c,data,sources):
    source_html=''.join(f'<li><a href="{e(sources[s]["url"])}">{e(sources[s]["title"])} ↗</a><br>{e(sources[s]["publisher"])} · {e(sources[s].get("document_date") or "—")} · {e(sources[s]["access"])}</li>' for s in c['source_ids'])
    obs={o['id']:o for o in data['observations']}
    locators='; '.join(sorted({obs[i].get('source_locator','') for i in c['observation_ids']}))
    labels={
      'pl':['Źródła i odtwarzalność','Obliczenie','Lokalizatory i identyfikatory','Cytowanie','Kopiuj cytowanie','Udostępnij w X','Zgłoś korektę','Dane historyczne, nie licznik na żywo. Wersja i data pobrania:','Zakres przeglądu AI','Archiwum wersji'],
      'be':['Крыніцы і аднаўляльнасць','Разлік','Лакатары і ідэнтыфікатары','Цытаванне','Скапіяваць цытаванне','Падзяліцца ў X','Паведаміць пра памылку','Гістарычныя даныя, не бягучы лічыльнік. Версія і дата атрымання:','Абсяг AI-праверкі','Архіў версіі'],
      'en':['Sources & reproducibility','Calculation','Locators & observation IDs','Citation','Copy citation','Share on X','Report a correction','Historical data, not a live counter. Version and retrieval date:','AI review scope','Version archive']}
    blocks=[]
    for lang,l in labels.items():
        title,body,caveat=[c[k+'_'+lang] for k in ['title','body','caveat']]
        url=f'{BASE}/facts/{c["id"]}/?lang={lang}'
        citation=f'{title}. {body} {caveat} — Residence Observatory, data v{data["version"]}. {url}'
        blocks.append(f'''<article class="fact-card locale-block" data-locale="{lang}" lang="{lang}" {'hidden' if lang!='pl' else ''}><div class="fact-top">{e(c['id'])} · v{e(data['version'])}</div><h1>{e(title)}</h1><p>{e(body)}</p><blockquote>{e(caveat)}</blockquote><div class="provenance"><h2>{l[0]}</h2><ul>{source_html}</ul><p><strong>{l[1]}:</strong> {e(c['calculation'])}</p><details><summary>{l[2]} ({len(c['observation_ids'])})</summary><p>{e(locators)}</p><code>{e(', '.join(c['observation_ids']))}</code></details><p>{l[7]} v{e(data['version'])} · {e(data['as_of'])}. <a href="../../verification/?lang={lang}">{l[8]}</a>.</p><p><a href="https://github.com/AIErudit/poland-residence-observatory/tree/v{e(data['version'])}/docs/facts/{e(c['id'])}/">{l[9]}</a> · <a href="../../data/dataset.json">Dataset JSON</a> · <a href="../../data/observations.csv">CSV</a> · <a href="../../data/claims.json">Claims JSON</a></p><h2>{l[3]}</h2><pre class="citation">{e(citation)}</pre><div class="fact-actions"><button data-copy-citation>{l[4]}</button><a href="https://twitter.com/intent/tweet?url={BASE}/facts/{c['id']}/%3Flang%3D{lang}" target="_blank" rel="noopener noreferrer">{l[5]} ↗</a><a href="https://github.com/AIErudit/poland-residence-observatory/issues/new/choose">{l[6]} ↗</a></div><p role="status"></p></div></article>''')
    return shell(c['title_pl'],c['body_pl']+' '+c['caveat_pl'],''.join(blocks),2,'facts/'+c['id']+'/',f'fact-{c["id"]}.png')

def build_pages(out):
    content=json.loads((ROOT/'site/privacy-content.json').read_text(encoding='utf-8'))
    blocks=[]
    for lang,d in content.items():
        blocks.append(f'<article class="locale-block prose" data-locale="{lang}" lang="{lang}" {"hidden" if lang!="pl" else ""}><h1>{e(d["title"])}</h1><p>{e(d["intro"])}</p>'+''.join(f'<h2>{e(h)}</h2><p>{e(p)}</p>' for h,p in d['sections'])+'</article>')
    links=[('GDPR / RODO','https://eur-lex.europa.eu/eli/reg/2016/679/oj'),('UODO','https://uodo.gov.pl/'),('GitHub privacy','https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement'),('Cloudflare DPA','https://www.cloudflare.com/cloudflare-customer-dpa/'),('Turnstile privacy','https://www.cloudflare.com/turnstile-privacy-policy/'),('D1 EU jurisdiction','https://developers.cloudflare.com/d1/configuration/data-location/'),('D1 recovery history','https://developers.cloudflare.com/d1/reference/time-travel/')]
    blocks.append('<p class="small">'+' · '.join(f'<a href="{u}">{e(t)} ↗</a>' for t,u in links)+'</p><p><a href="../survey/" data-keep-lang>Survey / Ankieta / Анкета →</a> · <a href="mailto:support@pagefabrica.com">support@pagefabrica.com</a></p>')
    (out/'privacy').mkdir(exist_ok=True)
    (out/'privacy/index.html').write_text(shell(content['pl']['title'],content['pl']['intro'],''.join(blocks),1,'privacy/'),encoding='utf-8',newline='\n')
    (out/'survey').mkdir(exist_ok=True)
    (out/'survey/index.html').write_text((ROOT/'site/survey.html').read_text(encoding='utf-8'),encoding='utf-8',newline='\n')

def review_html():
    blocks=[]
    texts={
      'pl':('Zakres osobnej weryfikacji','Osobny recenzent AI odtworzył 1 780 wartości podstawowego zbioru oraz 15 nowych wartości Eurostatu. Nie stwierdzono rozbieżności liczbowych. To kontrola źródeł i obliczeń, nie certyfikacja prawna, audyt bezpieczeństwa ani uwierzytelnienie kopii pism. Ograniczenia obejmują rekonstrukcję nazw regionów UdSC, różne zakresy i daty, brak wag krajowych i niezidentyfikowane różnice między tabelami. Kod ankiety sprawdzono na syntetycznych danych; wyniki nie dowodzą odporności na każdy atak.'),
      'be':('Абсяг асобнай праверкі','Асобны AI-рэцэнзент паўторна праверыў 1 780 значэнняў асноўнага набору і 15 новых значэнняў Eurostat. Лічбавых разыходжанняў не выяўлена. Гэта праверка крыніц і разлікаў, а не юрыдычная сертыфікацыя, аўдыт бяспекі або пацвярджэнне сапраўднасці копій лістоў. Абмежаванні: адноўленыя назвы рэгіёнаў UdSC, розныя даты і ахоп, адсутнасць нацыянальных вагаў і невытлумачаныя адрозненні табліц. Код анкеты правераны на сінтэтычных даных; гэта не даказвае абарону ад усіх атак.'),
      'en':('Scope of separate verification','A separate AI reviewer reproduced 1,780 core values and 15 new Eurostat values. No numeric discrepancies were found. This is a source and calculation review, not legal certification, a security audit or authentication of copied letters. Limitations include reconstructed UdSC region labels, differing scopes and dates, unavailable national weights and unexplained differences between tables. Survey code was tested with synthetic data; this does not establish protection against every attack.')}
    for lang,(title,text) in texts.items():
        blocks.append(f'<article class="locale-block prose" data-locale="{lang}" lang="{lang}" {"hidden" if lang!="pl" else ""}><h1>{title}</h1><p>{text}</p></article>')
    blocks.append('<div class="info-card"><h2>Review evidence</h2><ul><li><a href="round2/review.md">Round 2 review (Markdown)</a></li><li><a href="round2/critique.json">Findings JSON</a></li><li><a href="round2/numeric-recheck.json">1,780 values</a></li><li><a href="round2/eurostat-check.json">Eurostat check</a></li><li><a href="round2/backend-check.json">Synthetic backend check</a></li><li><a href="round2/release.json">Reviewed release hashes / status</a></li><li><a href="review.md">Round 1 archive (RU)</a></li></ul></div>')
    return shell(texts['pl'][0],'Source verification scope and limitations.',''.join(blocks),1,'verification/')
