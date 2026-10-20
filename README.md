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

## 快速开始（Dylan）
1. **生成 Application Password**：浏览器登录 wp-admin（学校 SSO），进入 Users → Profile，页面底部
   Application Passwords，新建一个，名字填 `github-actions`，复制生成的密码（只显示一次）。
   如果没有这一栏，说明 Voices 禁用了这个功能，先联系 UChicago Voices 支持。
2. **存入仓库 Secret**：本仓库 Settings → Secrets and variables → Actions → New repository secret，建两个：
   - `WP_USER`：你的 WordPress 用户名（后台右上角 "Howdy, dbian" 里的 dbian）
   - `WP_APP_PASSWORD`：刚才复制的密码
   密码只存在这里，不要发到任何聊天里。
3. **试运行**：Actions → Check site access → Run workflow。成功会显示认证结果、账户权限
   （`unfiltered_html` 决定页面能否保留 `<style>` 和 `<script>`）、所有页面的备份和公开页面检查表。
   勾选 content_test 会建一个私密测试页，直接告诉你哪些代码会被网站删掉（任务 F）。
4. **改内容**：改 `site/data/` 里的数据文件（或让 AI 改），提交后再发布。
5. **发布**：Actions → Publish page，选页面，先用 `dry-run` 看差异，确认后同一页面再选 `publish`。
6. 每天早上 8:17 自动检查一次公开页面，出问题 GitHub 会发邮件给你。

## Working with AI agents
- Connect the agent to this repository (Codex cloud, ChatGPT with GitHub, Claude Code). It reads `AGENTS.md` and the
  newest file in `tasks/`, works on a branch, and opens a pull request. No file uploads needed.
- Agents never need the WordPress password; publishing runs in GitHub Actions with the stored secrets.

## Handover
When the maintainer changes: transfer this repository (or add the new maintainer as a collaborator), have them create
their own Application Password and replace both secrets, and revoke the old Application Password in wp-admin.
