# Alivisatos Group website

Source of truth for https://alivisatoslab.uchicago.edu: page data, page generator, task lists, and the GitHub Actions
that publish to WordPress and check what visitors see. Agents start with `AGENTS.md`.

## Layout
| Path | What it holds |
|---|---|
| `AGENTS.md` | Rules for AI agents |
| `tasks/` | Task lists; the newest file is current |
| `site/data/` | Page data: members, alumni, news, home, selected publications, 484 publications |
| `site/` | Page generator (`build.py`, `validate.py`, `push.py`), see `site/README.md` |
| `scripts/` | Auth check, backup, readable diff, public check, content test |
| `prototypes/` | Design prototypes (open the HTML files in a browser) |
| `.github/workflows/` | Check site access, Publish page, Daily public check |

## Quick start (Dylan)
1. **Create an Application Password**: sign in to wp-admin in a browser (university SSO), go to Users → Profile, and at
   the bottom of the page under Application Passwords create a new one named `github-actions`. Copy the generated
   password (it is shown only once). If this section is missing, Voices has disabled the feature; contact UChicago
   Voices support first.
2. **Store it as repository secrets**: in this repository go to Settings → Secrets and variables → Actions → New
   repository secret and create two secrets:
   - `WP_USER`: your WordPress username (the "dbian" in "Howdy, dbian" at the top right of the dashboard)
   - `WP_APP_PASSWORD`: the password you just copied
   The password lives only here; never send it in any chat.
3. **Test run**: Actions → Check site access → Run workflow. A successful run shows the authentication result, the
   account's permissions (`unfiltered_html` decides whether pages keep `<style>` and `<script>`), a backup of every
   page, and the public page check table. Ticking content_test creates a private test page and reports which code the
   site removes (task F).
4. **Edit content**: change the data files in `site/data/` (or have an AI agent change them), commit, then publish.
5. **Publish**: Actions → Publish page, choose the page, run `dry-run` first to see the differences, then run the same
   page again with `publish` once they look right.
6. Every morning at 8:17 the public pages are checked automatically; GitHub emails you if something is wrong.

## Working with AI agents
- Connect the agent to this repository (Codex cloud, ChatGPT with GitHub, Claude Code). It reads `AGENTS.md` and the
  newest file in `tasks/`, works on a branch, and opens a pull request. No file uploads needed.
- Agents never need the WordPress password; publishing runs in GitHub Actions with the stored secrets.

## Handover
When the maintainer changes: transfer this repository (or add the new maintainer as a collaborator), have them create
their own Application Password and replace both secrets, and revoke the old Application Password in wp-admin.
