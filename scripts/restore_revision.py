"""Restore one page's content from its newest WordPress revision saved before a given UTC time.

Dry run (default) lists the recent revisions and names the one it would restore.
--apply writes that revision's content back and reads the page again to confirm the save.
Nothing is deleted; WordPress keeps the current content as a new revision.
"""
import argparse
import sys
from datetime import datetime

from wp import annotate, api, config, request, session, sha256, summary


def parse_utc(text):
    return datetime.fromisoformat(text.strip().replace("Z", ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--before", required=True, help="UTC time, e.g. 2026-10-20T10:47:00")
    ap.add_argument("--min-chars", type=int, default=1000, help="skip revisions shorter than this")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    page_id = config()["pages"][args.page]
    before = parse_utc(args.before)
    s = session()

    live = request(s, "GET", f"{api()}/pages/{page_id}", params={"context": "edit"})
    live.raise_for_status()
    live_raw = live.json()["content"]["raw"]

    chosen, rows, page_no = None, [], 1
    while chosen is None and page_no <= 5:
        r = request(s, "GET", f"{api()}/pages/{page_id}/revisions",
                    params={"context": "edit", "per_page": 10, "page": page_no,
                            "_fields": "id,date_gmt,modified_gmt,author,content"})
        if r.status_code == 400 and page_no > 1:
            break
        r.raise_for_status()
        items = r.json()
        if not items:
            break
        for rev in items:
            raw = rev["content"]["raw"]
            when = parse_utc(rev["modified_gmt"] or rev["date_gmt"])
            rows.append(f"{rev['id']} {rev['modified_gmt']} {len(raw)} chars")
            if chosen is None and when < before and len(raw) >= args.min_chars:
                chosen = (rev, raw)
        page_no += 1

    annotate("notice", f"Revisions {args.page}", f"live: {len(live_raw)} chars; newest revisions: " + "; ".join(rows[:12]))
    if chosen is None:
        annotate("error", f"Restore {args.page}", f"No revision before {args.before} with at least {args.min_chars} chars.")
        sys.exit(1)

    rev, raw = chosen
    msg = (f"revision {rev['id']} saved {rev['modified_gmt']} UTC, {len(raw)} chars, sha256 {sha256(raw)[:12]}; "
           f"live now {len(live_raw)} chars")
    if not args.apply:
        annotate("notice", f"Restore {args.page} (dry run)", "Would restore " + msg)
        summary(f"### Restore {args.page} (dry run)\n\nWould restore {msg}.")
        return

    again = request(s, "GET", f"{api()}/pages/{page_id}", params={"context": "edit"}).json()["content"]["raw"]
    if again != live_raw:
        annotate("error", f"Restore {args.page}", "Page changed while this job ran; nothing written.")
        sys.exit(1)
    w = request(s, "POST", f"{api()}/pages/{page_id}", json={"content": raw})
    if w.status_code in (401, 403):
        annotate("error", f"Restore {args.page}", f"Write refused ({w.status_code}).")
        sys.exit(1)
    w.raise_for_status()
    saved = request(s, "GET", f"{api()}/pages/{page_id}", params={"context": "edit"}).json()["content"]["raw"]
    if saved == raw:
        annotate("notice", f"Restore {args.page}", "Restored and read back identical: " + msg)
        summary(f"### Restore {args.page}\n\nRestored {msg}. Read-back identical.")
    else:
        annotate("error", f"Restore {args.page}",
                 f"Written, but read-back differs: saved {len(saved)} chars vs revision {len(raw)} chars. " + msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
