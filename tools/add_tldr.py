#!/usr/bin/env python3
"""Add TL;DR sections to articles that don't have one.

Scans articles/*/article.md via the GitHub API, detects missing TL;DR
sections, generates them with GPT-4o-mini, and pushes the updated files.

Usage:
    python3 tools/add_tldr.py                    # process all missing
    python3 tools/add_tldr.py --limit 50         # process up to 50
    python3 tools/add_tldr.py --dry-run --limit 5  # preview 5, don't push
"""

import argparse
import base64
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    sys.exit("openai package not installed. Run: pip install openai")

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

_script_dir = Path(__file__).resolve().parent
_repo_root = _script_dir.parent
load_dotenv(_repo_root / ".env")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    sys.exit("GITHUB_TOKEN not set. Copy .env.example to .env and add your token.")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    # Try fetching from 1Password at runtime
    import subprocess
    try:
        result = subprocess.run(
            ["op", "item", "get", "radar-engine",
             "--vault", "publicinnovation-infra",
             "--fields", "openrouter_api_key", "--reveal"],
            capture_output=True, text=True, timeout=15,
        )
        OPENAI_API_KEY = result.stdout.strip()
    except Exception:
        pass
    if not OPENAI_API_KEY:
        sys.exit(
            "OPENAI_API_KEY not set and 1Password lookup failed.\n"
            "Either set OPENAI_API_KEY in .env or sign in to 1Password: eval $(op signin)"
        )

REPO = "First-AI-Movers/articles"
API = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-4o-mini"

TLDR_PROMPT = """You are summarizing an article by Dr. Hernani Costa for First AI Movers.
Write a TL;DR of exactly 2-3 sentences (40-60 words).
- Lead with the core insight or decision the reader should take away
- Be specific — include a number, framework name, or concrete claim when possible
- Write for a busy executive who will read nothing else
- Do not start with "This article" or "In this article"
- Do not use the phrase "TL;DR" in the text itself

Article:
{article_text}"""

# Patterns that indicate a summary section already exists
SUMMARY_PATTERNS = re.compile(
    r"^##\s*(TL;DR|TLDR|Executive Summary|Key Takeaway|In Brief|Summary)\b",
    re.IGNORECASE | re.MULTILINE,
)

# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------


def get_all_folders():
    """Return sorted list of article folder names."""
    url = f"{API}/contents/articles"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return sorted(item["name"] for item in r.json() if item["type"] == "dir")


def fetch_file(path):
    """Return (content_str, sha) for a file in the repo."""
    url = f"{API}/contents/{path}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def push_file(path, content, sha, message):
    """Update a file via the GitHub Contents API."""
    encoded = base64.b64encode(content.encode()).decode()
    body = {
        "message": message,
        "content": encoded,
        "sha": sha,
        "committer": {"name": "Index Bot", "email": "info@firstaimovers.com"},
    }
    url = f"{API}/contents/{path}"
    r = requests.put(url, headers=HEADERS, json=body, timeout=30)
    r.raise_for_status()
    return r.json()["commit"]["sha"][:7]


# ---------------------------------------------------------------------------
# TL;DR detection and injection
# ---------------------------------------------------------------------------


def has_summary(content):
    """Check if article already has a TL;DR or equivalent section."""
    # Check first 50 lines after front matter
    lines = content.split("\n")
    # Skip past front matter
    in_front_matter = False
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if not in_front_matter:
                in_front_matter = True
            else:
                start = i + 1
                break

    check_region = "\n".join(lines[start : start + 50])
    return bool(SUMMARY_PATTERNS.search(check_region))


def strip_front_matter(content):
    """Return article text without YAML front matter."""
    lines = content.split("\n")
    in_fm = False
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if not in_fm:
                in_fm = True
            else:
                start = i + 1
                break
    return "\n".join(lines[start:]).strip()


def generate_tldr(article_text, client):
    """Generate a TL;DR using GPT-4o-mini."""
    # Truncate to ~3000 words to stay within token limits and save cost
    words = article_text.split()
    if len(words) > 3000:
        truncated = " ".join(words[:3000])
    else:
        truncated = article_text

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": TLDR_PROMPT.format(article_text=truncated)},
        ],
        max_tokens=150,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def inject_tldr(content, tldr_text):
    """Insert TL;DR section after the first H1 heading.

    Result:
        ---
        (front matter)
        ---

        # Title

        ## TL;DR

        > summary text here

        (rest of article)
    """
    lines = content.split("\n")

    # Find end of front matter
    fm_end = 0
    in_fm = False
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if not in_fm:
                in_fm = True
            else:
                fm_end = i
                break

    # Find first H1 after front matter
    h1_idx = None
    for i in range(fm_end + 1, len(lines)):
        if lines[i].startswith("# ") and not lines[i].startswith("## "):
            h1_idx = i
            break

    if h1_idx is None:
        # No H1 found — insert after front matter
        insert_at = fm_end + 1
    else:
        # Insert after the H1 line (and any blank line right after it)
        insert_at = h1_idx + 1
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1

    # Build the TL;DR block
    # Wrap each sentence as a blockquote line
    tldr_block = [
        "",
        "## TL;DR",
        "",
    ]
    for line in tldr_text.split("\n"):
        tldr_block.append(f"> {line}")
    tldr_block.append("")

    # Insert
    new_lines = lines[:insert_at] + tldr_block + lines[insert_at:]
    return "\n".join(new_lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Add TL;DR to articles missing one")
    parser.add_argument("--dry-run", action="store_true", help="Preview without pushing")
    parser.add_argument("--limit", type=int, default=0, help="Max articles to process (0=all)")
    args = parser.parse_args()

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENROUTER_BASE)

    print(f"Fetching article folders from {REPO}...")
    folders = get_all_folders()
    print(f"Found {len(folders)} folders\n")

    processed = 0
    skipped_has_summary = 0
    skipped_no_file = 0
    errors = 0

    for folder in folders:
        if args.limit and processed >= args.limit:
            break

        path = f"articles/{folder}/article.md"
        content, sha = fetch_file(path)

        if content is None:
            skipped_no_file += 1
            continue

        if has_summary(content):
            skipped_has_summary += 1
            continue

        # Generate TL;DR
        try:
            article_text = strip_front_matter(content)
            if len(article_text.split()) < 50:
                print(f"  SKIP {folder} (too short: {len(article_text.split())} words)")
                skipped_no_file += 1
                continue

            tldr = generate_tldr(article_text, client)
            new_content = inject_tldr(content, tldr)

            if args.dry_run:
                print(f"  PREVIEW {folder}")
                print(f"    TL;DR: {tldr[:120]}...")
                print()
            else:
                commit_sha = push_file(path, new_content, sha,
                                        f"content: add TL;DR to {folder}")
                print(f"  OK   {folder} ({commit_sha})")

            processed += 1

            # Small delay to be polite to APIs
            if not args.dry_run:
                time.sleep(0.5)

        except Exception as e:
            print(f"  ERR  {folder} ({e})")
            errors += 1

    print(f"\n--- Summary ---")
    print(f"Processed:       {processed}")
    print(f"Already had TL;DR: {skipped_has_summary}")
    print(f"Skipped (no file/short): {skipped_no_file}")
    print(f"Errors:          {errors}")

    if args.dry_run:
        print("\n[DRY RUN] No files were pushed.")
    else:
        print(f"\nDone. {processed} articles updated with TL;DR.")


if __name__ == "__main__":
    main()
