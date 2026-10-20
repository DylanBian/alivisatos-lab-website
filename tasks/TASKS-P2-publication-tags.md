# P2 addendum. Tag-filtered Publications page ("Publication Explorer")

Design: `publication-filter.html` (prototype with 35 papers from 2022-2026). Follow `AGENTS.md` for every write.

## Facets and how each tag is assigned

| Facet | Values | Source |
|---|---|---|
| Year | every year, plus decade groups for pre-2000 | Crossref `issued` |
| Journal | ISO abbreviation | Crossref `short-container-title` |
| Article type | Review or account, Perspective, Editorial, Article | journal (Acc. Chem. Res., Annu. Rev., Chem. Rev., MRS Bull.) or Crossref/publisher article type; otherwise Article |
| Group-led / Collaboration | Group-led when A. P. Alivisatos is the last author; otherwise Collaboration | author list (rule, no judgment) |
| Open access | yes / no | OpenAlex `open_access.is_oa` and license |
| Current group member | names from `members.yaml` | full-name match from Crossref authors (never initials alone) |
| Research area | the four Research-page areas, or none | suggested by AI from title + abstract; Dylan confirms |
| Material | controlled list below | suggested by AI from title + abstract |
| Approach | controlled list below | suggested by AI from title + abstract |

Controlled vocabulary (`data/tags.yaml`). Tags outside this list are not allowed; propose additions in the report instead.
- Material: Quantum dots; Nanorods, tetrapods and heterostructures; Perovskites; III-V and arsenides; Metals and plasmonics;
  Oxides and rare earths; Silicon and germanium; Polymer nanocomposites; DNA and biomolecule conjugates.
- Approach: Electron microscopy; Optical and ultrafast spectroscopy; Single-particle methods; X-ray and high pressure;
  Thermodynamics; Surface and ligand chemistry; Cation exchange and chemical transformation; Self-assembly and superlattices;
  Machine learning and automation; Theory and modeling.
- Application: Solar energy and photovoltaics; Catalysis; Biological imaging and sensing; Quantum information;
  Displays and LEDs; Mechanics and stress sensing. (Optional third content facet; include if the counts justify it.)

## Tasks
- [ ] Build `data/publications.yaml` (or `.bib` with extra fields) for the **full** list, one entry per DOI, citation fields
      from Crossref. Entries without a DOI keep the page text and get `status: no-doi`.
- [ ] Fill the automatic facets (year, journal, type, group-led/collaboration, open access, current members).
- [ ] Write a one-line definition with inclusion criteria for every tag in `data/tags.yaml` before tagging anything.
- [ ] **Calibration round (required):** tag the 35 papers from 2022-2026 first. Dylan corrects them; refine the tag
      definitions from his corrections. Run the full list only after this round.
- [ ] Tag every paper: research area (0 or 1), materials (0 to 2), approaches (0 to 3), from title and abstract.
  - Abstract sources, in order: OpenAlex `abstract_inverted_index`, Crossref `abstract`. Abstracts are used for tagging only
    and are never published on the site.
  - Papers with no abstract available (common before ~2000): tag from title and journal, mark `basis: title-only`.
  - For each tag, store a short evidence phrase from the title or abstract and a confidence (high / medium / low).
  - Store `tag_source: ai` per paper. A later run never overwrites tags with `tag_source: human`.
- [ ] Optional: run the tagging twice independently and flag papers where the two runs disagree. This doubles the agent
      time; use it if the calibration round shows inconsistent tagging.
- [ ] Write `reports/tag_review.csv` (DOI, year, title, basis, suggested tags, evidence, confidence, disagreement flag),
      ordered low confidence and disagreements first. Dylan reviews those rows plus a random 30-paper sample.
      If the sample has more than 2 wrong tags, refine definitions and rerun before publishing.
- [ ] Optional: send each current member the rows for their own papers to check.
- [ ] Generate the page with `build.py`: every entry rendered in HTML with `data-*` attributes; a small vanilla-JS filter
      (no external libraries); the full list stays readable with JavaScript off.
- [ ] Filters combine as: OR within a facet, AND across facets. Each option shows the count under the other active filters.
      Tags on each paper are clickable and apply that filter.
- [ ] Filter state goes in the query string (for example `/publications/?area=lctem&material=perovskites`) so the Research page
      can link each area to its filtered list, and filtered views can be shared.
- [ ] Keep the Selected Publications block (TASKS-P2-selected-publications.md) above the explorer. Keep year anchors for old links.
- [ ] Mobile: the filter panel collapses to one "Filters" button above the list.
