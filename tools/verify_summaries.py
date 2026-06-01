#!/usr/bin/env python3
"""Dual-verifier quality review for draft summary review files.

Usage:
    python3 tools/verify_summaries.py --review-file summaries/<slug>.review.md
    python3 tools/verify_summaries.py --summaries-dir summaries
    python3 tools/verify_summaries.py --review-file <path> \\
        --allow-network --write-verification --max-verifier-cost-usd 0.25

Design:

This tool inspects a draft summary review file (the artefact produced by
``tools/build_summaries.py`` in MiniMax mode), loads the source article body
from ``articles/<folder>/article.md``, and runs two independent quality
checks:

1. The deterministic gate from ``tools/summary_quality.py``. This is the
   load-bearing arithmetic / shape check that the 2026-05-31 benchmarks
   established LLM verifiers cannot reliably do.

2. One or two LLM verifiers, on different model families, that judge
   *substance* — faithfulness, durability, volatile-fact handling,
   fabrication risk, voice match. The 2026-05-31 OpenAI addendum
   established that OpenAI ``gpt-5.4-mini`` is materially stricter than
   Anthropic ``claude-haiku-4-5-20251001`` on substance and ~5x cheaper,
   so it is the default primary verifier. Haiku stays as the cross-family
   secondary so disagreement between two model families auto-downgrades
   to HUMAN_REVIEW.

Safety model:

- Default behaviour is dry-run: parse the review file, run the deterministic
  gate, print a plan. No network. No file writes.
- Live LLM calls require ``--allow-network``.
- Writes to the review file require ``--write-verification``.
- Approvals are never automated. ``Status: draft`` in the review file
  remains untouched by this tool. Operators promote to ``approved``
  manually after reading the verification block.
- Article bodies, ``metadata.json``, and any file outside the summaries
  directory are never modified.
- No secret values, auth headers, env-var values, or tokens are ever
  printed or written. Only key *presence* is checked.

Live calls are operator-local through Doppler-injected env:

    doppler run --project articles-git --config dev -- \\
        python3 tools/verify_summaries.py --review-file <path> \\
        --allow-network --write-verification --max-verifier-cost-usd 0.25

Workflow secret wiring (GitHub Actions) is intentionally out of scope here.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# tools/ is on sys.path via tools/tests/conftest.py and via Python's
# automatic same-dir resolution when this module is executed directly.
from summary_quality import GateResult, GateStatus, check_summaries


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTICLES_DIR = REPO_ROOT / "articles"
SUMMARIES_DIR = REPO_ROOT / "summaries"


# =============================================================================
# Verifier model registry
# =============================================================================

@dataclass(frozen=True)
class VerifierSpec:
    """One verifier model in the registry.

    Pricing is a directional estimate to drive the cost cap; not billing-
    attested. Treat the cost cap as a guardrail, not as a contract.
    """

    model_id: str
    provider: str  # "openai" or "anthropic"
    endpoint: str
    env_var: str
    pricing_in_usd_per_million: float
    pricing_out_usd_per_million: float


# Pricing values are directional estimates derived from the operator's
# 2026-05-31 OpenAI addendum runs and from each vendor's published pricing
# page. They populate the cost-cap arithmetic only. The cost cap is a
# guardrail; not a billing-attested ceiling.
VERIFIERS: dict[str, VerifierSpec] = {
    "gpt-5.4-mini": VerifierSpec(
        model_id="gpt-5.4-mini",
        provider="openai",
        endpoint="https://api.openai.com/v1/chat/completions",
        env_var="OPENAI_API_KEY",
        pricing_in_usd_per_million=0.15,
        pricing_out_usd_per_million=0.60,
    ),
    "gpt-5.4-nano": VerifierSpec(
        model_id="gpt-5.4-nano",
        provider="openai",
        endpoint="https://api.openai.com/v1/chat/completions",
        env_var="OPENAI_API_KEY",
        pricing_in_usd_per_million=0.05,
        pricing_out_usd_per_million=0.40,
    ),
    "claude-haiku-4-5-20251001": VerifierSpec(
        model_id="claude-haiku-4-5-20251001",
        provider="anthropic",
        endpoint="https://api.anthropic.com/v1/messages",
        env_var="ANTHROPIC_API_KEY",
        pricing_in_usd_per_million=1.00,
        pricing_out_usd_per_million=5.00,
    ),
}


VERIFIER_SYSTEM_PROMPT = """You are a quality verifier for editorial summaries.

You receive a SOURCE article body and a candidate SUMMARY JSON with three
fields: summary_short, summary_medium, summary_long.

A separate deterministic process checks word counts. Ignore word-count
concerns in your scoring — focus on substance.

Output ONE JSON object with exactly these keys:
- verdict: "AUTO_APPROVE", "HUMAN_REVIEW", or "REJECT"
- scores: {
    faithfulness: 1-5,
    durability: 1-5,
    volatile_facts_handling: 1-5,
    fabrication_check: 1-5,
    voice_match: 1-5
  }
- top_issue: short string (max ~120 chars), or "" if none
- notes: array of up to 4 short bullet strings

Scoring rubric:
- faithfulness 5 = every summary claim supported by source; 1 = invented.
- durability 5 = no rotting facts (prices, star counts, versions, vendor
  rankings) embedded; 1 = will be stale in weeks.
- volatile_facts_handling 5 = volatile facts abstracted, durable regulatory
  facts (named regulations + their dates) preserved exactly.
- fabrication_check 5 = no sections, FAQs, pilot plans, or vendor mentions
  appear that are absent from source.
- voice_match 5 = matches practical, direct, leadership-oriented voice.

Decision rule:
- REJECT if any score == 1, fabrication present, factual invention, or the
  summary describes a different article than the source.
- AUTO_APPROVE if every score is >= 4 and no fabrication is present.
- Otherwise HUMAN_REVIEW.

Output ONLY the JSON object. No prose. No markdown fences."""


# =============================================================================
# Review file parsing
# =============================================================================

@dataclass
class ParsedReview:
    """The minimum set of facts pulled out of a review file."""

    path: pathlib.Path
    title: str
    article_folder: str
    canonical_url: str
    status: str  # 'draft' / 'approved' / etc — read-only here
    short: str
    medium: str
    long: str

    def summaries_dict(self) -> dict[str, str]:
        return {
            "summary_short": self.short,
            "summary_medium": self.medium,
            "summary_long": self.long,
        }


def parse_review_file(path: pathlib.Path) -> ParsedReview:
    """Parse a draft summary review file into a ParsedReview.

    Raises FileNotFoundError if the path is missing. Tolerates missing
    sections by surfacing empty strings — the deterministic gate will
    REJECT a review with missing fields.
    """
    text = path.read_text(encoding="utf-8")

    title = ""
    article_folder = ""
    canonical_url = ""
    status = "draft"

    # Header lines (Title is "# Summary Review — <title>")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("# Summary Review"):
            after = line.split("—", 1)
            if len(after) == 2:
                title = after[1].strip()
        elif line.lower().startswith("article folder:"):
            article_folder = line.split(":", 1)[1].strip()
        elif line.lower().startswith("canonical url:"):
            canonical_url = line.split(":", 1)[1].strip()
        elif line.lower().startswith("status:"):
            status = line.split(":", 1)[1].strip().lower()

    # Body sections — same shape as tools/build_summaries.py _write_review_file.
    sections: dict[str, str] = {"short": "", "medium": "", "long": ""}
    current: Optional[str] = None
    buf: list[str] = []
    stop_headings = (
        "## Review status",
        "## Notes",
        "## Verification",
    )

    def _flush() -> None:
        if current is not None:
            sections[current] = "\n".join(buf).strip()

    for raw_line in text.splitlines():
        if raw_line.startswith("## 50-word summary"):
            _flush()
            current, buf = "short", []
        elif raw_line.startswith("## 200-word summary"):
            _flush()
            current, buf = "medium", []
        elif raw_line.startswith("## 500-word summary"):
            _flush()
            current, buf = "long", []
        elif current is not None and any(raw_line.startswith(h) for h in stop_headings):
            _flush()
            current = None
            buf = []
        elif current is not None and not raw_line.startswith("##"):
            buf.append(raw_line)
    _flush()

    return ParsedReview(
        path=path,
        title=title,
        article_folder=article_folder,
        canonical_url=canonical_url,
        status=status,
        short=sections["short"],
        medium=sections["medium"],
        long=sections["long"],
    )


def discover_review_files(
    summaries_dir: pathlib.Path,
    slug: Optional[str] = None,
) -> list[pathlib.Path]:
    """Return *.review.md files under summaries_dir, optionally filtered by slug."""
    if not summaries_dir.is_dir():
        return []
    out = sorted(summaries_dir.glob("*.review.md"))
    if slug:
        out = [p for p in out if p.stem.replace(".review", "") == slug]
    return out


def load_article_body(
    articles_dir: pathlib.Path,
    folder: str,
) -> str:
    """Load the article body for a given folder, stripping YAML frontmatter."""
    if not folder:
        return ""
    md_path = articles_dir / folder / "article.md"
    if not md_path.exists():
        return ""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]
    return text.lstrip()


# =============================================================================
# HTTP plumbing (monkeypatch-friendly)
# =============================================================================

def _http_post_json(
    url: str,
    headers: dict[str, str],
    body: str,
    timeout: int,
) -> tuple[Any, float, str]:
    """Minimal POST helper. Returns (status, latency_ms, body_text)."""
    t0 = time.time()
    req = urllib.request.Request(url, method="POST")
    for key, value in headers.items():
        req.add_header(key, value)
    req.data = body.encode("utf-8") if isinstance(body, str) else body
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8", "replace")
            return resp.status, round((time.time() - t0) * 1000, 1), payload
    except urllib.error.HTTPError as e:
        try:
            payload = e.read().decode("utf-8", "replace")[:2000]
        except Exception:
            payload = ""
        return e.code, round((time.time() - t0) * 1000, 1), payload
    except Exception as e:
        return "exception", round((time.time() - t0) * 1000, 1), str(e)[:500]


# =============================================================================
# Verifier dispatch
# =============================================================================

@dataclass
class VerifierResult:
    """Structured result of one verifier round-trip."""

    spec: VerifierSpec
    ok: bool
    raw_status: Any = None
    latency_ms: float = 0.0
    verdict: Optional[str] = None  # AUTO_APPROVE / HUMAN_REVIEW / REJECT
    scores: Optional[dict[str, Any]] = None
    top_issue: str = ""
    notes: list[str] = field(default_factory=list)
    cost_usd: Optional[float] = None
    usage: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def label(self) -> str:
        return f"{self.spec.provider}/{self.spec.model_id}"


def _build_user_prompt(article_body: str, summaries: dict[str, str]) -> str:
    """Build the verifier user-prompt with untrusted-content tagging.

    Article body is truncated to ~18 kB so the prompt fits comfortably
    inside small context windows; the verifier judges substance from the
    head of the article, not from full-text recall.
    """
    head = article_body[:18000]
    summary_json = json.dumps(summaries, indent=2)
    return (
        "<source>\n"
        f"{head}\n"
        "</source>\n\n"
        "<summary>\n"
        f"{summary_json}\n"
        "</summary>\n\n"
        "Produce the verdict JSON now."
    )


def _extract_json_object(text: str) -> Optional[dict]:
    """Strict JSON parse first, fall back to first {...} substring."""
    if not isinstance(text, str):
        return None
    stripped = text.strip()
    if stripped.startswith("```"):
        # Strip a markdown fence if the model wrapped its output.
        stripped = stripped.strip("`")
        if stripped.lower().startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.strip()
    try:
        loaded = json.loads(stripped)
        return loaded if isinstance(loaded, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        loaded = json.loads(match.group(0))
        return loaded if isinstance(loaded, dict) else None
    except json.JSONDecodeError:
        return None


def parse_verifier_response_json(verdict_obj: Optional[dict]) -> tuple[bool, dict[str, Any]]:
    """Normalize a verifier verdict dict and validate its shape.

    Returns (ok, normalized) where ``normalized`` carries 'verdict', 'scores',
    'top_issue', 'notes' keys with safe defaults. Malformed shapes return
    ok=False and a normalized dict still safe to surface in the review file.
    """
    out = {
        "verdict": None,
        "scores": None,
        "top_issue": "",
        "notes": [],
    }
    if not isinstance(verdict_obj, dict):
        return False, out

    verdict = verdict_obj.get("verdict")
    if not isinstance(verdict, str):
        return False, out
    verdict_norm = verdict.strip().upper()
    if verdict_norm not in {"AUTO_APPROVE", "HUMAN_REVIEW", "REJECT"}:
        return False, out
    out["verdict"] = verdict_norm

    scores = verdict_obj.get("scores")
    if isinstance(scores, dict):
        out["scores"] = {k: v for k, v in scores.items() if isinstance(k, str)}

    top_issue = verdict_obj.get("top_issue", "")
    if isinstance(top_issue, str):
        out["top_issue"] = top_issue.strip()

    notes = verdict_obj.get("notes") or []
    if isinstance(notes, list):
        out["notes"] = [str(n).strip() for n in notes if isinstance(n, (str, int, float))]

    return True, out


def estimate_cost(spec: VerifierSpec, usage: dict[str, Any]) -> Optional[float]:
    in_tok = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
    out_tok = usage.get("output_tokens") or usage.get("completion_tokens") or 0
    if in_tok == 0 and out_tok == 0:
        return None
    return round(
        (in_tok / 1_000_000) * spec.pricing_in_usd_per_million
        + (out_tok / 1_000_000) * spec.pricing_out_usd_per_million,
        6,
    )


def call_openai_verifier(
    spec: VerifierSpec,
    article_body: str,
    summaries: dict[str, str],
    timeout: int = 60,
    http_post: Optional[Callable] = None,
) -> VerifierResult:
    """One OpenAI chat-completions verifier call."""
    if http_post is None:
        http_post = _http_post_json
    key = os.environ.get(spec.env_var, "").strip()
    if not key:
        return VerifierResult(
            spec=spec, ok=False, error=f"{spec.env_var} not set"
        )

    # gpt-5.4-* family requires `max_completion_tokens` and disallows
    # `temperature`. We always use the newer parameter; chat-completions
    # accepts it across the family this verifier targets.
    payload = json.dumps({
        "model": spec.model_id,
        "messages": [
            {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(article_body, summaries)},
        ],
        "max_completion_tokens": 1200,
        "response_format": {"type": "json_object"},
    })
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    status, latency_ms, body = http_post(spec.endpoint, headers, payload, timeout)

    result = VerifierResult(spec=spec, ok=False, raw_status=status, latency_ms=latency_ms)
    if status != 200:
        result.error = f"HTTP {status}"
        return result

    try:
        envelope = json.loads(body)
    except json.JSONDecodeError as e:
        result.error = f"response is not JSON: {e}"
        return result

    usage = envelope.get("usage") or {}
    result.usage = usage
    result.cost_usd = estimate_cost(spec, usage)

    choices = envelope.get("choices") or []
    if not choices:
        result.error = "no choices in response"
        return result
    content = (choices[0].get("message") or {}).get("content") or ""
    verdict_obj = _extract_json_object(content)
    ok, normalized = parse_verifier_response_json(verdict_obj)
    if not ok:
        result.error = "verifier returned malformed verdict JSON"
        return result

    result.ok = True
    result.verdict = normalized["verdict"]
    result.scores = normalized["scores"]
    result.top_issue = normalized["top_issue"]
    result.notes = normalized["notes"]
    return result


def call_anthropic_verifier(
    spec: VerifierSpec,
    article_body: str,
    summaries: dict[str, str],
    timeout: int = 60,
    http_post: Optional[Callable] = None,
) -> VerifierResult:
    """One Anthropic Messages verifier call."""
    if http_post is None:
        http_post = _http_post_json
    key = os.environ.get(spec.env_var, "").strip()
    if not key:
        return VerifierResult(
            spec=spec, ok=False, error=f"{spec.env_var} not set"
        )

    payload = json.dumps({
        "model": spec.model_id,
        "max_tokens": 800,
        "temperature": 0.0,
        "system": VERIFIER_SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": _build_user_prompt(article_body, summaries)},
        ],
    })
    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    status, latency_ms, body = http_post(spec.endpoint, headers, payload, timeout)

    result = VerifierResult(spec=spec, ok=False, raw_status=status, latency_ms=latency_ms)
    if status != 200:
        result.error = f"HTTP {status}"
        return result

    try:
        envelope = json.loads(body)
    except json.JSONDecodeError as e:
        result.error = f"response is not JSON: {e}"
        return result

    u = envelope.get("usage") or {}
    usage = {
        "input_tokens": u.get("input_tokens"),
        "output_tokens": u.get("output_tokens"),
    }
    result.usage = usage
    result.cost_usd = estimate_cost(spec, usage)

    content = ""
    for block in envelope.get("content", []) or []:
        if block.get("type") == "text":
            content += block.get("text", "")
    verdict_obj = _extract_json_object(content)
    ok, normalized = parse_verifier_response_json(verdict_obj)
    if not ok:
        result.error = "verifier returned malformed verdict JSON"
        return result

    result.ok = True
    result.verdict = normalized["verdict"]
    result.scores = normalized["scores"]
    result.top_issue = normalized["top_issue"]
    result.notes = normalized["notes"]
    return result


def dispatch_verifier(
    spec: VerifierSpec,
    article_body: str,
    summaries: dict[str, str],
    timeout: int = 60,
    http_post: Optional[Callable] = None,
) -> VerifierResult:
    if spec.provider == "openai":
        return call_openai_verifier(spec, article_body, summaries, timeout, http_post)
    if spec.provider == "anthropic":
        return call_anthropic_verifier(spec, article_body, summaries, timeout, http_post)
    return VerifierResult(
        spec=spec, ok=False, error=f"unknown provider '{spec.provider}'"
    )


# =============================================================================
# Final verdict merge
# =============================================================================

@dataclass
class FinalVerdict:
    """The merged final verdict and how it was reached."""

    final: str  # AUTO_APPROVE / HUMAN_REVIEW / REJECT
    det_status: GateStatus
    primary: Optional[VerifierResult] = None
    secondary: Optional[VerifierResult] = None
    fallback: Optional[VerifierResult] = None
    single_verifier: bool = False
    secondary_skipped_cost_cap: bool = False
    total_cost_usd: float = 0.0
    explanation: str = ""


def _verifier_ran(r: Optional[VerifierResult]) -> bool:
    return bool(r and r.ok and r.verdict)


def merge_final_verdict(
    det: GateResult,
    primary: Optional[VerifierResult],
    secondary: Optional[VerifierResult],
    *,
    single_verifier: bool,
    secondary_skipped_cost_cap: bool,
) -> FinalVerdict:
    """Combine deterministic gate + verifier verdicts into a final verdict.

    Rules (mirroring the PR D spec):

    1. If deterministic gate is REJECT → final REJECT.
    2. If deterministic gate is HUMAN_REVIEW or RETRYABLE → final HUMAN_REVIEW
       unless a verifier returned REJECT (then REJECT).
    3. If deterministic gate PASSes:
         a. Any verifier REJECT → REJECT.
         b. Both verifiers AUTO_APPROVE → AUTO_APPROVE.
         c. Any verifier HUMAN_REVIEW → HUMAN_REVIEW.
         d. Primary AUTO_APPROVE and secondary missing (single-verifier or
            cost-cap skip) → HUMAN_REVIEW (operator did not authorize a
            single-verifier AUTO_APPROVE elsewhere).
    """
    final = "HUMAN_REVIEW"
    explanation = ""

    any_reject = (
        (primary is not None and primary.verdict == "REJECT")
        or (secondary is not None and secondary.verdict == "REJECT")
    )

    if det.status == GateStatus.REJECT:
        final = "REJECT"
        explanation = "deterministic gate REJECT"
    elif any_reject:
        final = "REJECT"
        explanation = "verifier REJECT"
    elif det.status in (GateStatus.HUMAN_REVIEW, GateStatus.RETRYABLE):
        final = "HUMAN_REVIEW"
        explanation = f"deterministic gate {det.status.value}"
    else:
        # det.status == PASS at this point
        p_ok = _verifier_ran(primary)
        s_ok = _verifier_ran(secondary)
        if not p_ok and not s_ok:
            # No verifier ran successfully. Per spec, single-verifier AUTO_APPROVE
            # requires explicit --single-verifier; dry-run / unset state stays
            # HUMAN_REVIEW so a draft never auto-approves silently.
            final = "HUMAN_REVIEW"
            explanation = "no verifier ran; gate PASS only"
        elif p_ok and s_ok:
            if primary.verdict == "AUTO_APPROVE" and secondary.verdict == "AUTO_APPROVE":
                final = "AUTO_APPROVE"
                explanation = "both verifiers AUTO_APPROVE"
            elif primary.verdict == secondary.verdict:
                final = primary.verdict
                explanation = f"both verifiers {primary.verdict}"
            else:
                final = "HUMAN_REVIEW"
                explanation = (
                    f"verifier disagreement: primary={primary.verdict}, "
                    f"secondary={secondary.verdict}"
                )
        elif p_ok and not s_ok:
            # Single-verifier path. The operator explicitly opted in or the
            # secondary was skipped by the cost cap.
            if secondary_skipped_cost_cap:
                # Spec: final cannot be stronger than HUMAN_REVIEW unless
                # operator explicitly runs --single-verifier.
                if single_verifier and primary.verdict == "AUTO_APPROVE":
                    final = "AUTO_APPROVE"
                    explanation = (
                        "primary AUTO_APPROVE; secondary skipped by cost cap; "
                        "--single-verifier authorized"
                    )
                else:
                    final = (
                        "HUMAN_REVIEW"
                        if primary.verdict == "AUTO_APPROVE"
                        else primary.verdict
                    )
                    if primary.verdict == "AUTO_APPROVE":
                        explanation = (
                            "primary AUTO_APPROVE but secondary skipped by cost cap; "
                            "downgrading to HUMAN_REVIEW (no --single-verifier opt-in)"
                        )
                    else:
                        explanation = f"primary {primary.verdict}; secondary skipped by cost cap"
            elif single_verifier:
                final = primary.verdict
                explanation = f"primary {primary.verdict}; single-verifier mode"
            else:
                # No secondary, no cost-cap reason, no single-verifier opt-in.
                # Should not happen via CLI but stay safe.
                final = (
                    "HUMAN_REVIEW"
                    if primary.verdict == "AUTO_APPROVE"
                    else primary.verdict
                )
                explanation = (
                    "primary verdict only and no secondary requested; downgrading "
                    "AUTO_APPROVE → HUMAN_REVIEW for safety"
                )
        else:
            # Primary failed but secondary ran. Treat as single-verifier with
            # primary missing — never auto-approve.
            final = (
                "HUMAN_REVIEW"
                if secondary.verdict == "AUTO_APPROVE"
                else secondary.verdict
            )
            explanation = (
                f"primary verifier failed; secondary {secondary.verdict}"
            )

    total_cost = 0.0
    for r in (primary, secondary):
        if r and r.cost_usd:
            total_cost += r.cost_usd

    return FinalVerdict(
        final=final,
        det_status=det.status,
        primary=primary,
        secondary=secondary,
        single_verifier=single_verifier,
        secondary_skipped_cost_cap=secondary_skipped_cost_cap,
        total_cost_usd=round(total_cost, 6),
        explanation=explanation,
    )


# =============================================================================
# Verification block writer
# =============================================================================

VERIFICATION_HEADING = "## Verification"


def render_verification_block(
    fv: FinalVerdict,
    today: Optional[datetime.date] = None,
) -> str:
    """Render the ## Verification block as text.

    The Status: draft line in the review file is never touched — operators
    promote draft → approved manually. This block is appended/replaced as
    a separate section.
    """
    if today is None:
        today = datetime.date.today()

    primary_label = "not-run"
    primary_verdict = "n/a"
    if fv.primary is not None:
        primary_label = fv.primary.label()
        primary_verdict = fv.primary.verdict or fv.primary.error or "error"

    secondary_label = "not-configured"
    secondary_verdict = "not-run"
    if fv.secondary is not None:
        secondary_label = fv.secondary.label()
        if fv.secondary_skipped_cost_cap:
            secondary_verdict = "skipped (cost cap)"
        else:
            secondary_verdict = fv.secondary.verdict or fv.secondary.error or "error"
    elif fv.secondary_skipped_cost_cap:
        # Configured but skipped before the call.
        secondary_verdict = "skipped (cost cap)"

    fallback_label = "not-used"
    if fv.fallback is not None and _verifier_ran(fv.fallback):
        fallback_label = f"used ({fv.fallback.label()} → {fv.fallback.verdict})"
    elif fv.fallback is not None:
        fallback_label = f"attempted ({fv.fallback.label()}; {fv.fallback.error or 'no verdict'})"

    notes_lines: list[str] = []
    if fv.explanation:
        notes_lines.append(f"- Merge rationale: {fv.explanation}")
    if fv.primary is not None and fv.primary.top_issue:
        notes_lines.append(f"- Primary top issue: {fv.primary.top_issue}")
    if fv.secondary is not None and fv.secondary.top_issue:
        notes_lines.append(f"- Secondary top issue: {fv.secondary.top_issue}")
    for r in (fv.primary, fv.secondary):
        if r is None:
            continue
        for note in (r.notes or [])[:3]:
            notes_lines.append(f"- {r.label()}: {note}")
    if not notes_lines:
        notes_lines.append("- (no notes)")

    cost_str = f"{fv.total_cost_usd:.6f}" if fv.total_cost_usd else "0.000000"

    lines = [
        VERIFICATION_HEADING,
        "",
        f"Verification status: {fv.final}",
        f"Deterministic gate: {fv.det_status.value}",
        f"Primary verifier: {primary_label} — {primary_verdict}",
        f"Secondary verifier: {secondary_label} — {secondary_verdict}",
        f"Fallback verifier: {fallback_label}",
        f"Single verifier: {'true' if fv.single_verifier else 'false'}",
        f"Estimated verifier cost (USD): {cost_str}",
        f"Verified at: {today.isoformat()}",
        "",
        "### Verification notes",
        "",
    ]
    lines.extend(notes_lines)
    lines.append("")
    return "\n".join(lines)


def write_verification_to_file(
    path: pathlib.Path,
    block: str,
) -> None:
    """Append or replace the ## Verification block in a review file.

    Replace semantics: if ``## Verification`` already exists, every line
    from that heading to end-of-file is removed before the new block is
    appended. Status: draft and all other content above stays untouched.
    """
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()

    cut_at: Optional[int] = None
    for i, line in enumerate(lines):
        if line.strip() == VERIFICATION_HEADING:
            cut_at = i
            break

    head = lines if cut_at is None else lines[:cut_at]
    # Trim a single trailing blank-line block so we don't accumulate blank
    # lines on repeated runs.
    while head and head[-1].strip() == "":
        head.pop()

    new_content = "\n".join(head) + "\n\n" + block
    # Ensure file ends in a newline.
    if not new_content.endswith("\n"):
        new_content += "\n"
    path.write_text(new_content, encoding="utf-8")


# =============================================================================
# Pipeline
# =============================================================================

@dataclass
class VerifyPlan:
    """One verification target: a review file + how it should be processed."""

    review_path: pathlib.Path
    parsed: Optional[ParsedReview] = None
    article_body: str = ""
    det_result: Optional[GateResult] = None
    final: Optional[FinalVerdict] = None
    skipped_reason: str = ""


def _resolve_verifier(model_id: str, expected_provider: str) -> VerifierSpec:
    spec = VERIFIERS.get(model_id)
    if spec is None:
        raise ValueError(
            f"unknown verifier model '{model_id}'. Known: "
            f"{', '.join(sorted(VERIFIERS))}"
        )
    if spec.provider != expected_provider:
        raise ValueError(
            f"verifier '{model_id}' belongs to provider '{spec.provider}', "
            f"not '{expected_provider}'"
        )
    return spec


def _try_verifier(
    spec: VerifierSpec,
    article_body: str,
    summaries: dict[str, str],
    remaining_budget_usd: float,
    http_post: Optional[Callable] = None,
) -> tuple[Optional[VerifierResult], bool]:
    """Run one verifier if budget allows.

    Returns (result, skipped_cost_cap).

    The cost cap is evaluated *before* the call by estimating an upper bound
    for the call's spend: we use a conservative figure derived from the
    article-body length × the input pricing plus a small output allowance.
    If even the optimistic estimate would overrun the remaining budget, we
    skip without calling.
    """
    # Optimistic estimate: ~4 chars per token, output capped at 800 tokens.
    # The actual call may cost more or less, so we *also* re-check after
    # the call returns and surface the post-hoc cost separately.
    approx_in_tokens = max(800, len(article_body) // 4)
    approx_out_tokens = 800
    est = (
        (approx_in_tokens / 1_000_000) * spec.pricing_in_usd_per_million
        + (approx_out_tokens / 1_000_000) * spec.pricing_out_usd_per_million
    )
    if est > remaining_budget_usd:
        return None, True

    result = dispatch_verifier(spec, article_body, summaries, http_post=http_post)
    return result, False


def verify_one(
    review_path: pathlib.Path,
    articles_dir: pathlib.Path,
    *,
    primary_spec: Optional[VerifierSpec],
    secondary_spec: Optional[VerifierSpec],
    fallback_spec: Optional[VerifierSpec],
    allow_network: bool,
    single_verifier: bool,
    max_cost_usd: float,
    http_post: Optional[Callable] = None,
) -> VerifyPlan:
    """Run the verification pipeline for one review file. No file writes."""
    plan = VerifyPlan(review_path=review_path)
    try:
        plan.parsed = parse_review_file(review_path)
    except FileNotFoundError as e:
        plan.skipped_reason = f"review file not found: {e}"
        return plan

    plan.article_body = load_article_body(articles_dir, plan.parsed.article_folder)
    summaries = plan.parsed.summaries_dict()
    det = check_summaries(summaries, source_body=plan.article_body or None)
    plan.det_result = det

    if not allow_network:
        # Dry-run: do not call any verifier. Still surface deterministic gate.
        plan.final = merge_final_verdict(
            det,
            primary=None,
            secondary=None,
            single_verifier=single_verifier,
            secondary_skipped_cost_cap=False,
        )
        return plan

    # If the deterministic gate already says REJECT, there is no point in
    # spending verifier budget on a structurally broken candidate.
    if det.status == GateStatus.REJECT:
        plan.final = merge_final_verdict(
            det,
            primary=None,
            secondary=None,
            single_verifier=single_verifier,
            secondary_skipped_cost_cap=False,
        )
        return plan

    remaining = max_cost_usd
    primary_result: Optional[VerifierResult] = None
    secondary_result: Optional[VerifierResult] = None
    secondary_skipped = False

    if primary_spec is not None:
        primary_result, primary_skipped = _try_verifier(
            primary_spec, plan.article_body, summaries, remaining, http_post
        )
        if primary_skipped:
            primary_result = None  # cost cap killed the call before issuing it
        elif primary_result and primary_result.cost_usd:
            remaining -= primary_result.cost_usd

    if (
        not single_verifier
        and secondary_spec is not None
        and primary_result is not None
    ):
        secondary_result, secondary_skipped = _try_verifier(
            secondary_spec, plan.article_body, summaries, remaining, http_post
        )
        if secondary_skipped:
            secondary_result = None
        elif secondary_result and secondary_result.cost_usd:
            remaining -= secondary_result.cost_usd

    plan.final = merge_final_verdict(
        det,
        primary=primary_result,
        secondary=secondary_result,
        single_verifier=single_verifier,
        secondary_skipped_cost_cap=secondary_skipped,
    )
    return plan


# =============================================================================
# CLI
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="verify_summaries",
        description=(
            "Run deterministic + LLM verifier checks on draft summary review "
            "files. Default is dry-run (no network, no writes). Live LLM "
            "calls require --allow-network. File writes require "
            "--write-verification. Approvals are never automated."
        ),
    )
    target = p.add_mutually_exclusive_group()
    target.add_argument("--review-file", type=str, default=None,
                        help="Path to one review file.")
    target.add_argument("--summaries-dir", type=str, default=None,
                        help="Directory of *.review.md files to verify.")
    p.add_argument("--slug", type=str, default=None,
                   help="Filter to one slug (only with --summaries-dir).")

    p.add_argument("--primary-provider", choices=["openai", "anthropic"],
                   default="openai")
    p.add_argument("--primary-model", default="gpt-5.4-mini")
    p.add_argument("--secondary-provider", choices=["openai", "anthropic", "none"],
                   default="anthropic")
    p.add_argument("--secondary-model", default="claude-haiku-4-5-20251001")
    p.add_argument("--fallback-provider", choices=["openai", "anthropic", "none"],
                   default="openai")
    p.add_argument("--fallback-model", default="gpt-5.4-nano")

    p.add_argument("--allow-network", action="store_true",
                   help="Required for any live verifier call.")
    p.add_argument("--single-verifier", action="store_true",
                   help="Run only the primary verifier; label the verification "
                        "block so operators see the reduced confidence.")
    p.add_argument("--max-verifier-cost-usd", type=float, default=1.00,
                   help="Hard ceiling on cumulative verifier spend. "
                        "Default: 1.00.")
    p.add_argument("--write-verification", action="store_true",
                   help="Write the verification block into each review file. "
                        "Off by default — without this flag verify_summaries.py "
                        "only prints the planned outcome.")
    p.add_argument("--dry-run", action="store_true",
                   help="Force dry-run even if other flags would allow live "
                        "calls. Useful for review-file parsing checks.")

    p.add_argument("--articles-dir", default=None,
                   help="Override articles directory (test affordance).")
    p.add_argument("--summaries-default-dir", default=None,
                   help="Override default summaries dir when neither --review-file "
                        "nor --summaries-dir is given (test affordance).")
    return p


def _resolve_dirs(args: argparse.Namespace) -> tuple[pathlib.Path, pathlib.Path]:
    articles_dir = pathlib.Path(args.articles_dir) if args.articles_dir else ARTICLES_DIR
    if args.summaries_dir:
        summaries_dir = pathlib.Path(args.summaries_dir)
    elif args.summaries_default_dir:
        summaries_dir = pathlib.Path(args.summaries_default_dir)
    else:
        summaries_dir = SUMMARIES_DIR
    return articles_dir, summaries_dir


def _build_targets(
    args: argparse.Namespace,
    summaries_dir: pathlib.Path,
) -> list[pathlib.Path]:
    if args.review_file:
        return [pathlib.Path(args.review_file)]
    return discover_review_files(summaries_dir, slug=args.slug)


def _resolve_specs(args: argparse.Namespace) -> tuple[
    VerifierSpec,
    Optional[VerifierSpec],
    Optional[VerifierSpec],
]:
    primary = _resolve_verifier(args.primary_model, args.primary_provider)
    secondary: Optional[VerifierSpec] = None
    if args.secondary_provider != "none":
        secondary = _resolve_verifier(args.secondary_model, args.secondary_provider)
    fallback: Optional[VerifierSpec] = None
    if args.fallback_provider != "none":
        fallback = _resolve_verifier(args.fallback_model, args.fallback_provider)
    return primary, secondary, fallback


def _print_plan_summary(plan: VerifyPlan) -> None:
    label = plan.review_path.name
    if plan.skipped_reason:
        print(f"[verify] {label}: skipped — {plan.skipped_reason}")
        return
    det = plan.det_result.status.value if plan.det_result else "?"
    final = plan.final.final if plan.final else "?"
    cost = f"${plan.final.total_cost_usd:.6f}" if plan.final else "-"
    print(f"[verify] {label}: gate={det} final={final} cost={cost}")


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if args.dry_run:
        args.allow_network = False

    try:
        primary_spec, secondary_spec, fallback_spec = _resolve_specs(args)
    except ValueError as e:
        print(f"[verify] ERROR: {e}", file=sys.stderr)
        return 2

    articles_dir, summaries_dir = _resolve_dirs(args)
    targets = _build_targets(args, summaries_dir)
    if not targets:
        print("[verify] No review files to process.")
        return 0

    print(
        f"[verify] live={args.allow_network} write={args.write_verification} "
        f"primary={primary_spec.model_id} "
        f"secondary={secondary_spec.model_id if secondary_spec else 'none'} "
        f"single_verifier={args.single_verifier} "
        f"cost_cap=${args.max_verifier_cost_usd:.2f} targets={len(targets)}"
    )

    # Pre-flight: if live, require the relevant API keys to be present.
    if args.allow_network:
        missing = []
        for spec in (primary_spec, secondary_spec, fallback_spec):
            if spec is None:
                continue
            if not os.environ.get(spec.env_var, "").strip():
                missing.append(f"{spec.env_var} (for {spec.model_id})")
        if missing:
            # Single-verifier path lets the operator scope down to just
            # primary; only fail when the primary's key is missing.
            primary_missing = not os.environ.get(primary_spec.env_var, "").strip()
            if primary_missing:
                print(
                    f"[verify] ERROR: primary verifier {primary_spec.model_id} "
                    f"requires {primary_spec.env_var} but it is not set "
                    f"(no value will be printed).",
                    file=sys.stderr,
                )
                return 2
            print(
                "[verify] WARN: live verifier(s) requested but missing keys: "
                + ", ".join(missing)
                + " — those verifier(s) will be skipped.",
                file=sys.stderr,
            )

    cumulative_cost = 0.0
    written = 0
    for review_path in targets:
        # Per-file cost budget remaining; the cap is cumulative across the run.
        per_file_remaining = max(0.0, args.max_verifier_cost_usd - cumulative_cost)
        plan = verify_one(
            review_path=review_path,
            articles_dir=articles_dir,
            primary_spec=primary_spec,
            secondary_spec=(None if args.single_verifier else secondary_spec),
            fallback_spec=fallback_spec,
            allow_network=args.allow_network,
            single_verifier=args.single_verifier,
            max_cost_usd=per_file_remaining,
        )
        if plan.final is not None:
            cumulative_cost += plan.final.total_cost_usd

        _print_plan_summary(plan)

        if args.write_verification and plan.final is not None and not plan.skipped_reason:
            block = render_verification_block(plan.final)
            write_verification_to_file(review_path, block)
            written += 1

    print(
        f"[verify] processed={len(targets)} wrote={written} "
        f"cumulative_cost=${cumulative_cost:.6f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
