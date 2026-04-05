#!/usr/bin/env python3
"""Update README.md and llms.txt with current stats from index.json.

Run this after rebuild_index.py to keep documentation in sync.
Reads index.json from the repo root, computes stats, and patches
README.md and llms.txt with the latest numbers. Then commits and
pushes the changes via the GitHub Contents API.

Usage:
    python3 tools/update_docs.py            # update and push
    python3 tools/update_docs.py --dry-run  # show changes, don't push
"""

import argparse
import base64
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

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


def push_file(path, content, sha, message):
    """Commit a file update via the GitHub Contents API."""
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
# Stats from index.json
# ---------------------------------------------------------------------------


def compute_stats(index):
    """Derive display stats from the index payload."""
    articles = index.get("articles", [])
    total = len(articles)

    tags = set()
    funnel = {}
    dates = []
    for a in articles:
        for t in a.get("tags", []):
            tags.add(t)
        stage = a.get("funnel_stage", "unknown")
        funnel[stage] = funnel.get(stage, 0) + 1
        d = a.get("published_date")
        if d:
            dates.append(d)

    dates.sort()
    date_min = dates[0] if dates else "unknown"
    date_max = dates[-1] if dates else "unknown"

    return {
        "total": total,
        "tags_count": len(tags),
        "funnel": funnel,
        "date_min": date_min,
        "date_max": date_max,
    }


def format_date_human(iso_date):
    """Convert '2025-02-17' to 'February 17, 2025'."""
    try:
        from datetime import datetime
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
        return dt.strftime("%B %-d, %Y")
    except (ValueError, AttributeError):
        return iso_date


def funnel_summary(funnel):
    """Build 'top (221 articles), middle (423), bottom (4)' string."""
    order = ["top", "middle", "bottom"]
    parts = []
    first = True
    for stage in order:
        if stage in funnel:
            label = f"{stage} ({funnel[stage]} articles)" if first else f"{stage} ({funnel[stage]})"
            parts.append(label)
            first = False
    # Include any stages not in the standard order
    for stage, count in sorted(funnel.items()):
        if stage not in order:
            parts.append(f"{stage} ({count})")
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Patchers
# ---------------------------------------------------------------------------


def patch_readme(content, stats):
    """Apply regex replacements to README.md. Returns (new_content, changes)."""
    changes = []
    original = content

    total = stats["total"]
    tags = stats["tags_count"]
    date_min_h = format_date_human(stats["date_min"])
    date_max_h = format_date_human(stats["date_max"])
    date_min_iso = stats["date_min"]
    date_max_iso = stats["date_max"]
    funnel_str = funnel_summary(stats["funnel"])
    today_iso = str(date.today())

    # 1. JSON-LD description
    content = re.sub(
        r'("description":\s*"The canonical, open-access article archive of First AI Movers: )\d+( original articles)',
        rf"\g<1>{total}\2",
        content,
    )

    # 2. JSON-LD dateCreated / dateModified
    content = re.sub(
        r'"dateCreated":\s*"\d{4}-\d{2}-\d{2}"',
        f'"dateCreated": "{date_min_iso}"',
        content,
    )
    content = re.sub(
        r'"dateModified":\s*"\d{4}-\d{2}-\d{2}"',
        f'"dateModified": "{today_iso}"',
        content,
    )

    # 3. Badge
    content = re.sub(
        r'Articles-\d+-orange',
        f"Articles-{total}-orange",
        content,
    )

    # 4. Elevator pitch (line after badge)
    content = re.sub(
        r'— \d+ original articles on AI strategy',
        f"— {total} original articles on AI strategy",
        content,
    )

    # 5. "What Is in This Archive?" opening line
    # Format: "February 2025–April 2026"
    from datetime import datetime
    try:
        dt_min = datetime.strptime(date_min_iso, "%Y-%m-%d")
        dt_max = datetime.strptime(date_max_iso, "%Y-%m-%d")
        span = f"{dt_min.strftime('%B %Y')}–{dt_max.strftime('%B %Y')}"
    except ValueError:
        span = f"{date_min_iso} – {date_max_iso}"
    content = re.sub(
        r'full-text, machine-readable versions of \d+ original articles spanning [^.]+\.',
        f"full-text, machine-readable versions of {total} original articles spanning {span}.",
        content,
    )

    # 6. Folder count in repo structure
    content = re.sub(
        r'\(\d+ article folders\)',
        f"({total} article folders)",
        content,
    )

    # 7. Quick stats block
    content = re.sub(
        r'\*\*\d+\*\* articles indexed',
        f"**{total}** articles indexed",
        content,
    )
    content = re.sub(
        r'\*\*[\d,]+\*\* unique topic tags',
        f"**{tags:,}** unique topic tags",
        content,
    )
    content = re.sub(
        r'\*\*3 funnel stages:\*\* .+',
        f"**3 funnel stages:** {funnel_str}",
        content,
    )
    content = re.sub(
        r'\*\*Date range:\*\* .+',
        f"**Date range:** {date_min_h} – {date_max_h}",
        content,
    )

    if content != original:
        changes.append("README.md")

    return content, changes


def patch_llms_txt(content, stats):
    """Apply replacements to llms.txt. Returns (new_content, changes)."""
    original = content
    total = stats["total"]
    date_min_h = format_date_human(stats["date_min"])
    date_max_h = format_date_human(stats["date_max"])

    # Summary line
    content = re.sub(
        r'\d+ original articles on AI strategy',
        f"{total} original articles on AI strategy",
        content,
    )
    # Date range in summary — format: "Published February 2025–April 2026."
    from datetime import datetime
    try:
        dt_min = datetime.strptime(stats["date_min"], "%Y-%m-%d")
        dt_max = datetime.strptime(stats["date_max"], "%Y-%m-%d")
        span = f"{dt_min.strftime('%B %Y')}–{dt_max.strftime('%B %Y')}"
    except ValueError:
        span = f"{stats['date_min']} – {stats['date_max']}"
    content = re.sub(
        r'Published [^.]+\.',
        f"Published {span}.",
        content,
    )

    changes = ["llms.txt"] if content != original else []
    return content, changes


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Update README.md and llms.txt from index.json")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without pushing")
    args = parser.parse_args()

    # 1. Fetch index.json
    print("Fetching index.json...")
    index_content, _ = fetch_file("index.json")
    index = json.loads(index_content)
    stats = compute_stats(index)

    print(f"  Total articles: {stats['total']}")
    print(f"  Unique tags:    {stats['tags_count']}")
    print(f"  Date range:     {stats['date_min']} to {stats['date_max']}")
    print(f"  Funnel:         {funnel_summary(stats['funnel'])}")
    print()

    # 2. Fetch and patch README.md
    print("Fetching README.md...")
    readme_content, readme_sha = fetch_file("README.md")
    new_readme, readme_changes = patch_readme(readme_content, stats)

    # 3. Fetch and patch llms.txt
    print("Fetching llms.txt...")
    llms_content, llms_sha = fetch_file("llms.txt")
    new_llms, llms_changes = patch_llms_txt(llms_content, stats)

    all_changes = readme_changes + llms_changes

    if not all_changes:
        print("\nNo changes needed — docs are already up to date.")
        return

    print(f"\nFiles to update: {', '.join(all_changes)}")

    if args.dry_run:
        print("\n[DRY RUN] Would push the following changes:\n")
        if readme_changes:
            print("--- README.md (diff) ---")
            _show_diff(readme_content, new_readme)
        if llms_changes:
            print("--- llms.txt (diff) ---")
            _show_diff(llms_content, new_llms)
        return

    # 4. Push updates
    today = date.today()
    if readme_changes:
        sha = push_file("README.md", new_readme, readme_sha,
                         f"docs: update README.md stats — {stats['total']} articles ({today})")
        print(f"  README.md pushed ({sha})")

    if llms_changes:
        sha = push_file("llms.txt", new_llms, llms_sha,
                         f"docs: update llms.txt stats — {stats['total']} articles ({today})")
        print(f"  llms.txt pushed ({sha})")

    print(f"\nDone. Docs updated to {stats['total']} articles.")


def _show_diff(old, new):
    """Print a simple line-by-line diff of changed lines."""
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    for i, (o, n) in enumerate(zip(old_lines, new_lines)):
        if o != n:
            print(f"  L{i+1}:")
            print(f"    - {o.strip()[:120]}")
            print(f"    + {n.strip()[:120]}")
    print()


if __name__ == "__main__":
    main()
