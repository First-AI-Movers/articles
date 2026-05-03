#!/usr/bin/env python3
"""Tests for tools/final_audit.py"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_SCRIPT = REPO_ROOT / "tools" / "final_audit.py"


def test_script_exists():
    assert AUDIT_SCRIPT.exists()


def test_help_flag():
    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "final archive audit harness" in result.stdout.lower()


def test_default_mode_exits_cleanly():
    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode in (0, 1)
    assert "FINAL ARCHIVE AUDIT" in result.stdout
    assert "Repo structure" in result.stdout
    assert "Check" in result.stdout
    assert "Status" in result.stdout


def test_strict_mode_runs():
    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), "--strict"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode in (0, 1)
    # In strict mode every check should be classified as required
    assert "YES" in result.stdout


def test_skip_local_flag():
    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT), "--skip-local"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode in (0, 1)
    assert "Skipped via --skip-local" in result.stdout


def test_read_only_behavior():
    import hashlib

    paths = [REPO_ROOT / "index.json", REPO_ROOT / "README.md"]
    hashes_before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.exists()}

    subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )

    hashes_after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.exists()}
    assert hashes_before == hashes_after, "final_audit.py modified file content on disk"
