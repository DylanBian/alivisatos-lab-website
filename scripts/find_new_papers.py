"""Find group papers that are not yet on the Publications page (OpenAlex + Crossref). Never writes to WordPress.

The OpenAlex author is chosen by overlap with the DOIs already in site/data/publications.csv, so no id has to be
typed in by hand; the run reports the overlap. Output: site/drafts/new_papers.yaml for review.
"""
import csv
import json
import re
import sys
import urllib.parse
from datetime import date
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "alivisatos-lab-website new-paper check (https://github.com/DylanBian/alivisatos-lab-website)"}


def known():
    dois, years = set(), []
    for row in csv.DictReader((ROOT / "site/data/publications.csv").open()):
        m = re.search(r"doi\.org/(10\.[^\s?#]+)", row["url"])
        if m:
            dois.add(urllib.parse.unquote(m.group(1)).lower())
        if row["year"].isdigit():
            years.append(int(row["year"]))
    return dois, max(years)


def get(url, **params):
    r = requests.get(url, params=params, headers=UA, timeout=40)
    r.raise_for_status()
    return r.json()


def main():
    dois, last_year = known()
    candidates = get("https://api.openalex.org/authors", search="Alivisatos", per_page=25)["results"]
    best, best_overlap = None, 0
    for a in candidates:
        if "alivisatos" not in a["display_name"].lower():
            continue
        works = get("https://api.openalex.org/works", filter=f"author.id:{a['id'].split('/')[-1]}", per_page=200, select="doi")["results"]
        overlap = sum(1 for w in works if (w.get("doi") or "").replace("https://doi.org/", "").lower() in dois)
        if overlap > best_overlap:
            best, best_overlap = a, overlap
    if not best:
        sys.exit("No OpenAlex author overlaps with the current list.")
    author = best["id"].split("/")[-1]
    since = f"{last_year - 1}-01-01"
    new = []
    cursor = "*"
    while cursor:
        page = get("https://api.openalex.org/works", filter=f"author.id:{author},from_publication_date:{since}",
                   per_page=100, cursor=cursor, select="doi,title,publication_date,type,primary_location,authorships")
        for w in page["results"]:
            doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
            if not doi or doi in dois or w.get("type") in ("preprint", "erratum", "paratext", "peer-review"):
                continue
            new.append({"doi": doi, "title": w.get("title"), "publication_date": w.get("publication_date"),
                        "journal": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                        "authors": [x["author"]["display_name"] for x in w.get("authorships", [])],
                        "status": "draft"})
        cursor = page["meta"].get("next_cursor")
    out = ROOT / "site/drafts"
    out.mkdir(exist_ok=True)
    header = (f"# New-paper candidates from OpenAlex author {author} ({best['display_name']}; overlap with the current list: "
              f"{best_overlap} DOIs), published since {since}, checked {date.today()}.\n"
              "# Review each entry; confirmed papers go into site/data/publications.csv with Crossref citation fields.\n")
    (out / "new_papers.yaml").write_text(header + yaml.safe_dump(new, allow_unicode=True, sort_keys=False, width=140))
    msg = f"{len(new)} candidate(s) not on the Publications page; author {author}, overlap {best_overlap}"
    print(msg)
    print(f"::notice title=New papers::{msg}")


if __name__ == "__main__":
    main()
