#!/usr/bin/env python3
"""Rebuild index.json from article metadata in GitHub.

Reads every articles/*/metadata.json via the GitHub API,
assembles a corpus-level index, and pushes index.json to the repo root.

Usage:
    python3 tools/rebuild_index.py            # build and push
    python3 tools/rebuild_index.py --dry-run  # print index, don't push
"""

import argparse
import base64
import json
import os
import sys
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load .env from repo root (works whether you run from root or tools/)
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


def get_all_folders():
    """Return sorted list of article folder names."""
    url = f"{API}/contents/articles"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return sorted(item["name"] for item in r.json() if item["type"] == "dir")


def get_metadata(folder):
    """Fetch and decode metadata.json for a given article folder."""
    url = f"{API}/contents/articles/{folder}/metadata.json"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    content = base64.b64decode(r.json()["content"]).decode("utf-8")
    return json.loads(content)


def get_sha(path):
    """Return the current SHA of a file, or None if it doesn't exist."""
    url = f"{API}/contents/{path}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 200:
        return r.json()["sha"]
    return None


def push_index(index_data):
    """Commit index.json to the repo root via the GitHub Contents API."""
    content = base64.b64encode(
        json.dumps(index_data, indent=2, ensure_ascii=False).encode()
    ).decode()
    sha = get_sha("index.json")
    body = {
        "message": f"Rebuild index.json — {date.today()}",
        "content": content,
        "committer": {"name": "Index Bot", "email": "info@firstaimovers.com"},
    }
    if sha:
        body["sha"] = sha
    url = f"{API}/contents/index.json"
    r = requests.put(url, headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    print("index.json pushed")


def main():
    parser = argparse.ArgumentParser(description="Rebuild index.json from article metadata")
    parser.add_argument("--dry-run", action="store_true", help="Print index without pushing")
    args = parser.parse_args()

    print(f"Fetching article folders from {REPO}...")
    folders = get_all_folders()
    print(f"Found {len(folders)} folders\n")

    articles = []
    skipped = 0
    for folder in folders:
        meta = get_metadata(folder)
        if not meta:
            print(f"  SKIP {folder} (no metadata.json)")
            skipped += 1
            continue
        articles.append({
            "folder": meta.get("folder"),
            "title": meta.get("title"),
            "published_date": meta.get("published_date"),
            "tags": meta.get("tags", []),
            "funnel_stage": meta.get("funnel_stage"),
            "canonical_url": meta.get("canonical_url"),
        })
        print(f"  OK   {folder}")

    index = {
        "last_updated": str(date.today()),
        "total_articles": len(articles),
        "author": "Dr. Hernani Costa",
        "publication": "First AI Movers",
        "canonical_base": "https://radar.firstaimovers.com",
        "license": "CC BY 4.0",
        "articles": articles,
    }

    print(f"\n--- Summary ---")
    print(f"Indexed: {len(articles)}")
    print(f"Skipped: {skipped}")

    if args.dry_run:
        print("\n[DRY RUN] Index would be:\n")
        print(json.dumps(index, indent=2, ensure_ascii=False))
    else:
        push_index(index)
        print(f"Done. {len(articles)} articles indexed.")


if __name__ == "__main__":
    main()
