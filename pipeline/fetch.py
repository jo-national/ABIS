"""
fetch.py — henter ABIS-listen fra skat.dk, men kun hvis den er ændret.

Sådan virker den:
1. Henter HTML-siden (stabil URL) og finder Excel-linket dynamisk.
   Linket må ALDRIG hardcodes: /media/-stien indeholder et tilfældigt slug,
   der skifter ved hver ny offentliggørelse.
2. Downloader filen og beregner SHA-256 (et digitalt fingeraftryk).
3. Sammenligner med sidst kendte fingeraftryk i data/state.json.
   - Uændret: afslutter stille (exit 0, "changed=false").
   - Ændret:  arkiverer den rå fil i data/raw/ med dato i filnavnet
              og opdaterer state.json.
4. Enhver uventet situation (intet link fundet, HTTP-fejl, tom fil)
   fejler HØJLYDT med exit 1, så GitHub Actions-jobbet fejler og du
   får besked — i stedet for at gamle data præsenteres som friske.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests

PAGE_URL = (
    "https://skat.dk/erhverv/ekapital/vaerdipapirer/"
    "beviser-og-aktier-i-investeringsforeninger-og-selskaber-ifpa"
)
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
STATE_FILE = DATA / "state.json"

# Linkmønster: en href der ender på .xlsx og indeholder "abis" (case-insensitivt).
LINK_RE = re.compile(r'href="([^"]*abis[^"]*\.xlsx)"', re.IGNORECASE)
# Offentliggørelsesdato: teksten på siden lyder fx
# "Liste over aktiebaserede investeringsselskaber (offentliggjort den 29. juni 2026)"
PUBLISHED_RE = re.compile(
    r"offentliggjort\s+den\s+(\d{1,2}\.?\s*\w+\s*\d{4})", re.IGNORECASE
)

HEADERS = {"User-Agent": "aktiebaseret-dk dataopdatering (kontakt: se /om paa sitet)"}


def fail(msg: str) -> None:
    print(f"FEJL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    print(f"Henter side: {PAGE_URL}")
    try:
        page = requests.get(PAGE_URL, headers=HEADERS, timeout=60)
        page.raise_for_status()
    except requests.RequestException as e:
        fail(f"Kunne ikke hente siden hos skat.dk: {e}")

    links = LINK_RE.findall(page.text)
    if not links:
        fail(
            "Fandt intet .xlsx-link med 'abis' i href'en. "
            "Skat.dk har muligvis ændret sidens struktur — kræver manuel kontrol."
        )
    if len(set(links)) > 1:
        print(f"ADVARSEL: fandt {len(set(links))} forskellige ABIS-links; bruger det første.")
    file_url = urljoin("https://skat.dk/", links[0])
    print(f"Fandt fil-link: {file_url}")

    m = PUBLISHED_RE.search(page.text)
    published_text = m.group(1).strip() if m else None
    if published_text:
        print(f"Offentliggørelsesdato ifølge siden: {published_text}")
    else:
        print("ADVARSEL: kunne ikke aflæse offentliggørelsesdato fra sidens tekst.")

    try:
        resp = requests.get(file_url, headers=HEADERS, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as e:
        fail(f"Kunne ikke downloade Excel-filen: {e}")
    if len(resp.content) < 10_000:
        fail(f"Downloadet fil er mistænkeligt lille ({len(resp.content)} bytes).")

    sha = hashlib.sha256(resp.content).hexdigest()
    print(f"SHA-256: {sha}")

    # Registrér dette tjek, uanset om filen er ændret. Skrives til en fil,
    # der IKKE versioneres (se .gitignore) — den lever kun i den enkelte
    # kørsel og læses af build_site.py umiddelbart efter. Sådan kan
    # statuslinjen ærligt vise "senest tjekket", uden en commit hver nat.
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "last_checked.json").write_text(
        json.dumps(
            {
                "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "http_last_modified": resp.headers.get("Last-Modified"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    state = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))

    if state.get("sha256") == sha:
        print("Ingen ændring siden sidste kørsel.")
        print("changed=false")
        return

    RAW.mkdir(parents=True, exist_ok=True)
    original_name = file_url.rsplit("/", 1)[-1]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_name = f"{today}_{original_name}"
    (RAW / archive_name).write_bytes(resp.content)
    print(f"Arkiveret som data/raw/{archive_name}")

    new_state = {
        "source_page": PAGE_URL,
        "file_url": file_url,
        "original_filename": original_name,
        "archived_as": archive_name,
        "sha256": sha,
        "published_text": published_text,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "http_last_modified": resp.headers.get("Last-Modified"),
    }
    DATA.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(new_state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("changed=true")


if __name__ == "__main__":
    main()
