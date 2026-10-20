"""Ask the caching proxy to revalidate each public page (request with Cache-Control: no-cache).

After a publish, visitors can see the previous version for up to an hour (max-age 3600). A no-cache request makes
the proxy fetch the page again from WordPress and store the new version. Read-only for WordPress.
"""
import time

import requests

from wp import annotate, base_url, config

HEADERS = {"User-Agent": "alivisatos-site-maintenance/1.0", "Cache-Control": "no-cache", "Pragma": "no-cache"}


def main():
    rows = []
    for key, path in config()["paths"].items():
        url = base_url() + path
        for attempt in range(3):
            try:
                r = requests.get(url, headers=HEADERS, timeout=60)
                rows.append(f"{path} {r.status_code} {r.headers.get('x-cache', '-')} {len(r.text)}")
                break
            except requests.RequestException as e:
                time.sleep(3)
                if attempt == 2:
                    rows.append(f"{path} ERR {type(e).__name__}")
    annotate("notice", "Cache refresh", "; ".join(rows))
    print("\n".join(rows))


if __name__ == "__main__":
    main()
