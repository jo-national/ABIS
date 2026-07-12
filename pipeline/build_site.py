"""
build_site.py — bygger hele det statiske website ud fra data/abis.json.

BASE_PATH: sitet ligger på jo-national.github.io/ABIS/ indtil et domæne er sat op.
Alle interne henvisninger får derfor et præfiks. Når domænet er på plads, sættes
BASE_PATH = "" og BASE_URL til domænet.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, select_autoescape

DK = ZoneInfo("Europe/Copenhagen")
MDR = ["januar", "februar", "marts", "april", "maj", "juni", "juli",
       "august", "september", "oktober", "november", "december"]


def dansk_dato(dt: datetime) -> str:
    dt = dt.astimezone(DK)
    return f"{dt.day}. {MDR[dt.month - 1]} {dt.year}"


def dansk_dato_tid(dt: datetime) -> str:
    dt = dt.astimezone(DK)
    return f"{dt.day}. {MDR[dt.month - 1]} {dt.year} kl. {dt:%H.%M} (dansk tid)"

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "abis.json"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
SITE = ROOT / "site"

BASE_PATH = ""
BASE_URL = "https://www.xn--ppositivlisten-lib.dk"


def bucket(navn: str, fid: str) -> str:
    first = (navn or fid)[0].lower()
    return first if first.isalpha() and first.isascii() else "0-9"


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    fonde: dict = data["fonde"]
    aktuelt_aar: int = data["seneste_indkomstaar"]

    def tusind(n):
        """Dansk tusindtalsseparering: 5303 -> 5.303"""
        try:
            return f"{int(n):,}".replace(",", ".")
        except (ValueError, TypeError):
            return str(n)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["tusind"] = tusind
    kilde = data["kilde"]

    # Tidsstempler til statuslinje og metodeside.
    hentet_dt = datetime.fromisoformat(kilde["hentet_utc"])
    lc_fil = ROOT / "data" / "last_checked.json"
    if lc_fil.exists():
        lc = json.loads(lc_fil.read_text(encoding="utf-8"))
        tjekket_dt = datetime.fromisoformat(lc["checked_at_utc"])
    else:
        tjekket_dt = hentet_dt

    # Kun ÉN brugervendt "senest opdateret"-dato på hele sitet: den officielle
    # offentliggørelsesdato, som Skattestyrelsen selv angiver på siden. Filens rå
    # HTTP Last-Modified-header bruges bevidst IKKE, da den (serverens
    # upload-tidsstempel) rutinemæssigt afviger fra offentliggørelsesdatoen og
    # ville fremstå som en modstridende dato. Én kilde, samme dato overalt.
    if kilde.get("offentliggjort_tekst"):
        senest_opdateret = f"den {kilde['offentliggjort_tekst']}"
    else:
        senest_opdateret = "- se skat.dk"

    ctx = {
        "aktuelt_aar": aktuelt_aar,
        "sidst_tjekket": dansk_dato_tid(tjekket_dt),
        "hentet_dansk": dansk_dato_tid(hentet_dt),
        "senest_opdateret": senest_opdateret,
        "opdateret_dato": kilde.get("offentliggjort_tekst") or "se skat.dk",
        "alle_aar": data["alle_aar"],
        "kilde": kilde,
        "antal_pr_aar": data["antal_pr_aar"],
        "antal_fonde": len(fonde),
        "antal_uden_isin": data["antal_uden_isin"],
        "base_url": BASE_URL,
        "base_path": BASE_PATH,
    }

    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    shutil.copytree(STATIC, SITE / "static")

    urls: list[str] = ["/"]
    (SITE / "index.html").write_text(env.get_template("index.html").render(**ctx), encoding="utf-8")

    tpl_fond = env.get_template("fond.html")
    buckets: dict[str, list] = {}
    for fid, e in fonde.items():
        navn = e["navne"][0] if e["navne"] else fid
        d = SITE / "fond" / fid
        d.mkdir(parents=True, exist_ok=True)
        d.joinpath("index.html").write_text(
            tpl_fond.render(fid=fid, fond=e, navn=navn,
                            paa_listen_nu=aktuelt_aar in e["aar"], **ctx),
            encoding="utf-8",
        )
        urls.append(f"/fond/{fid}/")
        buckets.setdefault(bucket(navn, fid), []).append((fid, e, navn))

    tpl_idx = env.get_template("fonde_indeks.html")
    (SITE / "fonde").mkdir(exist_ok=True)
    keys = sorted(buckets)
    for k in keys:
        items = sorted(buckets[k], key=lambda x: x[2].lower())
        (SITE / "fonde" / f"{k}.html").write_text(
            tpl_idx.render(bogstav=k, alle_bogstaver=keys, fonde=items, **ctx), encoding="utf-8"
        )
        urls.append(f"/fonde/{k}.html")

    for page in ("om", "metode"):
        (SITE / f"{page}.html").write_text(
            env.get_template(f"{page}.html").render(**ctx), encoding="utf-8"
        )
        urls.append(f"/{page}.html")

    # Ændringsside: nye og udgåede fonde ift. forrige indkomstår.
    forrige_aar = aktuelt_aar - 1
    nye, fjernede = [], []
    for fid, e in fonde.items():
        navn = e["navne"][0] if e["navne"] else fid
        if aktuelt_aar in e["aar"] and forrige_aar not in e["aar"]:
            nye.append((fid, e, navn))
        elif forrige_aar in e["aar"] and aktuelt_aar not in e["aar"]:
            fjernede.append((fid, e, navn))
    nye.sort(key=lambda t: t[2].lower())
    fjernede.sort(key=lambda t: t[2].lower())
    (SITE / "aendringer.html").write_text(
        env.get_template("aendringer.html").render(
            nye=nye, fjernede=fjernede, forrige_aar=forrige_aar, **ctx
        ),
        encoding="utf-8",
    )
    urls.append("/aendringer.html")

    # Søgeindeks: [id, primærnavn, på-listen-nu, [øvrige navne]]
    indeks = [
        [fid, (e["navne"][0] if e["navne"] else fid),
         1 if aktuelt_aar in e["aar"] else 0, e["navne"][1:]]
        for fid, e in fonde.items()
    ]
    (SITE / "sogeindeks.json").write_text(
        json.dumps(indeks, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{BASE_URL}{u}</loc></url>" for u in urls]
    sm.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # 404-side (GitHub Pages viser automatisk /404.html ved døde links).
    # Bevidst IKKE i sitemap - den skal ikke indekseres.
    (SITE / "404.html").write_text(
        env.get_template("404.html").render(**ctx), encoding="utf-8"
    )
    # Browsere beder automatisk om /favicon.ico i roden.
    shutil.copy(STATIC / "favicon.ico", SITE / "favicon.ico")
    (SITE / "CNAME").write_text("www.xn--ppositivlisten-lib.dk\n", encoding="utf-8")   
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    print(f"Byggede {len(urls)} sider ({len(fonde)} fondssider, heraf {data['antal_uden_isin']} uden ISIN).")


if __name__ == "__main__":
    main()
