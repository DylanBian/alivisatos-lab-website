"""Push one generated page into WordPress, with a diff first.

Input contract (written by site/build.py): site/out/manifest.json
  {"members": {"file": "members.raw.html", "base_sha256": "<sha256 of the live content.raw the build started from>"}, ...}
Each file holds the complete new `content.raw` for that page.

Default is a dry run: print the diff and stop. Add --publish to write.
Safety checks before writing:
  - live content has not changed since the build (base_sha256), unless --ignore-base
  - every block-comment JSON object parses
  - no forbidden text from config.yaml
After writing, the page is read back. If WordPress changed the content on save (for example by
stripping <style> or <script>), the difference is reported.
"""
import argparse
import difflib
import json
import sys
from pathlib import Path

from wp import ROOT, check_block_json, config, resolve_page, session, sha256, summary, update_content

MAX_DIFF_LINES = 400


def diff_text(old, new, name):
    lines = list(difflib.unified_diff(old.splitlines(), new.splitlines(), f"live/{name}", f"build/{name}", n=2, lineterm=""))
    shown = lines[:MAX_DIFF_LINES]
    more = len(lines) - len(shown)
    return "\n".join(shown) + (f"\n... {more} more diff lines" if more > 0 else ""), len(lines)


def push(s, key, entry, out_dir, publish, ignore_base):
    new_raw = (out_dir / entry["file"]).read_text(encoding="utf-8")
    page = resolve_page(s, key)
    live_raw = page["content"]["raw"]
    problems = []
    base = entry.get("base_sha256")
    if base and base != sha256(live_raw) and not ignore_base:
        problems.append("live page changed since the build started; rebuild first")
    count, errors = check_block_json(new_raw)
    problems += [f"block JSON: {e}" for e in errors]
    low = new_raw.lower()
    problems += [f"forbidden text: {f}" for f in config()["forbidden_strings"] if f.lower() in low]
    if "<script" in low:
        problems.append("contains <script> (will be stripped without unfiltered_html; see task F)")

    diff, n = diff_text(live_raw, new_raw, key)
    summary(f"### {key} (page {page['id']}): {n} diff lines · {count} block JSON objects checked\n")
    summary("```diff\n" + (diff or "(no change)") + "\n```")
    if problems:
        summary("**Blocked:**\n" + "\n".join(f"- {p}" for p in problems))
        return False
    if not publish or n == 0:
        summary("Dry run only. Re-run with mode = publish to write this page." if n else "Nothing to publish.")
        return True

    update_content(s, page["id"], new_raw)
    after = resolve_page(s, key)["content"]["raw"]
    if after == new_raw:
        summary(f"Published {key}. Read-back matches the build.")
    else:
        d, m = diff_text(new_raw, after, key)
        summary(f"Published {key}, but WordPress changed the content on save ({m} diff lines). "
                "Likely HTML filtering; review below.\n```diff\n" + d + "\n```")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True, help="page key from config.yaml, or 'all'")
    ap.add_argument("--manifest", default=str(ROOT / "site" / "out" / "manifest.json"))
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--ignore-base", action="store_true")
    args = ap.parse_args()
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        sys.exit(f"{manifest_path} not found. Run site/build.py first.")
    manifest = json.loads(manifest_path.read_text())
    keys = list(manifest) if args.page == "all" else [args.page]
    s = session()
    ok = True
    for key in keys:
        if key not in manifest:
            summary(f"{key}: not in manifest, skipped")
            continue
        ok &= push(s, key, manifest[key], manifest_path.parent, args.publish, args.ignore_base)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
