#!/usr/bin/env python3
"""Submit URLs to IndexNow (Bing, Yandex, and participating engines).

Reads the sitemap, filters to first-party indexable URLs on
articles.firstaimovers.com, and POSTs them to the IndexNow endpoint.

Usage:
    python3 tools/submit_indexnow.py --dry-run
    python3 tools/submit_indexnow.py
    python3 tools/submit_indexnow.py --sitemap path/to/sitemap.xml --key abc123...

The IndexNow key is public proof-of-host ownership, not a secret.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SITEMAP = REPO_ROOT / "sitemap.xml"
DEFAULT_ENDPOINT = "https://api.indexnow.org/indexnow"

# Host → environment variable mapping for multi-client support.
INDEXNOW_KEY_ENV_BY_HOST = {
    "articles.firstaimovers.com": "INDEXNOW_API_KEY_ARTICLES_FAIM",
    "radar.firstaimovers.com": "INDEXNOW_API_KEY_RADAR_FAIM",
}


def _get_key_for_host(host: str) -> str:
    """Read the IndexNow key for *host* from environment variables."""
    env_var = INDEXNOW_KEY_ENV_BY_HOST.get(host, "INDEXNOW_API_KEY")
    key = os.environ.get(env_var, "").strip()
    if key:
        if len(key) < 8 or len(key) > 128:
            raise ValueError(f"IndexNow key must be 8–128 chars, got {len(key)}")
        return key
    # Fallback to generic env var
    generic = os.environ.get("INDEXNOW_API_KEY", "").strip()
    if generic:
        if len(generic) < 8 or len(generic) > 128:
            raise ValueError(f"IndexNow key must be 8–128 chars, got {len(generic)}")
        return generic
    raise SystemExit(
        f"error: no IndexNow key found for {host}. "
        f"Set {env_var} or INDEXNOW_API_KEY, or pass --key."
    )


def _parse_sitemap(sitemap_path: Path) -> list:
    """Extract <loc> URLs from sitemap.xml."""
    from xml.etree.ElementTree import parse
    tree = parse(sitemap_path)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [loc.text for loc in tree.iterfind(".//s:loc", ns) if loc.text]
    return urls


def _filter_urls(urls: list, host: str) -> list:
    """Keep only indexable first-party HTML URLs on the given host."""
    prefix = f"https://{host}/"
    allowed = []
    for u in urls:
        if not u.startswith(prefix):
            continue
        # Exclude local archive article pages (noindex,follow)
        if "/articles/" in u:
            continue
        # Exclude raw data / feed / artifact extensions
        if any(u.endswith(ext) for ext in (".md", ".txt", ".json", ".cff", ".xml")):
            continue
        allowed.append(u)
    return allowed


def _build_payload(urls: list, key: str, host: str) -> dict:
    return {
        "host": host,
        "key": key,
        "keyLocation": f"https://{host}/{key}.txt",
        "urlList": urls,
    }


def _submit(urls: list, key: str, endpoint: str, host: str) -> bool:
    payload = _build_payload(urls, key, host)
    data = json.dumps(payload).encode("utf-8")
    req = Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""

    if status in (200, 202):
        print(f"IndexNow: submitted {len(urls)} URLs → {status} {endpoint}")
        return True

    print(f"IndexNow: FAILED {status} {endpoint}")
    print(f"  Response: {body[:500]}")
    print(f"  Submitted {len(urls)} URLs")
    return False


def _redact_key(key: str) -> str:
    """Show only first/last 4 chars of a key for tidy logs."""
    if len(key) <= 12:
        return key
    return key[:4] + "..." + key[-4:]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Submit URLs to IndexNow")
    parser.add_argument("--sitemap", type=Path, default=DEFAULT_SITEMAP,
                        help="Path to sitemap.xml")
    parser.add_argument("--host", default="articles.firstaimovers.com",
                        help="Target host (default: articles.firstaimovers.com)")
    parser.add_argument("--key", default=None,
                        help="IndexNow key (reads env var for --host if omitted)")
    parser.add_argument("--key-location", default=None,
                        help="Public key file URL")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                        help="IndexNow endpoint URL")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print payload without submitting")
    args = parser.parse_args(argv)

    key = args.key or _get_key_for_host(args.host)
    key_location = args.key_location or f"https://{args.host}/{key}.txt"

    if not args.sitemap.exists():
        print(f"Sitemap not found: {args.sitemap}", file=sys.stderr)
        return 1

    raw_urls = _parse_sitemap(args.sitemap)
    urls = _filter_urls(raw_urls, args.host)

    print(f"Sitemap URLs: {len(raw_urls)}")
    print(f"Filtered to {args.host} indexable: {len(urls)}")

    if not urls:
        print("No URLs to submit.")
        return 0

    payload = _build_payload(urls, key, args.host)
    payload["keyLocation"] = key_location

    if args.dry_run:
        env_var = INDEXNOW_KEY_ENV_BY_HOST.get(args.host, "INDEXNOW_API_KEY")
        print("--- DRY RUN ---")
        print(f"Endpoint: {args.endpoint}")
        print(f"Host: {payload['host']}")
        print(f"Key source: {env_var}")
        print(f"Key (redacted): {_redact_key(payload['key'])}")
        print(f"Key location: {payload['keyLocation']}")
        print(f"URL count: {len(payload['urlList'])}")
        print("First 5 URLs:")
        for u in payload["urlList"][:5]:
            print(f"  {u}")
        if len(payload["urlList"]) > 5:
            print(f"  ... and {len(payload['urlList']) - 5} more")
        print("--- END DRY RUN ---")
        return 0

    ok = _submit(urls, key, args.endpoint, args.host)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
