# New-paper highlight cards: drafts

Status 2026-10-20: the figures are published (every Selected Publication shows a TOC graphic or Figure 1 with a credit line, captured from the publisher pages). The draft sentences below are not used on the site; Dylan accepted the current form. The rest of this file is the original draft, kept for reference.

Follows `tasks/TASKS-P3-publication-images.md`. Each card would show an image, the citation, a DOI link and one
sentence. Nothing here is on the site; each card waits for Dylan's (or the first author's) approval.
License data: OpenAlex `best_oa_location` and Crossref `license`, read 2026-10-20.

## Image rule per paper
- **CC BY or CC BY-NC(-ND), publisher version**: a figure from the article may be shown with the credit line
  "Figure from <citation>, licensed under <license>". NC-ND allows unmodified, non-commercial display (resizing only).
- **CC BY preprint only (arXiv), subscription publisher version**: a figure from the arXiv version may be used with credit
  to the arXiv record. The published figure itself stays off the site.
- **Closed**: no figure from the article. Ask the first author for the original TOC/graphical-abstract file
  (`assets/toc/<doi-slug>.<ext>`); use it only after Dylan confirms the publisher's terms allow website reuse.

| Paper | License (version) | Image source | Draft sentence (25 words max) |
|---|---|---|---|
| Kang et al., *J. Am. Chem. Soc.* 2026, 10.1021/jacs.6c08238 | CC BY (arXiv 2603.24776, submitted version) | Figure from arXiv:2603.24776 | Millisecond liquid-cell electron microscopy with deep-learning denoising shows gold nanocrystals reversibly losing and regaining local crystallinity in reactive liquids. |
| Wu et al., *Nat. Synth.* 2026, 10.1038/s44160-026-01015-6 | closed | Ask Binyu Wu for the TOC file; the May 2026 cover image needs Springer Nature permission | Reaction kinetics decide whether Cu<sub>3</sub>As nanocubes convert into crystalline, multidomain, amorphous or hollow InAs and GaAs nanocubes. |
| Yang et al., *MRS Bull.* 2025, 10.1557/s43577-025-00958-z | CC BY (published) | Figure from the article, CC BY credit | A perspective on precision nanoscience: multimodal observation, including liquid-phase TEM, of atomic structure at surfaces and interfaces. |
| Yang et al., *ACS Nano* 2025, 10.1021/acsnano.5c07437 | closed | Ask Shengsong Yang for the TOC file | Liquid-cell TEM shows that pH, coordination and oxidants steer Cu<sub>3</sub>As nanocubes along distinct etching pathways. |
| Abbas et al., *Nat. Commun.* 2025, 10.1038/s41467-025-60992-y | CC BY-NC-ND (published) | Figure 1 from the article, unmodified, CC BY-NC-ND credit | A Pb–Br–Pb bending phonon drives up-conversion in CsPbBr<sub>3</sub> nanocrystals, with efficiencies up to 75%. |
| Calvin, Brewer et al., *Acc. Chem. Res.* 2025, 10.1021/acs.accounts.4c00708 | closed | Ask Amanda Brewer for the TOC file | Calorimetry and NMR, modeled together, show collective effects in the ligand shell govern ligand exchange on quantum dots. |
| Wong et al., *ACS Nano* 2024, 10.1021/acsnano.4c04083 | CC BY (arXiv 2406.07762, submitted version) | Figure from arXiv:2406.07762 | Single Er<sup>3+</sup> ions in CeO<sub>2</sub> nanocrystals keep spin coherence for nearly a microsecond, a step toward nanocrystal qubits. |
| Calvin, Brewer et al., *PNAS* 2024, 10.1073/pnas.2307633121 | CC BY-NC-ND (published) | Figure from the article, unmodified, CC BY-NC-ND credit | Calorimetry shows negative surface energies for ligand-capped quantum dots: surface atoms are more stable than interior atoms. |
| Brewer et al., *J. Phys. Chem. C* 2023, 10.1021/acs.jpcc.3c00187 | closed | Ask Amanda Brewer for the TOC file | Ligand exchange thermodynamics are nearly identical on (111) CdSe tetrahedra and (100) CdSe cubes. |
| Calvin, Brewer et al., *J. Phys. Chem. C* 2022, 10.1021/acs.jpcc.2c04223 | closed | Ask Amanda Brewer for the TOC file | A tetrahydrofuran-mediated equilibrium allows direct calorimetric measurement of cadmium oleate binding to CdS quantum dots. |
| Calvin, Brewer et al., *Nat. Synth.* 2022, 10.1038/s44160-022-00025-4 | CC BY-NC (published) | Figure from the article, CC BY-NC credit | A review of how ligand tails and ligand–ligand interactions shape nanocrystal growth, stability and assembly. |

## To publish a card
1. Dylan or the first author approves the sentence and the image.
2. The image is uploaded to the media library with alt text and the credit as caption.
3. Add `image`, `image_credit`, `license` and `highlight` to the paper in `data/selected_publications.yaml`.
4. Rendering these fields on the home page and in Selected Publications is a small addition to `build.py`
   (not written yet; do it together with the first approved card).
