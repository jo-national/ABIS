"""
build_site.py — bygger hele det statiske website ud fra data/abis.json.

Output i site/:
  index.html                    Forside med søgning
  fond/<ISIN>/index.html        Én side pr. papir ("Er X aktiebaseret?")
  fonde/<a-z|0-9>.html          Alfabetisk indeks (interne links til alle sider)
  om.html, metode.html          Om sitet, datagrundlag, huller, ansvarsfraskrivelse
  sogeindeks.json               Kompakt indeks til søgning i browseren
  sitemap.xml, robots.txt
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "abis.json"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
SITE = ROOT / "site"

# Sættes til det rigtige domæne, når det er købt (bruges i sitemap + canonical).
BASE_URL = "https://www.DITDOMÆNE.dk"


def slug_bucket(navn: str | None, isin: str) -> str:
    first = (navn or isin)[0].lower()
    return first if first.isalpha() and first.isascii() else "0-9"


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    fonde: dict = data["fonde"]
    aktuelt_aar: int = data["seneste_indkomstaar"]
    kilde = data["kilde"]

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    ctx_base = {
        "aktuelt_aar": aktuelt_aar,
        "kilde": kilde,
        "antal_pr_aar": data["antal_pr_aar"],
        "antal_fonde": len(fonde),
        "base_url": BASE_URL,
    }

    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    shutil.copytree(STATIC, SITE / "static")

    urls: list[str] = []

    # Forside
    (SITE / "index.html").write_text(
        env.get_template("index.html").render(**ctx_base), encoding="utf-8"
    )
    urls.append("/")

    # Fondssider
    buckets: dict[str, list[tuple[str, dict]]] = {}
    tpl_fond = env.get_template("fond.html")
    for isin, e in fonde.items():
        paa_listen_nu = aktuelt_aar in e["aar"]
        d = SITE / "fond" / isin
        d.mkdir(parents=True, exist_ok=True)
        d.joinpath("index.html").write_text(
            tpl_fond.render(
                isin=isin,
                fond=e,
                paa_listen_nu=paa_listen_nu,
                **ctx_base,
            ),
            encoding="utf-8",
        )
        urls.append(f"/fond/{isin}/")
        buckets.setdefault(slug_bucket(e["navn"], isin), []).append((isin, e))

    # Alfabetisk indeks
    tpl_idx = env.get_template("fonde_indeks.html")
    (SITE / "fonde").mkdir(exist_ok=True)
    bucket_keys = sorted(buckets)
    for key in bucket_keys:
        items = sorted(buckets[key], key=lambda kv: (kv[1]["navn"] or kv[0]).lower())
        (SITE / "fonde" / f"{key}.html").write_text(
            tpl_idx.render(bogstav=key, alle_bogstaver=bucket_keys, fonde=items, **ctx_base),
            encoding="utf-8",
        )
        urls.append(f"/fonde/{key}.html")

    # Om + metode
    for page in ("om", "metode"):
        (SITE / f"{page}.html").write_text(
            env.get_template(f"{page}.html").render(**ctx_base), encoding="utf-8"
        )
        urls.append(f"/{page}.html")

    # Søgeindeks (kompakt: [ISIN, navn, på-listen-i-aktuelt-år])
    indeks = [
        [isin, e["navn"] or "", 1 if aktuelt_aar in e["aar"] else 0]
        for isin, e in fonde.items()
    ]
    (SITE / "sogeindeks.json").write_text(
        json.dumps(indeks, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    # Sitemap + robots
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{BASE_URL}{u}</loc></url>" for u in urls]
    sm.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8"
    )

    print(f"Byggede {len(urls)} sider i {SITE} ({len(fonde)} fondssider).")


if __name__ == "__main__":
    main()
