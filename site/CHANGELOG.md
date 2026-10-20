# October 20, 2026 verification

## Live Publications completion

- Published 484 regular publication cards and 12 selected cards.
- Published 38 descending year links, 2026 through 1980s, with valid targets.
- Added 239 DOI links and two legitimate archive-record links. Saved source contains no Sci-Hub URLs.
- Converted the remaining 2023 perovskite machine-learning legacy citation into a card.
- Corrected the complete Wiley SICI DOI for DNA-based assembly of gold nanocrystals.
- Restored the full JoVE title and journal for DOI 10.3791/57665.
- Corrected the JCP 1987, 86, 6540–6549 record and the two malformed 2015 metadata rows.
- Removed the duplicate divider before the year list.
- Added scoped, client-side search through Divi Integration because the page sanitizer strips interactive form/script elements from the Code module.
- Verified an exact DOI returns the 2023 JACS paper, “Hauwiller graphene” returns five papers, a nonmatching query returns zero, and Clear restores 484 papers and the selected section.
- Public page reports 493 DOI anchors and two archive record links. One C&EN record remains without a confirmed link.

## P1/P2 public-page spot checks

- Members: 20 cards, 18 expandable education/link sections; corrected Chang Liu and Michelle Bishka mail links; no remaining requested name/degree/spelling artifacts. All content photos have alt text; empty admin-toolbar avatars are decorative.
- Research: all five anchors exist, MOSAIC uses its absolute HTTPS address, 14 DOI links are present, Cu3As citation includes 19 (36), 32291–32298.
- News: ten dated/highlighted items, including the requested group visits, papers, Carver Blue, workshop, festival and Kavli celebration.
- Home: latest three publications and three news cards, five research anchors and the public lab contact; no recruiting button or former manager reference in visible page text.
- Alumni: corrected typo checks pass; the source captures 199 cards. Cross-category repeated names and missing years are retained in QUESTIONS.md.

## Maintenance package

- Captured actual saved Divi source for Publications, Members, Alumni, News and Home.
- Imported publication metadata into CSV and the other card records into YAML without browser-extension markup.
- Built all five fragments and standalone previews. Round-trip comparisons preserve all visible text and hyperlink destinations, ignoring whitespace between blocks.
- Validated offline Divi block replacement: only the targeted marked module changes; block JSON parses; replacement is idempotent.
- REST push is provided for future use and has been tested offline only. Live changes in this session used the WordPress interface.

The snapshot import retains existing rich HTML inside YAML records to preserve layout. It is not a claim that every historical author name has been normalized against Crossref, or that all 484 records received a fresh Crossref response during this completion pass.


## Anonymous plain-URL check 2026-10-20T06:35:21.305498+00:00

Base: https://alivisatoslab.uchicago.edu

| Plain URL | HTTP | Result | Details |
|---|---:|---|---|
| / | 200 | PASS | — |
| /positions/ | 404 | PASS | — |
| /members/ | 200 | PASS | — |
| /alumni/ | 200 | PASS | — |
| /research/ | 200 | PASS | — |
| /publications/ | 200 | PASS | — |
| /news/ | 200 | PASS | — |
| /gallery/ | 200 | PASS | — |

## Sections C and D prepared locally 2026-10-20

- Research: corrected the three truncated journal labels (`Nat. Synth.`, `Sci. Adv.`, and `J. Am. Chem. Soc.`) in both Divi text modules that contain them. Added an exact-baseline guarded `push.py research` path; the offline diff changes only those labels and all 37 Divi block JSON objects parse. The broader scan found no other truncated journal labels.
- Members: added `areas` lists and confirmed anchors for the named current members. Replaced generic Research paths, changed Yi Cui's area label, and split Ida Vaghefi's two area links. Generated 20 responsive member cards with a group photo, cropped square portraits, role/start-year text, Scholar links where available, and a public lab contact button.
- News/Home: added a verified source URL to every published News card and all three Home Latest News cards. `reports/news_sources.md` records 13 claims and sources. The article publication date for the Nature Communications paper is verified, but its Editors' Highlights selection is not; that news item is omitted from the generated page until Dylan confirms it.
- Alumni: switched the generated page to the structured 187-person `alumni.yaml`. The 12 people formerly shown once under Ph.D. and once under Postdoc now appear in one card with both role tags. Added four summary figures, a sector bar and filters, role filters, and search over names, titles, and organizations.
- Shared styling: `assets/site.css` is the source for all generated page components; `build.py` inlines matching rules into the five page modules under the `ag-site-*` class prefix. Publications markup includes title/author/journal search and recent-year defaults; the Alumni and Publications behavior is in `assets/site-integration.html` because Divi strips scripts from page Code modules. That Integration snippet is included in local previews but was not installed in the global Divi settings. No Divi global CSS or SEO/theme setting was changed.
- SEO proposal: `reports/site-description-og-proposal.md` contains a draft meta description and a current group nanocrystal-cover image candidate. The setting location could not be confirmed because wp-admin redirected to UChicago SSO and returned 403; no setting was changed. The optional News-to-Posts migration was left untouched.
- Validation: `python3 build.py`, `python3 validate.py`, Python compilation, `node --check` on the generated Alumni/Publications scripts, and offline Research diff generation passed. The live WordPress pages were not updated in this round because the authenticated admin session was unavailable.

## Final primary-metadata audit and publication

Retrieved 791 Crossref author-query records, supplemented missing records by DOI and the 1992 NMR title query. All 484 regular publications are listed in reports/doi_check.csv. There are 478 automatic title/year matches and six explicit exceptions: three title variants and three entries without DOIs (two have archive records). Formal print year is used when supplied, otherwise the Crossref published date.

Published 11 further DOI corrections, including links that had pointed to news commentary or an erratum, two truncated Wiley SICI identifiers, and the 1992 NMR paper. Reclassified 11 records to their formal publication year. Normalized available Crossref author lists to ACS name format and restored chemical subscripts. The bibliography still contains 484 regular cards plus 12 selected cards, with one page root and no duplicated content. Before/after values and source DOIs are in reports/bibliographic-corrections.csv.

The new TASKS-2026-10-20 section A check passed all eight anonymous plain URLs; Positions is private, sanitized, and returns 404 without login. No cache/theme settings were changed.


## Anonymous plain-URL check 2026-10-20T07:17:14.831063+00:00

Base: https://alivisatoslab.uchicago.edu

| Plain URL | HTTP | Result | Details |
|---|---:|---|---|
| / | 200 | PASS | — |
| /positions/ | 404 | PASS | — |
| /members/ | 200 | PASS | — |
| /alumni/ | 200 | PASS | — |
| /research/ | 200 | PASS | — |
| /publications/ | 200 | PASS | — |
| /news/ | 200 | PASS | — |
| /gallery/ | 200 | PASS | — |


## Anonymous plain-URL check 2026-10-20T07:35:12.607771+00:00

Base: https://alivisatoslab.uchicago.edu

| Plain URL | HTTP | Result | Details |
|---|---:|---|---|
| / | 200 | PASS | — |
| /positions/ | 404 | PASS | — |
| /members/ | 200 | PASS | — |
| /alumni/ | 200 | PASS | — |
| /research/ | 200 | PASS | — |
| /publications/ | 200 | PASS | — |
| /news/ | 200 | PASS | — |
| /gallery/ | 200 | PASS | — |


## Anonymous plain-URL check 2026-10-20T07:39:50.737367+00:00

Base: https://alivisatoslab.uchicago.edu

| Plain URL | HTTP | Result | Details |
|---|---:|---|---|
| / | 200 | PASS | — |
| /positions/ | 404 | PASS | — |
| /members/ | 200 | PASS | — |
| /alumni/ | 200 | PASS | — |
| /research/ | 200 | PASS | — |
| /publications/ | 200 | PASS | — |
| /news/ | 200 | PASS | — |
| /gallery/ | 200 | PASS | — |

## Section B: Research citation correction 2026-10-20T07:17:34Z

- Updated the Nat. Synth. ligand-shell citation to volume 1, issue 2, pages 127–137. The Research page was saved through its Divi Text module; public output shows `1 (2), 127–137`.
- The three B DOI records now agree with Crossref in the Selected Publications YAML and Publications CSV: ACS Nano 19 (36), 32291–32298; Nat. Commun. 16, 5803; Nat. Synth. 1 (2), 127–137.
- `scripts/verify_public.py` passed all eight anonymous plain URLs; `/positions/` returned 404.

| Plain URL | HTTP | Result | Details |
|---|---:|---|---|
| / | 200 | PASS | — |
| /positions/ | 404 | PASS | — |
| /members/ | 200 | PASS | — |
| /alumni/ | 200 | PASS | — |
| /research/ | 200 | PASS | — |
| /publications/ | 200 | PASS | — |
| /news/ | 200 | PASS | — |
| /gallery/ | 200 | PASS | — |

## Section B: Publications and style fallback 2026-10-20T07:35:36Z

- Published the code-generated Selected Publications section: 11 selected papers from the agreed current-member rule, with 484 regular year-list cards retained below it.
- The Code module sanitizer removes `<style>` blocks, so the generated component now carries scoped inline styles. The public page retains the title, area chips, card hierarchy, spacing and maroon accents after save. No Sci-Hub URLs are present in generated source.
- Public output verified: 11 selected DOI links, 484 regular cards, year navigation starts 2026 and descends, prototype label absent, and all selected DOI links use `https://doi.org/`.
- `scripts/verify_public.py` passed all eight anonymous plain URLs; `/positions/` returned 404.

| Plain URL | HTTP | Result | Details |
|---|---:|---|---|
| / | 200 | PASS | — |
| /positions/ | 404 | PASS | — |
| /members/ | 200 | PASS | — |
| /alumni/ | 200 | PASS | — |
| /research/ | 200 | PASS | — |
| /publications/ | 200 | PASS | — |
| /news/ | 200 | PASS | — |
| /gallery/ | 200 | PASS | — |

## Section B complete: Home and cross-page citations 2026-10-20T07:40:09Z

- Generated Home's latest three publication cards from the same selected-publication records, ordered by publication date. Their DOI links are JACS `10.1021/jacs.6c08238`, Nat. Synth. `10.1038/s44160-026-01015-6`, and MRS Bulletin `10.1557/s43577-025-00958-z`.
- Verified Home retains three Latest News cards and the public lab contact. Research now shows the Crossref citation details consistently on all three pending items: ACS Nano 19 (36), 32291–32298; Nat. Commun. 16, 5803; Nat. Synth. 1 (2), 127–137.
- `python3 validate.py` passed selected-member eligibility, 11 selected and 484 regular records, Home data linkage, unchanged non-target modules, and balanced AUTO markers.
- `scripts/verify_public.py` passed all eight anonymous plain URLs; `/positions/` returned 404.

| Plain URL | HTTP | Result | Details |
|---|---:|---|---|
| / | 200 | PASS | — |
| /positions/ | 404 | PASS | — |
| /members/ | 200 | PASS | — |
| /alumni/ | 200 | PASS | — |
| /research/ | 200 | PASS | — |
| /publications/ | 200 | PASS | — |
| /news/ | 200 | PASS | — |
| /gallery/ | 200 | PASS | — |
