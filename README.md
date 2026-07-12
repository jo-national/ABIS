# På positivlisten? - opslagsværktøj for Skattestyrelsens ABIS-liste

Domæne: [påpositivlisten.dk](https://www.xn--ppositivlisten-lib.dk/)
(punycode for det danske æ/ø/å-domæne "påpositivlisten.dk").

Ét formål: hurtigt svar på om et værdipapir står på Skattestyrelsens liste over
aktiebaserede investeringsselskaber ("positivlisten"/ABIS-listen). Data kommer
udelukkende fra skat.dk. Sitet er statisk: der er ingen server og ingen
database at vedligeholde - kun filer, der genbygges automatisk, når
Skattestyrelsen offentliggør en ny liste.

## Sidestruktur

- **Forside** (`/`) - søgefelt (navn eller ISIN) og fem kontekst-faner
  (Aktiedepot, Aktiesparekonto, Depot for mindreårige, Børneopsparing,
  Pension), der forklarer, hvad man skal lede efter alt efter kontotype.
- **Fondssider** (`/fond/<ISIN eller CVR>/`) - én side pr. registrering,
  6.000+ i alt. JA/IKKE PÅ LISTEN-svar øverst, samme fem kontekst-faner
  tilpasset den konkrete fond, år-for-år-tabel og stamdata side om side,
  kildehenvisning nederst.
- **Alle fonde** (`/fonde/<bogstav>.html`) - alfabetisk indeks. Filtrerbart
  på navn/ISIN og på udbyder (automatisk genkendt fra fondsnavnet, se
  `UDBYDER_REGLER` i `build_site.py`). Søger man på noget, der ikke findes
  under det viste bogstav, slås der automatisk op i hele positivlisten
  (`static/listefilter.js`).
- **Ændringer** (`/aendringer.html`) - nye og udgåede fonde ift. forrige
  indkomstår, samme filtrering som Alle fonde. "Genoptaget" vs. "ny"
  beregnes ud fra hele historikken, ikke kun de seneste to år.
- **Viden** (`/metode.html`) - hvad hjemmesiden bruges til, hvad positivlisten
  er, og hvad den ikke dækker (med konkrete eksempler på fondssider).
- **Hvem står bag?** (`/om.html`) - afsender, uafhængighedserklæring,
  forbehold, hvordan data læses og opdateres, og den aktuelle kildefil.

## Sådan hænger det sammen

1. **GitHub Actions** kører `opdater.yml` hver dag kl. 04:45 UTC (06:45 dansk
   sommertid) - se afsnittet "Overvågning" for hvorfor tidspunktet kan variere.
2. `pipeline/fetch.py` henter skat.dk-siden, finder Excel-linket dynamisk
   (linkets adresse skifter ved hver offentliggørelse og må aldrig hardcodes),
   downloader filen og sammenligner dens SHA-256-fingeraftryk med sidste kørsel.
3. Kun ved ændring: `pipeline/parse.py` læser filen, validerer struktur og alle
   ISIN-koder, skriver `data/abis.json` og en læsbar rapport
   (`data/parse_report.txt`). Originalfilen arkiveres uændret i `data/raw/`.
4. `pipeline/build_site.py` genererer hele sitet i `site/`: alle sider ovenfor,
   `sitemap.xml`, `robots.txt`, en `404.html`, favicon/Open Graph-billede
   (allerede i `static/`), JSON-LD (WebSite på forsiden, BreadcrumbList +
   InvestmentFund på fondssider), samt en kopi af den aktuelle kildefil under
   `/kilde/<filnavn>`, så "hjemmesiden benytter lige nu filen X" er et rigtigt
   dybdelink. Alt udgives på GitHub Pages.
5. Fejler noget - siden er nede, linket er væk, strukturen er ændret - fejler
   jobbet højlydt, og sitet forbliver på seneste gode version. Gamle data
   præsenteres aldrig som friske: kontroldatoen i sidens statuslinje opdateres
   kun ved succesfuld kørsel.

## Redigerbare tekster

`data/tekster.yml` indeholder de "bløde" tekster (forsidens hero, intro-tekster,
om-siden) i almindeligt sprog. Ret direkte i filen på GitHub og commit - det
er publicér-knappen; sitet genbygger automatisk. Instruktion står øverst i
filen selv. De skattefaglige paneltekster (paragrafhenvisninger osv.) ligger
bevidst IKKE her, men i skabelonerne under `templates/`, så en rettelse altid
går gennem en fil, hvor fagligheden kan tjekkes, før den går live.

## Besøgsstatistik

Cookiefri, aggregeret besøgstælling via [GoatCounter](https://www.goatcounter.com/)
(scriptet ligger i `templates/base.html`, så det automatisk følger med på alle
sider - også nye fondssider, næste gang listen opdateres). Der sættes ingen
cookies og føres ingen sporing på tværs af andre hjemmesider. Søgefunktionens
brug tælles anonymt (`static/search.js`: hændelserne `soegning-brugt` og
`soegning-intet-fundet`) - selve søgeteksten sendes aldrig. Dashboard:
`jo-national.goatcounter.com` (kun synligt for indloggede).

## Overvågning

- `.github/workflows/opdater.yml` - den daglige datakørsel (kl. 04:45 UTC).
- `.github/workflows/vagthund.yml` - en uafhængig kontrol kl. 05:45 UTC, der
  tjekker via GitHubs API, om opdater.yml har kørt inden for de seneste
  26 timer. Har den ikke, fejler vagthunden bevidst (rødt kryds), hvilket
  udløser en mail, HVIS du har slået mail-varsling til (se nedenfor).
- GitHub Actions er "best effort": et par timers forsinkelse på den daglige
  kørsel er normalt og intet at bekymre sig om. Vagthunden fanger det, hvis
  en kørsel reelt udebliver, ikke bare kommer sent.

**Slå mail-varsling til (gør dette først, det sker ikke automatisk):** gå til
`github.com/settings/notifications` og sørg for, at "Actions" er markeret
under Watching. Det er en konto-indstilling, ikke en repo-indstilling under
Settings → Email notifications (den sidste sender kun mail ved almindelige
pushes, ikke ved fejlede workflows).

## Kom i gang (engangsopsætning, ca. 30 minutter)

**Trin 1 - GitHub.** Opret en gratis konto på github.com. Opret et nyt
*offentligt* repository (gratis GitHub Pages kræver offentligt repo - dataene
er alligevel offentlige). Upload alle filer fra denne mappe.

**Trin 2 - Aktivér Pages.** I repoet: Settings → Pages → under "Build and
deployment" vælg **Source: GitHub Actions**.

**Trin 3 - Første kørsel.** Fanen Actions → "Opdater data og udgiv site" →
"Run workflow". Første kørsel downloader den rigtige ABIS-fil for første gang.
**VIGTIGT:** Læs loggen fra trinnet "Parse og validér". Parseren er bygget til
ukendte strukturer og rapporterer præcis, hvad den fandt: arknavne, hvilken
række headeren stod i, hvilke kolonner den genkendte, antal rækker pr.
indkomstår og tre eksempler. Åbn selv Excel-filen fra skat.dk og kontrollér, at
tallene stemmer, før du deler sitet med nogen. Genkender parseren ikke
strukturen, fejler den med besked i stedet for at gætte.

**Trin 4 - Domæne.** Køb et .dk-domæne hos en registrator (f.eks. one.com,
simply.com eller dandomain.dk). Derefter hos registratoren:
- Opret en CNAME-record: `www` → `<dit-brugernavn>.github.io`
- Opret A-records for rod-domænet mod GitHub Pages' fire IP-adresser:
  185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- I GitHub: Settings → Pages → Custom domain → indtast domænet og slå
  "Enforce HTTPS" til (certifikatet er gratis og automatisk).
- Ret `BASE_URL` øverst i `pipeline/build_site.py` til dit domæne og push.

**Trin 5 - Google Search Console.** Opret ejendom som "Domæne" (ikke
"Webadressepræfiks") med selve domænet, verificér via DNS TXT-record hos din
registrator, og indsend `https://<dit-domæne>/sitemap.xml` under Sitemaps.

## Drift

- **Ny listeversion:** sker automatisk. Committen "Data opdateret [dato]" i
  historikken viser hvornår; `data/parse_report.txt` viser hvad der blev læst.
- **Fejl:** når en kørsel fejler, får den et rødt kryds under fanen Actions i
  stedet for et grønt hak. Kig i loggen for det trin, der fejlede; de tre
  sandsynlige årsager er (1) skat.dk var nede (løser sig selv næste dag),
  (2) siden har fået nyt link-format, (3) Excel-strukturen er ændret. Ved
  2 og 3: kør parseren lokalt med `python pipeline/parse.py --verify` og
  justér `COLUMN_HINTS`/`LINK_RE`.
- **Historik:** alle rå Excel-filer ligger urørt i `data/raw/` med dato og
  fingeraftryk - fuld sporbarhed tilbage i tid.
- **`data/tickers.json`:** en rest fra en fravalgt ticker-søgefunktion.
  Koden refererer den ikke længere - filen kan roligt slettes.

## Test

`tests/lav_fixture.py` bygger en bevidst besværlig test-Excel
(`tests/fixture_abis.xlsx`): skiftende arknavne, headers i forskellige
rækker, engelske kolonnenavne, ugyldige ISIN, dubletter. Kør parseren mod
fixturen for at verificere ændringer i `parse.py`, før de rammer rigtige
data. Testdata blandes aldrig med rigtige data: `data/` er tom, indtil
første rigtige kørsel har fundet sted.
