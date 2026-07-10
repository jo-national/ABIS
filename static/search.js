// Klientsøgning i det kompakte indeks. Ingen server, ingen cookies, ingen tracking.
(async function () {
  const input = document.getElementById("q");
  const list = document.getElementById("resultater");
  const notFound = document.getElementById("ikke-fundet");
  if (!input) return;

  let indeks = null;
  async function hent() {
    if (!indeks) {
      const r = await fetch("/sogeindeks.json");
      indeks = await r.json(); // [[isin, navn, paaListenNu], …]
    }
    return indeks;
  }

  const isinForm = /^[A-Za-z]{2}[A-Za-z0-9]{9}[0-9]$/;

  input.addEventListener("input", async () => {
    const q = input.value.trim().toLowerCase();
    list.innerHTML = "";
    list.classList.remove("vis");
    notFound.hidden = true;
    if (q.length < 3) return;

    const data = await hent();
    const hits = [];
    for (const [isin, navn, aktiv] of data) {
      if (isin.toLowerCase().includes(q) || navn.toLowerCase().includes(q)) {
        hits.push([isin, navn, aktiv]);
        if (hits.length >= 25) break;
      }
    }
    if (hits.length === 0) {
      // Vis kun det fulde "ikke fundet"-svar ved en komplet ISIN eller en længere søgning.
      if (isinForm.test(input.value.trim()) || q.length >= 6) notFound.hidden = false;
      return;
    }
    for (const [isin, navn, aktiv] of hits) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = "/fond/" + isin + "/";
      const n = document.createElement("span");
      n.textContent = navn || isin;
      const meta = document.createElement("span");
      meta.className = "isin";
      meta.innerHTML = isin + (aktiv ? ' · <span class="status-ja">på listen</span>' : "");
      a.append(n, meta);
      li.append(a);
      list.append(li);
    }
    list.classList.add("vis");
  });
})();
