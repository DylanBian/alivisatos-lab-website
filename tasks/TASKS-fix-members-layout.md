# Fix: Members page spacing and photo size (2026-10-20)

Follow `AGENTS.md` (backup, diff, approval, verify). Page: Members (slug `members`).

## 1. Remove the empty space above "Current Members"
Cause: two empty Divi sections sit above the AUTO members block. Each section and row carries Divi's default
top and bottom padding, which adds up to the blank band under the navigation.
- `et_pb_section_1` > `et_pb_row_24` > `et_pb_column_44` (empty column, no module)
- `et_pb_section_2` > `et_pb_row_25` > `et_pb_column_45` > `et_pb_image_20` (image module with no image)

Tasks:
- [ ] In `content.raw`, locate these two sections (Divi block markup or shortcodes) and remove both sections entirely.
      Do not touch `et_pb_section_3` (the Code module that holds `<!-- AUTO:members:START -->`).
- [ ] If `et_pb_image_20` was meant for a group photo, report it instead of deleting it; the group photo goes into
      the AUTO block later (D section), not into an empty Divi module.
- [ ] Target: the "Current Members" heading starts about 40 to 60 px below the navigation bar.
      If `et_pb_section_3` still leaves a large gap, reduce its top padding to 24px in that section's own settings
      (not in global Divi settings) and report the change.

## 2. Larger photos
Current inline style on each member `<img>`: `width:92px;height:92px`.
- [ ] In the members template used by `build.py`:
  - Member cards: 120px x 120px (keep `object-fit:cover;border-radius:50%`).
  - PI card: 140px x 140px.
  - Screens narrower than 600px: 96px. Inline styles cannot hold media queries, so move the card styles into one
    scoped `<style>` block at the top of the AUTO block (selectors prefixed with `#alivisatos-members`), and keep the
    same class names on cards and images. This also starts the shared-style work in section D.
- [ ] Widen the grid track so the text column is not squeezed by the larger photo:
      `grid-template-columns: repeat(auto-fit, minmax(min(100%, 360px), 1fr))`.
- [ ] Rebuild, show the diff, push after approval.

## 3. Verify
- [ ] Clear the page cache after the push (see section A of TASKS-2026-10-20.md). Logged-in views skip the cache,
      so check in a private window as well.
- [ ] Dylan checks the page at desktop width and on a phone: gap under the navigation, photo size, and that names,
      emails and research-area pills do not wrap awkwardly in the three-column layout.
