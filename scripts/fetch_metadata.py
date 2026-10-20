"""Fetch bibliographic metadata for every DOI in site/data/publications.csv from Crossref and OpenAlex.

Writes site/data/metadata/works.json (public bibliographic fields) and site/data/metadata/abstracts.enc
(abstracts, encrypted with abstracts-public-key.pem; abstracts are used for tagging only and are not published).
Runs in GitHub Actions, where these APIs are reachable.
"""
import base64
import csv
import json
import re
import sys
import time
from pathlib import Path

import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "metadata"
UA = {"User-Agent": "alivisatos-lab-website metadata (https://github.com/DylanBian/alivisatos-lab-website)"}
OA_SELECT = ("id,doi,title,publication_year,publication_date,type,type_crossref,primary_location,open_access,"
             "best_oa_location,authorships,biblio,cited_by_count,abstract_inverted_index,keywords,primary_topic,is_retracted")
CR_FIELDS = ["type", "subtype", "title", "container-title", "short-container-title", "volume", "issue", "page",
             "article-number", "issued", "published-print", "published-online", "license", "author", "update-to",
             "relation", "ISSN", "publisher", "is-referenced-by-count"]


def dois():
    out = []
    for row in csv.DictReader((ROOT / "site/data/publications.csv").open()):
        m = re.search(r"doi\.org/(10\.[^\s?#]+)", row["url"])
        if m:
            out.append((row["id"], m.group(1).lower()))
    return out


def get(url, **kw):
    for attempt in range(5):
        try:
            r = requests.get(url, headers=UA, timeout=40, **kw)
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 * (attempt + 1))
            continue
        return r
    return None


def abstract_from_index(index):
    if not index:
        return ""
    words = {}
    for word, positions in index.items():
        for p in positions:
            words[p] = word
    return " ".join(words[i] for i in sorted(words))


def main():
    items = dois()
    print(f"{len(items)} DOIs")
    openalex, crossref, abstracts = {}, {}, {}
    doi_list = [d for _, d in items]
    for i in range(0, len(doi_list), 40):
        batch = doi_list[i:i + 40]
        r = get("https://api.openalex.org/works", params={"filter": "doi:" + "|".join(batch), "per-page": 50, "select": OA_SELECT})
        if r is None or r.status_code != 200:
            print("OpenAlex batch failed", i, r.status_code if r else None)
            continue
        for w in r.json().get("results", []):
            doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
            text = abstract_from_index(w.pop("abstract_inverted_index", None))
            if text:
                abstracts.setdefault(doi, {})["openalex"] = text
            openalex[doi] = w
        time.sleep(0.2)
    for n, doi in enumerate(doi_list, 1):
        r = get(f"https://api.crossref.org/works/{requests.utils.quote(doi, safe='/')}")
        if r is None or r.status_code != 200:
            crossref[doi] = {"error": r.status_code if r is not None else "no response"}
            continue
        msg = r.json()["message"]
        if msg.get("abstract"):
            abstracts.setdefault(doi, {})["crossref"] = msg["abstract"]
        crossref[doi] = {k: msg.get(k) for k in CR_FIELDS if msg.get(k) is not None}
        if n % 50 == 0:
            print(f"Crossref {n}/{len(doi_list)}")
        time.sleep(0.12)
    works = {doi: {"row_id": rid, "crossref": crossref.get(doi), "openalex": openalex.get(doi)} for rid, doi in items}
    (OUT / "works.json").write_text(json.dumps(works, ensure_ascii=False, indent=1, sort_keys=True))
    key = Fernet.generate_key()
    token = Fernet(key).encrypt(json.dumps(abstracts, ensure_ascii=False).encode())
    pub = serialization.load_pem_public_key((OUT / "abstracts-public-key.pem").read_bytes())
    wrapped = pub.encrypt(key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    (OUT / "abstracts.enc").write_text(json.dumps({"key": base64.b64encode(wrapped).decode(), "data": token.decode()}))
    have = sum(1 for d in doi_list if d in abstracts)
    summary = (f"Metadata: {len(items)} DOIs; Crossref ok {sum(1 for v in crossref.values() if 'error' not in v)}; "
               f"OpenAlex ok {len(openalex)}; abstracts {have}")
    print(summary)
    print(f"::notice title=Metadata::{summary}")


if __name__ == "__main__":
    sys.exit(main())
