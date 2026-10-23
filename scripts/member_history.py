"""Read-only: for each given name, the first and last saved revision of the Members page that contains it.

Used to fill alumni years by the rule in site/reports/alumni_years.md. WordPress keeps only the newest revisions, so a
name present in the oldest revision has an unknown start.
"""
import sys

from wp import annotate, api, config, request, session


def main():
    names = [n.strip() for n in " ".join(sys.argv[1:]).split(";") if n.strip()]
    page_id = config()["pages"]["members"]
    s = session()
    revs, page_no = [], 1
    while True:
        r = request(s, "GET", f"{api()}/pages/{page_id}/revisions",
                    params={"context": "edit", "per_page": 50, "page": page_no, "_fields": "id,modified_gmt,content"})
        if r.status_code == 400 and page_no > 1:
            break
        r.raise_for_status()
        items = r.json()
        if not items:
            break
        revs += [(x["modified_gmt"], x["content"]["raw"]) for x in items]
        page_no += 1
    revs.sort()
    oldest = revs[0][0] if revs else "none"
    for name in names:
        dates = [d for d, raw in revs if name.casefold() in raw.casefold()]
        msg = (f"{name}: first {dates[0]}, last {dates[-1]} ({len(dates)} of {len(revs)} revisions; oldest revision {oldest})"
               if dates else f"{name}: not found in {len(revs)} revisions (oldest {oldest})")
        annotate("notice", "Member history", msg)


if __name__ == "__main__":
    main()
