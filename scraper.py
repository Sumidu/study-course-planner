#!/usr/bin/env python3
"""
Uni Lübeck Modulhandbuch Scraper
=================================
Scrapes a module handbook page and produces a JSON file with per-module:
  - title, code, kp
  - structure        : compact teaching format, e.g. "2V+2S" (derived from SWS)
  - duration         : "1 Semester"
  - offered          : "Jedes Wintersemester"
  - study_programs   : list of programmes that include this module
  - lehrveranstaltungen : list of course entries (Vorlesung, Seminar, …)
  - workload         : list of workload entries
  - content          : list of Lehrinhalte
  - competencies     : list of Qualifikationsziele/Kompetenzen
  - grading          : list of grading/exam info
  - prerequisites_for: list of modules this is a prerequisite for
  - prerequisites    : list of required prerequisite modules
  - responsible      : list of Modulverantwortliche
  - instructors      : list of Lehrende
  - literature       : list of literature entries
  - language         : language of instruction
  - remarks          : Bemerkungen (free text)
  - last_changed     : date string
  - other_courses    : other programmes (Verwendbarkeit)

Usage
-----
  python3 scraper.py [URL] [--output FILE] [--delay SECONDS] [--limit N]

Defaults
--------
  URL    = https://www2.uni-luebeck.de/studium/informatik-und-mathematik/
           medieninformatik/master-studiengang-medieninformatik/modulhandbuch/
  output = modules.json
  delay  = 1.0  (seconds between requests – be polite)
"""

import argparse
import json
import re
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Constants / configuration
# ---------------------------------------------------------------------------

DEFAULT_URL = (
    "https://www2.uni-luebeck.de/studium/informatik-und-mathematik/"
    "medieninformatik/master-studiengang-medieninformatik/modulhandbuch/"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

# ---------------------------------------------------------------------------
# Label keyword lists – used by parse_index_page table-column detection
# ---------------------------------------------------------------------------

KP_LABELS = [
    "kreditpunkt", "leistungspunkt", "credit point", " kp", "(kp)",
]

STRUCTURE_LABELS = [
    "lehrform", "lehr- und lernform", "veranstaltungsform",
    "unterrichtsform", "sws", "semesterwochenstunden",
]

COURSES_LABELS = [
    "verwendbarkeit", "eingesetzt in", "weitere studieng",
    "other program", "zugeordnet",
]

TITLE_LABELS = [
    "modulbezeichnung", "bezeichnung", "modulname", "name", "titel",
]

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches "Modul CS5158-KP04, CS5158" in a heading
MODUL_CODE_H1_RE = re.compile(r"^\s*Modul\s+(.+)", re.I)

# Extracts KP from a code fragment like "CS5158-KP04" → 4
KP_IN_CODE_RE = re.compile(r"-KP(\d+)", re.I)

# Extracts the primary code (first token) from "CS5158-KP04, CS5158"
PRIMARY_CODE_RE = re.compile(r"\b([A-Z]{2,4}\d{3,4}[A-Z0-9]*)\b")

# KP in a labeled field value: "6 Kreditpunkte", "6 KP", "ECTS: 4"
KP_LABELED_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:KP|CP|ECTS|Kreditpunkte?|Leistungspunkte?)\b"
    r"|(?:KP|CP|ECTS|Kreditpunkte?)\s*[:\-]?\s*(\d+(?:[.,]\d+)?)",
    re.I,
)

# Teaching-format: "2V+1Ü", "4V", "3V/2Ü/1P", "2S", "1K"
STRUCTURE_RE = re.compile(
    r"\b\d+\s*(?:V|Ü|S|P|K|T)(?!\w)"
    r"(?:\s*[+/]\s*\d+\s*(?:V|Ü|S|P|K|T)(?!\w))*",
    re.UNICODE,
)

# URLs that are module detail pages (Uni Lübeck pattern: /details/NNN/)
DETAIL_URL_RE = re.compile(r"/details/\d+/?$")

# URLs that look like sub-pages of a module handbook
MODUL_URL_RE = re.compile(r"/modulhandbuch/|/modul(?:e|liste)?/|/module\b", re.I)

# Pages that are clearly index/overview pages – skip as modules
NON_MODULE_TITLE_RE = re.compile(
    r"modulhandbuch|module\s+(manual|guide|handbook)|master.{0,30}(medieninformatik|informatik)",
    re.I,
)

# Matches "(Seminar, 2 SWS)" or "(Vorlesung, 4 SWS)" in Lehrveranstaltungen items
SWS_ENTRY_RE = re.compile(r"\(([^,)]+),\s*(\d+)\s*SWS\)", re.I)

# Map German course-type names → compact letter codes
SWS_TYPE_MAP = {
    "vorlesung": "V",
    "übung": "Ü", "uebung": "Ü",
    "seminar": "S",
    "praktikum": "P",
    "kolloquium": "K",
    "tutorial": "T",
    "tutorium": "T",
    "projekt": "Proj",
}

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch(url: str, retries: int = 3) -> BeautifulSoup | None:
    """Fetch *url* and return a BeautifulSoup, or None on failure."""
    for attempt in range(1, retries + 1):
        try:
            resp = SESSION.get(url, timeout=20)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
        except requests.RequestException as exc:
            print(f"  [warn] attempt {attempt}/{retries} failed for {url}: {exc}",
                  file=sys.stderr)
            if attempt < retries:
                time.sleep(2 ** attempt)
    return None


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def clean(text: str) -> str:
    return " ".join(text.split())


def label_matches(label: str, candidates: list[str]) -> bool:
    lc = label.lower()
    return any(c in lc for c in candidates)


def extract_kp_from_code(code_text: str) -> int | None:
    """Extract KP from a module-code string like 'CS5158-KP04'."""
    m = KP_IN_CODE_RE.search(code_text)
    return int(m.group(1)) if m else None


def extract_kp_from_value(value: str) -> int | None:
    """Extract KP from a labeled field value like '6 Kreditpunkte'."""
    m = KP_LABELED_RE.search(value)
    if m:
        raw = m.group(1) or m.group(2)
        return int(float(raw.replace(",", ".")))
    return None


def extract_structure(text: str) -> str:
    """Return the first teaching-format token from *text*, or ''."""
    m = STRUCTURE_RE.search(text)
    return m.group(0).strip() if m else ""


def extract_primary_code(code_text: str) -> str:
    """Return the first module-code token, e.g. 'CS5158' from 'CS5158-KP04, CS5158'."""
    m = PRIMARY_CODE_RE.search(code_text)
    return m.group(1) if m else ""


def derive_structure_from_courses(courses: list[str]) -> str:
    """Build compact format string like '2V+2S' from Lehrveranstaltungen items."""
    parts = []
    for entry in courses:
        m = SWS_ENTRY_RE.search(entry)
        if m:
            type_name = m.group(1).strip().lower()
            sws = m.group(2)
            code = next((v for k, v in SWS_TYPE_MAP.items() if k in type_name), None)
            if code:
                parts.append(f"{sws}{code}")
    return "+".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# Core data extraction
# ---------------------------------------------------------------------------

def _empty_module(url: str) -> dict:
    """Return a fresh module dict with all fields initialised."""
    return {
        "title": "",
        "code": "",
        "kp": None,
        "structure": "",
        "duration": "",
        "offered": "",
        "study_programs": [],
        "lehrveranstaltungen": [],
        "workload": [],
        "content": [],
        "competencies": [],
        "grading": [],
        "prerequisites_for": [],
        "prerequisites": [],
        "responsible": [],
        "instructors": [],
        "literature": [],
        "language": "",
        "remarks": "",
        "last_changed": "",
        "other_courses": [],
        "url": url,
    }


def _extend_list(module: dict, key: str, items: list[str]) -> None:
    """Append deduplicated, cleaned strings to module[key]."""
    existing = set(module[key])
    for item in items:
        item = clean(item)
        if item and item not in existing:
            module[key].append(item)
            existing.add(item)


def _process_label_content(module: dict, label: str, elem) -> None:
    """
    Route a (label, content-element) pair to the correct module field.

    Extracts <li> items when present; otherwise falls back to newline-split
    text so that multi-value fields stored as plain text are still split.
    """
    label_lc = label.lower().rstrip(":")

    # Prefer explicit <li> items; fall back to newline-split text
    li_items = [clean(li.get_text()) for li in elem.find_all("li") if clean(li.get_text())]
    raw_text = clean(elem.get_text())
    if not li_items:
        lines = [clean(ln) for ln in elem.get_text("\n").split("\n") if clean(ln)]
        if len(lines) > 1:
            li_items = lines
    items = li_items  # may be empty → callers fall back to raw_text

    # ── KP ──────────────────────────────────────────────────────────────────
    if any(k in label_lc for k in ["kreditpunkt", "leistungspunkt", "credit point", " kp", "(kp)"]):
        if module["kp"] is None:
            module["kp"] = extract_kp_from_value(raw_text)

    # ── Duration / Offered ──────────────────────────────────────────────────
    elif "dauer" in label_lc:
        if not module["duration"]:
            module["duration"] = raw_text

    elif any(k in label_lc for k in ["angebotsturnus", "turnus"]):
        if not module["offered"]:
            module["offered"] = raw_text

    # ── Study programmes ────────────────────────────────────────────────────
    elif any(k in label_lc for k in ["studiengang", "fachgebiet", "fachsemester"]):
        _extend_list(module, "study_programs", items or [raw_text])

    # ── Lehrveranstaltungen (course list) → also derive structure ───────────
    elif "lehrveranstaltung" in label_lc:
        _extend_list(module, "lehrveranstaltungen", items or [raw_text])
        if not module["structure"] and module["lehrveranstaltungen"]:
            module["structure"] = derive_structure_from_courses(module["lehrveranstaltungen"])

    # ── Lehrform / Unterrichtsform (explicit structure label) ───────────────
    elif any(k in label_lc for k in ["lehrform", "lehr- und lernform", "veranstaltungsform", "unterrichtsform"]):
        if not module["structure"]:
            s = extract_structure(raw_text)
            module["structure"] = s if s else raw_text

    # ── Workload ─────────────────────────────────────────────────────────────
    elif any(k in label_lc for k in ["workload", "arbeitsaufwand"]):
        _extend_list(module, "workload", items or [raw_text])

    # ── Lehrinhalte ──────────────────────────────────────────────────────────
    elif any(k in label_lc for k in ["lehrinhalt", "inhalt"]):
        _extend_list(module, "content", items or [raw_text])

    # ── Qualifikationsziele / Kompetenzen ───────────────────────────────────
    elif any(k in label_lc for k in ["qualifikationsziel", "kompetenz"]):
        _extend_list(module, "competencies", items or [raw_text])

    # ── Grading / Exams ──────────────────────────────────────────────────────
    elif any(k in label_lc for k in ["vergabe von leistungspunkt", "benotung", "prüfungsleistung"]):
        _extend_list(module, "grading", items or [raw_text])

    # ── Prerequisites (forward) ──────────────────────────────────────────────
    elif "voraussetzung für" in label_lc:
        _extend_list(module, "prerequisites_for", items or [raw_text])

    # ── Prerequisites (required) ─────────────────────────────────────────────
    elif any(k in label_lc for k in ["setzt voraus", "voraussetzung:"]):
        _extend_list(module, "prerequisites", items or [raw_text])

    # ── Responsible / Instructors ────────────────────────────────────────────
    elif "modulverantwortlich" in label_lc:
        _extend_list(module, "responsible", items or [raw_text])

    elif any(k in label_lc for k in ["lehrende", "dozent"]):
        _extend_list(module, "instructors", items or [raw_text])

    # ── Literature ───────────────────────────────────────────────────────────
    elif "literatur" in label_lc:
        _extend_list(module, "literature", items or [raw_text])

    # ── Language ─────────────────────────────────────────────────────────────
    elif "sprache" in label_lc:
        if not module["language"]:
            module["language"] = items[0] if items else raw_text

    # ── Remarks ──────────────────────────────────────────────────────────────
    elif any(k in label_lc for k in ["bemerkung", "hinweis"]):
        if not module["remarks"]:
            module["remarks"] = raw_text

    # ── Last changed ─────────────────────────────────────────────────────────
    elif any(k in label_lc for k in ["letzte änderung", "stand:"]):
        if not module["last_changed"]:
            module["last_changed"] = raw_text

    # ── Verwendbarkeit / other study programmes ───────────────────────────────
    elif any(k in label_lc for k in ["verwendbarkeit", "eingesetzt in", "weitere studieng", "other program", "zugeordnet"]):
        _extend_list(module, "other_courses",
                     items or [p for p in re.split(r"[;,\n]+", raw_text) if p.strip()])

    # ── Title (fallback from labeled row) ───────────────────────────────────
    elif any(k in label_lc for k in ["modulbezeichnung", "bezeichnung", "modulname", "name", "titel"]):
        if not module["title"]:
            module["title"] = raw_text

    # ── SWS fallback for structure ───────────────────────────────────────────
    if not module["structure"] and any(k in label_lc for k in ["sws", "semesterwochenstunden"]):
        s = extract_structure(raw_text)
        if s:
            module["structure"] = s


def _scan_structured_markup(soup: BeautifulSoup, module: dict) -> None:
    """Walk all <table> rows and <dl> items in *soup* and route each pair."""
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                _process_label_content(module, clean(cells[0].get_text()), cells[1])

    for dl in soup.find_all("dl"):
        for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
            _process_label_content(module, clean(dt.get_text()), dd)


# ---------------------------------------------------------------------------
# Module detail-page parser
# ---------------------------------------------------------------------------

def parse_module_page(soup: BeautifulSoup, url: str) -> dict:
    """
    Extract module data from a Uni Lübeck detail page.

    Uni Lübeck puts "Modul CS5158-KP04, CS5158" in the <h1>.
    The real module name appears in a subsequent heading or in a labeled
    table/dl row.  We handle both cases.
    """
    module = _empty_module(url)

    # ── Step 1: inspect the first heading ──────────────────────────────────
    first_heading = soup.find(re.compile(r"^h[1-4]$"))
    if first_heading:
        h1_text = clean(first_heading.get_text())
        m = MODUL_CODE_H1_RE.match(h1_text)
        if m:
            # h1 is "Modul CS5158-KP04, CS5158" – treat as code heading
            h1_code_part = m.group(1)
            module["code"] = extract_primary_code(h1_code_part)
            if module["kp"] is None:
                module["kp"] = extract_kp_from_code(h1_code_part)
        else:
            # h1 IS the real title (generic layout)
            module["title"] = h1_text

    # ── Step 2: if we got a code heading, find the real title ───────────────
    if not module["title"] and first_heading:
        for sib in first_heading.find_next_siblings(re.compile(r"^h[2-6]$")):
            candidate = clean(sib.get_text())
            if candidate and not MODUL_CODE_H1_RE.match(candidate):
                module["title"] = candidate
                break

    # ── Step 3: walk tables and dl for labeled fields ──────────────────────
    _scan_structured_markup(soup, module)

    # ── Step 4: structure fallback – scan full page text ───────────────────
    if not module["structure"]:
        full_text = soup.get_text(" ", strip=True)
        module["structure"] = extract_structure(full_text)

    # ── Step 5: title fallback – use <title> tag ────────────────────────────
    if not module["title"]:
        page_title = soup.find("title")
        if page_title:
            parts = re.split(r"[|\-–]", page_title.get_text())
            module["title"] = clean(parts[0])

    return module


# ---------------------------------------------------------------------------
# Index-page parsers
# ---------------------------------------------------------------------------

def find_module_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """
    Return de-duplicated absolute URLs of module detail pages.

    Priority:
      1. Links matching /details/NNN/ (Uni Lübeck TYPO3 pattern)
      2. Links matching generic /modulhandbuch/ sub-paths
      3. All same-host links in the main content area
    """
    base_host = urlparse(base_url).netloc
    found: list[str] = []
    seen: set[str] = set()

    def add(href: str) -> None:
        abs_url = urljoin(base_url, href).rstrip("/") + "/"
        if abs_url not in seen and urlparse(abs_url).netloc == base_host:
            # Skip the start page itself
            if abs_url.rstrip("/") == base_url.rstrip("/"):
                return
            seen.add(abs_url)
            found.append(abs_url)

    # 1. /details/NNN/ links (highest confidence for Uni Lübeck)
    for a in soup.find_all("a", href=DETAIL_URL_RE):
        add(a["href"])

    # 2. Generic modulhandbuch sub-links
    if not found:
        for a in soup.find_all("a", href=MODUL_URL_RE):
            href = a.get("href", "")
            if DETAIL_URL_RE.search(href) or href.count("/") > urlparse(base_url).path.count("/"):
                add(href)

    # 3. Any same-host sub-page inside main content
    if not found:
        content = (
            soup.find("main")
            or soup.find(id=re.compile(r"content|main|body", re.I))
            or soup.find(class_=re.compile(r"content|main|body", re.I))
            or soup
        )
        for a in content.find_all("a", href=True):
            href = a["href"]
            if href and not href.startswith(("#", "mailto:", "tel:")):
                add(href)

    # Filter out non-module URLs (PDFs, images, unrelated sections)
    found = [
        u for u in found
        if not re.search(r"\.(pdf|docx?|xlsx?|png|jpg|svg|zip)$", u, re.I)
    ]
    return found


def parse_index_page(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """
    Extract module data from a single listing page (no sub-pages).

    Tries:
      A) One <article>/<section> per module with an inner heading
      B) A big <table> with one row per module
    """
    modules: list[dict] = []

    # ── A: block per module ────────────────────────────────────────────────
    candidates = soup.find_all(["article", "section"])
    if not candidates:
        candidates = soup.find_all(
            "div", class_=re.compile(r"modul|course|lehrveranstaltung", re.I)
        )

    for block in candidates:
        heading = block.find(re.compile(r"^h[1-6]$"))
        if not heading:
            continue
        mod = _empty_module(base_url)
        mod["title"] = clean(heading.get_text())
        # Skip blocks whose heading is just an index/section title
        if NON_MODULE_TITLE_RE.search(mod["title"]):
            continue

        _scan_structured_markup(BeautifulSoup(str(block), "lxml"), mod)

        if not mod["structure"]:
            mod["structure"] = extract_structure(block.get_text(" "))

        if mod["title"]:
            modules.append(mod)

    # ── B: table-per-row ──────────────────────────────────────────────────
    if not modules:
        for table in soup.find_all("table"):
            headers = [clean(th.get_text()).lower() for th in table.find_all("th")]
            if not headers:
                continue
            col_map: dict[int, str] = {}
            for i, h in enumerate(headers):
                if any(k in h for k in ["titel", "name", "modul", "bezeichnung"]):
                    col_map[i] = "title"
                elif any(k in h for k in KP_LABELS):
                    col_map[i] = "kp_raw"
                elif any(k in h for k in STRUCTURE_LABELS):
                    col_map[i] = "structure_raw"
                elif any(k in h for k in COURSES_LABELS):
                    col_map[i] = "courses_raw"
                elif re.search(r"code|nummer|nr\.|kennung|kürzel", h):
                    col_map[i] = "code"
            if "title" not in col_map.values():
                continue
            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                mod = _empty_module(base_url)
                for idx, field in col_map.items():
                    if idx >= len(cells):
                        continue
                    val = clean(cells[idx].get_text())
                    if field == "title":
                        mod["title"] = val
                    elif field == "code":
                        mod["code"] = val
                    elif field == "kp_raw":
                        mod["kp"] = extract_kp_from_value(val)
                    elif field == "structure_raw":
                        mod["structure"] = extract_structure(val) or val
                    elif field == "courses_raw":
                        mod["other_courses"] = [
                            c.strip() for c in re.split(r"[;,\n]+", val) if c.strip()
                        ]
                if mod["title"]:
                    modules.append(mod)

    return modules


# ---------------------------------------------------------------------------
# Main scraping orchestration
# ---------------------------------------------------------------------------

def scrape(start_url: str, delay: float = 1.0, limit: int | None = None) -> list[dict]:
    print(f"Fetching index: {start_url}")
    soup = fetch(start_url)
    if soup is None:
        print("ERROR: Could not fetch start URL.", file=sys.stderr)
        sys.exit(1)

    links = find_module_links(soup, start_url)
    modules: list[dict] = []

    if links:
        if limit:
            print(f"Found {len(links)} module link(s). Test mode: fetching first {limit} …")
            links = links[:limit]
        else:
            print(f"Found {len(links)} module link(s). Fetching each …")
        for i, url in enumerate(links, 1):
            print(f"  [{i:3d}/{len(links)}] {url}")
            sub = fetch(url)
            if sub:
                mod = parse_module_page(sub, url)
                # Skip pages that look like overview/index pages
                if mod["title"] and not NON_MODULE_TITLE_RE.search(mod["title"]):
                    modules.append(mod)
            if i < len(links):
                time.sleep(delay)
    else:
        print("No sub-page links found – parsing current page directly.")
        modules = parse_index_page(soup, start_url)
        if limit:
            modules = modules[:limit]

    # Normalise types
    for m in modules:
        if m["kp"] is not None:
            m["kp"] = int(m["kp"])

    return modules


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape a Uni Lübeck Modulhandbuch and save modules as JSON."
    )
    parser.add_argument(
        "url", nargs="?", default=DEFAULT_URL,
        help="URL of the module handbook index page",
    )
    parser.add_argument(
        "--output", "-o", default="modules.json",
        help="Output JSON file (default: modules.json)",
    )
    parser.add_argument(
        "--delay", "-d", type=float, default=1.0,
        help="Delay in seconds between requests (default: 1.0)",
    )
    parser.add_argument(
        "--limit", "-n", "--test", type=int, default=None, metavar="N",
        help="Only fetch the first N module pages (quick test run)",
    )
    args = parser.parse_args()

    modules = scrape(args.url, delay=args.delay, limit=args.limit)

    output = {
        "source": args.url,
        "scraped_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "total": len(modules),
        "modules": modules,
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(modules)} module(s) → {args.output}")
    if modules:
        print("\nPreview (first 3):")
        for m in modules[:3]:
            print(
                f"  • {m['title']!r:45s} | KP: {str(m['kp']):4s} | "
                f"Structure: {m['structure'] or '—':10s} | "
                f"Code: {m['code']}"
            )


if __name__ == "__main__":
    main()
