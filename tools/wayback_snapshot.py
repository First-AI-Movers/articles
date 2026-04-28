#!/usr/bin/env python3
"""Submit public archive URLs to the Internet Archive Wayback Machine.

Usage:
    python3 tools/wayback_snapshot.py --dry-run
    python3 tools/wayback_snapshot.py --submit --limit 8 --sleep 2
"""

import argparse
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
SITEMAP_PATH = REPO_ROOT / "sitemap.xml"
DEFAULT_BASE_URL = "https://articles.firstaimovers.com"
WAYBACK_SAVE_URL = "https://web.archive.org/save"

# Deterministic topic hubs to snapshot (preferring highest-volume / most stable)
DEFAULT_TOPIC_SLUGS = [
    "ai-strategy",
    "ai-governance",
    "eu-ai-act",
    "ai-agents",
    "ai-productivity-tools",
]


def _parse_sitemap_urls(sitemap_path: Path) -> list[str]:
    """Extract all <loc> URLs from sitemap.xml."""
    if not sitemap_path.exists():
        return []
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text for loc in root.findall(".//ns:loc", ns) if loc.text]


def _build_url_list(base_url: str, sitemap_path: Path, topic_slugs: list[str]) -> list[str]:
    """Build deterministic list of URLs to snapshot."""
    urls = [
        base_url,
        urljoin(base_url, "/sitemap.xml"),
        urljoin(base_url, "/topics/"),
    ]
    # Add configured topic hubs
    for slug in topic_slugs:
        urls.append(urljoin(base_url, f"/topics/{slug}/"))
    # Fallback: if sitemap has more topic hubs and we want to extend, we could
    # parse them, but for v1 we keep the deterministic list.
    return urls


def _submit_url(url: str, timeout: int = 60) -> dict:
    """Submit one URL to Wayback Save Page Now."""
    save_url = f"{WAYBACK_SAVE_URL}/{url}"
    try:
        resp = requests.get(save_url, timeout=timeout, allow_redirects=True)
        # Wayback returns 200 on success (or redirects to the snapshot page)
        # Some responses may be 429 (rate limit) or 5xx (transient)
        if resp.status_code == 200:
            return {"url": url, "status": "submitted", "http_status": resp.status_code}
        elif resp.status_code == 429:
            return {"url": url, "status": "rate_limited", "http_status": resp.status_code}
        else:
            return {"url": url, "status": "warning", "http_status": resp.status_code}
    except requests.exceptions.Timeout:
        return {"url": url, "status": "timeout", "http_status": None}
    except requests.exceptions.RequestException as exc:
        return {"url": url, "status": "error", "http_status": None, "detail": str(exc)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Archive public URLs via Wayback Machine")
    parser.add_argument("--dry-run", action="store_true", help="List URLs without submitting (default)")
    parser.add_argument("--submit", action="store_true", help="Actually submit URLs to Wayback Machine")
    parser.add_argument("--limit", type=int, default=8, help="Max URLs to process")
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds between submissions")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base archive URL")
    parser.add_argument("--sitemap", default=str(SITEMAP_PATH), help="Path to sitemap.xml")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout per submission")
    args = parser.parse_args(argv)

    if not args.submit:
        args.dry_run = True

    sitemap_path = Path(args.sitemap)
    urls = _build_url_list(args.base_url, sitemap_path, DEFAULT_TOPIC_SLUGS)
    urls = urls[: args.limit]

    if args.dry_run:
        print(f"[wayback] DRY RUN — would submit {len(urls)} URL(s):")
        for u in urls:
            print(f"  - {u}")
        return 0

    print(f"[wayback] Submitting {len(urls)} URL(s) to Wayback Machine...")
    results = []
    for i, url in enumerate(urls, 1):
        print(f"[wayback] ({i}/{len(urls)}) {url} ...", end=" ", flush=True)
        result = _submit_url(url, timeout=args.timeout)
        results.append(result)
        print(result["status"])
        if i < len(urls) and args.sleep > 0:
            time.sleep(args.sleep)

    submitted = sum(1 for r in results if r["status"] == "submitted")
    warnings = sum(1 for r in results if r["status"] == "warning")
    errors = sum(1 for r in results if r["status"] in ("error", "timeout", "rate_limited"))
    print(f"[wayback] Done: {submitted} submitted, {warnings} warnings, {errors} errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
