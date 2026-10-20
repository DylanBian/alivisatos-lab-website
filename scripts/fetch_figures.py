"""Download candidate figure images (TOC graphic or Figure 1) for selected papers into site/assets/figures/.

Candidates per paper come from site/data/figure_sources.yaml. Each URL is tried; successes are saved as
<slug>__<n>.<ext>. Runs in GitHub Actions (publisher sites are not reachable from the agent workspace).
"""
import re
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site/assets/figures"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
           "Accept": "image/avif,image/webp,image/png,image/jpeg,image/gif,*/*;q=0.8"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = yaml.safe_load((ROOT / "site/data/figure_sources.yaml").read_text())
    lines = []
    for item in sources:
        slug = item["slug"]
        got = 0
        for n, url in enumerate(item["candidates"], 1):
            try:
                r = requests.get(url, headers=HEADERS, timeout=40)
            except requests.RequestException as e:
                lines.append(f"{slug} {n} ERR {type(e).__name__}")
                continue
            ctype = r.headers.get("content-type", "")
            ok = r.status_code == 200 and ctype.startswith("image/") and len(r.content) > 2000
            lines.append(f"{slug} {n} {r.status_code} {ctype.split(';')[0]} {len(r.content)}")
            if ok:
                ext = {"image/png": "png", "image/jpeg": "jpg", "image/gif": "gif", "image/webp": "webp"}.get(ctype.split(";")[0], "img")
                (OUT / f"{slug}__{n}.{ext}").write_bytes(r.content)
                got += 1
        print(f"::notice title=Figures {slug}::{got} of {len(item['candidates'])} downloaded")
    (OUT / "fetch_log.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
