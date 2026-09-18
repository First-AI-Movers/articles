#!/usr/bin/env python3
"""pytest configuration for tools/tests/."""

import sys
from pathlib import Path

# Add tools/ to path so test modules can import production modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_archive_eligibility_gate(monkeypatch):
    """The suite must not depend on the runner's environment.

    The ingestion, reconciliation and recovery workflows export
    ARCHIVE_ELIGIBILITY_GATE at workflow level, so their `Run pytest` step inherits
    the repository's live gate. A test that calls eligibility() without an explicit
    gate would then run the receipt gate with no verifier and fail on the runner
    while passing locally (run 35343958460). Every test starts from the default
    gate; a test that wants the receipt gate passes gate="receipt" explicitly or
    sets the variable itself.
    """
    monkeypatch.delenv("ARCHIVE_ELIGIBILITY_GATE", raising=False)
