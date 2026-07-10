// Klientsøgning i det kompakte indeks. Ingen server, ingen cookies, ingen tracking.
(function () {
  const BASE = window.BASE_PATH || "";
  const input = document.getElementById("q");
  const list = document.getElementById("resultater");
  const notFound = document.getElementById("ikke-fundet");
  if (!input) return;

  let indeks = null;
  async function hent() {
    if (!indeks) {
      const r = await fetch(BASE + "/sogeindeks.json");
      indeks = await r.json(); // [[id, navn, paaListenNu, [alias, ...]], …]
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
    if (hits.length === 0) {
      if (isinForm.test(input.value.trim()) || q.length >= 6) notFound.hidden = false;
      return;
    }
    for (const [id, navn, aktiv] of hits) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = BASE + "/fond/" + id + "/";
      const n = document.createElement("span");
      n.textContent = navn || id;
      const meta = document.createElement("span");
      meta.className = "isin";
      meta.textContent = id;
      if (aktiv) {
        const tag = document.createElement("span");
        tag.className = "status-ja";
        tag.textContent = " · på listen";
        meta.append(tag);
      }
      a.append(n, meta);
      li.append(a);
      list.append(li);
    }
    list.classList.add("vis");
  });
})();
