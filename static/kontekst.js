// Kontekstknapper på fondssider. Uden JavaScript vises alle fire paneler,
// så indholdet altid er læsbart og indekserbart af Google.
(function () {
  const tabs = Array.from(document.querySelectorAll('.kontekst-knapper [role="tab"]'));
  if (!tabs.length) return;
  const paneler = tabs.map((t) => document.getElementById(t.getAttribute("aria-controls")));

  function vis(i) {
    tabs.forEach((t, j) => {
      t.setAttribute("aria-selected", String(j === i));
      t.tabIndex = j === i ? 0 : -1;
      paneler[j].hidden = j !== i;
    });
  }
  tabs.forEach((t, i) => {
    t.addEventListener("click", () => vis(i));
    t.addEventListener("keydown", (e) => {
      const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!d) return;
      e.preventDefault();
      const n = (i + d + tabs.length) % tabs.length;
      vis(n);
      tabs[n].focus();
    });
  });
  vis(0);
})();

// Kopiér ISIN til udklipsholder. Knappen skjules, hvis browseren ikke kan.
(function () {
  const knapper = document.querySelectorAll("[data-kopier]");
  if (!knapper.length) return;
  if (!navigator.clipboard) {
    knapper.forEach((k) => (k.hidden = true));
    return;
  }
  knapper.forEach((k) => {
    k.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(k.dataset.kopier);
        const før = k.textContent;
        k.textContent = "Kopieret";
        setTimeout(() => (k.textContent = før), 1500);
      } catch {
        k.textContent = "Kunne ikke kopiere";
      }
    });
  });
})();
