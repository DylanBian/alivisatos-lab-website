"""Check that the Application Password works and report the account's relevant capabilities.

`unfiltered_html` decides what page content may contain: without it, WordPress strips <script>
and usually <style> from saved content (normal for site admins on a multisite such as UChicago Voices).
"""
import sys

from wp import api, request, session, summary

KEYS = ["edit_pages", "publish_pages", "edit_others_pages", "upload_files", "unfiltered_html", "edit_theme_options"]


def main():
    s = session()
    r = request(s, "GET", f"{api()}/users/me", params={"context": "edit"})
    if r.status_code != 200:
        summary(f"### Auth check: FAILED (HTTP {r.status_code})\n\n"
                "The Application Password was rejected or is missing. In wp-admin go to Users > Profile > "
                "Application Passwords, create a new one, and update the repository secret WP_APP_PASSWORD.")
        sys.exit(1)
    me = r.json()
    caps = me.get("capabilities", {})
    rows = "\n".join(f"| `{k}` | {'yes' if caps.get(k) else 'no'} |" for k in KEYS)
    summary(f"### Auth check: OK\n\nUser: `{me.get('slug')}` · roles: {', '.join(me.get('roles', []))}\n\n"
            f"| Capability | Granted |\n|---|---|\n{rows}\n")
    if not caps.get("unfiltered_html"):
        summary("> `unfiltered_html` is not granted: `<script>` (and probably `<style>`) will be removed from page "
                "content on save. Use inline styles or a page-scoped CSS field; see task F.")


if __name__ == "__main__":
    main()
