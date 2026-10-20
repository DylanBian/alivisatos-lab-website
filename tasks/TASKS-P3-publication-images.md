# P3. New-paper highlights with images (start after P2 publications.bib exists)

Follow `AGENTS.md` for every write (backup, diff, approval, verify).
Goal: each new group paper appears on the Publications page ("Recent" block) and the home page
("Latest papers") as a card: image, correct citation, DOI link, one-line highlight.
**Discovery and drafting are automatic. Publishing waits for Dylan's approval of each card.**

## 1. Discovery (automatic, weekly)
- [ ] `scripts/find_new_papers.py`:
  - Query OpenAlex works for Paul Alivisatos's OpenAlex author ID, `from_publication_date` = last run date.
    Resolve the author ID from his ORCID; confirm the ID with Dylan once and store it in `config.yaml`.
  - Cross-check each hit against Crossref (`https://api.crossref.org/works/<DOI>`).
  - Drop DOIs already in `data/publications.bib`. Drop corrections, errata and preprints whose journal
    version is already listed.
  - Write `drafts/new_papers.yaml` and print a short summary.
- [ ] Schedule weekly (cron on Dylan's machine, or GitHub Actions that only opens an issue/PR with the drafts).
  The schedule never pushes to WordPress.

## 2. Citation (automatic)
- [ ] Build the citation only from Crossref fields: authors, title, journal (ISO abbreviation), year, volume,
      issue, pages or article number, DOI. ACS style, DOI linked as `https://doi.org/<DOI>`.
- [ ] Bold current members and alumni names using `data/members.yaml` and `data/alumni.yaml`.
- [ ] Assign research-area tags from the five agreed areas; mark the tag as a suggestion in the draft.

## 3. Image (rules depend on the article license)
Read the license from OpenAlex `best_oa_location.license` and Crossref `license`. Record it in the draft.

- **Open license (cc-by, cc-by-nc, cc-by-sa, etc.)**
  - [ ] Fetch the graphical abstract if the article has one, otherwise Figure 1, from Europe PMC open-access
        full text or the publisher's article page. Save the source URL.
  - [ ] Caption credit: `Figure from <short citation>, licensed under CC BY 4.0` (use the actual license and version).
- **Subscription or unknown license**
  - [ ] Do not download or hotlink publisher-hosted images.
  - [ ] Add the paper to `reports/image_requests.md`: "Ask the first author for the original TOC/graphical-abstract
        file." The author's file goes into `assets/toc/<doi-slug>.<ext>`.
  - [ ] Credit line template, used only after Dylan confirms the publisher terms allow website reuse:
        `Reprinted with permission from <short citation>. Copyright <year> <publisher>.`
- [ ] Never use an image whose caption credits a third party.
- [ ] Resize to max 1200 px wide, JPG or WebP under 300 KB. Alt text: one plain sentence describing the image.

## 4. Highlight sentence (draft only)
- [ ] One sentence, at most 25 words, drafted from the abstract. States the finding directly. No hype words.
- [ ] Marked `status: draft` until the first author or Dylan approves it.

## 5. Review and publish (manual approval)
- [ ] Render `drafts/preview.html` showing each card exactly as it will appear (image, citation, highlight, credit, license).
- [ ] After Dylan approves a card:
  - Upload the image: `POST /wp/v2/media` with `alt_text` and `caption` (= citation + credit line).
  - Add the entry to `data/publications.bib` with fields `image`, `image_credit`, `license`, `highlight`, `tags`.
  - Rebuild the Publications "Recent" block and the home page "Latest papers" block; diff; push; verify logged out.
  - Optional: create a News post ("New paper in <Journal>") with the same image and citation.
- [ ] Log every published card in `CHANGELOG.md` with DOI, license and image source.

## Questions for Dylan
1. Confirm Paul Alivisatos's ORCID/OpenAlex author ID.
2. Should papers where Paul is a middle author (collaborations) get cards, or only papers with group first/corresponding authors?
3. Confirm publisher terms for website reuse of figures from subscription articles (ACS, Wiley, AAAS, Springer Nature).
   UChicago Library scholarly communications can confirm this once for all publishers.
