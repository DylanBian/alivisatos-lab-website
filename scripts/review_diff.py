"""Readable review diff for one page: live AUTO module (from site/push.py's backup) vs the generated fragment.

The raw Divi diff written by push.py is one huge JSON line per block and is hard to read, so this script
decodes the module, puts one tag per line, and writes a unified diff to the job summary.
"""
import argparse
import difflib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
sys.path.insert(0, str(SITE))
from push import BLOCK, replace_research_citations  # noqa: E402

MAX_LINES = 300


def latest_backup_raw(page):
    files = sorted((SITE / "backup").glob(f"*/{page}.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text())["content"]["raw"]


def module_value(raw, marker):
    start, end = f"<!-- AUTO:{marker}:START -->", f"<!-- AUTO:{marker}:END -->"
    for m in BLOCK.finditer(raw):
        found = []

        def walk(v):
            if isinstance(v, str) and start in v and end in v:
                found.append(v[v.index(start): v.index(end) + len(end)])
            elif isinstance(v, dict):
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)

        walk(json.loads(m.group(2)))
        if found:
            return found[0]
    if start in raw and end in raw:
        return raw[raw.index(start): raw.index(end) + len(end)]
    return ""


def tag_lines(html):
    return re.sub(r">\s*<", ">\n<", html).splitlines()


def out(text):
    print(text)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    page = ap.parse_args().page
    raw = latest_backup_raw(page)
    if raw is None:
        out(f"### {page}: no backup found; run site/push.py first")
        return
    if page == "research":
        new = replace_research_citations(raw)
        old_lines, new_lines = tag_lines(raw.encode().decode("unicode_escape", "ignore")), tag_lines(new.encode().decode("unicode_escape", "ignore"))
    else:
        marker = "home-updates" if page == "home" else page
        old_lines = tag_lines(module_value(raw, marker))
        new_lines = tag_lines((SITE / "build" / f"{page}.html").read_text().strip())
    diff = list(difflib.unified_diff(old_lines, new_lines, f"live/{page}", f"build/{page}", n=1, lineterm=""))
    added = sum(1 for d in diff if d.startswith("+") and not d.startswith("+++"))
    removed = sum(1 for d in diff if d.startswith("-") and not d.startswith("---"))
    shown = [d if len(d) <= 400 else d[:400] + " …" for d in diff[:MAX_LINES]]
    out(f"### {page}: {added} lines added, {removed} lines removed (one HTML tag per line)")
    if os.environ.get("GITHUB_ACTIONS"):
        def plain(line):
            return re.sub(r"<[^>]+>", " ", line[1:]).strip()
        changes = [d[0] + " " + plain(d)[:150] for d in diff if d[:1] in "+-" and d[:3] not in ("+++", "---") and plain(d)]
        sample = "%0A".join(c.replace("%", "%25") for c in changes[:25])
        print(f"::notice title=Diff {page}::+{added} / -{removed} lines; text changes (first 25):%0A{sample}")
    out("```diff\n" + ("\n".join(shown) or "(no change)") + ("\n… diff truncated" if len(diff) > MAX_LINES else "") + "\n```")


if __name__ == "__main__":
    main()
