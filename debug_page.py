#!/usr/bin/env python3
"""
Fetch a module detail page and print the HTML structure around known labels.
Usage: python3 debug_page.py [URL]
"""
import sys
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
print(f"HTTP {resp.status_code}")
if resp.status_code != 200:
    sys.exit(1)

soup = BeautifulSoup(resp.text, "lxml")

# 1. Show all tag types used on the page (frequency)
from collections import Counter
tag_counts = Counter(tag.name for tag in soup.find_all(True))
print("\nTag frequency:")
for tag, count in tag_counts.most_common(20):
    print(f"  {tag:15s} {count}")

# 2. Show all <dl> blocks
print("\n\n=== DL blocks ===")
for i, dl in enumerate(soup.find_all("dl")):
    print(f"\n-- dl #{i} --")
    print(dl.prettify()[:2000])

# 3. Show all <table> blocks
print("\n\n=== TABLE blocks ===")
for i, table in enumerate(soup.find_all("table")):
    print(f"\n-- table #{i} --")
    print(table.prettify()[:2000])

# 4. Find any element whose text contains known keywords
KEYWORDS = ["Dauer", "Leistungspunkt", "Lehrveranstaltung", "Studiengang", "Workload", "Lehrinhalt"]
print("\n\n=== Elements containing keywords ===")
for kw in KEYWORDS:
    elems = [e for e in soup.find_all(True) if kw.lower() in e.get_text().lower() and not e.find(True)]
    if elems:
        print(f"\n'{kw}' found in leaf elements:")
        for e in elems[:5]:
            print(f"  <{e.name} class={e.get('class')}> {repr(e.get_text()[:80])}")
            # Show parent chain
            parents = []
            p = e.parent
            while p and p.name not in ("body", "[document]") and len(parents) < 4:
                parents.append(f"<{p.name} class={p.get('class')}>")
                p = p.parent
            print(f"    parents: {' > '.join(reversed(parents))}")

# 5. Dump main content area HTML (first 3000 chars)
print("\n\n=== Main content HTML (first 3000 chars) ===")
main = (
    soup.find("main")
    or soup.find(id=lambda x: x and any(k in x.lower() for k in ["content", "main"]))
    or soup.find(class_=lambda x: x and any(k in " ".join(x).lower() for k in ["content", "main"]))
)
if main:
    print(main.prettify()[:3000])
else:
    print("No <main> found. Dumping <body> start:")
    body = soup.find("body")
    if body:
        print(body.prettify()[:3000])
