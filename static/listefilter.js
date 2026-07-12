/* ============================================================
   listefilter.js - Positivlisten?
   Filtrerer lange fondslister i realtid uden server.
   Virker på enhver <ul class="fondsliste" data-filtrerbar>.
   - Fritekst matcher navn + ISIN/CVR.
   - Dropdown matcher udbyder (data-udbyder på hver <li>),
     sorteret efter antal, med "Andre" sidst.
   - Live tælling af synlige rækker.
   - GLOBALT OPSLAG: har listen data-globalsoeg, og giver den
     lokale filtrering nul resultater, slås der op i hele
     søgeindekset (sogeindeks.json), og resultater fra alle
     bogstaver vises med links. Så finder man "Nordea ..."
     selvom man står på A-siden.
   Uden JS er hele listen synlig som normalt.
   ============================================================ */
(function () {
  "use strict";

  const lister = document.querySelectorAll("ul.fondsliste[data-filtrerbar]");
  lister.forEach(setup);

  function setup(liste) {
    const rows = Array.from(liste.querySelectorAll("li"));
    if (!rows.length) return;

    const BASE = liste.dataset.base || window.BASE_PATH || "";
    const globalSoeg = liste.hasAttribute("data-globalsoeg");

    // Kontrolpanel
    const panel = document.createElement("div");
    panel.className = "listefilter";

    const soeg = document.createElement("input");
    soeg.type = "search";
    soeg.className = "listefilter-soeg";
    soeg.placeholder = "Filtrér på navn eller ISIN ...";
    soeg.setAttribute("aria-label", "Filtrér listen på navn eller ISIN");

    // Udbydere, sorteret efter antal, "Andre" sidst
    const antal = {};
    rows.forEach((r) => {
      const u = r.dataset.udbyder;
      if (u) antal[u] = (antal[u] || 0) + 1;
    });
    const udbydere = Object.keys(antal).sort((a, b) => {
      if (a === "Andre") return 1;
      if (b === "Andre") return -1;
      return antal[b] - antal[a];
    });

    const vaelg = document.createElement("select");
    vaelg.className = "listefilter-vaelg";
    vaelg.setAttribute("aria-label", "Filtrér listen på udbyder");
    const alle = document.createElement("option");
    alle.value = "";
    alle.textContent = "Alle udbydere";
    vaelg.append(alle);
    udbydere.forEach((h) => {
      const o = document.createElement("option");
      o.value = h;
      o.textContent = h + " (" + antal[h].toLocaleString("da-DK") + ")";
      vaelg.append(o);
    });

    const tael = document.createElement("p");
    tael.className = "listefilter-tael";
    tael.setAttribute("aria-live", "polite");

    panel.append(soeg, vaelg, tael);
    if (udbydere.length < 2) vaelg.hidden = true;
    liste.parentNode.insertBefore(panel, liste);

    // Sektion til globale resultater (skjult indtil brug)
    let globalWrap = null, globalListe = null;
    if (globalSoeg) {
      globalWrap = document.createElement("div");
      globalWrap.hidden = true;
      const h = document.createElement("h2");
      h.textContent = "Resultater fra hele positivlisten";
      const note = document.createElement("p");
      note.textContent = "Ingen match under dette bogstav - her er fonde fra hele listen, der matcher din søgning:";
      globalListe = document.createElement("ul");
      globalListe.className = "fondsliste";
      globalWrap.append(h, note, globalListe);
      liste.parentNode.insertBefore(globalWrap, liste.nextSibling);
    }

    let indeks = null;
    async function hentIndeks() {
      if (!indeks) {
        const r = await fetch(BASE + "/sogeindeks.json");
        indeks = await r.json(); // [[id, navn, aktiv, [aliaser]], ...]
      }
      return indeks;
    }

    async function visGlobale(q) {
      const data = await hentIndeks();
      const hits = [];
      for (const [id, navn, aktiv, alias] of data) {
        const match =
          id.toLowerCase().includes(q) ||
          navn.toLowerCase().includes(q) ||
          (alias && alias.some((a) => a.toLowerCase().includes(q)));
        if (match) {
          hits.push([id, navn, aktiv]);
          if (hits.length >= 25) break;
        }
      }
      globalListe.innerHTML = "";
      if (!hits.length) { globalWrap.hidden = true; return; }
      for (const [id, navn, aktiv] of hits) {
        const li = document.createElement("li");
        const a = document.createElement("a");
        a.href = BASE + "/fond/" + id + "/";
        a.textContent = navn || id;
        const meta = document.createElement("span");
        meta.className = "fondsliste-meta";
        const isin = document.createElement("span");
        isin.className = "isin";
        isin.textContent = id.startsWith("NAVN-") ? "" : id.replace("CVR-", "CVR ");
        const tag = document.createElement("span");
        tag.className = aktiv ? "status-ja" : "status-nej";
        tag.textContent = aktiv ? "på positivlisten" : "ikke på positivlisten";
        meta.append(isin, tag);
        li.append(a, meta);
        globalListe.append(li);
      }
      globalWrap.hidden = false;
    }

    const ialt = rows.length;

    function opdater() {
      const q = soeg.value.trim().toLowerCase();
      const h = vaelg.value;
      let synlige = 0;
      for (const r of rows) {
        const tekst = r.textContent.toLowerCase();
        const okTekst = !q || tekst.includes(q);
        const okUdb = !h || r.dataset.udbyder === h;
        const vis = okTekst && okUdb;
        r.hidden = !vis;
        if (vis) synlige++;
      }
      tael.textContent =
        synlige === ialt
          ? ialt.toLocaleString("da-DK") + " fonde"
          : synlige.toLocaleString("da-DK") + " af " + ialt.toLocaleString("da-DK") + " fonde";

      if (globalSoeg) {
        if (synlige === 0 && q.length >= 3 && !h) {
          visGlobale(q);
        } else if (globalWrap) {
          globalWrap.hidden = true;
        }
      }
    }

    soeg.addEventListener("input", opdater);
    vaelg.addEventListener("change", opdater);
    opdater();
  }
})();
