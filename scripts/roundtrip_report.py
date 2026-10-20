"""Read-only: compare each page's saved AUTO module with the generated fragment and report what WordPress changed.

Run after site/build.py. Emits one annotation per page with the first differing lines (build vs saved).
"""
import difflib
import sys
from collections import Counter
from pathlib import Path

from wp import annotate, api, config, request, session, summary
from review_diff import module_value, tag_lines

MAX_PAIRS = 12
CUT = 230


def short(line):
    line = line.strip()
    return line if len(line) <= CUT else line[:CUT] + " …"


def report(s, page):
    page_id = config()["pages"][page]
    r = request(s, "GET", f"{api()}/pages/{page_id}", params={"context": "edit"})
    r.raise_for_status()
    p = r.json()
    raw = p["content"]["raw"]
    head = f"modified {p['modified_gmt']} UTC; raw {len(raw)} chars"
    marker = "home-updates" if page == "home" else page
    live = module_value(raw, marker)
    if not live:
        annotate("warning", f"Round-trip {page}",
                 f"{head}; AUTO:{marker} module NOT found. Raw starts: {raw[:400]!r}")
        return
    build = (Path(__file__).resolve().parent.parent / "site" / "build" / f"{page}.html").read_text().strip()
    a, b = tag_lines(build), tag_lines(live)
    changes = Counter()
    changed_lines = 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        changed_lines += max(i2 - i1, j2 - j1)
        if op == "replace" and i2 - i1 == j2 - j1:
            for x, y in zip(a[i1:i2], b[j1:j2]):
                for kind, frag in char_changes(x, y):
                    changes[(kind, frag)] += 1
        else:
            for x in a[i1:i2]:
                changes[("line only in build", short(x))] += 1
            for y in b[j1:j2]:
                changes[("line only in saved", short(y))] += 1
    if not changes:
        annotate("notice", f"Round-trip {page}", f"{head}; saved module identical to the build.")
        return
    top = [f"{n}x {kind}: {frag}" for (kind, frag), n in changes.most_common(MAX_PAIRS)]
    annotate("warning", f"Round-trip {page}",
             f"{head}; module {len(live)} chars vs build {len(build)}; {changed_lines} lines differ; "
             f"{len(changes)} distinct changes, most frequent first:\n" + "\n".join(top))
    summary(f"### Round-trip {page}\n\n{head}; {changed_lines} lines differ.\n\n" + "\n".join("- " + x for x in top))


def char_changes(x, y):
    """Character-level edits that turn a build line into the saved line, as (kind, text) pairs."""
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, x, y, autojunk=False).get_opcodes():
        if op == "delete":
            out.append(("removed", repr(x[i1:i2][:120])))
        elif op == "insert":
            out.append(("added", repr(y[j1:j2][:120])))
        elif op == "replace":
            out.append(("changed", f"{x[i1:i2][:80]!r} -> {y[j1:j2][:80]!r}"))
    return out


def main():
    pages = sys.argv[1:] or ["members", "alumni", "news", "home", "publications"]
    s = session()
    for page in pages:
        try:
            report(s, page)
        except Exception as error:  # report and continue with the next page
            annotate("error", f"Round-trip {page}", f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
