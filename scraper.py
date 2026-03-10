#!/usr/bin/env python3
"""
Uni Lübeck Modulhandbuch Scraper
=================================
Scrapes a module handbook page and produces a JSON file with:
  - title        : module name
  - code         : module code (e.g. "CS5158")
  - kp           : credit points (integer)
  - structure    : teaching format, e.g. "2V+1Ü"
  - category     : subject area (Informatik, Psychologie, …)
  - other_courses: list of other study programmes that use this module

Usage
-----
  python3 scraper.py [URL] [--output FILE] [--delay SECONDS]

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
# Label keyword lists (lowercase substrings)
# ---------------------------------------------------------------------------

KP_LABELS = [
    "kreditpunkt",      # "Kreditpunkte", "Kreditpunkte (KP)"
    "leistungspunkt",
    "credit point",
    " kp",
    "(kp)",
]

STRUCTURE_LABELS = [
    "lehrform",
    "lehr- und lernform",
    "veranstaltungsform",
    "unterrichtsform",
    "sws",              # Semesterwochenstunden – contains the format
    "semesterwochenstunden",
]

COURSES_LABELS = [
    "verwendbarkeit",
    "eingesetzt in",
    "weitere studieng",
    "other program",
    "zugeordnet",
]

TITLE_LABELS = [
    "modulbezeichnung",
    "bezeichnung",
    "modulname",
    "name",
    "titel",
]

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches "Modul CS5158-KP04, CS5158" or "Modul PY2300-KP06" in a heading.
# This is what Uni Lübeck puts in its <h1>.
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
# Uses negative lookahead (?!\w) so "S" won't match inside "Semester".
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
    if m:
        return int(m.group(1))
    return None


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


# ---------------------------------------------------------------------------
# Core data extraction
# ---------------------------------------------------------------------------

def _apply_label_value(module: dict, label: str, value: str) -> None:
    """Update *module* in-place from a (label, value) pair."""
    if label_matches(label, KP_LABELS) and module["kp"] is None:
        module["kp"] = extract_kp_from_value(value)

    if label_matches(label, STRUCTURE_LABELS) and not module["structure"]:
        s = extract_structure(value)
        module["structure"] = s if s else value.strip()

    if label_matches(label, COURSES_LABELS):
        parts = re.split(r"[;,\n]+", value)
        seen = set(module["other_courses"])
        for p in parts:
            p = clean(p)
            if p and p not in seen:
                module["other_courses"].append(p)
                seen.add(p)

    if label_matches(label, TITLE_LABELS) and not module["title"]:
        module["title"] = clean(value)


def _scan_structured_markup(soup: BeautifulSoup, module: dict) -> None:
    """Walk all <table> rows and <dl> items in *soup* and apply label→value."""
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                _apply_label_value(module, clean(cells[0].get_text()), clean(cells[1].get_text()))

    for dl in soup.find_all("dl"):
        for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
            _apply_label_value(module, clean(dt.get_text()), clean(dd.get_text()))


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
    module: dict = {
        "title": "",
        "code": "",
        "kp": None,
        "structure": "",
        "other_courses": [],
        "url": url,
    }

    # ── Step 1: inspect the first heading ──────────────────────────────────
    first_heading = soup.find(re.compile(r"^h[1-4]$"))
    h1_code_part = ""
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
    if not module["title"]:
        # (a) Next heading after h1
        if first_heading:
            for sib in first_heading.find_next_siblings(re.compile(r"^h[2-6]$")):
                candidate = clean(sib.get_text())
                if candidate and not MODUL_CODE_H1_RE.match(candidate):
                    module["title"] = candidate
                    break

        # (b) Labeled row: "Modulbezeichnung", "Name", "Titel", …
        # (handled in step 3 via _apply_label_value → TITLE_LABELS)

    # ── Step 3: walk tables and dl for labeled fields ──────────────────────
    _scan_structured_markup(soup, module)

    # ── Step 4: fallback – scan page text for structure only ───────────────
    # (Don't scan full text for KP – too many false positives)
    if not module["structure"]:
        full_text = soup.get_text(" ", strip=True)
        module["structure"] = extract_structure(full_text)

    # ── Step 5: if still no title, take the <title> tag (minus site name) ──
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
        mod: dict = {
            "title": clean(heading.get_text()),
            "code": "",
            "kp": None,
            "structure": "",
            "other_courses": [],
            "url": base_url,
        }
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
                mod: dict = {
                    "title": "", "code": "", "kp": None,
                    "structure": "", "other_courses": [], "url": base_url,
                }
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

def scrape(start_url: str, delay: float = 1.0) -> list[dict]:
    print(f"Fetching index: {start_url}")
    soup = fetch(start_url)
    if soup is None:
        print("ERROR: Could not fetch start URL.", file=sys.stderr)
        sys.exit(1)

    links = find_module_links(soup, start_url)
    modules: list[dict] = []

    if links:
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
    args = parser.parse_args()

    modules = scrape(args.url, delay=args.delay)

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
