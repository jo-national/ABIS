/* ============================================================
   motion.js — Positivlisten?
   Én bevægelse: indhold afsløres roligt, mens man ruller.
   Ingen åbningsanimation — siden står færdig fra første frame.
   Uden JS (eller ved prefers-reduced-motion) er siden urørt.
   ============================================================ */
(() => {
  "use strict";

  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const $  = (s, c) => (c || document).querySelector(s);
  const $$ = (s, c) => Array.from((c || document).querySelectorAll(s));
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
      const mål = [
        $(".forside-kontekst"), $(".kontekst"), $(".forklaring"),
        $(".stamdata"), $(".kilde"),
        $("footer .disclaimer"), $("footer .kolofon")
      ].filter(Boolean);

      const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          io.unobserve(e.target);
          loeft(e.target);
        });
      }, { rootMargin: "0px 0px -12% 0px", threshold: 0.05 });

      mål.forEach((el) => {
        /* kun elementer under folden — det synlige rører vi aldrig */
        if (el.getBoundingClientRect().top < innerHeight * 0.9) return;
        el.style.opacity = "0";
        io.observe(el);
      });
    } catch (fejl) {
      $$("[style*='opacity']").forEach((el) => { el.style.opacity = ""; });
      console.error(fejl);
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
