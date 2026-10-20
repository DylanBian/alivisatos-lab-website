# Page generator (site/)

Put the generator that produced the B, C and D builds here (`build.py`, templates, shared CSS).
The publish workflow runs `python site/build.py` and then `scripts/push_page.py`.

## Contract
`site/build.py` must:
1. Read data from `data/` (members, alumni, publications, selected_publications, news).
2. For each page it changes, start from the **live** `content.raw` (use `scripts/wp.py: resolve_page`), replace only
   the content between `<!-- AUTO:<name>:START -->` and `<!-- AUTO:<name>:END -->` (respecting how Divi stores it:
   plain markup or JSON-escaped inside block attributes), and write the complete new `content.raw` to
   `site/out/<page>.raw.html`.
3. Write `site/out/manifest.json`:
   ```json
   {"members": {"file": "members.raw.html", "base_sha256": "<sha256 of the live content.raw it started from>"}}
   ```
   Page keys are the keys in `config.yaml` (`home`, `research`, `members`, `alumni`, `publications`, `news`, `gallery`).
4. Never include credentials, `<script>` (unless task F shows scripts survive), Sci-Hub links, or forbidden text from
   `config.yaml`.

Run locally: `python site/build.py && python scripts/push_page.py --page members` (dry run).
