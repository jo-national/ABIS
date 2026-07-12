/* ============================================================
   listefilter.js - Positivlisten?
   Filtrerer lange fondslister i realtid uden server.
   Virker på enhver <ul class="fondsliste" data-filtrerbar>.
   - Fritekst matcher navn + ISIN/CVR.
   - Dropdown matcher skattemæssigt hjemsted (data-hjemsted på hver <li>).
   - Live tælling af synlige rækker.
   Uden JS er hele listen synlig som normalt (progressiv forbedring).
   ============================================================ */
(function () {
  "use strict";

  const lister = document.querySelectorAll("ul.fondsliste[data-filtrerbar]");
  lister.forEach(setup);

  function setup(liste) {
    const rows = Array.from(liste.querySelectorAll("li"));
    if (!rows.length) return;

    // Byg kontrolpanel
    const panel = document.createElement("div");
    panel.className = "listefilter";

    const soeg = document.createElement("input");
    soeg.type = "search";
    soeg.className = "listefilter-soeg";
    soeg.placeholder = "Filtrér på navn eller ISIN ...";
    soeg.setAttribute("aria-label", "Filtrér listen på navn eller ISIN");

    // Saml unikke hjemsteder
    const hjemsteder = Array.from(
      new Set(rows.map((r) => r.dataset.hjemsted).filter(Boolean))
    ).sort();

    const vaelg = document.createElement("select");
    vaelg.className = "listefilter-vaelg";
    vaelg.setAttribute("aria-label", "Filtrér listen på skattemæssigt hjemsted");
    const alle = document.createElement("option");
    alle.value = "";
    alle.textContent = "Alle hjemsteder";
    vaelg.append(alle);
    hjemsteder.forEach((h) => {
      const o = document.createElement("option");
      o.value = h;
      o.textContent = h;
      vaelg.append(o);
    });

    const tael = document.createElement("p");
    tael.className = "listefilter-tael";
    tael.setAttribute("aria-live", "polite");

    panel.append(soeg, vaelg, tael);
    if (hjemsteder.length < 2) vaelg.hidden = true;
    liste.parentNode.insertBefore(panel, liste);

    const ialt = rows.length;

    function opdater() {
      const q = soeg.value.trim().toLowerCase();
      const h = vaelg.value;
      let synlige = 0;
      for (const r of rows) {
        const tekst = r.textContent.toLowerCase();
        const okTekst = !q || tekst.includes(q);
        const okHjem = !h || r.dataset.hjemsted === h;
        const vis = okTekst && okHjem;
        r.hidden = !vis;
        if (vis) synlige++;
      }
      tael.textContent =
        synlige === ialt
          ? ialt.toLocaleString("da-DK") + " fonde"
          : synlige.toLocaleString("da-DK") + " af " + ialt.toLocaleString("da-DK") + " fonde";
    }

    soeg.addEventListener("input", opdater);
    vaelg.addEventListener("change", opdater);
    opdater();
  }
})();
