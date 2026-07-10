# På positivlisten? - opslagsværktøj for Skattestyrelsens ABIS-liste

Domæne: [påpositivlisten.dk](https://www.xn--ppositivlisten-lib.dk/)
(punycode for det danske æ/ø/å-domæne "påpositivlisten.dk").

Ét formål: hurtigt svar på om et værdipapir står på Skattestyrelsens liste over
aktiebaserede investeringsselskaber ("positivlisten"). Data kommer udelukkende
fra skat.dk. Sitet er statisk: der er ingen server og ingen database at
vedligeholde - kun filer, der genbygges automatisk, når Skattestyrelsen
offentliggør en ny liste.

## Sådan hænger det sammen

1. **GitHub Actions** (gratis "robot" hos GitHub) kører hver nat kl. 04:45 UTC
   (06:45 dansk sommertid).
2. `pipeline/fetch.py` henter skat.dk-siden, finder Excel-linket dynamisk
   (linkets adresse skifter ved hver offentliggørelse og må aldrig hardcodes),
   downloader filen og sammenligner dens SHA-256-fingeraftryk med sidste kørsel.
3. Kun ved ændring: `pipeline/parse.py` læser filen, validerer struktur og alle
   ISIN-koder, skriver `data/abis.json` og en læsbar rapport
   (`data/parse_report.txt`). Originalfilen arkiveres uændret i `data/raw/`.
4. `pipeline/build_site.py` genererer hele sitet (én side pr. ISIN, søgning,
   sitemap) i `site/`, som udgives på GitHub Pages.
5. Fejler noget - siden er nede, linket er væk, strukturen er ændret - fejler
   jobbet højlydt, og sitet forbliver på seneste gode version. Gamle data
   præsenteres aldrig som friske: kontroldatoen i sidens statuslinje opdateres
   kun ved succesfuld kørsel. Se afsnittet "Drift" for hvordan du selv skal
   slå mail-varsling til - det sker ikke automatisk.

## Kom i gang (engangsopsætning, ca. 30 minutter)

**Trin 1 - GitHub.** Opret en gratis konto på github.com. Opret et nyt
*offentligt* repository (gratis GitHub Pages kræver offentligt repo - dataene
er alligevel offentlige). Upload alle filer fra denne mappe: enten via
"uploading an existing file" i browseren, eller med git fra terminalen.

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

**Trin 4 - Domæne.** Køb et .dk-domæne hos en registrator (fx one.com,
simply.com eller dandomain.dk - fra 1. juli 2026 skal alle .dk-domæner
administreres via en registrator). Grundprisen hos Punktum dk (registret bag
.dk) er 71 kr./år inkl. moms; registratorer har ofte førsteårsrabat og
lidt højere fornyelsespris (typisk 90-110 kr./år). Derefter hos registratoren:
- Opret en CNAME-record: `www` → `<dit-brugernavn>.github.io`
- Opret A-records for rod-domænet mod GitHub Pages' fire IP-adresser:
  185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- I GitHub: Settings → Pages → Custom domain → indtast domænet og slå
  "Enforce HTTPS" til (certifikatet er gratis og automatisk).
- Ret `BASE_URL` øverst i `pipeline/build_site.py` til dit domæne og push.

## Drift

- **Ny listeversion:** sker automatisk. Committen "Data opdateret [dato]" i
  historikken viser hvornår; `data/parse_report.txt` viser hvad der blev læst.
  Se kørslerne under fanen Actions.
- **Slå mail-varsling til (gør dette først):** GitHub sender IKKE automatisk
  mail ved en fejlet kørsel, medmindre du selv har slået det til. Gå til
  `github.com/settings/notifications` og sørg for, at "Actions" er markeret
  under Watching. Uden dette opdager du kun en fejl ved selv at tjekke
  Actions-fanen.
- **Fejl:** når en kørsel fejler, får den et rødt kryds under fanen Actions i
  stedet for et grønt hak. Kig i loggen for det trin, der fejlede; de tre
  sandsynlige årsager er (1) skat.dk var nede (løser sig selv næste nat),
  (2) siden har fået nyt link-format, (3) Excel-strukturen er ændret. Ved
  2 og 3: kør parseren lokalt med `python pipeline/parse.py --verify` og
  justér `COLUMN_HINTS`/`LINK_RE`.
- **Historik:** alle rå Excel-filer ligger urørt i `data/raw/` med dato og
  fingeraftryk - fuld sporbarhed tilbage i tid.

## Test

`tests/lav_fixture.py` bygger en bevidst besværlig test-Excel (skiftende
arknavne, headers i forskellige rækker, engelske kolonnenavne, ugyldige ISIN,
dubletter). `tests/eksempel_output/` viser pipeline-output fra fixturen.
Testdata blandes aldrig med rigtige data: `data/` er tom, indtil første rigtige
kørsel har fundet sted.

## Annoncer (endnu ikke aktiveret)

Skabelonerne har reserverede annoncepladser (`<aside class="annonce">`) - én
under svaret på fondssider, én under søgningen på forsiden. De fylder intet,
før de aktiveres. Se udleveringsnotatet for krav (samtykkeløsning m.m.), inden
du tilmelder dig et annoncenetværk.
