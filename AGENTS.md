# AGENTS.md: Alivisatos Group website maintenance

Rules for any AI agent (Codex, ChatGPT, Claude) working in this repository. Read fully before every task.
Current tasks live in `tasks/`. The newest task file is the one to follow.

## Site facts
- Public URL: https://alivisatoslab.uchicago.edu (same site as https://voices.uchicago.edu/alivisatosgroup)
- WordPress multisite (UChicago Voices), Divi 5. Page bodies are Divi layouts; generated sections sit in Divi Code
  modules between `<!-- AUTO:<name>:START -->` and `<!-- AUTO:<name>:END -->`.
- REST API: https://alivisatoslab.uchicago.edu/wp-json/ (`wp/v2`, `divi/v1`). Auth: WordPress Application Password.
- Page ids and slugs: `config.yaml`.
- A caching proxy (`envoy`, `max-age` about 3600 s) sits in front of the site. Plain URLs, and anonymous REST
  responses too, can show old versions for a while after a change, and different networks can get different versions.
  The source of truth for "published" is an **authenticated** REST read (`context=edit`); plain URLs show what visitors see.
- REST with the Application Password works on `https://voices.uchicago.edu/alivisatosgroup/wp-json/`; the
  `alivisatoslab.uchicago.edu/wp-json/` host drops the Authorization header.
- What survives saving page content (tested 2026-10-20 on the private test page `zz-content-test`, id 2081):
  - Removed: `<style>`, `<script>`, `<input>`, `<svg>`; inline CSS properties outside WordPress's safe list
    (for example `box-shadow`, `overflow-wrap`, `transform`, `transition`, `filter`, `inset`).
  - Kept: `<details name>`, `<time>`, `<nav>`, `<wbr>`, `data-*`, `aria-*`; inline `clamp()`, `min()`, `var()`,
    `aspect-ratio`, grid and flex properties (spaces after `:` and `;` are normalized away).
  - **Divi module Free-Form CSS** (`css.desktop.value.freeForm` on the Code module) is kept as written, except that
    `>` becomes `&gt;`; Divi prints it in a `<style>` element on that page only. All generated styles live there
    (`site/build/<page>.css`), so never use the child combinator `>` in `site/assets/site.css`.
  - Divi intercepts clicks on in-page `#links` for smooth scrolling unless the link has class
    `et_smooth_scroll_disabled`. Filters use `:target`, so every filter link carries that class.
- An `<img>` element inside the large Publications module makes WordPress render that page **empty** (saved content
  is fine; tested 2026-10-20). Use background images (`style="background-image:url(...)"` with `role="img"` and
  `aria-label`) in that module. Smaller modules (Members, Home) render `<img>` normally. `push.py` writes the previous
  content back if a saved page renders under 1,000 characters.
- After publishing, the caching proxy may serve the previous version (or a broken one) for up to an hour.
  `scripts/refresh_cache.py` (run by the publish workflow) asks it to revalidate each page.
- A saved page larger than about 1,000,000 characters comes back **empty** (PHP regex backtrack limit). 879,405 chars
  saved fine; 1,074,426 did not (2026-10-20 incident, restored from revision 2079). `push.py` refuses anything over
  850,000 characters, and writes the previous content back at once if a save loses the AUTO module.
- Maintainer: Dylan Bian. Lab administrator: Freddie Sharmini. Lab address: GCIS E247H, 929 E 57th Street, Chicago, IL 60637.
- The only public contact for inquiries and applications is **alivisatos-lab@uchicago.edu**. Students and postdocs are
  never listed as recipients of inquiries, applications or CVs (HR and privacy policy).

## How work flows
1. Agents change files in this repository (data, generator, tasks) on a branch and open a pull request.
2. Dylan reviews and merges.
3. Publishing happens only through GitHub Actions: **Publish page** with `mode = dry-run` (diff in the run summary),
   then the same page with `mode = publish`, and only after Dylan says so. Each run backs up every page first
   (artifact, 90 days), stops at the first page that fails, reports what WordPress changed (round-trip report) and runs
   the public check.
   - Before publishing a new kind of markup, stage it on the private test page (`zz-content-test`) and compare the
     saved module with the build.
   - **Restore page from revision** puts back the newest WordPress revision saved before a given UTC time.
   - **Fetch publication metadata** refreshes Crossref and OpenAlex data in `site/data/metadata/` (abstracts are
     stored encrypted; they are used for tagging only and never published).
4. **Daily public check** runs every morning and fails loudly if forbidden text or the Positions page becomes visible.
5. Record every publish in `CHANGELOG.md` (page, date, run link, result of the public check).

## Credentials
- The WordPress Application Password exists only as GitHub Actions secrets `WP_USER` and `WP_APP_PASSWORD`
  (or in Dylan's local `.env`, which git ignores). Agents never ask for it in chat and never print, log or commit it.
- If an Actions run reports 401/403, stop and report. Do not try other auth methods.
- Browser use: only when Dylan has signed in himself; prefer WordPress admin screens over the Divi Visual Builder.

## Rules for changes
- Minimal, targeted edits. Never rebuild a page from rendered HTML. Preserve Divi attributes, classes and IDs.
- `site/push.py` replaces content only between AUTO markers in the live `content.raw` (see `site/README.md`).
- Page data lives in `site/data/`; edit data and templates, never the generated files in `site/build/` by hand.
  - `members.yaml`: structured people records. When someone leaves, move the entry to `alumni.yaml` with `end: <year>`.
  - `selected_publications.yaml`: only papers with Paul Alivisatos as last (corresponding) author; outside Quantum
    Information Science only papers from 2025 on; bold only the first author and Paul (Dylan, 2026-10-21). Removed
    papers go to `selected_publications_excluded.yaml`. build.py stops on a paper that breaks these rules.
  - `publications.csv` (the list), `metadata/works.json` (Crossref/OpenAlex), `publication_tags.yaml` (tags; set
    `tag_source: human` on any entry you correct so AI runs never overwrite it), `tags.yaml` (allowed tags and their
    definitions), `selected_publications.yaml`, `key_papers.yaml` (featured paper per research area on the home page).
  - Current members are bolded in author lists only by full-name match on Crossref authors, never by initials.
- Never delete pages, media, menus or users. To take a page offline, set it to private.
- Do not install plugins, change themes, change global Divi settings (including Theme Options > Integration),
  or edit other sites on the network.
- Do not invent facts (names, titles, dates, DOIs, emails, honors). Missing information goes to the task file's
  "Open questions" and the related edit waits.
- Bibliographic data comes only from Crossref, OpenAlex or the publisher page; list every change in the PR description.
- No links to Sci-Hub or any other source of unauthorized copies. Free-access links only from the publisher
  (ACS Articles on Request, Springer Nature SharedIt) supplied by the authors.
- "Done" means published and verified on plain URLs. A local build that passes is "built", not "published".

## Writing style for site text
- Plain, direct English. No em dashes. ACS-style citations with DOI links (`https://doi.org/<DOI>`).
- Chemical formulas use `<sub>` (CsPbBr<sub>3</sub>).
