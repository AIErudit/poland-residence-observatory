/* Office and Eurostat charts. Only source rows are displayed; no pooled means. */
(() => {
  'use strict';
  const text = {
    pl: {
      office: 'Urząd', duration: 'Raportowana średnia czasu postępowań (dni)', pending: 'Sprawy w toku na wskazany dzień', flow: 'Zakończone sprawy — wszystkie rozstrzygnięcia', line: 'Linia', bar: 'Słupki', period: 'Okres / data', value: 'Wartość', source: 'Źródło', flags: 'Flagi źródła', none: 'Brak danych', days: 'dni', cases: 'sprawy', officeLink: 'Oficjalna strona urzędu', directoryLink: 'Oficjalny wykaz MSWiA', openSource: 'Otwórz źródło', unknown: 'Data odcięcia nieznana', partial: '2026: okres niepełny.', chartOmitted: 'Wartość za 2026 rok pokazano w tabeli; pominięto ją na wykresie, ponieważ data odcięcia nie jest znana.', noChart: 'Wykres jest niedostępny; wszystkie wartości i źródła są w tabeli.', durationNote: 'Średnia opisuje raportowany czas zakończonych postępowań, nie czas oczekiwania wszystkich wnioskodawców ani termin w Twojej sprawie. Odpowiedź MSWiA nie ustala jednoznacznie zdarzenia rozpoczynającego pomiar w systemie.', pendingNote: 'To stan niezakończonych spraw, nie roczny napływ. Nazwy organów w kopii UdSC są zakryte: przypisanie regionów odtworzono. W 2026 możliwa zmiana zakresu lub sposobu liczenia; wzrost raportowanych liczb nie dowodzi wzrostu przy stałym zakresie.', flowNote: 'Liczby obejmują decyzje pozytywne, negatywne, umorzenia i pozostawienia bez rozpoznania. Zakres różni się od portalu UdSC. Nie są to liczby osób ani czas oczekiwania.', noWeighted: 'Wybrano jeden urząd i jedną serię; nie obliczamy średniej krajowej z regionalnych średnich.', plAll: 'Polska — ogółem w zbiorze obywateli spoza UE', euAll: 'UE27 — ogółem w zbiorze obywateli spoza UE', plBy: 'Polska — obywatelstwo białoruskie', permits: 'Pierwsze zezwolenia (Eurostat, PER)', euroNote: 'Kontekst: pierwsze uprawnienia do pobytu na co najmniej 3 miesiące dla obywateli spoza UE. TOTAL nie oznacza wszystkich migrantów. Zakres może obejmować wizy długoterminowe; nie jest to seria czasu oczekiwania ani liczba spraw w toku. UE27 obejmuje Polskę — nie sumuj tych serii.', euroReview: 'Bezpośrednie dane Eurostat; osobny recenzent sprawdził 15/15 wartości.', flagNote: 'Brak podanej flagi nie jest dowodem braku zmian metodologii.', chartOffice: 'Wykres danych wybranego urzędu', chartEuro: 'Wykres kontekstu Eurostat'
    },
    be: {
      office: 'Упраўленне', duration: 'Апублікаваная сярэдняя працягласць спраў (дні)', pending: 'Незавершаныя справы на пазначаную дату', flow: 'Завершаныя справы — усе віды рашэнняў', line: 'Лінія', bar: 'Слупкі', period: 'Перыяд / дата', value: 'Значэнне', source: 'Крыніца', flags: 'Пазнакі крыніцы', none: 'Няма звестак', days: 'дні', cases: 'справы', officeLink: 'Афіцыйная старонка ўпраўлення', directoryLink: 'Афіцыйны спіс MSWiA', openSource: 'Адкрыць крыніцу', unknown: 'Дата зрэзу невядомая', partial: '2026: няпоўны перыяд.', chartOmitted: 'Значэнне за 2026 паказана ў табліцы, але не на графіку, бо дата зрэзу невядомая.', noChart: 'Графік недаступны; усе значэнні і крыніцы ёсць у табліцы.', durationNote: 'Сярэдняе апісвае апублікаваную працягласць завершаных спраў, а не чаканне ўсіх заяўнікаў ці тэрмін у вашай справе. Адказ MSWiA не вызначае адназначна падзею, з якой сістэма пачынае адлік.', pendingNote: 'Гэта колькасць незавершаных спраў на дату, а не гадавы паток заяў. Назвы органаў у копіі UdSC закрытыя: прывязка рэгіёнаў адноўленая. У 2026 маглі змяніцца ахоп або падлік; рост апублікаваных лічбаў не даказвае росту пры нязменным ахопе.', flowNote: 'Улічаны станоўчыя і адмоўныя рашэнні, спыненне спраў і пакіданне без разгляду. Ахоп адрозніваецца ад партала UdSC. Гэта не колькасць людзей і не час чакання.', noWeighted: 'Выбраныя адно ўпраўленне і адзін шэраг; агульнапольскае сярэдняе з рэгіянальных сярэдніх не разлічваецца.', plAll: 'Польшча — усе ў зборы грамадзян па-за ЕС', euAll: 'ЕС27 — усе ў зборы грамадзян па-за ЕС', plBy: 'Польшча — грамадзянства Беларусі', permits: 'Першыя дазволы (Eurostat, PER)', euroNote: 'Кантэкст: першыя дазволы на пражыванне не менш за 3 месяцы для грамадзян па-за ЕС. TOTAL не азначае ўсіх мігрантаў. Ахоп можа ўключаць доўгатэрміновыя візы; гэта не час чакання і не колькасць незавершаных спраў. ЕС27 ужо ўключае Польшчу — не складайце гэтыя шэрагі.', euroReview: 'Прамыя звесткі Eurostat; асобны рэцэнзент праверыў 15/15 значэнняў.', flagNote: 'Адсутнасць пазнакі не даказвае адсутнасці метадалагічных змен.', chartOffice: 'Графік звестак выбранага ўпраўлення', chartEuro: 'Графік кантэксту Eurostat'
    },
    en: {
      office: 'Office', duration: 'Reported mean processing duration (days)', pending: 'Pending cases at the stated date', flow: 'Concluded cases — all outcomes', line: 'Line', bar: 'Bars', period: 'Period / date', value: 'Value', source: 'Source', flags: 'Source flags', none: 'No data', days: 'days', cases: 'cases', officeLink: 'Official office page', directoryLink: 'Official MSWiA directory', openSource: 'Open source', unknown: 'Cut-off unknown', partial: '2026 is a partial period.', chartOmitted: 'The 2026 value is shown in the table and omitted from the chart because its cut-off is unknown.', noChart: 'Chart unavailable; all values and sources are in the table.', durationNote: 'The mean describes reported duration of concluded proceedings, not the wait of every applicant or the timing of your case. The MSWiA reply does not unambiguously establish the event that starts the system measurement.', pendingNote: 'This is an unfinished-case stock, not annual inflow. Office labels in the UdSC copy are redacted: regional assignments are reconstructed. Scope or counting may have changed in 2026; larger reported counts do not establish growth in a constant-scope population.', flowNote: 'Counts include positive/negative decisions, discontinuance and leaving applications unexamined. Their scope differs from the UdSC portal. These are not counts of persons or waiting times.', noWeighted: 'One office and one series are selected; no national mean is calculated from regional means.', plAll: 'Poland — total within non-EU citizen collection', euAll: 'EU27 — total within non-EU citizen collection', plBy: 'Poland — Belarus citizenship', permits: 'First permits (Eurostat, PER)', euroNote: 'Context: first authorisations to stay at least 3 months for non-EU citizens. TOTAL does not mean all migrants. Scope may include long-stay visas; this is neither waiting time nor pending cases. EU27 includes Poland — do not add these series.', euroReview: 'Direct Eurostat data; a separate reviewer checked all 15 values.', flagNote: 'No supplied flag is not proof of no methodological changes.', chartOffice: 'Chart for the selected office', chartEuro: 'Eurostat context chart'
    }
  };
  const officeState = { data: null, lang: 'pl', chart: null };
  const euroState = { data: null, lang: 'pl', chart: null };
  const bound = new WeakSet();
  const $ = id => document.getElementById(id);
  const language = lang => text[String(lang).toLowerCase()] ? String(lang).toLowerCase() : 'pl';
  const safeURL = value => {
    try { const u = new URL(value); return ['https:', 'http:'].includes(u.protocol) ? u.href : null; }
    catch (_) { return null; }
  };
  function element(tag, value) {
    const node = document.createElement(tag);
    if (value !== undefined) node.textContent = value;
    return node;
  }
  function format(value, lang) {
    if (value === null || value === undefined) return text[lang].none;
    return new Intl.NumberFormat({ pl: 'pl-PL', be: 'be-BY', en: 'en-GB' }[lang], { maximumFractionDigits: 2 }).format(value);
  }
  function options(select, entries, fallback) {
    if (!select) return;
    const chosen = select.value;
    select.replaceChildren(...entries.map(([id, label]) => {
      const option = element('option', label); option.value = id; return option;
    }));
    select.value = entries.some(([id]) => id === chosen) ? chosen : fallback || entries[0]?.[0] || '';
  }
  function bind(node, handler) {
    if (node && !bound.has(node)) { node.addEventListener('change', handler); bound.add(node); }
  }
  function renderTable(target, columns, rows, lang, withFlags = false) {
    if (!target) return;
    const table = target.tagName === 'TABLE' ? target : element('table');
    const thead = element('thead'), heading = element('tr');
    columns.forEach(label => { const th = element('th', label); th.scope = 'col'; heading.append(th); });
    thead.append(heading);
    const tbody = element('tbody');
    rows.forEach(r => {
      const tr = element('tr'), period = element('th', r.period); period.scope = 'row';
      const value = element('td', format(r.value, lang));
      if (r.note) value.append(element('small', ' — ' + r.note));
      tr.append(period, value);
      if (withFlags) tr.append(element('td', r.flags || '—'));
      const source = element('td'), url = safeURL(r.source?.url);
      if (url) {
        const link = element('a', text[lang].openSource); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer';
        link.title = r.source.title || r.source.publisher || ''; source.append(link);
      } else source.append(element('span', text[lang].none));
      if (r.locator) source.append(element('small', ' — ' + r.locator));
      tr.append(source); tbody.append(tr);
    });
    table.replaceChildren(thead, tbody);
    if (table !== target) target.replaceChildren(table);
  }
  function draw(state, canvas, type, labels, values, label, ariaLabel) {
    if (state.chart) { state.chart.destroy(); state.chart = null; }
    if (!canvas) return false;
    canvas.setAttribute('role', 'img'); canvas.setAttribute('aria-label', ariaLabel);
    if (typeof window.Chart !== 'function') return false;
    const color = '#3679a8';
    state.chart = new window.Chart(canvas, {
      type, data: { labels, datasets: [{ label, data: values, borderColor: color, backgroundColor: type === 'bar' ? '#3679a899' : '#3679a822', borderWidth: 2, pointRadius: 4, fill: false, spanGaps: false }] },
      options: { responsive: true, maintainAspectRatio: false, animation: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: item => label + ': ' + format(item.parsed.y, state.lang) } } },
        scales: { y: { beginAtZero: true, title: { display: true, text: label } }, x: { ticks: { maxRotation: 0 } } }
      }
    });
    return true;
  }
  window.initAnalytics = function initAnalytics(dataset, lang) {
    officeState.data = dataset;
    bind($('analytics-office'), () => window.renderAnalytics(officeState.lang));
    bind($('analytics-metric'), () => window.renderAnalytics(officeState.lang));
    bind($('analytics-type'), () => window.renderAnalytics(officeState.lang));
    window.renderAnalytics(lang);
  };
  window.renderAnalytics = function renderAnalytics(lang) {
    const state = officeState; state.lang = language(lang); const t = text[state.lang], data = state.data;
    if (!data?.observations) return;
    const relevant = data.observations.filter(r => r.geography_level === 'voivodeship');
    const available = new Map(relevant.map(r => [r.geography_id, r.geography_name]));
    const officeOptions = [...available.entries()].sort((a, b) => a[1].localeCompare(b[1], 'pl'));
    options($('analytics-office'), officeOptions);
    options($('analytics-metric'), [['duration', t.duration], ['pending', t.pending], ['flow', t.flow]], 'duration');
    options($('analytics-type'), [['line', t.line], ['bar', t.bar]], 'line');
    const gid = $('analytics-office')?.value || officeOptions[0]?.[0];
    const metric = $('analytics-metric')?.value || 'duration', type = $('analytics-type')?.value || 'line';
    const contract = {
      duration: { series: 'mswia_18089_concluded_mean_days', indicator: 'processing_duration_mean_days', unit: 'days', note: t.durationNote },
      pending: { series: 'udsc_20260828_pending_stock', indicator: 'pending_cases', unit: 'cases', note: t.pendingNote },
      flow: { series: 'warehouse_all_outcomes', indicator: 'concluded_resolutions', unit: 'cases', note: t.flowNote }
    }[metric];
    const sources = new Map((data.sources || []).map(s => [s.id, s]));
    const rows = relevant.filter(r => r.geography_id === gid && r.series_id === contract.series && r.indicator_id === contract.indicator && r.permit_type === 'temporary_residence')
      .sort((a, b) => a.reference_period.localeCompare(b.reference_period));
    const seen = new Set(), unique = rows.filter(r => { if (seen.has(r.reference_period)) return false; seen.add(r.reference_period); return true; });
    const ambiguous = r => !r.as_of_date || String(r.quality_status).includes('period_ambiguous');
    const tableRows = unique.map(r => ({ period: r.reference_period, value: r.value, note: ambiguous(r) ? t.unknown : '', source: sources.get(r.source_id), locator: r.source_locator }));
    renderTable($('trend-table'), [t.period, t.value + ' (' + t[contract.unit] + ')', t.source], tableRows, state.lang);
    const plotLabel = r => metric === 'pending' ? r.reference_period : r.reference_period.slice(0, 4) + (r.reference_period.startsWith('2026') ? '*' : '');
    const rendered = draw(state, $('trend-chart'), type, unique.map(plotLabel), unique.map(r => ambiguous(r) ? null : r.value), t[metric], t.chartOffice + ': ' + available.get(gid));
    const notes = [contract.note, t.noWeighted];
    if (metric !== 'pending' && unique.some(r => r.reference_period.startsWith('2026'))) notes.push(t.partial);
    if (unique.some(ambiguous)) notes.push(t.chartOmitted);
    if (!rendered) notes.push(t.noChart);
    if ($('analytics-context')) $('analytics-context').textContent = notes.join(' ');
    const directory = Array.isArray(data.offices) ? data.offices : data.offices?.offices || [];
    const office = directory.find(o => o.geography_id === gid), link = $('office-link');
    if (link) {
      const url = safeURL(office?.contact_or_foreigners_url || office?.official_url) || 'https://www.gov.pl/web/mswia/urzedy-wojewodzkie';
      link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.textContent = office?.verification_status?.includes('profile_not_confirmed') || !office ? t.directoryLink : t.officeLink;
      link.title = office?.office_name || available.get(gid) || t.office;
    }
  };
  window.initEurostat = function initEurostat(context, lang) {
    euroState.data = context;
    bind($('eurostat-group'), () => window.renderEurostat(euroState.lang));
    window.renderEurostat(lang);
  };
  window.renderEurostat = function renderEurostat(lang) {
    const state = euroState; state.lang = language(lang); const t = text[state.lang], data = state.data;
    if (!data?.observations) return;
    options($('eurostat-group'), [['pl_all', t.plAll], ['eu_all', t.euAll], ['pl_by', t.plBy]], 'pl_all');
    const group = $('eurostat-group')?.value || 'pl_all';
    const geo = group === 'eu_all' ? 'EU27_2020' : 'PL', citizenship = group === 'pl_by' ? 'BY' : 'TOTAL';
    const rows = data.observations.filter(r => r.geography_id === geo && r.citizenship_code === citizenship && r.category === 'context-not-waiting' && r.unit_code === 'PER').sort((a, b) => a.reference_period.localeCompare(b.reference_period));
    const sources = new Map((data.sources || []).map(s => [s.id, s]));
    renderTable($('eurostat-table'), [t.period, t.permits, t.flags, t.source], rows.map(r => ({ period: r.reference_period, value: r.value, flags: r.flags, source: sources.get(r.source_id), locator: r.source_locator })), state.lang, true);
    const rendered = draw(state, $('eurostat-chart'), 'bar', rows.map(r => r.reference_period), rows.map(r => r.value), t.permits, t.chartEuro);
    const notes = [t.euroNote, t.flagNote];
    if (String(data.status).includes('pending')) notes.push(t.euroReview);
    if (!rendered) notes.push(t.noChart);
    if ($('eurostat-context')) $('eurostat-context').textContent = notes.join(' ');
  };
})();
