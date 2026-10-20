"""Small WordPress REST client shared by the maintenance scripts.

Credentials come only from environment variables WP_USER and WP_APP_PASSWORD
(GitHub Actions secrets, or a local .env file that git ignores). Never print them.
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
UA = "alivisatos-site-maintenance/1.0"


def load_dotenv():
    """Load KEY=VALUE lines from a local .env without overriding existing variables."""
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def config():
    return yaml.safe_load((ROOT / "config.yaml").read_text())


def base_url():
    return os.environ.get("WP_BASE", config()["base_url"]).rstrip("/")


def api():
    return base_url() + "/wp-json/wp/v2"


def session(auth=True):
    load_dotenv()
    s = requests.Session()
    s.headers["User-Agent"] = UA
    if auth:
        user = os.environ.get("WP_USER")
        password = os.environ.get("WP_APP_PASSWORD")
        if not user or not password:
            annotate("error", "Secrets", f"Missing in this run: {'WP_USER ' if not user else ''}{'WP_APP_PASSWORD' if not password else ''}. "
                     "Add them under Settings > Secrets and variables > Actions > Repository secrets.")
            sys.exit("WP_USER and WP_APP_PASSWORD are not set (GitHub secret or local .env).")
        s.auth = (user, password)
    return s


def request(s, method, url, retries=4, **kw):
    """HTTP request with retries on transient 5xx responses (the site returns occasional 503s)."""
    kw.setdefault("timeout", 60)
    for attempt in range(retries):
        r = s.request(method, url, **kw)
        if r.status_code in (502, 503, 504) and attempt < retries - 1:
            time.sleep(5 * (attempt + 1))
            continue
        return r
    return r


def resolve_page(s, key):
    """Return the page object (context=edit) for a config key, id or slug."""
    target = config()["pages"].get(key, key)
    if isinstance(target, int) or str(target).isdigit():
        r = request(s, "GET", f"{api()}/pages/{int(target)}", params={"context": "edit"})
        r.raise_for_status()
        return r.json()
    r = request(s, "GET", f"{api()}/pages", params={"slug": target, "context": "edit", "status": "any"})
    r.raise_for_status()
    items = r.json()
    if not items:
        sys.exit(f"No page found for slug '{target}'.")
    return items[0]


def update_content(s, page_id, raw):
    r = request(s, "POST", f"{api()}/pages/{page_id}", json={"content": raw})
    if r.status_code in (401, 403):
        sys.exit(f"Write refused ({r.status_code}). Stop and report; do not try other auth methods.")
    r.raise_for_status()
    return r.json()


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


BLOCK_RE = re.compile(r"<!--\s+wp:[\w/-]+\s+(\{.*?\})\s+/?-->", re.S)


def check_block_json(raw):
    """Parse every block-comment JSON attribute object. Returns (count, errors)."""
    errors = []
    count = 0
    for m in BLOCK_RE.finditer(raw):
        count += 1
        try:
            json.loads(m.group(1))
        except json.JSONDecodeError as e:
            errors.append(f"offset {m.start()}: {e}")
    return count, errors


def annotate(level, title, message):
    """Emit a GitHub Actions annotation (readable through the check-runs API). Never pass secrets."""
    if os.environ.get("GITHUB_ACTIONS"):
        msg = str(message).replace("%", "%25").replace("\r", "").replace("\n", "%0A")
        print(f"::{level} title={title}::{msg}")


def summary(markdown):
    """Append markdown to the GitHub Actions job summary when running in Actions; always print."""
    print(markdown)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(markdown + "\n")
