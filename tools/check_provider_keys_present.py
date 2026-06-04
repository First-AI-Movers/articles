#!/usr/bin/env python3
"""Presence-only provider-key smoke for the summary-automation rollout.

Reports ``present`` / ``absent`` for named environment variables **without ever
revealing a value, length, prefix, suffix, or hash**, and **fails closed**: it
exits non-zero if any *required* key is absent. It makes **zero** outbound calls
and imports no provider SDK and no secret-manager client — it reads
``os.environ`` only.

Used by ``.github/workflows/summary-automation-smoke.yml`` (Envelope 2 of the
summary-CI-automation rollout). The generator + dual-verifier keys are REQUIRED;
DeepSeek is OPTIONAL (it is the long-only-undersize fallback and is reported but
never enforced unless a future decision promotes it into ``--required``).

Canonical keys::

    MINIMAX_API_KEY    primary generator        (required)
    OPENAI_API_KEY     primary verifier         (required)
    ANTHROPIC_API_KEY  secondary verifier       (required)
    DEEPSEEK_API_KEY   long-undersize fallback  (optional)
"""

from __future__ import annotations

import argparse
import os
import sys

DEFAULT_REQUIRED = ("MINIMAX_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
DEFAULT_OPTIONAL = ("DEEPSEEK_API_KEY",)


def _is_present(name: str) -> bool:
    """Return True iff the env var is set and non-empty.

    The ONLY contact with the value is ``bool(...)`` over a stripped lookup; the
    value is never returned, logged, measured, or hashed.
    """
    return bool(os.environ.get(name, "").strip())


def check_presence(required: list[str], optional: list[str]) -> int:
    """Print present/absent per key; return non-zero iff a required key is absent."""
    print("[key-presence] provider-key presence probe (no network):")
    missing_required: list[str] = []
    for name in required:
        present = _is_present(name)
        print(f"  - {name}: {'present' if present else 'absent'} (required)")
        if not present:
            missing_required.append(name)
    for name in optional:
        present = _is_present(name)
        print(f"  - {name}: {'present' if present else 'absent'} (optional)")

    if missing_required:
        # Names only — never a value. This is the fail-closed signal.
        print(
            "[key-presence] FAIL: required key(s) absent: "
            + ", ".join(missing_required)
        )
        return 1
    print("[key-presence] OK: all required keys present.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Presence-only provider-key smoke (no network, no secret values).",
    )
    parser.add_argument(
        "--required",
        nargs="+",
        default=list(DEFAULT_REQUIRED),
        metavar="ENV_VAR",
        help=(
            "Env-var names that MUST be present; the command fails closed "
            "(non-zero exit) if any is absent. "
            "Default: MINIMAX_API_KEY OPENAI_API_KEY ANTHROPIC_API_KEY."
        ),
    )
    parser.add_argument(
        "--optional",
        nargs="*",
        default=list(DEFAULT_OPTIONAL),
        metavar="ENV_VAR",
        help="Env-var names reported but never enforced. Default: DEEPSEEK_API_KEY.",
    )
    args = parser.parse_args(argv)
    return check_presence(args.required, args.optional)


if __name__ == "__main__":
    raise SystemExit(main())
