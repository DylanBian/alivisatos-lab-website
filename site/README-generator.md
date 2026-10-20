# Alivisatos Group website maintenance

Public site: https://alivisatoslab.uchicago.edu (also https://voices.uchicago.edu/alivisatosgroup). WordPress multisite with Divi 5. Sections A and B were published earlier. Sections C and D are now prepared in the local generator and have not yet been published because the WordPress admin session redirected to UChicago SSO and returned 403.

## Source data and build

- `data/publications.csv` contains the 484 regular year-list entries. `data/selected_publications.yaml` contains the 11 selected papers. The generator applies the current-member rule and uses those records for Home's latest publication cards.
- `data/members.yaml` contains member profiles and an `areas` list of confirmed Research anchor slugs. Profile cards retain existing education and Scholar links; public contact buttons point to the lab address `alivisatos-lab@uchicago.edu`.
- `data/alumni.yaml` is the structured source for 187 unique alumni. One record can have both `phd` and `postdoc` roles. Sector values drive the summaries, sector bar and filters.
- `data/news.yaml` has `source_url`, `verified`, and `publish` fields. An unverified item is omitted from the generated News page. `data/home.yaml` contains three Latest News cards with their sources.
- `templates/` controls the page structures. `assets/site.css` is the shared visual source; `build.py` inlines its class rules into each generated Divi module because Divi Code modules can strip `<style>` blocks. Generated classes use the `ag-site-*` prefix.

Run `python3 build.py` and then `python3 validate.py`. Review the generated fragments in `build/` and their diffs in `reports/`. Publication search filters title, author and journal; year groups older than three years are collapsed by default. Alumni search and role/sector controls are generated with the page fragment. Their behavior is in `assets/site-integration.html` and is included in local previews. Divi strips scripts from page Code modules, so this snippet must also be installed in the existing Divi Integration area before the controls become interactive on the live site. It was prepared but not installed in this round.

The Research citation correction has its own raw-content baseline in `build/research-content.before-c.raw` and target in `build/research-content.raw`. The parser changes only the three journal labels inside one Divi text block. `python3 push.py research --snapshot build/research-content.before-c.raw` creates an offline diff; it does not publish.

## Publishing

`push.py` saves a timestamped raw backup, produces a diff, checks for concurrent edits and reads saved content back after a write. Use it only with the authorized WordPress application password in `WP_USER` and `WP_APP_PASSWORD`; never put credentials in files or logs. `--snapshot` is offline review only. If WordPress returns 401/403 on a write, stop and report it.

For normal pages, use `python3 push.py <publications|members|alumni|news|home>` for a dry run and `--apply` only when the authenticated production path is available. Section C's Research edit uses the exact baseline guard described above. After publication, check the page logged out and run `python3 scripts/verify_public.py` to check the eight plain URLs and the Positions 404.

## Boundaries and pending items

Do not install plugins, change themes, edit global Divi settings, or publish unverified claims. `assets/publications-integration.html` and `assets/site-custom.css` are legacy snapshots; `assets/site.css` is the source for generated page styling, and `assets/site-integration.html` is the prepared interaction snippet. No Sci-Hub links or widgets are included.

The News-to-WordPress-Posts migration is optional and was not part of this implementation. The exact SEO setting location is not confirmed; see `reports/site-description-og-proposal.md`. No description, Open Graph image, SEO, theme, or global Divi setting was changed.

`reports/doi_check.csv` contains the prior Crossref audit. `reports/bibliographic-corrections.csv` records the prior bibliographic updates. `scripts/verify_public.py` checks anonymous public URLs; it does not publish page changes.
