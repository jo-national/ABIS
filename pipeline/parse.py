"""
parse.py — læser den arkiverede ABIS-Excel og bygger data/abis.json.

Designprincip: parseren GÆTTER IKKE på filens struktur. Den:
1. Finder selv ark, der repræsenterer indkomstår (arknavne der indeholder et årstal).
2. Finder selv header-rækken i hvert ark (første række med en celle, der ligner "ISIN").
3. Mapper kolonner tolerant på header-tekst — og rapporterer alt, den ikke genkender.
4. Validerer hver ISIN mod det officielle format (2 bogstaver + 9 tegn + kontrolciffer)
   og rapporterer alle rækker, der afvises.
5. Skriver en fuld parse-rapport (data/parse_report.txt), så et menneske kan
   efterprøve antal rækker, headers og eksempler — og fejler med exit 1,
   hvis noget grundlæggende er galt (intet ISIN-kolonne, ingen års-ark, osv.).

Kør med --verify for kun at udskrive rapporten uden at skrive abis.json.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
STATE_FILE = DATA / "state.json"
OUT_FILE = DATA / "abis.json"
REPORT_FILE = DATA / "parse_report.txt"

YEAR_RE = re.compile(r"(20\d{2})")
ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

# Tolerant kolonnegenkendelse: nøgle -> liste af tekststumper vi leder efter i headeren.
COLUMN_HINTS = {
    "isin": ["isin"],
    "navn": ["navn", "name"],
    "lei": ["lei"],
    "cvr_se": ["cvr", "se-n", "se n"],
    "land": ["land", "country"],
}


def find_header(rows: list[tuple]) -> tuple[int, dict[str, int], list[str]] | None:
    """Find header-rækken og map kolonner. Returnerer (rækkeindex, mapping, ukendte)."""
    for idx, row in enumerate(rows[:20]):
        cells = [str(c).strip() if c is not None else "" for c in row]
        lowered = [c.lower() for c in cells]
        if not any("isin" in c for c in lowered):
            continue
        mapping: dict[str, int] = {}
        unknown: list[str] = []
        for col_idx, text in enumerate(lowered):
            if not text:
                continue
            for key, hints in COLUMN_HINTS.items():
                if key not in mapping and any(h in text for h in hints):
                    mapping[key] = col_idx
                    break
            else:
                unknown.append(cells[col_idx])
        return idx, mapping, unknown
    return None


def main(verify_only: bool = False) -> None:
    if not STATE_FILE.exists():
        sys.exit("FEJL: data/state.json findes ikke. Kør fetch.py først.")
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    xlsx_path = RAW / state["archived_as"]
    if not xlsx_path.exists():
        sys.exit(f"FEJL: arkiveret fil mangler: {xlsx_path}")

    report: list[str] = [
        f"Parse-rapport — genereret {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Kildefil: {state['original_filename']} (SHA-256 {state['sha256'][:16]}…)",
        f"Hentet fra: {state['file_url']}",
        "",
    ]

    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    funds: dict[str, dict] = {}
    years_found: dict[int, int] = {}
    rejected: list[str] = []
    problems: list[str] = []

    for sheet in wb.worksheets:
        m = YEAR_RE.search(sheet.title)
        if not m:
            report.append(f"Ark '{sheet.title}': intet årstal i navnet — SPRINGES OVER.")
            continue
        year = int(m.group(1))
        rows = [tuple(r) for r in sheet.iter_rows(values_only=True)]
        header = find_header(rows)
        if header is None:
            problems.append(f"Ark '{sheet.title}': ingen header-række med 'ISIN' fundet.")
            continue
        header_idx, mapping, unknown = header
        if "isin" not in mapping:
            problems.append(f"Ark '{sheet.title}': ISIN-kolonne kunne ikke identificeres.")
            continue

        count = 0
        for row in rows[header_idx + 1 :]:
            raw_isin = row[mapping["isin"]] if mapping["isin"] < len(row) else None
            if raw_isin is None:
                continue
            isin = str(raw_isin).strip().upper().replace(" ", "")
            if not isin:
                continue
            if not ISIN_RE.match(isin):
                rejected.append(f"{sheet.title}: '{raw_isin}'")
                continue

            def cell(key: str) -> str | None:
                i = mapping.get(key)
                if i is None or i >= len(row) or row[i] is None:
                    return None
                v = str(row[i]).strip()
                return v or None

            entry = funds.setdefault(isin, {"navn": None, "lei": None, "cvr_se": None, "land": None, "aar": []})
            if year not in entry["aar"]:
                entry["aar"].append(year)
                count += 1
            # Navn m.m. opdateres, så det nyeste år vinder.
            if year == max(entry["aar"]):
                for key in ("navn", "lei", "cvr_se", "land"):
                    v = cell(key)
                    if v:
                        entry[key] = v

        years_found[year] = years_found.get(year, 0) + count
        genkendt = ", ".join(f"{k}→kolonne {v+1}" for k, v in sorted(mapping.items()))
        report.append(
            f"Ark '{sheet.title}' → indkomstår {year}: {count} gyldige rækker. "
            f"Header i række {header_idx + 1}. Genkendte kolonner: {genkendt}."
        )
        if unknown:
            report.append(f"  Ikke-genkendte kolonneoverskrifter (medtages ikke): {unknown}")

    report.append("")
    report.append(f"Unikke ISIN i alt: {len(funds)}")
    for y in sorted(years_found):
        report.append(f"  Indkomstår {y}: {years_found[y]} papirer")
    if rejected:
        report.append(f"Afviste rækker (ugyldigt ISIN-format): {len(rejected)}")
        for r in rejected[:10]:
            report.append(f"  - {r}")
    eksempler = list(funds.items())[:3]
    report.append("Eksempler til efterprøvning:")
    for isin, e in eksempler:
        report.append(f"  {isin}: {e['navn']} — år: {sorted(e['aar'])}")

    if problems:
        report.append("")
        report.append("KRITISKE PROBLEMER:")
        report.extend(f"  - {p}" for p in problems)

    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))

    if problems or not funds or not years_found:
        sys.exit("FEJL: parsning ufuldstændig — se rapporten ovenfor. Intet output skrevet.")

    if verify_only:
        print("\n--verify: abis.json IKKE skrevet.")
        return

    out = {
        "genereret_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kilde": {
            "side": state["source_page"],
            "fil_url": state["file_url"],
            "filnavn": state["original_filename"],
            "sha256": state["sha256"],
            "offentliggjort_tekst": state.get("published_text"),
            "hentet_utc": state["fetched_at_utc"],
        },
        "seneste_indkomstaar": max(years_found),
        "antal_pr_aar": {str(y): n for y, n in sorted(years_found.items())},
        "fonde": {
            isin: {**e, "aar": sorted(e["aar"])} for isin, e in sorted(funds.items())
        },
    }
    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nSkrev {OUT_FILE} med {len(funds)} fonde.")


if __name__ == "__main__":
    main(verify_only="--verify" in sys.argv)
