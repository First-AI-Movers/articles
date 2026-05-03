#!/usr/bin/env python3
"""Final archive audit harness.

Runs a suite of read-only, deterministic checks to verify archive readiness
for v1 freeze. Returns nonzero if any required check fails.

Usage:
    python3 tools/final_audit.py
    python3 tools/final_audit.py --strict      # treat optional checks as required
    python3 tools/final_audit.py --skip-local  # skip checks that need optional deps
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = REPO_ROOT / "articles"

# Expected article count at v1 freeze
EXPECTED_ARTICLE_COUNT = 829


def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def check_repo_structure() -> dict:
    """Verify article folder structure."""
    errors = []
    warnings = []

    if not ARTICLES_DIR.exists():
        errors.append("articles/ directory does not exist")
        return {"name": "Repo structure", "required": True, "passed": False, "errors": errors, "warnings": warnings}

    folders = [d for d in ARTICLES_DIR.iterdir() if d.is_dir() and d.name != "__pycache__"]
    count = len(folders)

    if count != EXPECTED_ARTICLE_COUNT:
        warnings.append(f"Article count {count} != expected {EXPECTED_ARTICLE_COUNT}")

    missing_md = 0
    missing_meta = 0
    for folder in folders:
        if not (folder / "article.md").exists():
            missing_md += 1
        if not (folder / "metadata.json").exists():
            missing_meta += 1

    if missing_md:
        errors.append(f"{missing_md} article folder(s) missing article.md")
    if missing_meta:
        errors.append(f"{missing_meta} article folder(s) missing metadata.json")

    # Check required root files
    for fname in ("README.md", "LICENSE", "LICENSE-CODE", "CITATION.cff", "index.json", "sitemap.xml"):
        if not (REPO_ROOT / fname).exists():
            errors.append(f"Missing root file: {fname}")

    passed = len(errors) == 0
    return {"name": "Repo structure", "required": True, "passed": passed, "errors": errors, "warnings": warnings}


def check_tool(name: str, cmd: list[str], required: bool) -> dict:
    """Run an existing tool and classify the result."""
    try:
        rc, stdout, stderr = run_cmd(cmd)
    except FileNotFoundError as e:
        return {
            "name": name,
            "required": required,
            "passed": False,
            "errors": [f"Command not found: {e}"],
            "warnings": [],
        }
    except Exception as e:
        return {
            "name": name,
            "required": required,
            "passed": False,
            "errors": [f"Exception: {e}"],
            "warnings": [],
        }

    output = (stdout + stderr).strip()
    passed = rc == 0
    errors = []
    warnings = []

    if not passed:
        # Truncate long output
        msg = output.splitlines()[0] if output else f"Exit code {rc}"
        if len(msg) > 200:
            msg = msg[:200] + "..."
        errors.append(msg)

    return {"name": name, "required": required, "passed": passed, "errors": errors, "warnings": warnings}


def check_generated_artifacts() -> dict:
    """Check whether committed generated artifacts are current."""
    return check_tool(
        "Generated artifacts current",
        [sys.executable, "tools/check_generated_artifacts.py"],
        required=True,
    )


def check_duplicate_titles() -> dict:
    return check_tool(
        "No duplicate titles",
        [sys.executable, "tools/check_duplicate_titles.py"],
        required=True,
    )


def check_citation() -> dict:
    return check_tool(
        "CITATION.cff valid",
        [sys.executable, "tools/check_citation.py"],
        required=True,
    )


def check_errata() -> dict:
    return check_tool(
        "Errata valid",
        [sys.executable, "tools/check_errata.py"],
        required=True,
    )


def check_translations() -> dict:
    return check_tool(
        "Translations valid",
        [sys.executable, "tools/check_translations.py"],
        required=True,
    )


def check_translation_quality() -> dict:
    return check_tool(
        "Translation QA",
        [sys.executable, "tools/check_translation_quality.py"],
        required=True,
    )


def check_citation_graph() -> dict:
    return check_tool(
        "Citation graph current",
        [sys.executable, "tools/build_citation_graph.py", "--check"],
        required=True,
    )


def check_normalize_tags() -> dict:
    return check_tool(
        "Tags normalized",
        [sys.executable, "tools/normalize_tags.py", "--dry-run"],
        required=True,
    )


def check_changelog() -> dict:
    return check_tool(
        "CHANGELOG.md current",
        [sys.executable, "tools/build_changelog.py", "--check"],
        required=False,
    )


def check_pytest() -> dict:
    # Avoid infinite recursion when the audit is run from inside pytest.
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return {
            "name": "pytest tools/tests",
            "required": False,
            "passed": None,
            "errors": [],
            "warnings": ["Skipped: already running inside pytest"],
        }
    return check_tool(
        "pytest tools/tests",
        [sys.executable, "-m", "pytest", "tools/tests", "-q"],
        required=False,
    )


def check_sitemap_urls() -> dict:
    """Quick sitemap sanity check."""
    sitemap = REPO_ROOT / "sitemap.xml"
    errors = []
    warnings = []
    if not sitemap.exists():
        errors.append("sitemap.xml not found")
        return {"name": "Sitemap parseable", "required": True, "passed": False, "errors": errors, "warnings": warnings}

    text = sitemap.read_text(encoding="utf-8")
    url_count = text.count("<url>")
    if url_count == 0:
        errors.append("No URLs in sitemap.xml")
    # Expected: ~80 URLs (topics + articles + static pages)
    # We do not enforce exact count because it changes with content
    passed = len(errors) == 0
    return {"name": "Sitemap parseable", "required": True, "passed": passed, "errors": errors, "warnings": warnings}


def check_llms_files() -> dict:
    """Verify llms files exist and have content."""
    errors = []
    warnings = []
    for fname in ("llms.txt", "llms-full.txt", "llms-recent.txt"):
        path = REPO_ROOT / fname
        if not path.exists():
            errors.append(f"{fname} missing")
            continue
        size = path.stat().st_size
        if size == 0:
            errors.append(f"{fname} is empty")
        elif size < 100:
            warnings.append(f"{fname} suspiciously small ({size} bytes)")

    passed = len(errors) == 0
    return {"name": "LLMS files present", "required": True, "passed": passed, "errors": errors, "warnings": warnings}


def check_feed_files() -> dict:
    """Verify feed files exist and have content."""
    errors = []
    warnings = []
    for fname in ("feed.xml", "feed.json"):
        path = REPO_ROOT / fname
        if not path.exists():
            errors.append(f"{fname} missing")
            continue
        size = path.stat().st_size
        if size == 0:
            errors.append(f"{fname} is empty")

    passed = len(errors) == 0
    return {"name": "Feed files present", "required": True, "passed": passed, "errors": errors, "warnings": warnings}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Final archive audit harness")
    parser.add_argument("--strict", action="store_true", help="Treat optional checks as required")
    parser.add_argument("--skip-local", action="store_true", help="Skip checks that need optional local deps")
    args = parser.parse_args(argv)

    checks = [
        check_repo_structure(),
        check_generated_artifacts(),
        check_duplicate_titles(),
        check_citation(),
        check_errata(),
        check_translations(),
        check_translation_quality(),
        check_citation_graph(),
        check_normalize_tags(),
        check_sitemap_urls(),
        check_llms_files(),
        check_feed_files(),
    ]

    if not args.skip_local:
        checks.append(check_changelog())
        checks.append(check_pytest())
    else:
        checks.append({
            "name": "CHANGELOG.md current",
            "required": False,
            "passed": None,
            "errors": [],
            "warnings": ["Skipped via --skip-local"],
        })
        checks.append({
            "name": "pytest tools/tests",
            "required": False,
            "passed": None,
            "errors": [],
            "warnings": ["Skipped via --skip-local"],
        })

    if args.strict:
        for c in checks:
            c["required"] = True

    # Summary table
    print("=" * 70)
    print("FINAL ARCHIVE AUDIT")
    print("=" * 70)
    print(f"{'Check':<40} {'Req':>4} {'Status':>10} {'Notes':>12}")
    print("-" * 70)

    required_failures = 0
    optional_failures = 0
    for c in checks:
        name = c["name"]
        req = "YES" if c["required"] else "no"
        if c["passed"] is None:
            status = "SKIP"
        else:
            status = "PASS" if c["passed"] else "FAIL"
        notes = ""
        if c["errors"]:
            notes = c["errors"][0]
        elif c["warnings"]:
            notes = c["warnings"][0]
        if len(notes) > 30:
            notes = notes[:27] + "..."
        print(f"{name:<40} {req:>4} {status:>10} {notes:>12}")

        if not c["passed"]:
            if c["required"]:
                required_failures += 1
            else:
                optional_failures += 1

    print("-" * 70)
    total = len([c for c in checks if c["passed"] is not None])
    passed = len([c for c in checks if c["passed"] is True])
    print(f"Results: {passed}/{total} checks passed")
    if required_failures:
        print(f"REQUIRED failures: {required_failures}")
    if optional_failures:
        print(f"Optional failures: {optional_failures}")
    print("=" * 70)

    if required_failures:
        print("AUDIT FAILED — required checks did not pass.")
        return 1

    if optional_failures:
        print("AUDIT PASSED with optional warnings.")
    else:
        print("AUDIT PASSED — all checks green.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
