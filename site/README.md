# Page generator (site/)

Built by Codex on 2026-10-20 (sections C and D) and connected to GitHub Actions here.
Details of each data file and template: `README-generator.md`.

## How a publish runs (`.github/workflows/publish.yml`)
1. `scripts/auth_check.py` and `scripts/backup.py` (repo root): confirm the Application Password, back up every page.
2. `site/build.py`: renders page fragments from `site/data/` and `site/templates/` into `site/build/<page>.html`.
   CSS from `site/assets/site.css` is inlined into each element, because page content cannot keep `<style>` blocks.
3. `site/validate.py`: checks counts, markers, sources and links.
4. `site/push.py <page>` (dry run) or `--apply`: fetches the live page, replaces only the module between
   `<!-- AUTO:<page>:START -->` and `<!-- AUTO:<page>:END -->`, saves a backup and a raw diff, checks the page did not
   change in the meantime, writes, and reads it back. For `members` it also removes empty Divi sections above the list.
   `research` uses the reviewed baseline `build/research-content.before-c.raw` and refuses if the live page differs.
5. `scripts/review_diff.py <page>`: readable diff (one HTML tag per line) in the run summary.
6. `scripts/verify_public.py`: plain-URL check after a publish.

## Editing content
Change files in `site/data/` (members, alumni, news, home, selected_publications, publications.csv), run
`python site/build.py && python site/validate.py` locally if you can, open a pull request, then publish.

## Not active yet
- `assets/site-integration.html` (search boxes and filter buttons). Page content cannot hold scripts and the only
  site-wide place is Divi Theme Options > Integration, a global setting. Decide after the content test (task F).
  Until then the controls render but do nothing; consider hiding them in the templates.
