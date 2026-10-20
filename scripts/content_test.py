"""Task F: find out which HTML survives saving page content on this site.

Creates (or reuses) a PRIVATE page with slug zz-content-test, saves a small sample, reads it back,
reports what survived, then sets the page to draft. The page is never deleted.
"""
from wp import annotate, api, request, session, summary

SLUG = "zz-content-test"
SAMPLE = """<style>#zz-test:has(p){outline:2px solid red}</style>
<div id="zz-test" style="padding:8px;border:1px solid #ccc"><p>inline style element</p></div>
<details><summary>details element</summary><p>inside details</p></details>
<script>document.getElementById('zz-test').dataset.js='ran';</script>"""

CHECKS = {
    "<style> block": "<style",
    ":has() rule text": ":has(",
    "inline style attribute": 'style="padding:8px',
    "<details> element": "<details",
    "<script> element": "<script",
}


def main():
    s = session()
    r = request(s, "GET", f"{api()}/pages", params={"slug": SLUG, "status": "any", "context": "edit"})
    r.raise_for_status()
    items = r.json()
    payload = {"title": "zz content test (private, safe to ignore)", "slug": SLUG, "status": "private", "content": SAMPLE}
    if items:
        page_id = items[0]["id"]
        r = request(s, "POST", f"{api()}/pages/{page_id}", json=payload)
    else:
        r = request(s, "POST", f"{api()}/pages", json=payload)
    r.raise_for_status()
    page_id = r.json()["id"]
    saved = request(s, "GET", f"{api()}/pages/{page_id}", params={"context": "edit"}).json()["content"]["raw"]
    rows = "\n".join(f"| {name} | {'kept' if needle in saved else 'REMOVED'} |" for name, needle in CHECKS.items())
    annotate("notice", "Content test", "; ".join(f"{n}: {'kept' if needle in saved else 'REMOVED'}" for n, needle in CHECKS.items()))
    request(s, "POST", f"{api()}/pages/{page_id}", json={"status": "draft"})
    summary(f"### Content test (page {page_id}, now draft)\n\n| Element | After save |\n|---|---|\n{rows}\n")


if __name__ == "__main__":
    main()
