"""Collect identity-linked career data for each alumnus. Read-only; changes nothing on the website.

Identity comes from the group's own papers: an alumnus is matched to the OpenAlex author ids that appear on papers in
site/data/publications.csv (authorships stored in site/data/metadata/works.json) under the same name. For each matched
id the script reads the OpenAlex author record, the affiliations on that author's five most recent works, and, when the
id carries an ORCID, the public ORCID employments, educations and the DOIs on the record (to confirm that the ORCID
record lists a group paper).

Output: site/data/metadata/alumni_sources.enc, encrypted with abstracts-public-key.pem. The file is for reviewing
the Alumni page and is not published.
"""
import base64
import json
import re
import sys
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

import requests
import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site/data"
OUT = DATA / "metadata"
UA = {"User-Agent": "alivisatos-lab-website alumni check (https://github.com/DylanBian/alivisatos-lab-website)"}


def get(url, accept="application/json", **params):
    for attempt in range(5):
        try:
            r = requests.get(url, params=params, headers={**UA, "Accept": accept}, timeout=40)
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code != 200:
            return None
        return r.json()
    return None


def fold(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("oe", "o").replace("ue", "u").replace("ae", "a")
    return re.sub(r"[^a-z ]", " ", s.replace(".", " ").replace("-", " "))


def tokens(s):
    return fold(s).split()


def name_forms(name):
    alts = re.findall(r'[("“]([^)"”]+)[)"”]', name)
    base = re.sub(r'[("“][^)"”]+[)"”]', " ", name)
    t = tokens(base)
    firsts = {t[0]} | {tokens(a)[0] for a in alts if tokens(a)}
    if len(t) >= 3:
        firsts.add(t[1])
    lasts = {t[-1]}
    if len(t) >= 3:
        lasts |= {t[-2], t[-2] + t[-1]}
    return firsts, lasts


def first_ok(f, firsts):
    if f in firsts:
        return 2
    if len(f) >= 3 and any(len(x) >= 3 and (x.startswith(f) or f.startswith(x)) for x in firsts):
        return 2
    if len(f) == 1 and any(x.startswith(f) for x in firsts):
        return 1
    return 0


def coauthor_index():
    works = json.loads((OUT / "works.json").read_text())
    idx = defaultdict(lambda: {"names": set(), "years": [], "dois": [], "orcid": None})
    for doi, w in works.items():
        oa = w.get("openalex") or {}
        for a in oa.get("authorships", []):
            aid = (a["author"].get("id") or "").rsplit("/", 1)[-1]
            if not aid:
                continue
            e = idx[aid]
            e["names"].add(a["author"]["display_name"])
            if a.get("raw_author_name"):
                e["names"].add(a["raw_author_name"])
            e["orcid"] = e["orcid"] or a["author"].get("orcid")
            e["years"].append(oa.get("publication_year"))
            e["dois"].append(doi)
    return idx, set(works)


def match(name, idx):
    firsts, lasts = name_forms(name)
    found = []
    for aid, e in idx.items():
        score = 0
        for n in e["names"]:
            t = tokens(n)
            if len(t) < 2 or not (lasts & {t[-1], t[-2] + t[-1]}):
                continue
            score = max([score] + [first_ok(f, firsts) for f in t[:-1]])
        if score:
            years = [y for y in e["years"] if y]
            found.append({"openalex": aid, "score": score, "names": sorted(e["names"]), "orcid": e["orcid"],
                          "group_papers": len(e["dois"]), "group_years": [min(years), max(years)] if years else []})
    return sorted(found, key=lambda x: (-x["score"], -x["group_papers"]))


def ym(d):
    parts = [((d or {}).get(p) or {}).get("value") or "" for p in ("year", "month")]
    return "-".join(x for x in parts if x)


def orcid_items(orcid, section, key):
    data = get(f"https://pub.orcid.org/v3.0/{orcid}/{section}") or {}
    out = []
    for group in data.get("affiliation-group", []):
        for s in group.get("summaries", []):
            x = s.get(key) or {}
            org = x.get("organization") or {}
            out.append({"org": org.get("name"), "city": (org.get("address") or {}).get("city"),
                        "department": x.get("department-name"), "role": x.get("role-title"),
                        "start": ym(x.get("start-date")), "end": ym(x.get("end-date")),
                        "modified": ((x.get("last-modified-date") or {}).get("value"))})
    return out


def orcid_record(orcid, group_dois):
    oid = orcid.rsplit("/", 1)[-1]
    works = get(f"https://pub.orcid.org/v3.0/{oid}/works") or {}
    dois = set()
    for g in works.get("group", []):
        for ext in (g.get("external-ids") or {}).get("external-id", []):
            if ext.get("external-id-type") == "doi":
                dois.add(ext.get("external-id-value", "").lower())
    return {"orcid": oid,
            "employments": orcid_items(oid, "employments", "employment-summary"),
            "educations": orcid_items(oid, "educations", "education-summary"),
            "works_on_record": len(dois),
            "group_papers_on_record": sorted(dois & group_dois)[:5]}


def openalex_author(aid):
    a = get(f"https://api.openalex.org/authors/{aid}") or {}
    recent = get("https://api.openalex.org/works", filter=f"author.id:{aid}", sort="publication_date:desc",
                 per_page=5, select="doi,title,publication_date,authorships") or {}
    latest = []
    for w in recent.get("results", []):
        for au in w.get("authorships", []):
            if (au["author"].get("id") or "").endswith(aid):
                latest.append({"date": w.get("publication_date"), "doi": w.get("doi"), "title": (w.get("title") or "")[:120],
                               "affiliations": au.get("raw_affiliation_strings") or
                               [i["display_name"] for i in au.get("institutions", [])]})
    return {"display_name": a.get("display_name"), "orcid": a.get("orcid"), "works_count": a.get("works_count"),
            "last_known": [i.get("display_name") for i in a.get("last_known_institutions") or []],
            "affiliations": [{"institution": x["institution"]["display_name"], "years": [min(x["years"]), max(x["years"])]}
                             for x in (a.get("affiliations") or [])[:12] if x.get("years")],
            "latest_works": latest}


def main():
    idx, group_dois = coauthor_index()
    alumni = yaml.safe_load((DATA / "alumni.yaml").read_text())
    report, n_ids, n_orcid = {}, 0, 0
    for i, r in enumerate(alumni, 1):
        entry = {"roles": r.get("roles"), "listed": f"{r.get('title', '')} · {r.get('org', '')}", "candidates": []}
        for c in match(r["name"], idx)[:3]:
            c["author"] = openalex_author(c["openalex"])
            n_ids += 1
            orcid = c["orcid"] or c["author"].get("orcid")
            if orcid:
                c["orcid_record"] = orcid_record(orcid, group_dois)
                n_orcid += 1
            entry["candidates"].append(c)
            time.sleep(0.2)
        report[r["name"]] = entry
        if i % 20 == 0:
            print(f"{i}/{len(alumni)}")
    key = Fernet.generate_key()
    token = Fernet(key).encrypt(json.dumps(report, ensure_ascii=False).encode())
    pub = serialization.load_pem_public_key((OUT / "abstracts-public-key.pem").read_bytes())
    wrapped = pub.encrypt(key, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    (OUT / "alumni_sources.enc").write_text(json.dumps({"key": base64.b64encode(wrapped).decode(), "data": token.decode()}))
    matched = sum(1 for e in report.values() if e["candidates"])
    msg = f"{len(alumni)} alumni; {matched} matched to co-author ids on group papers; {n_ids} ids read; {n_orcid} ORCID records"
    print(msg)
    print(f"::notice title=Alumni sources::{msg}")


if __name__ == "__main__":
    sys.exit(main())
