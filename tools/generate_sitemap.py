#!/usr/bin/env python3
"""Generate sitemap.xml from index.json and push to repo root.

Run this after rebuild_index.py and update_docs.py to keep the sitemap
in sync with the article archive. Ensures Google, Gemini, Perplexity,
and other crawlers can discover all articles within 24 hours.

Usage:
    python3 tools/generate_sitemap.py            # generate and push
    python3 tools/generate_sitemap.py --dry-run  # print XML, don't push
"""

import argparse
import base64
import json
import os
import sys
from datetime import date
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

_script_dir = Path(__file__).resolve().parent
_repo_root = _script_dir.parent
load_dotenv(_repo_root / ".env")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    sys.exit("GITHUB_TOKEN not set. Copy .env.example to .env and add your token.")

REPO = "First-AI-Movers/articles"
API = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

SITE_BASE = "https://articles.firstaimovers.com"

# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------


def fetch_file(path):
    """Return (content_str, sha) for a file in the repo."""
    url = f"{API}/contents/{path}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def get_sha(path):
    """Return the current SHA of a file, or None if it doesn't exist."""
    url = f"{API}/contents/{path}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 200:
        return r.json()["sha"]
    return None


def push_file(path, content, message):
    """Create or update a file via the GitHub Contents API."""
    encoded = base64.b64encode(content.encode()).decode()
    sha = get_sha(path)
    body = {
        "message": message,
        "content": encoded,
        "committer": {"name": "Index Bot", "email": "info@firstaimovers.com"},
    }
    if sha:
        body["sha"] = sha
    url = f"{API}/contents/{path}"
    r = requests.put(url, headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    return r.json()["commit"]["sha"][:7]


# ---------------------------------------------------------------------------
# Sitemap generation
# ---------------------------------------------------------------------------


def build_sitemap(articles, today):
    """Build sitemap XML string from article list."""
    urlset = Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Home page
    _add_url(urlset, f"{SITE_BASE}/", today, "daily", "1.0")

    # Key files
    for path in ["ABOUT.md", "CITATION.cff", "hernanicosta.json", "llms.txt", "index.json"]:
        _add_url(urlset, f"{SITE_BASE}/{path}", today, "weekly", "0.5")

    # README
    _add_url(urlset, f"{SITE_BASE}/README.md", today, "weekly", "0.7")

    # Articles
    for article in articles:
        folder = article.get("folder", "")
        pub_date = article.get("published_date", "")
        if not folder:
            continue
        loc = f"{SITE_BASE}/articles/{folder}/"
        _add_url(urlset, loc, pub_date or today, "monthly", "0.8")

    raw_xml = tostring(urlset, encoding="unicode")
    pretty = parseString(raw_xml).toprettyxml(indent="  ", encoding="UTF-8")
    # Remove extra blank lines from minidom
    lines = pretty.decode("utf-8").split("\n")
    cleaned = "\n".join(line for line in lines if line.strip())
    return cleaned + "\n"


def _add_url(parent, loc, lastmod, changefreq, priority):
    """Add a <url> entry to the urlset."""
    url_el = SubElement(parent, "url")
    SubElement(url_el, "loc").text = loc
    SubElement(url_el, "lastmod").text = lastmod
    SubElement(url_el, "changefreq").text = changefreq
    SubElement(url_el, "priority").text = priority


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Generate sitemap.xml from index.json")
    parser.add_argument("--dry-run", action="store_true", help="Print XML without pushing")
    args = parser.parse_args()

    today = str(date.today())

    # Fetch index.json
    print("Fetching index.json...")
    index_content, _ = fetch_file("index.json")
    index = json.loads(index_content)
    articles = index.get("articles", [])
    print(f"  {len(articles)} articles found")

    # Build sitemap
    sitemap_xml = build_sitemap(articles, today)
    url_count = sitemap_xml.count("<url>")
    print(f"  {url_count} URLs in sitemap")

    if args.dry_run:
        print(f"\n[DRY RUN] sitemap.xml ({len(sitemap_xml)} bytes):\n")
        # Print first 40 and last 10 lines
        lines = sitemap_xml.split("\n")
        for line in lines[:40]:
            print(line)
        if len(lines) > 50:
            print(f"  ... ({len(lines) - 50} lines omitted) ...")
            for line in lines[-10:]:
                print(line)
        return

    # Push sitemap.xml
    sha = push_file("sitemap.xml", sitemap_xml,
                     f"Rebuild sitemap.xml — {len(articles)} articles ({today})")
    print(f"  sitemap.xml pushed ({sha})")
    print(f"\nDone. {url_count} URLs in sitemap.")


if __name__ == "__main__":
    main()
