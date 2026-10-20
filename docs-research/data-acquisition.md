# Где получать новые сведения

План исследования на 20.10.2026. Запросы ниже — черновики: они не отправлены. Сохранять только агрегаты и документы об определениях; не запрашивать персональные карточки иностранцев, номера паспортов, адреса или частную переписку.

| Источник | Что брать и как | Что это не измеряет |
|---|---|---|
| [UdSC: статистики](https://www.gov.pl/web/udsc/statystyki-migracyjne) | Периодические XLSX и специальные месячные DOCX по Беларуси/Украине; сохранять дату среза, публикации и SHA-256 каждого файла | Сам по себе отчёт не доказывает сроки выдачи пластика |
| [migracje.gov.pl](https://migracje.gov.pl/) | Публичный API `wp-json/udscmap/v1/`: `applications/poland`, `decisions/poland`; параметры `year`, `caseType`, `groupBy`, `fields`. Сначала выгрузить справочники типов/гражданств и проверить фильтры контрольными запросами. Сохранять точный URL и ответ | Заявления не равны людям. Тип решения нельзя считать отфильтрованным, пока изменение параметра действительно меняет результат. Исторические годы могут пересчитываться |
| [Otwarte Dane, dataset948](https://api.dane.gov.pl/1.4/datasets/948/resources?page=1&per_page=50) | Каталог UdSC с ресурсом 2986, ведущим на Migracje. Это навигационный источник, а не независимая статистическая серия | Второй каталог той же базы не является независимым подтверждением |
| [Otwarte Dane, dataset2715](https://api.dane.gov.pl/1.4/datasets/2715/resources?page=1&per_page=50) | CSV заявлений UKR и агрегаты XLSX. Пройти все страницы; выбирать по `data_date`, а не первой строке. Различать накопленные регистрации и активные статусы | Это не очередь временных разрешений, не число заявлений CUKR |
| [NSA: статистики WSA](https://www.nsa.gov.pl/dokumenty/statystyki-wsa/) | Годовые файлы Dział2, листы по судам и символам. Сохранять исходные значения всех исходов и обе базы процентов. Учитывать составные символы 658/6272 и 659/6272 | 6272 шире выдачи ВНЖ. WSA — первая инстанция; решения NSA учитываются отдельно. CBOSA не заменяет полный реестр |
| [CBOSA](https://orzeczenia.nsa.gov.pl/) | Отбирать решения по статье, сигнатуре, дате и правовому вопросу. Проверять резолютивную часть, мотивировку, окончательность и последующую кассацию | Поиск опубликованных решений не даёт репрезентативный знаменатель всех дел |
| [NIK](https://www.nik.gov.pl/kontrole/wyniki-kontroli-nik/) | Информации о результатах, выступления по конкретным UW, выборка и период контроля. Данные об издержках судов и штатах сверять с приложениями | Контрольная выборка не национальная частота нарушений; разные виды производств могут быть смешаны |
| [GUS: работающие иностранцы](https://publikacje.new.stat.gov.pl/portal-publikacje/cudzoziemcy-wykonujacy-prace-w-polsce-w-marcu-2026-r) | Месячные XLSX, таблицы и определения занятости; регион, гражданство, форма занятости | Не то же население, что застрахованные ZUS, и не очередь ВНЖ |
| [ZUS: портал статистики](https://psz.zus.pl/kategorie/ubezpieczeni/ubezpieczenia-emerytalne-i-rentowe) | Месячные XLS/XLSX по гражданству/региону/возрасту, годовой отчёт «Cudzoziemcy». Физлицо учитывать один раз по определению таблицы | Количество застрахованных не сумма налогов и не полный бюджетный баланс |
| [Eurostat: методология](https://ec.europa.eu/eurostat/cache/metadata/en/migr_resval_esms.htm) | `migr_resfirst` — первые разрешения; `migr_resvalid` — действующие на конец года; `migr_reslong` — долгосрочные; Single Permit и Blue Card — отдельные коллекции. Фильтр `geo=PL`, гражданство, основание, длительность; сохранять флаги и `lastUpdate` | Это не польская административная очередь или время производства. Временная защита — отдельная коллекция; первые разрешения могут охватывать иные основания, чем pobyt czasowy |
| [Sejm API](https://api.sejm.gov.pl/) | Интерпелляции 18089,12584 и новые по ключевым словам; сохранять метаданные, даты поступления/ответа и тело, включая сноски | Дата ответа не всегда дата среза таблицы. Разные ответы нельзя склеивать без определения |
| [RCL UD408](https://legislacja.rcl.gov.pl/projekt/12412103) | Все версии проекта, OSR, замечания, ответы и отчёт консультаций; сверять актуальный этап с Sejm/ELI | Проект и дата планируемого принятия не действующий закон |
| [COPE/FAMI](https://www.gov.pl/web/dfe-mswia/projekty-fami-2021-2027) | Список соглашений, изменения, KPI и отчёты реализации; отдельно запрошено/одобрено/законтрактовано/выплачено/сертифицировано | Плановая цель и договорная сумма не фактический результат или расход |

## Приоритетный запрос UdSC: сопоставимость и баланс

Адресат — UdSC через актуальный канал, указанный на официальной странице «Uzyskaj informację publiczną». Попросить существующие отчёты и инструкции, а не персональные выгрузки. [Закон DIP](https://eli.gov.pl/api/acts/DU/2022/902/text.html): право каждого; без лишней задержки, обычно не позднее 14 дней; при мотивированном уведомлении срок продлевается максимум до 2 месяцев. Если создание ответа квалифицируют как переработку информации, объяснить общественную значимость или сузить запрос. Отказ оформляется решением; способы обжалования определяются по его содержанию.

```text
Wniosek o udostępnienie informacji publicznej

Na podstawie art. 2 ust. 1 i art. 10 ust. 1 u.d.i.p. proszę o przesłanie elektronicznych kopii istniejących raportów oraz instrukcji dotyczących:

1. definicji „sprawy o pobyt czasowy w toku” w tabeli pisma BSZ.WAiSM.0361.16.2026/DH z 28.08.2026: daty odniesienia, statusów, organów i rodzajów spraw;
2. sposobu uwzględniania spraw MOS, CUKR, postępowań zawieszonych, duplikatów, ponownych wniosków, przekazania właściwości i spraw faktycznie zakończonych, lecz niezamkniętych w systemie;
3. istniejących zestawień miesięcznych: stan początkowy, wpływ, zakończenia według rodzaju, korekty/przeniesienia i stan końcowy, osobno dla każdego wojewody oraz rodzaju postępowania, za okres [okres];
4. specyfikacji raportów „Średni czas postępowania — legalizacja — podział na wojewodów” i danych portalu migracje.gov.pl: źródła dat, filtrów, walidacji i deduplikacji;
5. istniejących dokumentów wyjaśniających różnicę między liczbą 398337 zakończeń w raportach Hurtowni za 2025 r., liczbą 445458 w tekście prognozy Głos Migranta oraz liczbą 445462 w sprawdzonym CSV Głos Migranta i bezpośrednim zapytaniu do API UdSC z 20.10.2026. Różnice względem Hurtowni wynoszą odpowiednio 47121 dla tekstu prognozy i 47125 dla CSV/API. Przyczyna rozbieżności 4 spraw między tekstem a danymi nie jest ustalona; istnienie starszego CSV ani rewizja danych nie zostały ustalone.

Proszę o udostępnienie dokumentów w istniejącej postaci, bez tworzenia nowego opracowania. Jeżeli część informacji nie jest posiadana, proszę wskazać brak i udostępnić pozostałą część. Proszę nie przekazywać danych osobowych wnioskodawców.
Adres odpowiedzi: [e-mail].
```

Проверка: `stock_end = stock_start + incoming − completed + net_transfers + corrections`. Не объявлять разность «ошибкой», пока не известны изменения охвата и корректировки.

## Воеводам: сроки, старые дела и этап карты

```text
Proszę o elektroniczne kopie istniejących raportów za [okres], osobno dla pobytu czasowego, art.114, Niebieskiej Karty UE, pobytu stałego i rezydenta UE:

— liczby wniosków, zakończeń według rodzaju i spraw w toku;
— definicji mierzonego czasu oraz istniejących zestawień mediany, percentyli i wieku spraw w toku;
— obsady faktycznej i wakatów, z rozdzieleniem osób orzekających, rejestracji, informacji, kart/PDPC i zadań CUKR;
— istniejących raportów etapu po decyzji: zamówienie personalizacji, otrzymanie karty przez urząd, zawiadomienie i odbiór;
— dokumentów o zmianach sposobu raportowania przy wdrożeniu MOS/CUKR.

Proszę o istniejące dokumenty, bez nowego opracowania; w razie braku miernika proszę wskazać ten brak. Dane wyłącznie zagregowane, bez danych osobowych stron.
```

Отсутствие готового p90 не превращать в обязанность построить новую сложную аналитику по первоначальному простому запросу. Для старых дел запросить существующие возрастные корзины; для длительности после решения уточнить, какая дата означает окончательность и какая — печать/получение.

## COPE и аудит

```text
Proszę o aktualne zestawienie statusu16projektów naboru FAMI.02.05-IZ.00-001/26 oraz istniejące zestawienia: wnioskowane, zatwierdzone, zakontraktowane, wypłacone i rozliczone środki. Proszę o aktualne wersje wskaźników16projektów2024 oraz dokumenty ewaluacji wpływu na czas postępowań. Proszę także o wskazanie sygnatury, daty, zakresu i kopii raportu audytu KAS przywoływanego w publicznej dyskusji, o ile taki dokument jest posiadany.
```

По состоянию на проверку первичный отчёт об упомянутом The Warsaw аудите KAS **не установлен**. Не подменять его письмом MF о резерве зарплат.

## Судам и будущим выпускам

Запрашивать агрегаты Dział2 по одинаковым периодам и письменное определение `uwzględniono / oddalono / odrzucono / w inny sposób / zamknięto`, включая смешанные 658/6272 и 659/6272. Полный реестр здесь не нужен для публичного набора. Если для проверки он необходим, хранить вне Git, публиковать только агрегаты.

При каждом обновлении сохранять сырой файл вне репозитория, время получения, SHA-256, единицу, население, дату/период, версию отчёта и место числа. Новое наблюдение сначала проходит сверку и независимый review. Наличие ссылки в каталоге не означает проверку всего документа; отсутствие найденного ответа не доказывает, что орган его не создавал.
