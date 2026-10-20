# Changelog

Record every publish: date (UTC), page, Actions run link, public-check result.

## 2026-10-20

### 14:31-14:41 UTC publish runs 39439892128, 39440789261, 39441466289 (approved by Dylan)
- Content: open access counted by journal (20 papers); six new 2025-2026 papers; three new Selected Publications;
  13 tag corrections from an independent AI review; alumni years and 16 updated positions; no "Not listed" category;
  home slider headings; figures for Selected Publications.
- Incident: at 14:31 the Publications page rendered empty although the saved content was complete. Cause: an `<img>`
  inside the large Publications module (bisected on the private test page: one `<img>` is enough). Restored at 14:33
  from revision 2109. Figures are now background images; push.py writes the previous content back when a saved page
  renders under 1,000 characters. The proxy had cached the empty page; publish runs now send no-cache requests to
  refresh the cache.
- 14:37 run: all pages read back identical and render; 14:41: Alumni years for Abbas, Wang, Crook (2018-2024).

### 13:52 UTC publish run 39434123477 (page all, publish, approved by Dylan): all pages published
- Research (links to each area's publication list), News, Home, Members, Alumni, Publications. Every page read back
  identical to the build (round-trip report). Public check: all pages pass, `/positions/` 404.
- Checked as a logged-out visitor in Chrome: Members 20 people, 262 px photos, no banner, contact block; Publications
  484 papers, filters work by link and by click; Alumni filters; Home featured papers and contact; News 13 items.
- 13:55 UTC run 39434619172: Publications filter status text punctuation; read-back identical.

### 10:47 UTC publish run 39410422524 (page all, publish): partial, one page restored
- Research: published (three journal labels).
- Publications: the 1,074,426-character save came back **empty**. Restored at 10:55 UTC from revision 2079
  (07:34 UTC, 449,942 chars) through the REST API in Dylan's signed-in browser; read-back identical.
- Members, Alumni, News, Home: new content written; WordPress normalized inline styles and dropped `box-shadow` and
  `overflow-wrap` (read-back check failed, pages displayed correctly).
- Fixes: 850,000-character limit in push.py, immediate write-back when a save loses the module, publish stops at the
  first failure, round-trip report, restore workflow.

### Rebuild (built and staged on the private test page; not yet published)
- Styles moved from inline attributes into Divi module Free-Form CSS (tested: kept on save, printed on that page only).
  Publications module drops from about 1.07 M to 0.51 M characters.
- Members: structured data, larger photos, PI feature card, group-visit banner removed, contact block (GCIS E247H).
- Publications: 484 numbered papers; Crossref citation fields; AI tags from abstracts with evidence and confidence;
  JS-free filters by area, journal, type, open access, material, approach, application, each with its own URL.
- Alumni: JS-free sector and role filters. News: three people items from Gallery captions, newest first.
- Home: research area cards with a featured paper and links to the filtered publication list; contact block.
- All five modules staged on page 2081 and read back identical (module and CSS).
- Repository created. Imported task lists, data (alumni, selected publications), prototypes, scripts and workflows.
- State before this repository: P0, most of P1, and B (Selected Publications, 11 papers; 484-entry list) were written
  to WordPress between about 23:00 UTC on 2026-10-19 and 07:40 UTC on 2026-10-20 through a browser session.
  C and D builds exist only in Codex's local package (`Alivisatos-site-maintenance-C-D-2026-10-20.zip`) and still need
  to be added under `site/` and published.
- Plain URLs and anonymous REST gave different versions from different networks around 08:25-08:50 UTC
  (cache nodes not yet updated; intermittent 503s from the origin).
