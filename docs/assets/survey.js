/* Survey answers stay in memory. Only a deletion receipt is stored locally. */
(() => {
  'use strict';
  const KEY = 'residence-observatory-survey-receipt-v1';
  const PRIVACY_VERSION = '2026-10-20';
  const DAY = 86400000;
  const REGIONS = ['PL-DS','PL-KP','PL-LU','PL-LB','PL-LD','PL-MA','PL-MZ','PL-OP','PL-PK','PL-PD','PL-PM','PL-SL','PL-SK','PL-WN','PL-WP','PL-ZP'];
  const T = {
    skip: ['Przejdź do ankiety','Перайсці да анкеты','Skip to survey'], back: ['Wróć do danych','Вярнуцца да даных','Back to data'], privacy: ['Prywatność i usuwanie danych','Прыватнасць і выдаленне даных','Privacy and deletion'],
    eyebrow: ['DOBROWOLNA ANKIETA · JEDNA SPRAWA','ДОБРААХВОТНАЯ АНКЕТА · АДНА СПРАВА','VOLUNTARY SURVEY · ONE CASE'],
    title: ['Opowiedz o sprawie — bez numerów spraw i dokumentów.','Раскажыце пра справу — без нумароў спраў і дакументаў.','Tell us about your case — without case or document numbers.'],
    intro: ['Wypełnij jedną ankietę dla jednego złożonego wniosku. Pola * są wymagane; pozostałe możesz pominąć. Nie zbieramy nazwisk, PESEL, numerów spraw, dokumentów ani załączników.','Адна анкета — адна ўжо пададзеная заява. Палі * абавязковыя; астатнія можна прапусціць. Не збіраем імёнаў, PESEL, нумароў спраў, дакументаў або дадаткаў.','Complete one survey for one submitted application. Fields * are required; everything else is optional. We collect no names, PESEL, case numbers, documents or attachments.'],
    bias: ['To próba ochotnicza, niereprezentatywna dla wszystkich wnioskodawców. Sprawy otwarte i zakończone analizujemy osobno; publikujemy tylko sprawdzone agregaty. Ankieta nie wpływa na Twoją sprawę i nie składa skargi.','Гэта добраахвотная выбарка, якая не рэпрэзентуе ўсіх заяўнікаў. Адкрытыя і завершаныя справы аналізуюцца асобна; публікуюцца толькі правераныя агрэгаты. Анкета не ўплывае на вашу справу і не падае скаргу.','This self-selected sample does not represent all applicants. Ongoing and concluded cases are analysed separately; only reviewed aggregates are published. The survey does not affect your case or file a complaint.'],
    controller: ['Administrator danych:','Адміністратар даных:','Data controller:'], core: ['1. Twoja sprawa','1. Ваша справа','1. Your case'],
    region: ['Urząd / województwo *','Упраўленне / ваяводства *','Office / voivodeship *'], permit: ['Rodzaj zezwolenia *','Від дазволу *','Permit type *'], status: ['Obecny stan sprawy *','Бягучы стан справы *','Current case status *'], applied: ['Data złożenia wniosku *','Дата падачы заявы *','Application submission date *'], decision: ['Data decyzji / innego zakończenia sprawy *','Дата рашэння / іншага завяршэння справы *','Decision / other case conclusion date *'],
    dateHelp: ['Podaj daty, które znasz. Jeśli nie znasz wymaganej daty, nie zgaduj — wróć po sprawdzeniu dokumentów. Najwcześniejsza obsługiwana data: 01.01.2014.','Указвайце вядомыя даты. Калі абавязковая дата невядомая, не здагадвайцеся — вярніцеся пасля праверкі дакументаў. Найранейшая дата: 01.01.2014.','Use dates you know. If a required date is unknown, do not guess; return after checking your documents. Earliest supported date: 1 Jan 2014.'],
    extras: ['2. Dodatkowe informacje — wszystkie opcjonalne','2. Дадатковыя звесткі — усё неабавязкова','2. Extra information — all optional'], basis: ['Główny powód pobytu','Асноўная падстава пражывання','Main reason for residence'], submission: ['Sposób złożenia wniosku','Спосаб падачы заявы','Submission method'], nationality: ['Obywatelstwo','Грамадзянства','Citizenship'],
    reportedDays: ['Deklarowany czas oczekiwania w dniach','Паведамлены час чакання ў днях','Self-reported wait in days'], household: ['Liczba osób w gospodarstwie domowym (1–10)','Колькасць чалавек у хатняй гаспадарцы (1–10)','Household size (1–10)'], court: ['Wynik skargi do sądu, jeśli była','Вынік судовай скаргі, калі была','Court complaint outcome, if applicable'], bank: ['Bank, jeśli wystąpił problem','Банк, калі была праблема','Bank, if you had a problem'], bankIssue: ['Rodzaj problemu z bankiem','Від праблемы з банкам','Type of banking problem'],
    reportedHelp: ['Deklarowany czas zachowujemy osobno od obliczenia z dat. Nie dopisuj danych innych osób.','Паведамлены час захоўваецца асобна ад разліку з дат. Не дадавайце звестак іншых людзей.','The self-reported wait is kept separate from the date calculation. Do not include other people’s details.'],
    difficulties: ['Jakie trudności wystąpiły? Możesz zaznaczyć kilka.','Якія былі цяжкасці? Можна выбраць некалькі.','What difficulties occurred? Select any that apply.'], actions: ['Jakie działania podjęto? Możesz zaznaczyć kilka.','Якія дзеянні былі зробленыя? Можна выбраць некалькі.','What actions were taken? Select any that apply.'],
    contact: ['Kontakt — całkowicie opcjonalny','Кантакт — цалкам неабавязкова','Contact — completely optional'], email: ['Email do ewentualnego kontaktu','Email для магчымага кантакту','Email for possible follow-up'],
    contactConsent: ['Osobno zgadzam się na kontakt pod podanym adresem. Email nie będzie publikowany ani dodawany do publicznych danych.','Асобна пагаджаюся на кантакт праз гэты адрас. Email не будзе апублікаваны або дададзены да публічных даных.','I separately consent to contact at this address. My email will not be published or included in public data.'],
    emailHelp: ['Bez emaila ankieta jest równie ważna. Jeśli go podasz, potrzebna jest odrębna zgoda na kontakt.','Без email анкета мае такую ж каштоўнасць. Калі яго ўказваеце, патрэбная асобная згода на кантакт.','The survey is equally valuable without email. Providing one requires separate contact consent.'],
    consentTitle: ['3. Zgoda na przetwarzanie','3. Згода на апрацоўку','3. Processing consent'],
    consent: ['Dobrowolnie zgadzam się na przetwarzanie podanych odpowiedzi do badania opisanego w informacji o prywatności (wersja 20.10.2026). Wiem, że mogę wycofać zgodę i usunąć zapis przy użyciu klucza usunięcia.','Добраахвотна пагаджаюся на апрацоўку адказаў для даследавання, апісанага ў паведамленні аб прыватнасці (версія 20.10.2026). Ведаю, што магу адклікаць згоду і выдаліць запіс з дапамогай ключа выдалення.','I voluntarily consent to processing my answers for the research described in the privacy notice (version 20 Oct 2026). I understand I can withdraw consent and delete the record using my deletion key.'],
    readPrivacy: ['Przeczytaj zasady prywatności i okresy przechowywania','Прачытайце правілы прыватнасці і тэрміны захоўвання','Read the privacy notice and retention periods'], verificationTitle: ['4. Weryfikacja i wysłanie','4. Праверка і адпраўка','4. Verification and submission'],
    verificationInfo: ['Cloudflare Turnstile sprawdza, czy formularza nie wysyła automat. Nie łączymy się z tym dostawcą, dopóki nie uruchomisz weryfikacji. Odpowiedzi nie są wysyłane podczas tej weryfikacji.','Cloudflare Turnstile правярае, ці не адпраўляе форму аўтамат. Злучэнне з гэтым сэрвісам пачынаецца толькі пасля вашага дзеяння. Адказы падчас праверкі не адпраўляюцца.','Cloudflare Turnstile checks for automated submissions. We connect to this provider only after you enable verification. Your answers are not sent during that check.'],
    verificationAck: ['Zapoznałem(-am) się z informacją o prywatności i chcę załadować zewnętrzną weryfikację Cloudflare.','Я азнаёміўся(-лася) з паведамленнем аб прыватнасці і хачу загрузіць знешнюю праверку Cloudflare.','I have read the privacy notice and want to load Cloudflare’s external verification.'],
    enableVerification: ['Uruchom weryfikację','Запусціць праверку','Enable verification'], send: ['Wyślij ankietę','Адправіць анкету','Submit survey'], retry: ['Ponów tę samą próbę','Паўтарыць тую ж спробу','Retry this same attempt'],
    receiptTitle: ['Twój klucz usunięcia','Ваш ключ выдалення','Your deletion receipt'],
    receiptNotice: ['W tym urządzeniu zapisujemy tylko identyfikator i klucz usunięcia, nigdy odpowiedzi ani email. Osoba posiadająca klucz może usunąć zapis. Pobierz go i przechowuj prywatnie. Przeglądarka zachowuje tylko ostatni taki klucz.','На гэтай прыладзе захоўваюцца толькі ідэнтыфікатар і ключ выдалення, ніколі адказы або email. Уладальнік ключа можа выдаліць запіс. Спампуйце і захоўвайце яго прыватна. Браўзер захоўвае толькі апошні такі ключ.','This device stores only the record ID and deletion key, never answers or email. Anyone with the key can delete the record. Download it and keep it private. The browser retains only the latest receipt.'],
    receiptId: ['Identyfikator zapisu','Ідэнтыфікатар запісу','Record ID'], receiptToken: ['Prywatny klucz usunięcia','Прыватны ключ выдалення','Private deletion key'], downloadReceipt: ['Pobierz klucz JSON','Спампаваць ключ JSON','Download receipt JSON'], clearReceipt: ['Usuń zapisaną kopię klucza','Прыбраць захаваную копію ключа','Clear saved receipt copy'], newCase: ['Nowa sprawa / wyczyść formularz','Новая справа / ачысціць форму','New case / reset form'],
    clearHelp: ['Najpierw pobierz klucz JSON i zachowaj go prywatnie. Kopię można wyczyścić po potwierdzeniu przyjęcia lub usunięcia zapisu, a także po ponownym otwarciu strony. Klucz aktywnej próby o nieznanym wyniku pozostaje chroniony. Wyczyszczenie nie usuwa zapisu na serwerze. Na wspólnym urządzeniu zamknij potem tę kartę.','Спачатку спампуйце ключ JSON і захавайце яго прыватна. Копію можна прыбраць пасля пацверджання прыняцця або выдалення запісу, а таксама пасля паўторнага адкрыцця старонкі. Ключ актыўнай спробы з невядомым вынікам застаецца абароненым. Ачыстка не выдаляе запіс на серверы. На агульнай прыладзе пасля гэтага закрыйце ўкладку.','Download the receipt JSON first and keep it private. You may clear the copy after confirmed acceptance or deletion, or after reopening the page. An active attempt with an unknown outcome keeps its recovery key. Clearing does not delete the server record. On a shared device, close this tab afterwards.'],
    clearFailed: ['Nie udało się usunąć zapisanej kopii z przeglądarki. Klucz pozostaje widoczny; pobierz go i sprawdź ustawienia pamięci przeglądarki.','Не ўдалося прыбраць захаваную копію з браўзера. Ключ застаецца бачным; спампуйце яго і праверце налады сховішча браўзера.','The saved browser copy could not be cleared. The key remains visible; download it and check the browser’s storage settings.'],
    deleteTitle: ['Usuń wcześniejszy zapis','Выдаліць папярэдні запіс','Delete an earlier record'], deleteInfo: ['Wpisz identyfikator i klucz, aby usunąć odpowiedzi oraz powiązany kontakt. Usunięcie klucza z przeglądarki nie usuwa danych na serwerze.','Увядзіце ідэнтыфікатар і ключ, каб выдаліць адказы і звязаны кантакт. Выдаленне ключа з браўзера не выдаляе даных на серверы.','Enter the ID and key to delete the answers and linked contact. Clearing a browser receipt does not delete server data.'], deleteSend: ['Usuń zapis','Выдаліць запіс','Delete record'],
    choose: ['Wybierz','Выберыце','Choose'], optional: ['Nie podaję / nie dotyczy','Не паведамляю / не датычыцца','Prefer not to say / not applicable'],
    loading: ['Sprawdzamy dostępność ankiety…','Правяраем даступнасць анкеты…','Checking survey availability…'], ready: ['Ankieta jest dostępna. Odpowiedzi wyślemy dopiero po naciśnięciu „Wyślij”.','Анкета даступная. Адказы будуць адпраўленыя толькі пасля націску «Адправіць».','The survey is available. Answers are sent only when you press Submit.'],
    unavailable: ['Zbieranie odpowiedzi jest obecnie niedostępne. Niczego nie wysłano. Spróbuj później.','Збор адказаў цяпер недаступны. Нічога не адпраўлена. Паспрабуйце пазней.','Response collection is currently unavailable. Nothing has been sent. Please return later.'],
    configFailed: ['Nie udało się sprawdzić połączenia. Wysyłanie jest wyłączone; odśwież stronę później.','Не ўдалося праверыць злучэнне. Адпраўка выключаная; абнавіце старонку пазней.','The connection could not be checked. Submission is disabled; reload later.'],
    selectDates: ['Wybierz stan sprawy i podaj daty, aby zobaczyć obliczenie.','Выберыце стан справы і ўкажыце даты для разліку.','Select the case status and enter dates to see the calculation.'],
    pendingDays: ['Sprawa nadal otwarta: {n} dni od złożenia do {date} (UTC). To obserwacja nieukończona, nie czas do decyzji.','Справа яшчэ адкрытая. Працягласць, дзён: {n}, ад падачы да {date} (UTC). Гэта незавершанае назіранне, не час да рашэння.','Still pending: {n} days from submission to {date} (UTC). This is an ongoing, right-censored observation, not time to decision.'],
    concludedDays: ['Sprawa zakończona: {n} dni od złożenia do zakończenia sprawy. Odbiór karty nie wchodzi do tego obliczenia.','Справа завершаная. Працягласць, дзён: {n}, ад падачы да завяршэння справы. Атрыманне карткі не ўваходзіць у разлік.','Concluded case: {n} days from submission to case conclusion. Card collection is not included.'],
    required: ['Uzupełnij wymagane pole.','Запоўніце абавязковае поле.','Complete this required field.'], invalidDates: ['Sprawdź daty: od 01.01.2014 do dzisiaj; decyzja nie może być przed wnioskiem.','Праверце даты: ад 01.01.2014 да сёння; рашэнне не можа быць раней за заяву.','Check dates: 1 Jan 2014 through today; the decision cannot precede submission.'], invalidNumber: ['Podaj liczbę całkowitą w podanym zakresie.','Увядзіце цэлы лік у пазначаных межах.','Enter a whole number within the stated range.'], invalidEmail: ['Sprawdź adres email.','Праверце адрас email.','Check the email address.'], needContact: ['Email wymaga osobnej zgody na kontakt.','Для email патрэбная асобная згода на кантакт.','Email requires separate contact consent.'], needConsent: ['Do wysłania potrzebna jest dobrowolna zgoda na przetwarzanie.','Для адпраўкі патрэбная добраахвотная згода на апрацоўку.','Submission requires voluntary processing consent.'],
    verifyLoading: ['Ładowanie zewnętrznej weryfikacji…','Загрузка знешняй праверкі…','Loading external verification…'], verifyReady: ['Weryfikacja zakończona. Możesz wysłać ankietę.','Праверка завершаная. Можна адправіць анкету.','Verification complete. You can submit the survey.'], verifyNeeded: ['Uruchom i zakończ weryfikację przed wysłaniem.','Запусціце і завяршыце праверку перад адпраўкай.','Enable and complete verification before submitting.'], verifyFailed: ['Weryfikacja nie powiodła się lub wygasła. Uruchom ją ponownie.','Праверка не атрымалася або скончылася. Запусціце яе зноў.','Verification failed or expired. Start it again.'],
    sending: ['Wysyłanie… Nie zamykaj tej karty.','Адпраўка… Не закрывайце гэтую ўкладку.','Submitting… Please keep this tab open.'], accepted: ['Ankieta została przyjęta. Zachowaj klucz usunięcia.','Анкета прынятая. Захавайце ключ выдалення.','Survey accepted. Keep your deletion receipt.'],
    attempted: ['Klucz tej próby jest gotowy. Sam klucz nie potwierdza przyjęcia ankiety.','Ключ гэтай спробы гатовы. Сам ключ не пацвярджае прыняцця анкеты.','This attempt’s receipt is ready. A receipt alone does not confirm acceptance.'],
    restored: ['Znaleziono klucz wcześniejszej próby. Nie potwierdza on przyjęcia ankiety. Możesz pobrać klucz, usunąć zapis lub jawnie rozpocząć nową sprawę. Odpowiedzi nie są przechowywane w przeglądarce.','Знойдзены ключ папярэдняй спробы. Ён не пацвярджае прыняцця анкеты. Можна спампаваць ключ, выдаліць запіс або пачаць новую справу. Адказы ў браўзеры не захоўваюцца.','A receipt from an earlier attempt was found. It does not confirm acceptance. Download it, delete the record or explicitly start a new case. Answers are not stored in the browser.'],
    uncertain: ['Nie potwierdzono wyniku wysłania. Zachowano ten sam identyfikator i klucz. Odpowiedzi tej próby są zablokowane; ponów weryfikację i tę samą próbę albo użyj klucza do usunięcia zapisu.','Вынік адпраўкі не пацверджаны. Захаваныя тыя ж ідэнтыфікатар і ключ. Адказы гэтай спробы заблакаваныя; паўтарыце праверку і тую ж спробу або выдаліце запіс ключом.','Submission outcome is unconfirmed. The same ID and key are retained. This attempt’s answers are locked; verify again and retry the same attempt, or use the receipt to delete the record.'],
    conflict: ['Ten klucz jest już związany z inną wersją odpowiedzi. Nie wysłano nowego zapisu. Zachowaj klucz i użyj usuwania albo skontaktuj się z administratorem.','Гэты ключ ужо звязаны з іншай версіяй адказаў. Новы запіс не створаны. Захавайце ключ, скарыстайцеся выдаленнем або звяжыцеся з адміністратарам.','This receipt is already linked to different answers. No new record was created. Keep the receipt and use deletion or contact the controller.'],
    rateLimited: ['Zbyt wiele prób. Poczekaj co najmniej 20 minut i ponów tę samą próbę.','Занадта шмат спроб. Пачакайце не менш за 20 хвілін і паўтарыце тую ж спробу.','Too many attempts. Wait at least 20 minutes, then retry the same attempt.'],
    storageFailed: ['Przeglądarka nie pozwala zapisać klucza. Pobierz go teraz; po zamknięciu karty możesz go utracić.','Браўзер не дазваляе захаваць ключ. Спампуйце яго цяпер; пасля закрыцця ўкладкі ён можа згубіцца.','The browser cannot save the receipt. Download it now; closing this tab may lose it.'], saved: ['Klucz zapisano lokalnie. Odpowiedzi i email nie są zapisywane.','Ключ захаваны лакальна. Адказы і email не захоўваюцца.','Receipt saved locally. Answers and email are not stored.'], cleared: ['Klucz usunięto z tej przeglądarki. To nie usuwa zapisu na serwerze.','Ключ прыбраны з гэтага браўзера. Гэта не выдаляе запіс на серверы.','Receipt cleared from this browser. This does not delete the server record.'],
    invalidReceipt: ['Sprawdź identyfikator i prywatny klucz z otrzymanego pliku.','Праверце ідэнтыфікатар і прыватны ключ з атрыманага файла.','Check the ID and private key from your receipt file.'], deleting: ['Usuwanie…','Выдаленне…','Deleting…'], deleted: ['Usunięto zapis albo nie było już go na serwerze. Nie można z tego ustalić, czy wcześniejsza próba została przyjęta.','Запіс выдалены або яго ўжо не было на серверы. Гэта не дазваляе вызначыць, ці была папярэдняя спроба прынятая.','The record was deleted or was already absent. This does not establish whether an earlier submission was accepted.'], deleteFailed: ['Nie udało się potwierdzić usunięcia. Sprawdź klucz i spróbuj później; zachowaj plik.','Не ўдалося пацвердзіць выдаленне. Праверце ключ і паспрабуйце пазней; захавайце файл.','Deletion could not be confirmed. Check the key and retry later; retain the receipt.'], resetNotice: ['Formularz wyczyszczono. Nowe wysłanie utworzy nową próbę; wcześniejszy zapis nie zostaje przez to usunięty.','Форма ачышчаная. Наступная адпраўка створыць новую спробу; папярэдні запіс не выдаляецца.','Form reset. A new submission creates a new attempt; it does not delete an earlier record.']
  };
  const OPTIONS = {
    permit: [['temporary','Pobyt czasowy','Часовае пражыванне','Temporary residence'],['permanent','Pobyt stały','Пастаяннае пражыванне','Permanent residence'],['eu_long_term','Rezydent długoterminowy UE','Доўгатэрміновы рэзідэнт ЕС','EU long-term resident']],
    status: [['pending','W toku','У працэсе','Pending'],['positive','Decyzja pozytywna','Станоўчае рашэнне','Positive decision'],['negative','Decyzja odmowna','Адмоўнае рашэнне','Negative decision'],['discontinued','Umorzenie','Спыненне справы','Discontinued'],['unexamined','Pozostawiono bez rozpoznania','Пакінута без разгляду','Left unexamined']],
    basis: [['work','Praca','Праца','Work'],['family','Rodzina','Сям’я','Family'],['study','Studia / nauka','Навучанне','Study'],['business','Działalność gospodarcza','Прадпрымальніцтва','Business'],['other','Inny','Іншая','Other']],
    submission: [['mos','MOS','MOS','MOS'],['post','Poczta','Пошта','Post'],['in_person','Osobiście','Асабіста','In person'],['other','Inny','Іншы','Other']],
    nationality: [['BY','Białoruś','Беларусь','Belarus'],['UA','Ukraina','Украіна','Ukraine'],['RU','Rosja','Расія','Russia'],['other','Inne','Іншае','Other']],
    court_outcome: [['pending','Jeszcze brak rozstrzygnięcia','Рашэння яшчэ няма','Still pending'],['upheld','Uwzględniono','Скарга задаволеная','Upheld'],['dismissed','Oddalono','Адмоўлена па сутнасці','Dismissed on merits'],['rejected','Odrzucono','Адхілена без разгляду па сутнасці','Rejected procedurally'],['other','Inny','Іншы','Other']],
    bank: [['millennium','Millennium','Millennium','Millennium'],['pko_bp','PKO BP','PKO BP','PKO BP'],['pekao','Pekao','Pekao','Pekao'],['other','Inny bank','Іншы банк','Other bank']],
    bank_issue: [['opening','Otwarcie konta','Адкрыццё рахунку','Opening an account'],['digital','Dostęp cyfrowy','Лічбавы доступ','Digital access'],['card','Karta bankowa','Банкаўская картка','Bank card'],['termination','Zamknięcie / wypowiedzenie konta','Закрыццё / скасаванне рахунку','Account closure / termination'],['other','Inny problem','Іншая праблема','Other issue']],
    difficulties: [['appointment','Termin wizyty','Дата візіту','Appointment'],['delivery','Dostarczenie / doręczenie korespondencji','Дастаўка карэспандэнцыі','Mail delivery / service'],['documents','Dokumenty / uzupełnienia','Дакументы / дапаўненні','Documents / additional requests'],['no_response','Brak odpowiedzi','Няма адказу','No response'],['bank','Bank','Банк','Bank'],['work','Praca','Праца','Work'],['travel','Podróże','Паездкі','Travel'],['other','Inne','Іншае','Other']],
    actions: [['ponaglenie','Ponaglenie','Панагленне (ponaglenie)','Administrative reminder (ponaglenie)'],['wsa','Skarga do WSA','Скарга ў WSA','WSA court complaint'],['lawyer','Pomoc prawnika','Дапамога юрыста','Lawyer assistance'],['rpo','Kontakt z RPO','Кантакт з RPO','Contacting the Ombudsman (RPO)'],['bank_complaint','Reklamacja do banku','Прэтэнзія ў банк','Bank complaint']]
  };
  const $ = id => document.getElementById(id);
  const tr = (key, values = {}) => Object.entries(values).reduce((s, [k,v]) => s.replaceAll('{'+k+'}', String(v)), RO.t(...T[key]));
  const state = { initialized: false, config: null, endpoint: null, offices: [], phase: 'editing', attempt: null, receipt: null, receiptFinal: false, receiptCleared: false, accepted: false, busy: false, deleting: false, token: '', widget: null, script: null, verifying: false, storage: '', notice: '', submission: '', verification: '', deletion: '' };
  const today = () => new Date().toISOString().slice(0, 10);
  function dateNumber(s) {
    if (!/^20\d{2}-\d{2}-\d{2}$/.test(s)) return null;
    const n = Date.parse(s+'T00:00:00Z'); return Number.isFinite(n) && new Date(n).toISOString().slice(0,10) === s ? n : null;
  }
  function duration(payload) {
    const a = dateNumber(payload.applied_date), end = payload.status === 'pending' ? dateNumber(today()) : dateNumber(payload.decision_date || '');
    return a !== null && end !== null && end >= a ? Math.round((end-a)/DAY) : null;
  }
  function setOptions(select, entries, required = false) {
    const value = select.value; select.replaceChildren();
    const empty = document.createElement('option'); empty.value = ''; empty.textContent = tr(required ? 'choose' : 'optional'); select.append(empty);
    for (const [code, ...labels] of entries) { const o = document.createElement('option'); o.value = code; o.textContent = RO.t(...labels); select.append(o); }
    select.value = entries.some(([code]) => code === value) ? value : '';
  }
  function checkOptions(group) {
    const checked = new Set([...$(group+'-group').querySelectorAll('input:checked')].map(x => x.value));
    const fragment = document.createDocumentFragment();
    for (const [code, ...labels] of OPTIONS[group]) {
      const label = document.createElement('label'); label.className = 'check';
      const input = document.createElement('input'); input.type = 'checkbox'; input.name = group; input.value = code; input.checked = checked.has(code);
      const span = document.createElement('span'); span.textContent = RO.t(...labels); label.append(input,span); fragment.append(label);
    }
    $(group+'-group').replaceChildren(fragment);
  }
  function fillOptions() {
    setOptions($('survey-region'), state.offices.map(o => [o.geography_id, ...Array(3).fill(o.geography_name+' — '+o.office_name)]), true);
    const ids = { permit:'survey-permit',status:'survey-status',basis:'survey-basis',submission:'survey-submission',nationality:'survey-nationality',court_outcome:'survey-court',bank:'survey-bank',bank_issue:'survey-bank-issue' };
    for (const [key,id] of Object.entries(ids)) setOptions($(id), OPTIONS[key], ['permit','status'].includes(key));
    checkOptions('difficulties'); checkOptions('actions');
  }
  function showReceipt() {
    $('receipt-box').hidden = !state.receipt && !state.receiptCleared;
    $('receipt-id').textContent = state.receipt?.id || ''; $('receipt-token').textContent = state.receipt?.token || '';
    $('receipt-download').disabled = !state.receipt;
    if (!state.receipt && !state.receiptCleared) return;
    $('receipt-state').textContent = tr(state.receiptCleared ? 'cleared' : state.deletion === 'deleted' && state.receiptFinal ? 'deleted' : state.accepted ? 'accepted' : state.phase === 'restored' ? 'restored' : 'attempted');
    $('receipt-storage-status').textContent = state.storage ? tr(state.storage) : '';
  }
  function refreshControls() {
    const available = state.config?.collection_enabled === true && state.endpoint && state.offices.length === 16;
    $('survey-fields').disabled = !available || state.phase !== 'editing' || state.busy;
    const decided = $('survey-status').value !== '' && $('survey-status').value !== 'pending';
    $('decision-wrap').hidden = !decided; $('survey-decision').disabled = !decided;
    $('survey-decision').required = decided;
    $('survey-applied').max = today(); $('survey-decision').max = today(); $('survey-decision').min = $('survey-applied').value || '2014-01-01';
    const email = $('survey-email').value.trim(); $('contact-consent').disabled = !email;
    if (!email) $('contact-consent').checked = false;
    const final = state.phase === 'restored' || state.phase === 'final';
    $('enable-verification').disabled = !available || !$('verification-ack').checked || state.busy || state.verifying || state.accepted || final;
    $('verification-ack').disabled = !available || state.busy || state.accepted || final;
    $('survey-submit').disabled = !available || !state.token || state.busy || state.accepted || final;
    $('survey-submit').textContent = tr(state.busy ? 'sending' : state.attempt ? 'retry' : 'send');
    $('delete-submit').disabled = !state.endpoint || state.deleting || state.busy;
    $('receipt-clear').disabled = !state.receipt || !(state.receiptFinal || state.phase === 'restored' && !state.attempt) || state.busy || state.deleting;
    $('delete-submit').textContent = tr(state.deleting ? 'deleting' : 'deleteSend');
    $('new-case').disabled = state.busy || Boolean(state.receipt);
    $('collection-status').textContent = tr(state.config === null ? 'loading' : available ? 'ready' : state.notice === 'configFailed' ? 'configFailed' : 'unavailable');
    $('submission-status').textContent = state.submission ? tr(state.submission) : '';
    $('verification-status').textContent = state.verification ? tr(state.verification) : '';
    $('delete-status').textContent = state.deletion ? tr(state.deletion) : '';
  }
  function preview() {
    const payload = state.attempt?.payload || { status:$('survey-status').value, applied_date:$('survey-applied').value, decision_date:$('survey-decision').value };
    const n = duration(payload), status = payload.status;
    $('duration-output').textContent = n === null || !status ? tr('selectDates') : tr(status === 'pending' ? 'pendingDays' : 'concludedDays', { n:RO.format(n),date:today() });
  }
  function render() {
    document.querySelectorAll('[data-s]').forEach(node => { if (T[node.dataset.s]) node.textContent = tr(node.dataset.s); });
    document.title = RO.t('Ankieta o sprawie pobytowej','Анкета пра справу пражывання','Residence-case survey')+' · Residence Observatory';
    $('widget-language-note').hidden = RO.language !== 'be';
    $('widget-language-note').textContent = RO.language === 'be' ? 'Сам віджэт Cloudflare паказваецца па-англійску: сэрвіс не падтрымлівае беларускую мову.' : '';
    fillOptions(); preview(); showReceipt(); refreshControls();
  }
  function values() {
    const form = new FormData($('survey-form'));
    const out = { region:form.get('region') || '',permit:form.get('permit') || '',status:form.get('status') || '',applied_date:form.get('applied_date') || '',consent:$('survey-consent').checked,privacy_version:PRIVACY_VERSION,website:form.get('website') || '' };
    if (out.status !== 'pending') out.decision_date = form.get('decision_date') || '';
    for (const key of ['basis','submission','nationality','court_outcome','bank','bank_issue']) if (form.get(key)) out[key] = form.get(key);
    for (const key of ['reported_days','household_size']) if (form.get(key) !== null && form.get(key) !== '') out[key] = Number(form.get(key));
    out.difficulties = form.getAll('difficulties'); out.actions = form.getAll('actions');
    const email = $('survey-email').value.trim(); if (email) { out.email = email; out.contact_consent = $('contact-consent').checked; }
    return out;
  }
  function validate() {
    const f = $('survey-form'); f.querySelectorAll('input,select').forEach(x => x.setCustomValidity(''));
    const payload = values();
    for (const id of ['survey-region','survey-permit','survey-status','survey-applied']) if (!$(id).value) $(id).setCustomValidity(tr('required'));
    const a = dateNumber(payload.applied_date), d = dateNumber(payload.decision_date || ''), now = dateNumber(today());
    if (a === null || a < Date.UTC(2014,0,1) || a > now) $('survey-applied').setCustomValidity(tr('invalidDates'));
    if (payload.status && payload.status !== 'pending' && (d === null || d < a || d > now)) $('survey-decision').setCustomValidity(tr('invalidDates'));
    for (const [id,min,max] of [['survey-days',0,10000],['survey-household',1,10]]) if ($(id).value !== '' && (!Number.isInteger(Number($(id).value)) || Number($(id).value)<min || Number($(id).value)>max)) $(id).setCustomValidity(tr('invalidNumber'));
    if (payload.email && (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email) || payload.email.length > 254)) $('survey-email').setCustomValidity(tr('invalidEmail'));
    if (payload.email && !$('contact-consent').checked) $('contact-consent').setCustomValidity(tr('needContact'));
    if (!$('survey-consent').checked) $('survey-consent').setCustomValidity(tr('needConsent'));
    return f.reportValidity() ? payload : null;
  }
  function persist(receipt) {
    state.receipt = { id:receipt.id,token:receipt.token };
    state.receiptFinal = false; state.receiptCleared = false;
    try { localStorage.setItem(KEY,JSON.stringify(state.receipt)); state.storage = 'saved'; }
    catch (_) { state.storage = 'storageFailed'; }
    $('delete-id').value = receipt.id; $('delete-token').value = receipt.token;
    showReceipt();
  }
  function makeReceipt() {
    const bytes = crypto.getRandomValues(new Uint8Array(32));
    const token = btoa(String.fromCharCode(...bytes)).replaceAll('+','-').replaceAll('/','_').replaceAll('=','');
    return { id:crypto.randomUUID(),token };
  }
  function removeWidget() {
    state.token = '';
    if (state.widget !== null && window.turnstile) { try { window.turnstile.remove(state.widget); } catch (_) {} }
    state.widget = null; $('turnstile-container').replaceChildren();
  }
  function loadProvider() {
    if (window.turnstile?.render) return Promise.resolve();
    if (state.script) return state.script;
    state.script = new Promise((resolve,reject) => {
      const script = document.createElement('script'); script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'; script.async = true;
      const timer = setTimeout(() => { script.remove(); state.script = null; reject(new Error('verification_failed')); },20000);
      script.onload = () => { clearTimeout(timer); window.turnstile?.render ? resolve() : reject(new Error('verification_failed')); };
      script.onerror = () => { clearTimeout(timer); script.remove(); state.script = null; reject(new Error('verification_failed')); };
      document.head.append(script);
    });
    return state.script;
  }
  async function enableVerification() {
    if (!$('verification-ack').checked || !state.config?.collection_enabled || state.busy || state.accepted || ['restored','final'].includes(state.phase)) return;
    state.verifying = true; state.verification = 'verifyLoading'; refreshControls();
    try {
      await loadProvider();
      if (!$('verification-ack').checked || state.accepted) return;
      removeWidget();
      state.widget = window.turnstile.render($('turnstile-container'), {
        sitekey:state.config.sitekey,action:'residence_survey',language:RO.language === 'pl' ? 'pl' : 'en',
        size:$('turnstile-container').getBoundingClientRect().width < 300 ? 'compact' : 'flexible',theme:'light','response-field':false,
        callback:token => { state.token = token; state.verification = 'verifyReady'; refreshControls(); },
        'expired-callback':() => { state.token = ''; state.verification = 'verifyFailed'; refreshControls(); },
        'error-callback':() => { state.token = ''; state.verification = 'verifyFailed'; refreshControls(); return true; }
      });
    } catch (_) { state.verification = 'verifyFailed'; }
    finally { state.verifying = false; refreshControls(); }
  }
  async function post(path,payload) {
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(),25000);
    try {
      const response = await fetch(new URL(path,state.endpoint), { method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),credentials:'omit',cache:'no-store',referrerPolicy:'no-referrer',redirect:'error',signal:controller.signal });
      const body = await response.json().catch(() => ({}));
      return { response,body };
    } finally { clearTimeout(timer); }
  }
  async function submit(event) {
    event.preventDefault();
    if (state.busy || state.accepted || ['restored','final'].includes(state.phase) || !state.config?.collection_enabled || !state.endpoint) return;
    const payload = state.attempt?.payload || validate(); if (!payload) return;
    if (!state.token || !$('verification-ack').checked) { state.verification = 'verifyNeeded'; refreshControls(); return; }
    if (!state.attempt) {
      try { const receipt = makeReceipt(); state.attempt = { receipt,payload }; persist(receipt); }
      catch (_) { state.submission = 'configFailed'; refreshControls(); return; }
    }
    state.busy = true; state.phase = 'attempt'; state.submission = 'sending'; refreshControls();
    try {
      const { response,body } = await post('/v1/responses',{ ...state.attempt.payload,request_id:state.attempt.receipt.id,deletion_token:state.attempt.receipt.token,turnstile_token:state.token });
      if (response.status === 201 && body.accepted === true && body.id === state.attempt.receipt.id && body.deletion_token === state.attempt.receipt.token) {
        state.accepted = true; state.receiptFinal = true; state.submission = 'accepted'; removeWidget(); $('receipt-box').scrollIntoView({ block:'nearest',behavior:'smooth' });
      } else {
        state.submission = response.status === 409 ? 'conflict' : response.status === 429 ? 'rateLimited' : 'uncertain'; removeWidget(); state.verification = 'verifyNeeded';
      }
    } catch (_) { state.submission = 'uncertain'; removeWidget(); state.verification = 'verifyNeeded'; }
    finally { state.busy = false; render(); }
  }
  async function deleteRecord(event) {
    event.preventDefault(); if (!state.endpoint || state.deleting || state.busy) return;
    const id = $('delete-id').value.trim(), token = $('delete-token').value.trim();
    $('delete-id').setCustomValidity(''); $('delete-token').setCustomValidity('');
    if (!/^[0-9a-f-]{36}$/.test(id)) $('delete-id').setCustomValidity(tr('invalidReceipt'));
    if (!/^[A-Za-z0-9_-]{32,100}$/.test(token)) $('delete-token').setCustomValidity(tr('invalidReceipt'));
    if (!$('delete-form').reportValidity()) return;
    state.deleting = true; state.deletion = 'deleting'; refreshControls();
    try {
      const { response,body } = await post('/v1/delete',{id,token});
      if (response.ok && body.deleted === true) {
        state.deletion = 'deleted';
        if (state.receipt?.id === id) { try { localStorage.removeItem(KEY); } catch (_) {} state.storage = ''; state.receiptFinal = true; state.phase = 'final'; removeWidget(); }
      } else state.deletion = response.status === 429 ? 'rateLimited' : 'deleteFailed';
    } catch (_) { state.deletion = 'deleteFailed'; }
    finally { state.deleting = false; render(); }
  }
  function downloadReceipt() {
    if (!state.receipt) return;
    const blob = new Blob([JSON.stringify({id:state.receipt.id,token:state.receipt.token},null,2)+'\n'],{type:'application/json'}), url = URL.createObjectURL(blob), a = document.createElement('a');
    a.href = url; a.download = 'residence-observatory-receipt.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
  }
  function clearReceipt() {
    // Protect active-attempt keys; a restored receipt has no in-flight payload.
    if (!state.receipt || !(state.receiptFinal || state.phase === 'restored' && !state.attempt) || state.busy || state.deleting) return;
    try { localStorage.removeItem(KEY); }
    catch (_) { state.storage = 'clearFailed'; showReceipt(); return; }
    removeWidget(); $('survey-form').reset();
    state.receipt = null; state.attempt = null; state.receiptFinal = false; state.receiptCleared = true; state.storage = 'cleared';
    $('receipt-id').textContent = ''; $('receipt-token').textContent = '';
    $('delete-id').value = ''; $('delete-token').value = '';
    // Keep the accepted/final form locked. Only an explicit New case resets it.
    render();
  }
  function resetForm() {
    if (state.busy || state.receipt) return;
    removeWidget(); $('survey-form').reset(); state.phase = 'editing'; state.attempt = null; state.accepted = false; state.receiptFinal = false; state.receiptCleared = false; state.submission = 'resetNotice'; state.verification = '';
    $('survey-form').querySelectorAll('input,select').forEach(x => x.setCustomValidity('')); render();
  }
  async function configure() {
    try {
      const [c,o] = await Promise.all([fetch('../data/survey-config.json',{cache:'no-store',credentials:'omit'}),fetch('../data/offices.json',{credentials:'omit'})]);
      if (!c.ok || !o.ok) throw new Error('config');
      const config = await c.json(), offices = await o.json();
      const url = new URL(config.endpoint); if (url.protocol !== 'https:') throw new Error('config');
      state.endpoint = url.origin;
      state.offices = (Array.isArray(offices) ? offices : offices.offices || []).filter(x => REGIONS.includes(x.geography_id));
      if (new Set(state.offices.map(x => x.geography_id)).size !== 16 || state.offices.length !== 16) throw new Error('offices');
      state.config = { ...config,collection_enabled:config.collection_enabled === true && typeof config.sitekey === 'string' && config.sitekey.length > 5 };
      render();
      const office = new URLSearchParams(location.search).get('office'); if (state.phase === 'editing' && REGIONS.includes(office)) $('survey-region').value = office;
    } catch (_) { state.config = {collection_enabled:false}; state.notice = 'configFailed'; render(); }
  }
  document.addEventListener('DOMContentLoaded',() => {
    state.initialized = true;
    try {
      const saved = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (saved && /^[0-9a-f-]{36}$/.test(saved.id) && /^[A-Za-z0-9_-]{32,100}$/.test(saved.token)) { state.receipt = {id:saved.id,token:saved.token}; state.phase = 'restored'; $('delete-id').value = saved.id; $('delete-token').value = saved.token; }
    } catch (_) {}
    $('survey-form').addEventListener('submit',submit); $('delete-form').addEventListener('submit',deleteRecord);
    $('survey-form').addEventListener('input',event => { event.target.setCustomValidity?.(''); refreshControls(); preview(); });
    $('survey-status').addEventListener('change',() => { if ($('survey-status').value === 'pending') $('survey-decision').value = ''; refreshControls(); preview(); });
    $('verification-ack').addEventListener('change',() => { if (!$('verification-ack').checked) { removeWidget(); state.verification = ''; } refreshControls(); });
    $('enable-verification').addEventListener('click',enableVerification);
    $('receipt-download').addEventListener('click',downloadReceipt);
    $('receipt-clear').addEventListener('click',clearReceipt);
    $('new-case').addEventListener('click',resetForm);
    render(); configure();
  });
  window.addEventListener('languagechange',() => { if (!state.initialized) return; render(); if (state.widget !== null && $('verification-ack').checked && !state.busy && !state.accepted) enableVerification(); });
})();
