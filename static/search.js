// Klientsøgning i det kompakte indeks. Ingen server, ingen cookies.
// Bruges tælles anonymt via GoatCounter (se tael() nedenfor) - selve
// søgeteksten sendes ALDRIG, kun at søgning blev brugt, og om den gav
// resultater. Virker uden fejl selvom GoatCounter er blokeret (fx adblock).
(function () {
  const BASE = window.BASE_PATH || "";
  const input = document.getElementById("q");
  const list = document.getElementById("resultater");
  const notFound = document.getElementById("ikke-fundet");
  if (!input) return;

  function tael(sti) {
    try {
      if (window.goatcounter && window.goatcounter.count) {
        window.goatcounter.count({ path: sti, title: sti, event: true });
      }
    } catch (e) { /* sporing må aldrig kunne knække søgningen */ }
  }
  // Én søgning = fra man begynder at skrive, til feltet tømmes igen.
  // "Intet fundet" tælles først, når brugeren har holdt pause i skrivningen
  // og stadig står uden resultater - ellers ville hvert tastetryk tælle.
  let harTaltDenneSoegning = false;
  let harTaltIntetFundet = false;
  let intetFundetTimer = null;

  // Små bogstaver, og tegn som & ® - , ( ) bliver til mellemrum, så
  // "s&p 500" og "S&P 500" matcher hinanden.
  function normaliser(s) {
    return s.toLowerCase().replace(/[^a-z0-9æøåäöüé]+/g, " ").trim();
  }

  let indeks = null;
  async function hent() {
    if (!indeks) {
      const r = await fetch(BASE + "/sogeindeks.json");
      const data = await r.json(); // [[id, navn, paaListenNu, [alias, ...]], …]
      indeks = data.map(([id, navn, aktiv, alias]) => ({
        id, navn, aktiv,
        navnNorm: normaliser(navn || ""),
        tekst: normaliser([id, navn || ""].concat(alias || []).join(" ")),
      }));
    }
    return indeks;
  }

  const isinForm = /^[A-Za-z]{2}[A-Za-z0-9]{9}[0-9]$/;

  input.addEventListener("input", async () => {
    const raa = input.value.trim();
    const q = normaliser(raa);
    list.innerHTML = "";
    list.classList.remove("vis");
    notFound.hidden = true;
    clearTimeout(intetFundetTimer);
    if (raa.length < 3 || !q) {
      harTaltDenneSoegning = false;
      harTaltIntetFundet = false;
      return;
    }

    if (!harTaltDenneSoegning) { tael("soegning-brugt"); harTaltDenneSoegning = true; }

    const data = await hent();
    if (input.value.trim() !== raa) return; // brugeren har skrevet videre
    // Alle ord skal findes, men i vilkårlig rækkefølge:
    // "msci world ishares" finder "iShares Core MSCI World UCITS ETF".
    const ord = q.split(" ");
    const isin = q.replace(/ /g, "");
    const hits = data.filter((f) => ord.every((o) => f.tekst.includes(o)));
    // Bedste først: præcis ISIN, så navne der starter med søgningen,
    // så fonde på positivlisten nu, så korteste navn (typisk hovedklassen
    // frem for "Hedged"-varianter), så alfabetisk.
    const point = (f) =>
      (f.id.toLowerCase() === isin ? 0 : 4) +
      (f.navnNorm.startsWith(q) ? 0 : 2) +
      (f.aktiv ? 0 : 1);
    hits.sort((a, b) =>
      point(a) - point(b) ||
      a.navnNorm.length - b.navnNorm.length ||
      a.navnNorm.localeCompare(b.navnNorm, "da"));

    if (hits.length === 0) {
      if (isinForm.test(raa) || raa.length >= 6) {
        notFound.hidden = false;
        if (!harTaltIntetFundet) {
          intetFundetTimer = setTimeout(() => {
            tael("soegning-intet-fundet");
            harTaltIntetFundet = true;
          }, 1500);
        }
      }
      return;
    }
    for (const { id, navn, aktiv } of hits.slice(0, 25)) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = BASE + "/fond/" + id + "/";
      const n = document.createElement("span");
      n.textContent = navn || id;
      const meta = document.createElement("span");
      meta.className = "isin";
      meta.textContent = id;
      const tag = document.createElement("span");
      if (aktiv) {
        tag.className = "status-ja";
        tag.textContent = " · på positivlisten";
      } else {
        tag.className = "status-nej";
        tag.textContent = " · ikke på positivlisten";
      }
      meta.append(tag);
      a.append(n, meta);
      li.append(a);
      list.append(li);
    }
    list.classList.add("vis");
  });
})();
