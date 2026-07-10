# Designbrief — "Aktiebaseret?" (til Claude Design)

## Hvad sitet er
Et opslagsværktøj med ét job: svare på om et værdipapir står på Skattestyrelsens
liste over aktiebaserede investeringsselskaber. Målgruppen er danske
privatinvestorer, der står midt i en købsbeslutning (ofte på mobil, ofte via
Google-søgning på et fondsnavn). Skatteinformation er tillidsstof: designet
skal signalere myndighedsnær nøgternhed — ikke fintech-marketing. Klarhed over
effekter, altid.

## Informationshierarki (vigtigst først)
1. **Svaret.** På en fondsside skal JA/IKKE PÅ LISTEN kunne aflæses på under
   ét sekund, også i squint-test. Svaret står over folden på mobil.
2. **Grundlaget.** Umiddelbart under svaret: indkomstår, listeversion og
   offentliggørelsesdato — det er svarets gyldighedsstempel.
3. **Konsekvensen.** Én sætning: hvad betyder det for skat og aktiesparekonto.
4. **Detaljer.** År-for-år-tabel og stamdata (ISIN, LEI, land).
5. **Forbehold og kildelink.** Altid synligt uden scroll-jagt, aldrig i
   mikroskrift.

På forsiden er søgefeltet helten — stort, med autofokus og eksempeltekst, der
viser at både navn og ISIN virker.

## Status skal kunne aflæses uden at læse
Tre visuelle tilstande, som skal kunne skelnes af farveblinde (brug altid
form/tekst sammen med farve):
- **På listen (JA):** grøn, roligt og entydigt.
- **Historisk/ikke på listen for i år:** advarselsgul — ikke rød, for det er
  ikke en fejl, det er en oplysning der kræver opmærksomhed.
- **Ikke fundet (søgning uden resultat):** neutral/gul informationsboks. Denne
  tilstand er designmæssigt ligeværdig med de to andre — sitet lover at
  kommunikere fravær af data lige så tydeligt som tilstedeværelse. Teksten er
  længere her (to forklarende afsnit); den skal have luft og må ikke ligne en
  fejlmeddelelse.

## Statuslinjen
En tynd, gennemgående linje på alle sider: "Datagrundlag: … offentliggjort
den …, gældende for indkomståret …. Senest kontrolleret: …". Den er sitets
troværdighedssignatur og må gerne være det ene genkendelige designelement.

## Tabeller med mange rækker (indeks-siderne, 5.000+ fonde fordelt på bogstaver)
- Én række = navn + ISIN, intet andet. Zebra-striber eller tydelige skillelinjer.
- Fast synlig bogstavsnavigation.
- Lange fondsnavne trunkeres aldrig på mobil — de må ombrydes; ISIN må aldrig
  ombrydes (monospace anbefales til ISIN overalt).

## Annoncer
Reserverede pladser: under svaret på fondssider og under søgeresultatet på
forsiden — aldrig over svaret, aldrig mellem svar og grundlag, aldrig i
statuslinjen eller footeren med forbeholdene. Altid tydeligt mærket "Annonce".
Maks. én annonce synlig pr. viewport. Reservér pladsens højde i layoutet, så
indholdet ikke hopper, når annoncen indlæses (ingen layout shift).

## Typografi og tone
Rolig, saglig, dansk. God læsbarhed ved små størrelser (stamdata, forbehold).
Tal og koder (ISIN, årstal, datoer) i tabelvenlig/monospace variant. Ingen
illustrationer, ingen stockfotos, ingen dekorative ikoner ud over de tre
statusmarkeringer.

## Tekniske rammer
Statisk HTML/CSS (skabeloner i Jinja2 — behold klassenavne og struktur fra de
eksisterende templates, så designet kan lægges ovenpå som ren CSS-udskiftning).
Ingen webfonts der blokerer rendering; system-stack eller én selvhostet font.
Mørk tilstand er valgfri, ikke prioriteret. Skal fungere ned til 320 px bredde.
