"""Check that the Application Password works and report the account's relevant capabilities.

`unfiltered_html` decides what page content may contain: without it, WordPress strips <script>
and usually <style> from saved content (normal for site admins on a multisite such as UChicago Voices).
"""
import sys

import os

import requests

from wp import annotate, api, config, request, session, summary

KEYS = ["edit_pages", "publish_pages", "edit_others_pages", "upload_files", "unfiltered_html", "edit_theme_options"]


def host_test(s):
    """Diagnostic: which REST host passes the Authorization header (set HOST_TEST=1)."""
    for base in config().get("api_base_candidates", []):
        try:
            t = request(s, "GET", base.rstrip("/") + "/wp-json/wp/v2/users/me", retries=1, timeout=20,
                        params={"context": "edit"}, allow_redirects=False)
            annotate("notice", "Host test", f"{base}: HTTP {t.status_code}")
        except requests.RequestException as e:
            annotate("notice", "Host test", f"{base}: {type(e).__name__}")


def main():
    s = session()
    user = os.environ.get("WP_USER", "")
    pw = os.environ.get("WP_APP_PASSWORD", "")
    annotate("notice", "Secrets", f"WP_USER length {len(user)}; WP_APP_PASSWORD length {len(pw)} "
             f"({len(pw.replace(' ', ''))} without spaces)")
    if os.environ.get("HOST_TEST"):
        host_test(s)
    try:
        r = request(s, "GET", f"{api()}/users/me", params={"context": "edit"})
    except requests.RequestException as e:
        annotate("error", "Auth check", f"Could not reach the site from GitHub Actions: {type(e).__name__}: {e}")
        sys.exit(1)
    if r.status_code != 200:
        try:
            body = r.json()
            detail = f"code={body.get('code')} message={body.get('message')}"
        except ValueError:
            detail = r.text[:300]
        annotate("error", "Auth check", f"HTTP {r.status_code} from {r.url.split('?')[0]}; {detail}; "
                 f"server={r.headers.get('server')} content-type={r.headers.get('content-type')}")
        summary(f"### Auth check: FAILED (HTTP {r.status_code})\n\n"
                "The Application Password was rejected or is missing. In wp-admin go to Users > Profile > "
                "Application Passwords, create a new one, and update the repository secret WP_APP_PASSWORD.")
        sys.exit(1)
    me = r.json()
    caps = me.get("capabilities", {})
    annotate("notice", "Auth check", f"OK as {me.get('slug')}; roles={me.get('roles')}; "
             + "; ".join(f"{k}={'yes' if caps.get(k) else 'no'}" for k in KEYS))
    rows = "\n".join(f"| `{k}` | {'yes' if caps.get(k) else 'no'} |" for k in KEYS)
    summary(f"### Auth check: OK\n\nUser: `{me.get('slug')}` · roles: {', '.join(me.get('roles', []))}\n\n"
            f"| Capability | Granted |\n|---|---|\n{rows}\n")
    if not caps.get("unfiltered_html"):
        summary("> `unfiltered_html` is not granted: `<script>` (and probably `<style>`) will be removed from page "
                "content on save. Use inline styles or a page-scoped CSS field; see task F.")


if __name__ == "__main__":
    main()
