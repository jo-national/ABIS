/* ============================================================
   motion.js — Positivlisten?
   Én bevægelse: indhold afsløres roligt, mens man ruller.
   Ingen åbningsanimation — siden står færdig fra første frame.
   Uden JS (eller ved prefers-reduced-motion) er siden urørt.

   Robusthedsregler:
   - Footeren animeres ALDRIG (troværdighedsindhold må ikke
     kunne gemmes af pynt).
   - Ingen beskåret afsløringszone: er elementet synligt,
     afsløres det.
   - Sikkerhedsnet: alt, der stadig er skjult efter 4 sekunder,
     tvangsvises uden animation.
   ============================================================ */
(() => {
  "use strict";

  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const $  = (s, c) => (c || document).querySelector(s);
  const UD = "cubic-bezier(0.16, 1, 0.3, 1)";

  function loeft(el) {
    el.animate(
      [
        { opacity: 0, transform: "translateY(30px)", filter: "blur(4px)" },
        { opacity: 1, transform: "none", filter: "blur(0px)" }
      ],
      { duration: 950, easing: UD, fill: "both" }
    ).finished.then(() => { el.style.opacity = ""; });
  }

  function init() {
    try {
      /* Footeren er bevidst udeladt: filnavn, dato og forbehold
         skal være synlige altid, uden undtagelse. */
      const mål = [
        $(".forside-kontekst"), $(".kontekst"), $(".forklaring"),
        $(".stamdata"), $(".kilde")
      ].filter(Boolean);

      const skjulte = new Set();

      const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          io.unobserve(e.target);
          skjulte.delete(e.target);
          loeft(e.target);
        });
      }, { threshold: 0.05 });

      mål.forEach((el) => {
        /* kun elementer under folden — det synlige rører vi aldrig */
        if (el.getBoundingClientRect().top < innerHeight * 0.9) return;
        el.style.opacity = "0";
        skjulte.add(el);
        io.observe(el);
      });

      /* Sikkerhedsnet: intet må forblive skjult, uanset årsag. */
      setTimeout(() => {
        skjulte.forEach((el) => {
          io.unobserve(el);
          el.style.opacity = "";
        });
        skjulte.clear();
      }, 4000);
    } catch (fejl) {
      document.querySelectorAll("[style*='opacity']").forEach((el) => { el.style.opacity = ""; });
      console.error(fejl);
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
