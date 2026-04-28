#!/usr/bin/env python3
"""Generate docs/CHANGELOG.md from git history.

This is a manual-reviewed snapshot tool. It is not wired into CI.
Run it locally when you want to refresh the changelog, then review and commit.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG_PATH = REPO_ROOT / "docs" / "CHANGELOG.md"
# Extracted from git remote URL; fallback if detection fails.
DEFAULT_REPO_URL = "https://github.com/First-AI-Movers/articles"

# Conventional commit types we recognize and group by.
TYPE_LABELS = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "docs": "Documentation",
    "test": "Tests",
    "refactor": "Refactors",
    "chore": "Chores",
    "style": "Style",
    "ci": "CI/CD",
    "build": "Build",
    "perf": "Performance",
}


def _repo_url() -> str:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
        )
        url = result.stdout.strip()
        # Normalize SSH → HTTPS
        if url.startswith("git@github.com:"):
            url = url.replace("git@github.com:", "https://github.com/")
        if url.endswith(".git"):
            url = url[:-4]
        return url
    except subprocess.CalledProcessError:
        return DEFAULT_REPO_URL


def _git_log(max_entries: int) -> list[dict]:
    """Return list of {sha, subject, pr} dicts for commits with PR numbers."""
    result = subprocess.run(
        ["git", "log", "--oneline", "--format=%H %s"],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    entries = []
    pr_re = re.compile(r"\(#(\d+)\)$")
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        sha, subject = line.split(" ", 1)
        m = pr_re.search(subject)
        if not m:
            continue
        pr = int(m.group(1))
        # Strip PR suffix from subject for cleaner display
        clean_subject = subject[: m.start()].strip()
        entries.append({"sha": sha, "subject": clean_subject, "pr": pr})
        if len(entries) >= max_entries:
            break
    return entries


def _parse_type(subject: str) -> str | None:
    """Extract conventional commit type, or None if not conventional."""
    m = re.match(r"^(feat|fix|docs|test|refactor|chore|style|ci|build|perf)(\(.+\))?!?:\s*(.+)$", subject)
    if m:
        return m.group(1)
    return None


def _pr_link(repo_url: str, pr: int) -> str:
    return f"[{pr}]({repo_url}/pull/{pr})"


def _render(entries: list[dict], repo_url: str) -> str:
    lines = [
        "# Changelog",
        "",
        "> This is a reviewed snapshot generated manually. It is not deployment-generated.",
        "> Run `python3 tools/build_changelog.py` to refresh.",
        "",
    ]

    grouped: dict[str, list[dict]] = {label: [] for label in TYPE_LABELS.values()}
    other: list[dict] = []

    for entry in entries:
        ctype = _parse_type(entry["subject"])
        if ctype and ctype in TYPE_LABELS:
            grouped[TYPE_LABELS[ctype]].append(entry)
        else:
            other.append(entry)

    # Render in a deterministic order
    for label in TYPE_LABELS.values():
        group = grouped[label]
        if not group:
            continue
        lines.append(f"## {label}")
        lines.append("")
        for entry in group:
            link = _pr_link(repo_url, entry["pr"])
            lines.append(f"- {entry['subject']} ({link})")
        lines.append("")

    if other:
        lines.append("## Other Changes")
        lines.append("")
        for entry in other:
            link = _pr_link(repo_url, entry["pr"])
            lines.append(f"- {entry['subject']} ({link})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate CHANGELOG.md from git history")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if CHANGELOG.md would change")
    parser.add_argument("--max-entries", type=int, default=50, help="Max PR entries to include (default: 50)")
    args = parser.parse_args(argv)

    repo_url = _repo_url()
    entries = _git_log(args.max_entries)
    output = _render(entries, repo_url)

    if args.check:
        if not CHANGELOG_PATH.exists():
            print("[changelog] CHANGELOG.md does not exist")
            return 1
        existing = CHANGELOG_PATH.read_text(encoding="utf-8")
        if existing == output:
            print("[changelog] CHANGELOG.md is up to date")
            return 0
        print("[changelog] CHANGELOG.md would change")
        return 1

    CHANGELOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHANGELOG_PATH.write_text(output, encoding="utf-8")
    print(f"[changelog] wrote {CHANGELOG_PATH} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
