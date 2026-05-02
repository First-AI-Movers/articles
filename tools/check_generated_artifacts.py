#!/usr/bin/env python3
"""Check whether committed generated artifacts are current.

Runs rebuild_local.py on the working tree, compares the generated artifacts
against their committed versions, and restores the originals. Exits nonzero
if any committed artifact would change.

Does not commit, push, or auto-fix drift.
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Artifacts produced by rebuild_local.py that are committed to the repo.
# Order matches the rough dependency chain (index first, then derived files).
ARTIFACTS = [
    "index.json",
    "sitemap.xml",
    "feed.xml",
    "feed.json",
    "llms.txt",
    "llms-full.txt",
    "llms-recent.txt",
    "README.md",
]


def check_artifacts(repo_root: Path, rebuild_cmd: list[str] | None = None) -> tuple[int, list[str]]:
    """Check whether committed generated artifacts are current.

    Returns (exit_code, drift_messages).  exit_code 0 means all artifacts
    match; 1 means at least one artifact would change.
    """
    if rebuild_cmd is None:
        rebuild_cmd = [sys.executable, str(repo_root / "tools" / "rebuild_local.py")]

    backups: dict[str, bytes] = {}
    try:
        # Backup current artifacts
        for name in ARTIFACTS:
            path = repo_root / name
            if path.exists():
                backups[name] = path.read_bytes()

        # Run rebuild_local.py
        result = subprocess.run(
            rebuild_cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return 1, [f"rebuild_local.py failed: {result.stderr.strip()}"]

        # Compare artifacts
        drift: list[str] = []
        for name in ARTIFACTS:
            path = repo_root / name
            if name not in backups:
                if path.exists():
                    drift.append(f"{name} (new, not previously committed)")
                else:
                    drift.append(f"{name} (missing)")
                continue
            if not path.exists():
                drift.append(f"{name} (deleted)")
                continue
            current = path.read_bytes()
            if current != backups[name]:
                drift.append(f"{name} (changed)")

        if drift:
            return 1, drift

        return 0, []

    finally:
        # Restore original artifacts so the working tree is unchanged
        for name, content in backups.items():
            (repo_root / name).write_bytes(content)
        # Remove any artifacts that were newly created but not previously committed
        for name in ARTIFACTS:
            if name not in backups:
                path = repo_root / name
                if path.exists():
                    path.unlink()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check committed generated artifacts for drift against rebuild_local.py output."
    )
    parser.parse_args(argv)

    code, messages = check_artifacts(REPO_ROOT)
    if code != 0:
        print("[artifact-check] FAILED: committed artifacts are stale", file=sys.stderr)
        for msg in messages:
            print(f"  - {msg}", file=sys.stderr)
        return 1

    print("[artifact-check] PASSED: all artifacts current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
