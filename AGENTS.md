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
- Site administrators on Voices probably lack `unfiltered_html`; `<script>` and likely `<style>` are removed on save.
  `scripts/auth_check.py` reports this; `scripts/content_test.py` confirms it (task F).
- Maintainer: Dylan Bian. Lab administrator: Freddie Sharmini. Lab address: GCIS E247H, 929 E 57th Street, Chicago, IL 60637.
- The only public contact for inquiries and applications is **alivisatos-lab@uchicago.edu**. Students and postdocs are
  never listed as recipients of inquiries, applications or CVs (HR and privacy policy).

## How work flows
1. Agents change files in this repository (data, generator, tasks) on a branch and open a pull request.
2. Dylan reviews and merges.
3. Publishing happens only through GitHub Actions: **Publish page** with `mode = dry-run` (diff in the run summary),
   then the same page with `mode = publish`. Each run backs up every page first (artifact, 90 days) and runs the public check.
4. **Daily public check** runs every morning and fails loudly if forbidden text or the Positions page becomes visible.
5. Record every publish in `CHANGELOG.md` (page, date, run link, result of the public check).

## Credentials
- The WordPress Application Password exists only as GitHub Actions secrets `WP_USER` and `WP_APP_PASSWORD`
  (or in Dylan's local `.env`, which git ignores). Agents never ask for it in chat and never print, log or commit it.
- If an Actions run reports 401/403, stop and report. Do not try other auth methods.
- Browser use: only when Dylan has signed in himself; prefer WordPress admin screens over the Divi Visual Builder.

## Rules for changes
- Minimal, targeted edits. Never rebuild a page from rendered HTML. Preserve Divi attributes, classes and IDs.
- The generator replaces content only between AUTO markers and starts from the live `content.raw` (see `site/README.md`).
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
