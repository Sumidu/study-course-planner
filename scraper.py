#!/usr/bin/env python3
"""
Uni Lübeck Modulhandbuch Scraper
=================================
Scrapes a module handbook page and produces a JSON file with:
  - title        : module name
  - code         : module code / number (if found)
  - kp           : credit points (integer)
  - structure    : teaching format, e.g. "2V/1Ü" or "2V+1Ü"
  - other_courses: list of other study programmes that use this module

Usage
-----
  python3 scraper.py [URL] [--output FILE] [--delay SECONDS]

Defaults
--------
  URL     = https://www2.uni-luebeck.de/studium/informatik-und-mathematik/
            medieninformatik/master-studiengang-medieninformatik/modulhandbuch/
  output  = modules.json
  delay   = 1.0   (seconds between requests, be polite to the server)
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
# Constants
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

# German labels used on the page, mapped to our field names.
# Keys are lowercase substrings to match flexibly.
KP_LABELS = [
    "kreditpunkt",  # "Kreditpunkte", "Kreditpunkte (KP)"
    "leistungspunkt",
    "credit",
    " kp",
    "(kp)",
]

STRUCTURE_LABELS = [
    "lehrform",
    "lehr- und lernform",
    "sws",
    "semesterwochenstunden",
    "veranstaltungsform",
    "unterrichtsform",
]

COURSES_LABELS = [
    "verwendbarkeit",
    "einsatz",
    "studiengang",
    "eingesetzt",
    "zugeordnet",
    "genutzt",
    "other program",
    "weitere studieng",
]

# Regex patterns ---------------------------------------------------------------

# Matches things like "4", "4,0", "4.0"
KP_NUMBER_RE = re.compile(r"\b(\d+(?:[.,]\d+)?)\s*(?:KP|CP|ECTS|Kreditpunkte?)?\b", re.I)

# Matches teaching formats: "2V+1Ü", "2V/1Ü", "4V", "2S", "3V+1Ü+1P", …
STRUCTURE_RE = re.compile(r"\d+\s*[VvSsPpÜü][A-Za-zÜüÖöÄä]*(?:\s*[+/]\s*\d+\s*[VvSsPpÜü][A-Za-zÜüÖöÄä]*)*")

# Module-page link heuristic – picks up URLs that look like a module sub-page
MODULE_HREF_RE = re.compile(r"/modul(?:e|handbuch)?/|/module\b", re.I)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch(url: str, retries: int = 3) -> BeautifulSoup | None:
    """Fetch *url* and return a BeautifulSoup object, or None on failure."""
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
# Text extraction helpers
# ---------------------------------------------------------------------------

def clean(text: str) -> str:
    return " ".join(text.split())


def extract_kp(text: str) -> int | None:
    """Return the first integer KP value found in *text*, or None."""
    match = KP_NUMBER_RE.search(text)
    if match:
        raw = match.group(1).replace(",", ".")
        try:
            return int(float(raw))
        except ValueError:
            pass
    return None


def extract_structure(text: str) -> str:
    """Return the first teaching-format token found in *text*, or ''."""
    match = STRUCTURE_RE.search(text)
    return match.group(0).strip() if match else ""


def label_matches(label: str, candidates: list[str]) -> bool:
    label_lower = label.lower()
    return any(c in label_lower for c in candidates)


# ---------------------------------------------------------------------------
# Parser: single module page
# ---------------------------------------------------------------------------

def parse_module_page(soup: BeautifulSoup, url: str) -> dict:
    """
    Extract module data from a dedicated module sub-page.

    Strategy:
      1. Find the page title (h1 / h2).
      2. Walk every <table> and <dl> looking for labelled rows.
      3. Fall back to full-text heuristics.
    """
    module: dict = {
        "title": "",
        "code": "",
        "kp": None,
        "structure": "",
        "other_courses": [],
        "url": url,
    }

    # ── title ──────────────────────────────────────────────────────────────
    for tag in ("h1", "h2", "h3"):
        heading = soup.find(tag)
        if heading:
            module["title"] = clean(heading.get_text())
            break

    # ── labelled rows in tables ────────────────────────────────────────────
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue
            label = clean(cells[0].get_text())
            value = clean(cells[1].get_text())
            _apply_label_value(module, label, value)

    # ── definition lists (<dl><dt>…<dd>…</dl>) ────────────────────────────
    for dl in soup.find_all("dl"):
        terms = dl.find_all("dt")
        defs  = dl.find_all("dd")
        for dt, dd in zip(terms, defs):
            label = clean(dt.get_text())
            value = clean(dd.get_text())
            _apply_label_value(module, label, value)

    # ── fallback: scan all paragraphs / list items ─────────────────────────
    if module["kp"] is None or not module["structure"]:
        full_text = soup.get_text(" ", strip=True)
        if module["kp"] is None:
            module["kp"] = extract_kp(full_text)
        if not module["structure"]:
            module["structure"] = extract_structure(full_text)

    return module


def _apply_label_value(module: dict, label: str, value: str) -> None:
    """Update *module* dict from a (label, value) pair found on the page."""
    if label_matches(label, KP_LABELS) and module["kp"] is None:
        module["kp"] = extract_kp(value)

    if label_matches(label, STRUCTURE_LABELS) and not module["structure"]:
        module["structure"] = extract_structure(value) or value

    if label_matches(label, COURSES_LABELS):
        # Value may be a comma/semicolon/newline-separated list
        courses = re.split(r"[;,\n]+", value)
        seen = set(module["other_courses"])
        for c in courses:
            c = clean(c)
            if c and c not in seen:
                module["other_courses"].append(c)
                seen.add(c)

    # Module code heuristic: "Modulnummer", "Modul-Nr", "Kennzeichen", …
    if re.search(r"modul.?(nummer|nr|code|kennung|kürzel)", label, re.I) and not module["code"]:
        module["code"] = clean(value)


# ---------------------------------------------------------------------------
# Parser: index / listing page
# ---------------------------------------------------------------------------

def find_module_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """
    Return a de-duplicated list of absolute URLs that look like module pages.

    Tries three heuristics (in order of reliability):
      1. Links whose href path contains "modul"
      2. All links inside the main content area
      3. Any <a> tag pointing to a same-host page
    """
    base_host = urlparse(base_url).netloc
    found: list[str] = []
    seen: set[str] = set()

    def add(href: str) -> None:
        abs_url = urljoin(base_url, href)
        if abs_url not in seen and urlparse(abs_url).netloc == base_host:
            seen.add(abs_url)
            found.append(abs_url)

    # 1. Links matching module-URL patterns
    for a in soup.find_all("a", href=MODULE_HREF_RE):
        add(a["href"])

    # 2. Links inside typical content containers
    if not found:
        content = (
            soup.find("main")
            or soup.find(id=re.compile(r"content|main|body", re.I))
            or soup.find(class_=re.compile(r"content|main|body|typo3", re.I))
            or soup
        )
        for a in content.find_all("a", href=True):
            href = a["href"]
            if href and not href.startswith(("#", "mailto:", "tel:")):
                add(href)

    return found


def parse_index_page(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """
    Try to extract module data directly from a single listing page.

    This handles pages where every module is an accordion, card, or section
    on the same page rather than having individual sub-pages.
    """
    modules: list[dict] = []

    # ── strategy A: one <article> / <section> per module ──────────────────
    candidates = soup.find_all(["article", "section"])
    if not candidates:
        # Fallback: look for repeated <div class="…module…"> or similar
        candidates = soup.find_all("div", class_=re.compile(r"modul|course|lehrveranstaltung", re.I))

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
        text = block.get_text(" ", strip=True)
        if mod["kp"] is None:
            mod["kp"] = extract_kp(text)
        if not mod["structure"]:
            mod["structure"] = extract_structure(text)

        # Labelled rows inside this block
        for row in block.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                _apply_label_value(mod, clean(cells[0].get_text()), clean(cells[1].get_text()))
        for dl in block.find_all("dl"):
            for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
                _apply_label_value(mod, clean(dt.get_text()), clean(dd.get_text()))

        if mod["title"]:
            modules.append(mod)

    # ── strategy B: one big table (one row per module) ─────────────────────
    if not modules:
        for table in soup.find_all("table"):
            headers = [clean(th.get_text()).lower() for th in table.find_all("th")]
            if not headers:
                continue
            # Map column index → field
            col_map: dict[int, str] = {}
            for i, h in enumerate(headers):
                if any(k in h for k in ["titel", "name", "modul"]):
                    col_map[i] = "title"
                elif any(k in h for k in KP_LABELS):
                    col_map[i] = "kp_raw"
                elif any(k in h for k in STRUCTURE_LABELS):
                    col_map[i] = "structure_raw"
                elif any(k in h for k in COURSES_LABELS):
                    col_map[i] = "courses_raw"
                elif any(k in h for k in ["code", "nummer", "nr.", "kennung"]):
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
                        mod["kp"] = extract_kp(val)
                    elif field == "structure_raw":
                        mod["structure"] = extract_structure(val) or val
                    elif field == "courses_raw":
                        mod["other_courses"] = [c for c in re.split(r"[;,\n]+", val) if c.strip()]
                if mod["title"]:
                    modules.append(mod)

    return modules


# ---------------------------------------------------------------------------
# Main scraping logic
# ---------------------------------------------------------------------------

def scrape(start_url: str, delay: float = 1.0) -> list[dict]:
    print(f"Fetching index page: {start_url}")
    soup = fetch(start_url)
    if soup is None:
        print("ERROR: Could not fetch the start URL.", file=sys.stderr)
        sys.exit(1)

    # 1. Look for links to individual module sub-pages
    links = find_module_links(soup, start_url)
    # Exclude the start URL itself and obvious non-module URLs
    links = [
        url for url in links
        if url.rstrip("/") != start_url.rstrip("/")
        and not re.search(r"\.(pdf|docx?|xlsx?|png|jpg|svg)$", url, re.I)
    ]

    modules: list[dict] = []

    if links:
        print(f"Found {len(links)} module sub-page link(s). Fetching each …")
        for i, url in enumerate(links, 1):
            print(f"  [{i}/{len(links)}] {url}")
            sub_soup = fetch(url)
            if sub_soup:
                mod = parse_module_page(sub_soup, url)
                if mod["title"]:
                    modules.append(mod)
            if i < len(links):
                time.sleep(delay)
    else:
        print("No sub-page links found – parsing current page directly.")
        modules = parse_index_page(soup, start_url)

    # Remove entries where we couldn't find a title at all
    modules = [m for m in modules if m["title"]]

    # Normalise: ensure kp is int or null, structure is a string
    for m in modules:
        if m["kp"] is not None:
            m["kp"] = int(m["kp"])
        m["structure"] = m["structure"] or ""

    return modules


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape a Uni Lübeck Modulhandbuch page and save modules as JSON."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=DEFAULT_URL,
        help="URL of the module handbook index page (default: Medieninformatik Master)",
    )
    parser.add_argument(
        "--output", "-o",
        default="modules.json",
        help="Output JSON file path (default: modules.json)",
    )
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=1.0,
        help="Delay in seconds between HTTP requests (default: 1.0)",
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

    print(f"\nDone. Extracted {len(modules)} module(s) → {args.output}")

    # Quick preview of first 3 modules
    if modules:
        print("\nPreview (first 3):")
        for m in modules[:3]:
            print(
                f"  • {m['title']} | KP: {m['kp']} | "
                f"Structure: {m['structure'] or '—'} | "
                f"Other courses: {len(m['other_courses'])}"
            )


if __name__ == "__main__":
    main()
