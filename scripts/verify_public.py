"""Check what an anonymous visitor sees, page by page, using plain URLs (no query string, no cookies).

For each page it also reads the anonymous REST copy of the same page. That separates two problems:
  - text is wrong in the database (REST shows it)        -> FAIL
  - database is right, plain URL still shows old content  -> STALE CACHE
Exit code: 0 all pass; 1 any FAIL; 2 only STALE CACHE (unless --no-fail).
"""
import argparse
import os
import sys

from wp import api, base_url, config, load_dotenv, request, session, summary

CACHE_HEADERS = ["cache-control", "age", "x-cache", "server"]


def hits(text, forbidden):
    low = text.lower()
    return [f for f in forbidden if f.lower() in low]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fail", action="store_true", help="report only; always exit 0")
    args = ap.parse_args()
    cfg = config()
    forbidden = cfg["forbidden_strings"]
    s = session(auth=False)
    s.headers["Cache-Control"] = "no-cache"  # a request hint only; caches may ignore it
    # Database copy: anonymous REST responses can be cached by the proxy too, so use the
    # Application Password when it is available (authenticated requests bypass the cache).
    load_dotenv()
    if os.environ.get("WP_USER") and os.environ.get("WP_APP_PASSWORD"):
        db = session(auth=True)
        db_note = "authenticated REST"
    else:
        db = s
        db_note = "anonymous REST (may be cached)"
    rows, fail, stale = [], False, False

    for key, path in cfg["paths"].items():
        r = request(s, "GET", base_url() + path, allow_redirects=True)
        page_hits = hits(r.text, forbidden) if r.status_code == 200 else []
        target = cfg["pages"][key]
        if isinstance(target, int):
            rr = request(db, "GET", f"{api()}/pages/{target}")
            db_text = rr.json().get("content", {}).get("rendered", "") if rr.ok else ""
        else:
            rr = request(db, "GET", f"{api()}/pages", params={"slug": target})
            items = rr.json() if rr.ok else []
            db_text = items[0]["content"]["rendered"] if items else ""
        db_hits = hits(db_text, forbidden)
        if r.status_code != 200 or db_hits:
            verdict, fail = "FAIL", True
        elif page_hits:
            verdict, stale = "STALE CACHE", True
        else:
            verdict = "pass"
        hdr = " · ".join(f"{h}: {r.headers.get(h, '-')}" for h in CACHE_HEADERS)
        rows.append(f"| {path} | {r.status_code} | {verdict} | {', '.join(db_hits) or '-'} | "
                    f"{', '.join(page_hits) or '-'} | {hdr} |")

    for key, path in cfg.get("private_pages", {}).items():
        r = request(s, "GET", base_url() + path, allow_redirects=True)
        rr = request(s, "GET", f"{api()}/pages", params={"slug": key, "status": "publish"})
        listed = bool(rr.ok and rr.json())
        if listed:
            verdict, fail = "FAIL (public in REST)", True
        elif r.status_code != 404:
            verdict, stale = f"STALE CACHE (HTTP {r.status_code})", True
        else:
            verdict = "pass (404)"
        hdr = " · ".join(f"{h}: {r.headers.get(h, '-')}" for h in CACHE_HEADERS)
        rows.append(f"| {path} | {r.status_code} | {verdict} | - | - | {hdr} |")

    summary(f"### Public check (plain URLs, anonymous; database via {db_note})\n\n"
            "| URL | HTTP | Result | Forbidden text in database | Forbidden text served | Cache headers |\n"
            "|---|---|---|---|---|---|\n" + "\n".join(rows))
    if args.no_fail:
        return
    if fail:
        sys.exit(1)
    if stale:
        summary("> The database is correct but some plain URLs still serve old pages. Clear the page cache or ask "
                "UChicago Voices support to purge alivisatoslab.uchicago.edu.")
        sys.exit(2)


if __name__ == "__main__":
    main()
