"""Deterministic quality gate for AI-generated summaries.

This module is intentionally narrow and stateless. It owns the
arithmetic and shape checks that LLM-based verifiers consistently
miss — word bands, citation IDs, fabricated headings, empty fields,
markdown leakage — and returns a structured ``GateResult`` that
``tools/build_summaries.py`` consumes to decide whether to retry,
mark for human review, or reject outright.

Design notes:

- The 2026-05-31 smoke + addendum + 12-article live benchmark established
  that Anthropic Haiku 4.5 is unreliable for word-count arithmetic and
  scored band-missing outputs 5/5 on ``word_count_compliance``. This
  gate exists to be the load-bearing word-count enforcer.

- ``RETRYABLE`` is reserved for the case where exactly one or more
  fields are below their minimum word count and everything else is clean.
  That is the failure shape the retry loop in ``build_summaries.py``
  can actually fix by re-prompting only the offending fields.

- All other failure modes (over-maximum, orphan citations, fabricated
  FAQ headings, markdown leakage, empty fields, schema breaks) require
  human attention and surface as ``HUMAN_REVIEW`` or ``REJECT``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


WORD_TARGETS: dict[str, tuple[int, int]] = {
    "short": (40, 60),
    "medium": (170, 230),
    "long": (430, 570),
}

# Map the public field names exposed in the summary JSON object to the
# internal target keys above. Build/apply paths use "summary_short",
# "summary_medium", "summary_long"; the canonical-key form keeps the
# gate compatible with both shapes.
FIELD_TO_TARGET: dict[str, str] = {
    "summary_short": "short",
    "summary_medium": "medium",
    "summary_long": "long",
    "short": "short",
    "medium": "medium",
    "long": "long",
}


class GateStatus(str, Enum):
    """Discrete outcome of the deterministic quality gate.

    PASS:         Summaries clear every check; safe to write as draft
                  review with a clean gate stamp.
    RETRYABLE:    One or more fields are below their minimum word count
                  and nothing else is wrong. The build pipeline may
                  re-prompt the offending fields up to ``--max-retries``.
    HUMAN_REVIEW: A non-arithmetic problem (over-maximum, citation drift,
                  fabricated heading, markdown leakage) or a mixed failure
                  the retry loop cannot safely fix without operator eyes.
    REJECT:      Structurally broken output that should not become a
                  review file — invalid JSON shape, missing required
                  fields, or empty summary text.
    """

    PASS = "PASS"
    RETRYABLE = "RETRYABLE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECT = "REJECT"


@dataclass
class GateResult:
    """Structured outcome of ``check_summaries``.

    Attributes:
        status: One of the four ``GateStatus`` values.
        issues: Human-readable list of every problem the gate detected.
            Suitable for embedding in the review file's notes block.
        undersize_fields: Public-name fields that are below their minimum
            word count. Populated only when those are the *only* problems
            (i.e. ``status == RETRYABLE``); otherwise this stays empty.
        oversize_fields: Public-name fields that are above their maximum
            word count. Surfaced for the review notes but does not by
            itself qualify for retry — operators may want to inspect
            why the model overshot before re-prompting.
        word_counts: Public-name -> word count mapping for every field
            present on input. Empty fields and missing fields are
            omitted; the ``issues`` list flags those separately.
    """

    status: GateStatus
    issues: list[str] = field(default_factory=list)
    undersize_fields: list[str] = field(default_factory=list)
    oversize_fields: list[str] = field(default_factory=list)
    word_counts: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pattern helpers
# ---------------------------------------------------------------------------

# Orphan citation IDs we surface in the gate. ``[1]`` / ``[12]`` are
# numeric footnote refs; ``S1`` / ``R5`` are the "S/R" markers the
# articles in this repo intermittently use. The gate flags these when
# they appear in the summary but not in the source — the call site
# decides whether to surface or suppress.
_ORPHAN_CITATION_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b[SR]\d{1,3}\b"),
    re.compile(r"\[\d{1,3}\]"),
)

# Fabrication heuristic: the v1 DeepSeek failure mode was to invent
# a "Frequently Asked Questions" or "Pilot plan" block at the end of
# the long summary. When the model echoes these headings inside the
# summary text but the source article doesn't introduce them, that's
# a fabrication signal worth surfacing for review.
_FABRICATION_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    ("FAQ heading", re.compile(r"\bFrequently Asked Questions\b|\bFAQ\s*:", re.IGNORECASE)),
    ("Pilot-plan heading", re.compile(r"\b(?:Pilot|Implementation)\s+Plan\b", re.IGNORECASE)),
)

# Markdown structural leakage. The summary fields are plain prose;
# anything that looks like a setext / ATX heading or a list bullet
# is most likely the model echoing article structure rather than
# producing a clean summary.
_MARKDOWN_HEADING_PATTERN = re.compile(r"(?m)^#{1,6}\s+\S")
_MARKDOWN_BULLET_PATTERN = re.compile(r"(?m)^[*\-+]\s+\S")


# ---------------------------------------------------------------------------
# Word counting
# ---------------------------------------------------------------------------

def count_words(text: str) -> int:
    """Match Python str.split convention — the project's canonical word count."""
    if not isinstance(text, str):
        return 0
    return len(text.split())


def _normalise_summaries(summaries: dict) -> dict[str, str]:
    """Return a copy keyed by canonical short/medium/long short-names.

    Accepts either the public ``summary_short`` form or the internal
    ``short`` form so the gate can run against either build_summaries.py
    paths (current and forthcoming review-file extraction).
    """
    out: dict[str, str] = {}
    for raw_key, value in summaries.items():
        target = FIELD_TO_TARGET.get(raw_key)
        if target is None:
            continue
        if isinstance(value, str):
            out[target] = value
    return out


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def check_summaries(
    summaries: object,
    source_body: Optional[str] = None,
    targets: dict[str, tuple[int, int]] = WORD_TARGETS,
) -> GateResult:
    """Run the deterministic gate against a candidate summary object.

    Args:
        summaries: The candidate dict. May use either public-form keys
            (``summary_short`` / ``summary_medium`` / ``summary_long``)
            or internal short-name keys (``short`` / ``medium`` / ``long``).
            The gate accepts both because build and review-file paths
            historically use the public form, while the provider returns
            the internal form.
        source_body: Optional article body. When supplied, the
            fabricated-heading detector skips its flag if the source
            already contains the offending heading (legitimate
            preservation of source structure). When ``None`` (the
            default), every fabrication-pattern match counts as an issue.
        targets: Per-field ``(min, max)`` word counts. Overridable for
            tests; defaults to the project-standard 40-60 / 170-230 /
            430-570 bands.

    Returns:
        ``GateResult`` with a ``status`` and a populated ``issues`` list.
    """
    issues: list[str] = []
    undersize: list[str] = []
    oversize: list[str] = []
    word_counts: dict[str, int] = {}

    # ---- Schema check ----
    if not isinstance(summaries, dict):
        return GateResult(
            status=GateStatus.REJECT,
            issues=["candidate is not a JSON object"],
        )

    normalised = _normalise_summaries(summaries)

    # The three canonical fields must all be present and non-empty. We
    # surface missing/empty fields as REJECT because there is nothing
    # for the retry loop to expand.
    missing_or_empty: list[str] = []
    for short_key in ("short", "medium", "long"):
        if short_key not in normalised:
            missing_or_empty.append(short_key)
            continue
        if not normalised[short_key].strip():
            missing_or_empty.append(short_key)
    if missing_or_empty:
        issues.append(
            f"missing or empty required fields: {', '.join(missing_or_empty)}"
        )
        return GateResult(status=GateStatus.REJECT, issues=issues)

    # ---- Word-band check (per field) ----
    for short_key, (lo, hi) in targets.items():
        text = normalised[short_key]
        wc = count_words(text)
        word_counts[short_key] = wc
        public_key = f"summary_{short_key}"
        if wc < lo:
            issues.append(
                f"{public_key} word_count={wc} BELOW minimum {lo}"
            )
            undersize.append(public_key)
        elif wc > hi:
            issues.append(
                f"{public_key} word_count={wc} ABOVE maximum {hi}"
            )
            oversize.append(public_key)

    # ---- Pattern checks (orphan citations, fabricated headings, markdown leakage) ----
    pattern_issues: list[str] = []
    for short_key, text in normalised.items():
        public_key = f"summary_{short_key}"

        for pattern in _ORPHAN_CITATION_PATTERNS:
            if pattern.search(text):
                # If the source already contains the same token, skip —
                # author may have intentionally preserved it.
                if source_body and pattern.search(source_body):
                    continue
                pattern_issues.append(
                    f"{public_key} contains orphan citation ID (regex {pattern.pattern!r})"
                )

        for name, pattern in _FABRICATION_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            if source_body and pattern.search(source_body):
                # Source uses the same heading; not fabrication.
                continue
            pattern_issues.append(
                f"{public_key} fabricated heading match ({name!r})"
            )

        if _MARKDOWN_HEADING_PATTERN.search(text):
            pattern_issues.append(
                f"{public_key} contains markdown heading (lines starting with #)"
            )
        if _MARKDOWN_BULLET_PATTERN.search(text):
            pattern_issues.append(
                f"{public_key} contains markdown bullet (lines starting with - or *)"
            )

    issues.extend(pattern_issues)

    # ---- Decide status ----
    has_undersize = bool(undersize)
    has_oversize = bool(oversize)
    has_pattern = bool(pattern_issues)

    if not (has_undersize or has_oversize or has_pattern):
        return GateResult(
            status=GateStatus.PASS,
            issues=[],
            undersize_fields=[],
            oversize_fields=[],
            word_counts=word_counts,
        )

    # RETRYABLE is reserved for "only undersize" — the case the retry
    # loop can safely fix. Oversize and pattern violations are
    # operator-eyes work.
    if has_undersize and not has_oversize and not has_pattern:
        return GateResult(
            status=GateStatus.RETRYABLE,
            issues=issues,
            undersize_fields=undersize,
            oversize_fields=[],
            word_counts=word_counts,
        )

    return GateResult(
        status=GateStatus.HUMAN_REVIEW,
        issues=issues,
        undersize_fields=undersize,
        oversize_fields=oversize,
        word_counts=word_counts,
    )
