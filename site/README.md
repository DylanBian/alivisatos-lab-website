# Page generator (site/)

Renders the code-managed sections of Members, Alumni, News, Publications and Home from `site/data/`.
Older notes on individual data files: `README-generator.md`.

## How a publish runs (`.github/workflows/publish.yml`)
1. `scripts/auth_check.py` and `scripts/backup.py` (repo root): confirm the Application Password, back up every page.
2. `site/build.py`: writes, for each page, `build/<page>.html` (the AUTO module content) and `build/<page>.css`
   (`assets/site.css` plus generated filter rules, minified). Page content on Voices cannot keep `<style>`, so the CSS is
   stored as the Divi Code module's Free-Form CSS, which Divi prints on that page only.
3. `site/validate.py`: counts, markers, sources, forbidden text, filter targets, CSS without `>`, size.
4. `site/push.py <page>` (dry run) or `--apply`: fetches the live page, replaces only the module between
   `<!-- AUTO:<page>:START -->` and `<!-- AUTO:<page>:END -->` and its Free-Form CSS, refuses pages over 850,000
   characters, checks the page did not change in the meantime, writes, and reads it back. If the save lost the module,
   it writes the previous content back immediately. `research` applies three journal-label fixes to the live text.
5. `scripts/review_diff.py <page>`: readable diff in the run summary. `scripts/roundtrip_report.py`: what WordPress
   changed on save (expected: nothing).
6. `scripts/verify_public.py`: plain-URL check after a publish.

## Filters without scripts
Each filter chip is a link to `#<target>` with class `et_smooth_scroll_disabled`; empty `<span class="ag-site-target">`
elements carry the ids. CSS rules of the form `.ag-site-root.ag-site-publications:has(#f-lctem:target) .ag-site-pub:not(.t-lctem){display:none}`
do the filtering. Every filter therefore has a shareable URL, for example `/publications/#f-lctem` or
`/alumni/#alumni-sector-industry`.

## Publications data
- `data/publications.csv`: the list as it appears on the site (id, year group, title, authors, URL).
- `data/metadata/works.json`: Crossref and OpenAlex records per DOI (refresh with the "Fetch publication metadata"
  workflow). Journal abbreviation, volume, issue and pages come from Crossref when the titles match;
  `reports/publication_metadata.md` lists the exceptions.
- `data/tags.yaml`: the controlled vocabulary with a definition for every tag.
- `data/publication_tags.yaml`: tags per paper, suggested by AI from the title and abstract, each with evidence and
  confidence. `reports/tag_review.csv` lists them, lowest confidence first, for review. Set `tag_source: human` after
  correcting an entry.

## Editing content
Change files in `site/data/`, run `python site/build.py && python site/validate.py`, commit, then publish (dry run first).
To preview without publishing, open `site/build/<page>-preview.html` in a browser.
