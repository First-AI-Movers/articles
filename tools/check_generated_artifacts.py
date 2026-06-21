#!/usr/bin/env python3
"""Check whether committed generated artifacts are current.

Runs rebuild_local.py on the working tree, compares the generated artifacts
against their committed versions, and restores the originals. Exits nonzero
if any committed artifact would change.

Does not commit, push, or auto-fix drift.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# --- generation-timestamp normalization ---------------------------------------
# rebuild_local.py stamps a *generation date* (`date.today()`) into a few fields:
# index.json `last_updated`, README.md `dateModified`, the llms-*.txt `- Generated:`
# footer, and the sitemap `<lastmod>` of the STATIC aggregate pages (homepage,
# /about/, /topics/ — see build_sitemap()). These drift on every rebuild that lands
# on a different calendar day, even with zero content change, which made the
# advisory drift check a recurring false failure for docs/maintenance PRs.
#
# The comparison normalizes ONLY those generation timestamps. It must NOT touch
# content dates: per-article / per-topic sitemap `<lastmod>` (the topic hub's
# newest-article date), feed `feed_updated`/`pubDate`/`date_published` (the newest
# article's published date), or any human-authored/source date — a real
# content-freshness change must still fail the check.
_DATE = rb"\d{4}-\d{2}-\d{2}"
_DATE_PLACEHOLDER = b"<GENERATION-DATE>"
# Sitemap loc paths whose <lastmod> is the build date (NOT a content date), per
# rebuild_local.build_sitemap(). Keep in sync with that function.
_SITEMAP_STATIC_LOCS = (
    b"https://articles.firstaimovers.com/",
    b"https://articles.firstaimovers.com/about/",
    b"https://articles.firstaimovers.com/topics/",
)


def _normalize_generation_dates(name: str, data: bytes) -> bytes:
    """Replace generation-time date stamps with a placeholder so a build-date-only
    diff does not register as drift. Content dates are left untouched."""
    if name == "index.json":
        data = re.sub(rb'("last_updated":\s*")' + _DATE + rb'(")', rb"\1" + _DATE_PLACEHOLDER + rb"\2", data)
    elif name == "README.md":
        data = re.sub(rb'("dateModified":\s*")' + _DATE + rb'(")', rb"\1" + _DATE_PLACEHOLDER + rb"\2", data)
    elif name in ("llms.txt", "llms-index.txt", "llms-full.txt", "llms-recent.txt"):
        data = re.sub(rb"(?m)^(- Generated: )" + _DATE + rb"[ \t]*$", rb"\1" + _DATE_PLACEHOLDER, data)
    elif name == "sitemap.xml":
        for loc in _SITEMAP_STATIC_LOCS:
            data = re.sub(
                rb"(<loc>" + re.escape(loc) + rb"</loc>\s*<lastmod>)" + _DATE + rb"(</lastmod>)",
                rb"\1" + _DATE_PLACEHOLDER + rb"\2",
                data,
            )
    return data

REPO_ROOT = Path(__file__).resolve().parent.parent

# Artifacts produced by the rebuild pipeline that are committed to the repo.
# Order matches the rough dependency chain (index first, then derived files,
# then docs whose stats reference them, then export artifacts that consume them).
#
# rebuild_local.py owns: index.json, sitemap.xml, feed.xml, feed.json,
#   llms.txt, llms-full.txt, llms-recent.txt, README.md
# update_docs.py owns:   ROADMAP.md's `auto:operational-state` block
# export_mcp_data.py owns: mcp-server/src/generated/archive-data.json
#
# Each of those rebuild tools is invoked by check_artifacts() in turn so the
# diff step compares all committed outputs against a fresh regeneration.
# This catches the recurring "stale derived file" drift that landed cleanup
# commits in PRs #178, #179, and #180.
ARTIFACTS = [
    "index.json",
    "sitemap.xml",
    "feed.xml",
    "feed.json",
    "llms.txt",
    "llms-index.txt",
    "llms-full.txt",
    "llms-recent.txt",
    "README.md",
    "ROADMAP.md",
    "mcp-server/src/generated/archive-data.json",
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

        # Run update_docs.py to patch ROADMAP.md's auto:operational-state block.
        # rebuild_local.py covers README/llms.txt; update_docs.py owns ROADMAP.
        # Mirrors the ingestion workflows' two-step pattern. Skipped if the
        # script is missing (older trees without E16 dynamic docs).
        update_docs = repo_root / "tools" / "update_docs.py"
        if update_docs.exists():
            result = subprocess.run(
                [sys.executable, str(update_docs)],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return 1, [f"update_docs.py failed: {result.stderr.strip()}"]

        # Run export_mcp_data.py to refresh mcp-server/src/generated/archive-data.json.
        # The MCP server's bundled data is fed from index.json + article markdown,
        # so it drifts whenever those drift. Catching it here in the same `check`
        # job consolidates a class of "surprise drift" that previously only
        # surfaced when an unrelated PR happened to touch mcp-server/** paths
        # (cf. the cleanup commit in PR #180).
        #
        # pyarrow is only needed for the embeddings.json sibling output; the
        # archive-data.json export uses stdlib only. We pass the --skip-embeddings
        # flag if the script supports it; otherwise we treat a pyarrow-missing
        # error as a non-blocking skip so the check still passes in environments
        # without pyarrow. CI installs pyarrow via tools/requirements.txt.
        export_mcp = repo_root / "tools" / "export_mcp_data.py"
        if export_mcp.exists():
            result = subprocess.run(
                [sys.executable, str(export_mcp)],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                err = (result.stderr or "").strip()
                # Tolerate the local-env pyarrow gap; archive-data.json itself
                # only needs stdlib + index.json. Still report so the operator
                # sees there was a soft skip.
                if "pyarrow" in err.lower():
                    print(
                        f"[artifact-check] WARN: skipping MCP export (pyarrow missing); "
                        f"archive-data.json drift cannot be verified locally",
                        file=sys.stderr,
                    )
                else:
                    return 1, [f"export_mcp_data.py failed: {err}"]

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
            # Compare with generation-date stamps normalized so a build-date-only
            # difference is not reported as drift (content dates stay exact).
            if _normalize_generation_dates(name, current) != _normalize_generation_dates(name, backups[name]):
                drift.append(f"{name} (changed)")

        if drift:
            return 1, drift

        return 0, []

    finally:
        # Restore original artifacts so the working tree is unchanged.
        # mkdir parents in case a rebuild step deleted an intermediate dir
        # (defense in depth — should not happen in practice for the current
        # rebuild pipeline, but cheap insurance).
        for name, content in backups.items():
            path = repo_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
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
