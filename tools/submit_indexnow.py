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
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SITEMAP = REPO_ROOT / "sitemap.xml"
DEFAULT_KEY_FILE = REPO_ROOT / ".indexnow-key"
DEFAULT_ENDPOINT = "https://api.indexnow.org/indexnow"


def _read_key(key_path: Path) -> str:
    if not key_path.exists():
        raise FileNotFoundError(f"IndexNow key file not found: {key_path}")
    key = key_path.read_text(encoding="utf-8").strip()
    if len(key) < 8 or len(key) > 128:
        raise ValueError(f"IndexNow key must be 8–128 chars, got {len(key)}")
    return key


def _parse_sitemap(sitemap_path: Path) -> list:
    """Extract <loc> URLs from sitemap.xml."""
    from xml.etree.ElementTree import parse
    tree = parse(sitemap_path)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [loc.text for loc in tree.iterfind(".//s:loc", ns) if loc.text]
    return urls


def _filter_urls(urls: list) -> list:
    """Keep only indexable first-party HTML URLs on articles.firstaimovers.com."""
    allowed = []
    for u in urls:
        if not u.startswith("https://articles.firstaimovers.com/"):
            continue
        # Exclude local archive article pages (noindex,follow)
        if "/articles/" in u:
            continue
        # Exclude raw data / feed / artifact extensions
        if any(u.endswith(ext) for ext in (".md", ".txt", ".json", ".cff", ".xml")):
            continue
        allowed.append(u)
    return allowed


def _build_payload(urls: list, key: str) -> dict:
    return {
        "host": "articles.firstaimovers.com",
        "key": key,
        "keyLocation": f"https://articles.firstaimovers.com/{key}.txt",
        "urlList": urls,
    }


def _submit(urls: list, key: str, endpoint: str) -> bool:
    payload = _build_payload(urls, key)
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


def main(argv=None):
    parser = argparse.ArgumentParser(description="Submit URLs to IndexNow")
    parser.add_argument("--sitemap", type=Path, default=DEFAULT_SITEMAP,
                        help="Path to sitemap.xml")
    parser.add_argument("--key", default=None,
                        help="IndexNow key (reads .indexnow-key if omitted)")
    parser.add_argument("--key-location", default=None,
                        help="Public key file URL")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                        help="IndexNow endpoint URL")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print payload without submitting")
    args = parser.parse_args(argv)

    key = args.key or _read_key(DEFAULT_KEY_FILE)
    key_location = args.key_location or f"https://articles.firstaimovers.com/{key}.txt"

    if not args.sitemap.exists():
        print(f"Sitemap not found: {args.sitemap}", file=sys.stderr)
        return 1

    raw_urls = _parse_sitemap(args.sitemap)
    urls = _filter_urls(raw_urls)

    print(f"Sitemap URLs: {len(raw_urls)}")
    print(f"Filtered to articles.firstaimovers.com indexable: {len(urls)}")

    if not urls:
        print("No URLs to submit.")
        return 0

    payload = _build_payload(urls, key)
    payload["keyLocation"] = key_location

    if args.dry_run:
        print("--- DRY RUN ---")
        print(f"Endpoint: {args.endpoint}")
        print(f"Host: {payload['host']}")
        print(f"Key: {payload['key']}")
        print(f"Key location: {payload['keyLocation']}")
        print(f"URL count: {len(payload['urlList'])}")
        print("First 5 URLs:")
        for u in payload["urlList"][:5]:
            print(f"  {u}")
        if len(payload["urlList"]) > 5:
            print(f"  ... and {len(payload['urlList']) - 5} more")
        print("--- END DRY RUN ---")
        return 0

    ok = _submit(urls, key, args.endpoint)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
