# Changelog

Record every publish: date (UTC), page, Actions run link, public-check result.

## 2026-10-23

### 19:41-19:43 UTC publish runs 40013376898 (members), 40013564999 (alumni)
- Julien Perce (2024–2026) and Isaac Spiller (2025–2026, per Dylan) moved from Members to Alumni as undergraduates;
  Members 18 people, Alumni 189. Start years from the Members-page revision history (new read-only workflow
  `member-history.yml`). Both pages read back identical; checked as a visitor.

## 2026-10-21

### 23:53-23:55 UTC publish runs 39696296116 (publications), 39696440868 (home)
- Selected Publications: Kang et al., J. Am. Chem. Soc. 2026 (millisecond atomic dynamics) added back to Electron
  Microscopy in Liquid at Dylan's request (`last_author_exception`; last author Jungwon Park). Home latest three:
  JACS 2026, Nat. Synth. 2026, Chem. Mater. 2025. Both pages read back identical.
- README quick start translated to English.

### 19:29 UTC publish run 39662099324 (publications)
- Selected Publications: Shengsong Yang and Binyu Wu bold as co-first authors of ACS Nano 2025 (Dylan). The sentence
  added under the heading at 19:13 was not requested and is removed; no equal-contribution note.
- Full list: no bold names (Dylan). Run 39661883487 at 19:28 had published an intermediate version (Paul bold, name
  normalized); this run replaced it. Checked as a visitor.

### 19:13-19:16 UTC publish runs 39659691287 (publications), 39659930117 (home): Selected Publications rules (Dylan)
- Only papers with Paul Alivisatos as last (and corresponding) author; outside Quantum Information Science only 2025 on.
  Seven papers moved to `site/data/selected_publications_excluded.yaml`: JACS 2026 GaAs quantum dots and JACS 2026 molten
  indium halide salts (Talapin group collaborations), JACS 2026 millisecond dynamics (last author Jungwon Park), PNAS 2024,
  J. Phys. Chem. C 2023 and 2022, Nat. Synth. 2022. Seven papers remain; the full list still has all 490.
- Electron Microscopy in Liquid is the first area in Selected Publications; bold only for first authors and Paul Alivisatos.
  build.py and validate.py enforce these rules.
- Home: latest three are now Nat. Synth. 2026, Chem. Mater. 2025 (new one-line summary) and MRS Bull. 2025. The "Recent
  results" line for Electron Microscopy in Liquid now cites ACS Nano 2025 (Cu3As etching; Paul last author), edited in
  Chrome outside the AUTO module. Both pages read back identical; checked as a visitor.

## 2026-10-20

### 17:26-17:52 UTC: fixes from the external site review (Dylan asked for them; edits in Dylan's signed-in Chrome via REST)
- Placeholder posts hello-world (1), welcome-to-your-blog-news-feed (209), blank-post (240): set to private with comments
  closed (not deleted). Their URLs return 404; the posts sitemap is gone; category and author archives are empty.
- Home (page 2, outside the AUTO module): first slide heading is the page H1; the group-photo slide (slider6.jpg) is titled
  "Our Team" (also in push.py SLIDE_TITLES); "Our current Research Interests/Projects are (but not limited to)" replaced
  by one result per research direction, each linked to its paper (PNAS 2024, JACS 2026, Nat. Commun. 2025, ACS Nano 2024).
- Research (page 1198): Quantum section shows the ACS Nano 2024 TOC graphic (media 2136) with the ACS credit line;
  image titles "44160_2022_25_Figa_HTML" and "图片2" replaced by descriptive titles (page and media 1881, 1890).
  The two Kate Nichols artworks still load from her Squarespace site; uploading them needs her permission.
- Gallery (page 1269): wrong duplicates fixed with the files already in the media library (Team Excited State now shows
  Excited_State16.jpg; Alivisluggers Softball 2017 shows Alivisluggers-Softball-2017.png); all 55 image titles come from
  their alt text (no hash or timestamp names); year headings 2026-2013 with anchors (#year-2026 ...) and a Jump-to line.
- Every save read back identical to what was sent; checked as a visitor.
- News (publish run 39468001277): JACS millisecond-dynamics item shows its TOC graphic (whole image, ACS credit line);
  Carver blue pigment item shows the photo Dylan supplied (media 2154, carver-blue-pigment-fecl3.jpg).
- Alumni (publish run 39469207908): Joeson Wong's placeholder title "Engineer" (no employer, no source) removed.

### 16:22 UTC publish run 39456774253 (alumni, approved by Dylan): positions with identity ties
- Read back identical to the build; cache refreshed; public check passed. Checked as a visitor: 187 cards, Ophir Klein under Undergraduate, Colvin, Scheele, Seo, Luther, Ha and Chou show the new entries; Betzler and Thau show no position.
- Ophir Klein's role changed from Ph.D./postdoc to undergraduate (Dylan).
- Rule from Dylan: a found person must be proven to be the Alivisatos group member. Each changed entry records the
  page that shows the position (`source`) and the page or ORCID/OpenAlex record that ties the person to the group
  (`identity`); `validate.py` requires both whenever `verified` is set.
- Starting data: OpenAlex co-author records on the group's own papers and public ORCID records
  (`scripts/alumni_sources.py`, run 39446015067; 154 of 187 alumni matched; output encrypted).
- 58 positions updated (including the 14 kept from this morning's 16), 2 reverted to blank (Sophia Betzler,
  Sarah Thau), 48 confirmed unchanged, 5 not found. Report: `site/reports/alumni_positions_2026-10-20.md`.
- The four research sub-agents started at 15:15 UTC were stopped by an interruption at 15:21 UTC after 4 results;
  the check was finished by hand in the main session.

### 14:52 UTC publish run 39443098268: figures for all 14 Selected Publications
- 14 images in the media library with alt text and credit lines: 9 ACS TOC graphics ("Reprinted with permission ...
  Copyright American Chemical Society"), 3 Springer Nature Figure 1 (licence named where CC), PNAS Figure 1
  (CC BY-NC-ND 4.0), MRS Bulletin graphical abstract (CC BY 4.0). Captured in Dylan's signed-in Chrome
  (publisher sites block automated downloads); one ACS SVG converted to PNG.
- All pages read back identical; cache refreshed; checked as a visitor (14 figures, 490 papers).

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
