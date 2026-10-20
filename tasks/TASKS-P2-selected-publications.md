# P2 addendum. "Selected Publications" block on the Publications page

Follow `AGENTS.md` (backup, diff, approval, verify). Inputs: `selected_publications.yaml` (data) and
`selected-publications.html` (design prototype).

## Rule
A paper is "selected" when **year >= 2022** and **at least one current group member (PI excluded)** is an author.
Match members by full name against `data/members.yaml` (initials alone are ambiguous: "Zhang, Y." on two
2022-2026 papers is Ye Zhang and Yugang Zhang, not Yuxuan Zhang).
Decision (Dylan, 2026-10-20): the rule uses **current** members only. When someone moves from members.yaml to
alumni.yaml, their papers leave the block on the next build unless another current member is an author.
Amanda Brewer is a current postdoc, so her papers stay.

## Tasks
- [ ] Fill the three `status: pending` entries (volume, issue, pages or article number) from Crossref:
      10.1021/acsnano.5c07437, 10.1038/s41467-025-60992-y, 10.1038/s44160-022-00025-4.
      For the Nat. Commun. paper, use Crossref's article number and fix the Research and Publications pages to match.
- [ ] Insert the block at the **top** of the Publications page (page 1147), above the year list, as one Divi Code
      module between `<!-- AUTO:selected:START -->` and `<!-- AUTO:selected:END -->`. Keep the full year list below.
- [ ] Use the prototype's markup and CSS, scoped under `.ag-pubs`. Remove the "Prototype" pill.
- [ ] `build.py` regenerates the block from the data file. When `members.yaml` or `publications.bib` changes,
      the selection updates automatically.
- [ ] Research-area anchors (`#synthesis`, `#lctem`, `#spectroscopy`, `#quantum`) must exist on the Research page
      (P1 task) so the "About this research area" links work.
- [ ] New papers from the P3 pipeline enter `selected_publications.yaml` with a suggested `area`, after approval.

## Questions for Dylan
1. Confirm the research area of each paper (the file follows the Research page's own placement where it lists the paper).
2. "Daqian Bian" on the Nat. Commun. 2025 up-conversion paper is Dylan Bian: confirm.
