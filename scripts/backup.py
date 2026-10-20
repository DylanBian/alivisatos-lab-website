"""Snapshot the raw content of every configured page (and private pages) before any write."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from wp import config, resolve_page, session, sha256, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="backup")
    args = ap.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.out) / stamp
    out.mkdir(parents=True, exist_ok=True)
    s = session()
    cfg = config()
    keys = list(cfg["pages"]) + list(cfg.get("private_pages", {}))
    rows = []
    for key in keys:
        try:
            p = resolve_page(s, key)
        except SystemExit as e:
            rows.append(f"| {key} | not found | | |")
            continue
        raw = p["content"]["raw"]
        (out / f"{key}.json").write_text(json.dumps({
            "id": p["id"], "slug": p["slug"], "status": p["status"], "modified_gmt": p["modified_gmt"],
            "title": p["title"]["raw"], "content_raw": raw, "sha256": sha256(raw)}, ensure_ascii=False, indent=1))
        rows.append(f"| {key} | {p['id']} | {p['status']} | {p['modified_gmt']} |")
    summary(f"### Backup {stamp}\n\n| Page | ID | Status | Modified (GMT) |\n|---|---|---|---|\n" + "\n".join(rows))


if __name__ == "__main__":
    main()
