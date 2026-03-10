#!/usr/bin/env python3
"""
Print a compact structural summary of a module detail page.
Paste the output directly into the chat.
Usage: python3 debug_page.py [URL]
"""
import sys
import re
import requests
from bs4 import BeautifulSoup

URL = sys.argv[1] if len(sys.argv) > 1 else (
    "https://www2.uni-luebeck.de/studium/informatik-und-mathematik/"
    "medieninformatik/master-studiengang-medieninformatik/modulhandbuch/details/927/"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}

resp = requests.get(URL, headers=HEADERS, timeout=20)
print(f"HTTP {resp.status_code}  url={URL}\n")
if resp.status_code != 200:
    sys.exit(1)

soup = BeautifulSoup(resp.text, "lxml")

KNOWN = ["dauer", "angebotsturnus", "leistungspunkt", "studiengang",
         "lehrveranstaltung", "workload", "lehrinhalt", "qualifikation",
         "vergabe", "voraussetzung", "modulverantwortlich", "lehrende",
         "literatur", "sprache", "bemerkung", "letzte"]

print("=" * 60)
print("ELEMENTS CONTAINING KNOWN LABELS (leaf nodes + parent chain)")
print("=" * 60)
for kw in KNOWN:
    hits = [e for e in soup.find_all(True)
            if kw in e.get_text().lower() and not e.find(True)]
    if hits:
        print(f"\n[{kw}]")
        for e in hits[:3]:
            txt = e.get_text().strip()[:60].replace("\n", " ")
            cls = e.get("class", "")
            parents = []
            p = e.parent
            while p and p.name not in ("body", "[document]", None) and len(parents) < 5:
                pcls = ".".join(p.get("class", []))
                parents.append(f"{p.name}{'.' + pcls if pcls else ''}")
                p = p.parent
            print(f"  <{e.name}{'.' + '.'.join(cls) if cls else ''}> {repr(txt)}")
            print(f"    in: {' > '.join(reversed(parents))}")

print("\n" + "=" * 60)
print("ALL DL BLOCKS (dt → dd pairs)")
print("=" * 60)
for i, dl in enumerate(soup.find_all("dl")):
    print(f"\n-- dl #{i} --")
    for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
        dt_txt = dt.get_text().strip()[:50]
        dd_txt = dd.get_text().strip()[:80].replace("\n", " | ")
        print(f"  dt: {repr(dt_txt)}")
        print(f"  dd: {repr(dd_txt)}")

print("\n" + "=" * 60)
print("HEADINGS (h1-h5) IN MAIN CONTENT")
print("=" * 60)
main = soup.find("main") or soup.find(id=re.compile(r"content|main", re.I)) or soup
for h in main.find_all(re.compile(r"^h[1-5]$")):
    txt = h.get_text().strip()[:80]
    cls = ".".join(h.get("class", []))
    print(f"  <{h.name}{'.' + cls if cls else ''}> {repr(txt)}")
    # Show immediately following sibling
    sib = h.find_next_sibling()
    if sib:
        stxt = sib.get_text().strip()[:80].replace("\n", " | ")
        scls = ".".join(sib.get("class", []))
        print(f"    next: <{sib.name}{'.' + scls if scls else ''}> {repr(stxt)}")

print("\n" + "=" * 60)
print("FIRST 30 TAGS INSIDE MAIN CONTENT (name + class)")
print("=" * 60)
for tag in list(main.find_all(True))[:30]:
    cls = ".".join(tag.get("class", []))
    txt = tag.get_text().strip()[:40].replace("\n", " ")
    print(f"  <{tag.name}{'.' + cls if cls else ''}> {repr(txt)}")
