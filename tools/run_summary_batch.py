#!/usr/bin/env python3
"""Automated summary batch runner.

Chains the full operator-local summary pipeline for one or more missing-
summary articles:

    select missing-summary articles
        |
        v
    MiniMax-M2 generation (+ deterministic gate + retry loop)
        |
        v
    OpenAI primary verifier + Anthropic secondary verifier
        |
        v
    final verdict (AUTO_APPROVE / HUMAN_REVIEW / REJECT)
        |
        v
    optional auto-apply (only for AUTO_APPROVE, only when explicitly
                         opted in)
        |
        v
    batch report (always written outside the repo)

Usage:

    # Default: dry-run, no network, no writes, prints plan only.
    python3 tools/run_summary_batch.py --limit 3

    # Live batch (Doppler-injected keys):
    doppler run -- \\
        python3 tools/run_summary_batch.py --batch --limit 5 \\
        --allow-network --max-budget-usd 0.10

    # Live batch + auto-apply AUTO_APPROVE summaries to metadata:
    doppler run -- \\
        python3 tools/run_summary_batch.py --batch --limit 5 \\
        --allow-network --max-budget-usd 0.10 \\
        --apply-auto-approved

Safety model (mirrors PR #224 / PR #225 conventions):

- Triple gate before any outbound HTTP: ``--batch`` AND ``--allow-network``
  AND a positive ``--max-budget-usd``.
- ``--apply-auto-approved`` is a fourth gate, required to touch
  metadata.json. Even with it set, only final ``AUTO_APPROVE`` review
  files are promoted. HUMAN_REVIEW, REJECT, single-verifier results,
  cost-cap-skipped-secondary results, and any item with a missing
  verification block stay draft exceptions.
- ``--rebuild-artifacts`` is wired but intentionally not implemented in
  this PR (no generated-artifact diffs in PR F per spec). The flag emits
  a "next-command" hint instead.
- Report is written outside the repository by default (``/tmp/...``).
  A repo-internal report path is rejected with an exit-2 unless it
  resolves outside the repo.
- Secret values, auth headers, env-var values, hashes, and provider
  account details are never printed or written. Provider error bodies
  are truncated and redacted.

The runner intentionally calls into ``tools/build_summaries.py`` and
``tools/verify_summaries.py`` via direct function imports rather than
subprocess, so monkeypatched HTTP transports in tests propagate through
the whole pipeline.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

# tools/ is on sys.path via tools/tests/conftest.py and via Python's
# automatic same-dir resolution when this module is executed directly.
import build_summaries as bs
import summary_quality as sq
import verify_summaries as vs


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTICLES_DIR = REPO_ROOT / "articles"
INDEX_PATH = REPO_ROOT / "index.json"
DEFAULT_SUMMARIES_DIR = REPO_ROOT / "summaries"


# Reuse provider_smoke's article-selection helper if available, but fall
# back to a local equivalent so this module is self-contained.
try:
    from provider_smoke import select_missing_summary_articles as _select_missing
except ImportError:  # pragma: no cover - defensive
    _select_missing = None


# =============================================================================
# Article selection
# =============================================================================

def select_articles(
    index_path: pathlib.Path,
    articles_dir: pathlib.Path,
    *,
    missing_only: bool,
    slug: Optional[str],
    limit: int,
) -> list[dict]:
    """Pick the article candidates for this batch.

    The selection chain mirrors `tools/build_summaries.py` semantics so an
    operator can preview with `--dry-run` and run with `--batch` against
    the same set:

    1. If ``slug`` is supplied, restrict to that one folder/slug.
    2. If ``missing_only`` is True, drop articles whose
       ``metadata.json::summary_short`` is already populated.
    3. Apply ``limit``.
    """
    if not index_path.exists():
        return []
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    candidates: list[dict] = []
    for entry in index.get("articles", []):
        folder = entry.get("folder", "")
        if not folder:
            continue
        if slug and not (entry.get("slug") == slug or folder == slug):
            continue
        if missing_only:
            meta_path = articles_dir / folder / "metadata.json"
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                # Soft-skip — same convention as build_summaries.py.
                continue
            ss = meta.get("summary_short")
            if isinstance(ss, str) and ss.strip():
                continue
        candidates.append({
            "slug": entry.get("slug", folder),
            "folder": folder,
            "title": entry.get("title", ""),
            "canonical_url": entry.get("canonical_url", ""),
        })

    if limit is not None and limit > 0:
        candidates = candidates[:limit]
    return candidates


# =============================================================================
# Per-article result
# =============================================================================

ACTION_AUTO_APPLIED = "auto_applied"
ACTION_DRAFT_ONLY = "draft_only"
ACTION_HUMAN_REVIEW = "human_review"
ACTION_REJECTED = "rejected"
ACTION_SKIPPED_COST_CAP = "skipped_cost_cap"
ACTION_GENERATION_FAILED = "generation_failed"


@dataclass
class ArticleOutcome:
    """One article's pipeline result, ready for the batch report."""

    folder: str
    slug: str
    title: str
    # Generation
    gen_gate_status: str = "n/a"
    gen_retries: int = 0
    gen_cost_usd: float = 0.0
    gen_error: str = ""
    # Fallback (DeepSeek) — populated when the build_summaries fallback
    # path actually evaluated for this article. Default zero/empty so
    # rows with no fallback consideration aggregate to clean zeros.
    fallback_attempts_used: int = 0
    fallback_provider_used: Optional[str] = None
    fallback_model_used: Optional[str] = None
    fallback_skipped_reason: str = ""
    # Verification
    primary_verdict: Optional[str] = None
    secondary_verdict: Optional[str] = None
    single_verifier: bool = False
    secondary_skipped_cost_cap: bool = False
    verifier_cost_usd: float = 0.0
    final_verdict: Optional[str] = None
    top_issue: str = ""
    # Repair loop (PR L) — populated only when --enable-verifier-repair-loop
    # is set and the first-pass dual-verify did not auto-apply. Default
    # zero/empty so rows with no repair consideration aggregate to clean
    # zeros across the report.
    repair_loop_enabled: bool = False
    repair_cycles_used: int = 0
    repair_reason: str = ""
    repair_skipped_reason: str = ""
    pre_repair_final_verdict: Optional[str] = None
    pre_repair_top_issue: str = ""
    repair_cost_usd: float = 0.0
    repair_succeeded: bool = False
    # Action
    action: str = ACTION_DRAFT_ONLY
    notes: list[str] = field(default_factory=list)

    def total_cost_usd(self) -> float:
        return round(
            self.gen_cost_usd + self.verifier_cost_usd + self.repair_cost_usd,
            6,
        )


# =============================================================================
# Auto-apply eligibility
# =============================================================================

def can_auto_apply(
    final: Optional[vs.FinalVerdict],
    *,
    require_dual_verifier: bool = True,
) -> tuple[bool, str]:
    """Return (eligible, reason).

    Auto-apply rules — every condition must be True:

    - A final verdict exists (verifier actually ran).
    - Final verdict is AUTO_APPROVE.
    - ``single_verifier`` is False (both verifiers must have run).
    - ``secondary_skipped_cost_cap`` is False.

    The flag-driven escape hatch for single-verifier or cost-cap-skipped
    AUTO_APPROVE is *not* exposed in this PR by design.
    """
    if final is None:
        return False, "no verifier ran"
    if final.final != "AUTO_APPROVE":
        return False, f"final verdict {final.final}"
    if require_dual_verifier and final.single_verifier:
        return False, "single-verifier mode (dual-verifier confidence required)"
    if final.secondary_skipped_cost_cap:
        return False, "secondary verifier skipped by cost cap"
    return True, "AUTO_APPROVE with dual-verifier confidence"


def _promote_draft_to_approved(review_path: pathlib.Path) -> None:
    """Replace ``Status: draft`` with ``Status: approved`` in a review file.

    Narrow surgery: only flips the Status line. Everything else (title,
    summaries, verification block) is preserved verbatim so the existing
    ``build_summaries._apply_review_to_metadata`` path can run unchanged.
    """
    text = review_path.read_text(encoding="utf-8")
    new_text = re.sub(
        r"^Status:\s*draft\s*$",
        "Status: approved",
        text,
        count=1,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if new_text == text:
        raise ValueError(f"review file {review_path} has no draft status line")
    review_path.write_text(new_text, encoding="utf-8")


# =============================================================================
# Report path safety
# =============================================================================

def resolve_report_path(
    requested: Optional[str],
    today: Optional[datetime.datetime] = None,
    repo_root: Optional[pathlib.Path] = None,
) -> pathlib.Path:
    """Resolve ``--report-path``. Reject any path inside the repository.

    Default goes to ``/tmp/articles-summary-batch-<YYYY-MM-DD-HHMM>.md``.
    Explicit requests are resolved and checked against the repo root; a
    repo-internal path raises ValueError so the operator never silently
    commits a private report.

    Pytest test paths under ``/tmp`` or the OS temp dir continue to work
    because they live outside the repo.
    """
    if today is None:
        today = datetime.datetime.now()
    if repo_root is None:
        repo_root = REPO_ROOT
    if not requested:
        stamp = today.strftime("%Y-%m-%d-%H%M")
        return pathlib.Path(f"/tmp/articles-summary-batch-{stamp}.md")

    candidate = pathlib.Path(requested).expanduser().resolve()
    repo = pathlib.Path(repo_root).resolve()
    try:
        candidate.relative_to(repo)
    except ValueError:
        # NOT a subpath — that is the OK case.
        return candidate
    raise ValueError(
        f"--report-path must be outside the repository (got {candidate}). "
        f"Repo root: {repo}. Use a path under /tmp or another scratch dir."
    )


# =============================================================================
# Secret redaction in report content
# =============================================================================

_SECRET_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"),
    re.compile(r"DeepL-Auth-Key\s+[A-Za-z0-9:\-]{20,}"),
)


def redact(text: str) -> str:
    if not text:
        return text
    out = text
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def _truncate(text: str, limit: int = 240) -> str:
    if text is None:
        return ""
    text = redact(str(text))
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


# =============================================================================
# Per-article pipeline
# =============================================================================

def _clamp_max_repair_cycles(n: int) -> int:
    """Clamp --max-repair-cycles to [0, 2]. Negative values become 0."""
    if n is None:
        return 1
    try:
        v = int(n)
    except (TypeError, ValueError):
        return 1
    if v < 0:
        return 0
    if v > 2:
        return 2
    return v


def _parse_repair_on(spec: Optional[str]) -> frozenset[str]:
    """Parse --repair-on into a validated frozenset.

    Defaults to deterministic_gate + human_review. Unknown tokens are
    dropped silently rather than raising, so a typo doesn't break the
    runner; the runner logs the resolved set in the report.
    """
    if not spec:
        return bs.REPAIR_ON_DEFAULT
    tokens = {t.strip() for t in spec.split(",") if t.strip()}
    valid = tokens & bs.REPAIR_ON_VALID
    if not valid:
        return bs.REPAIR_ON_DEFAULT
    return frozenset(valid)


def _run_repair_cycle(
    *,
    outcome: "ArticleOutcome",
    article: dict,
    body: str,
    review_path: pathlib.Path,
    articles_dir: pathlib.Path,
    minimax_api_key: str,
    repair_model: str,
    primary_spec: vs.VerifierSpec,
    secondary_spec: Optional[vs.VerifierSpec],
    article_budget_remaining: float,
    apply_auto_approved: bool,
    require_dual_verifier_for_apply: bool,
    gen: dict,
    last_plan_final: Optional[vs.FinalVerdict],
) -> tuple[bool, Optional[vs.FinalVerdict], dict]:
    """Run ONE repair cycle for a single article.

    Returns ``(auto_applied_now, repaired_plan_final, repaired_gen_meta)``.

    * Builds a feedback packet from the previous deterministic-gate issues
      and the most recent dual-verifier rationale.
    * Calls the repair generator (MiniMax with REPAIR_SYSTEM_PROMPT).
    * Re-runs ``check_summaries`` on the repaired output for a fresh gate.
    * Re-runs both verifiers via ``vs.verify_one``.
    * Updates ``outcome`` in place with the new verdicts and cost.
    * If both repaired verifier verdicts are AUTO_APPROVE and the runner
      is in apply mode, promotes the review file and writes metadata.
    * Returns the repaired plan.final so the caller can decide whether
      to run another cycle.
    """
    from summary_quality import check_summaries  # local import — avoid cycles in tests

    # Build feedback packet from the most recent verdicts. If the previous
    # cycle was the initial pass, primary/secondary verifier values live
    # on ``last_plan_final``; otherwise they live on ``outcome`` after a
    # prior repair cycle updated it.
    primary_top = ""
    secondary_top = ""
    if last_plan_final is not None:
        if last_plan_final.primary is not None:
            primary_top = last_plan_final.primary.top_issue or ""
        if last_plan_final.secondary is not None:
            secondary_top = last_plan_final.secondary.top_issue or ""

    packet = bs._build_repair_feedback_packet(
        previous_summaries=gen.get("summaries") or {},
        gate_issues=gen.get("gate_issues") or [],
        primary_verdict=outcome.primary_verdict,
        primary_top_issue=primary_top,
        secondary_verdict=outcome.secondary_verdict,
        secondary_top_issue=secondary_top,
    )

    # Call repair. Bound by remaining article budget so cost cap holds.
    if article_budget_remaining <= 0:
        outcome.repair_skipped_reason = "budget exhausted before repair"
        return False, last_plan_final, gen

    repair_response = bs._call_repair_once(
        article_text=body,
        model=repair_model,
        api_key=minimax_api_key,
        feedback_packet=packet,
    )
    if repair_response.get("cost_usd"):
        outcome.repair_cost_usd += float(repair_response["cost_usd"])

    if not repair_response.get("ok"):
        outcome.notes.append(
            _truncate(
                f"repair cycle {outcome.repair_cycles_used + 1} failed: "
                f"{repair_response.get('error_kind') or repair_response.get('error', 'unknown')}",
                200,
            )
        )
        # Even a failed repair call counts as a cycle used for accounting.
        outcome.repair_cycles_used += 1
        return False, last_plan_final, gen

    repaired_summaries = repair_response.get("summaries") or {}

    # Re-run the deterministic gate on the repaired output.
    new_gate = check_summaries(repaired_summaries, body)
    repaired_gen = dict(gen)
    repaired_gen["gate_status"] = new_gate.status
    repaired_gen["gate_issues"] = list(new_gate.issues)
    repaired_gen["summaries"] = repaired_summaries

    # Rewrite the review file with the repaired summaries so the
    # verifier reads the post-repair text.
    bs._write_review_file(
        review_path,
        article,
        repaired_summaries,
        provider="minimax-repair",
        model=repair_model,
        gate_meta=repaired_gen,
    )

    # Re-run both verifiers on the repaired review file.
    remaining_after_repair = max(
        0.0,
        article_budget_remaining - (repair_response.get("cost_usd") or 0.0),
    )
    repaired_plan = vs.verify_one(
        review_path=review_path,
        articles_dir=articles_dir,
        primary_spec=primary_spec,
        secondary_spec=secondary_spec,
        fallback_spec=None,
        allow_network=True,
        single_verifier=(secondary_spec is None),
        max_cost_usd=remaining_after_repair,
    )

    outcome.repair_cycles_used += 1

    if repaired_plan.final is None:
        outcome.notes.append(
            f"repair cycle {outcome.repair_cycles_used} produced summaries "
            f"but verifier did not return a verdict"
        )
        return False, None, repaired_gen

    # Update outcome with repaired verdicts.
    outcome.final_verdict = repaired_plan.final.final
    outcome.single_verifier = repaired_plan.final.single_verifier
    outcome.secondary_skipped_cost_cap = repaired_plan.final.secondary_skipped_cost_cap
    outcome.verifier_cost_usd += float(repaired_plan.final.total_cost_usd or 0.0)
    if repaired_plan.final.primary is not None:
        outcome.primary_verdict = repaired_plan.final.primary.verdict
        if repaired_plan.final.primary.top_issue:
            outcome.top_issue = _truncate(
                repaired_plan.final.primary.top_issue, 200
            )
    if repaired_plan.final.secondary is not None:
        outcome.secondary_verdict = repaired_plan.final.secondary.verdict
        if repaired_plan.final.secondary.top_issue and not outcome.top_issue:
            outcome.top_issue = _truncate(
                repaired_plan.final.secondary.top_issue, 200
            )

    # Always write a fresh verification block for the repaired output.
    block = vs.render_verification_block(repaired_plan.final)
    vs.write_verification_to_file(review_path, block)

    # Auto-apply only if both repaired verifier verdicts are AUTO_APPROVE.
    if repaired_plan.final.final == "AUTO_APPROVE":
        eligible, reason = can_auto_apply(
            repaired_plan.final,
            require_dual_verifier=require_dual_verifier_for_apply,
        )
        if apply_auto_approved and eligible:
            try:
                _promote_draft_to_approved(review_path)
                review_data = bs._parse_review_file(review_path)
                bs._apply_review_to_metadata(
                    outcome.folder, review_data, allow_partial=False
                )
                outcome.action = ACTION_AUTO_APPLIED
                outcome.repair_succeeded = True
                outcome.notes.append(
                    f"repair cycle {outcome.repair_cycles_used} converted "
                    f"to AUTO_APPROVE; reason: {outcome.repair_reason}"
                )
                return True, repaired_plan.final, repaired_gen
            except Exception as e:  # noqa: BLE001
                outcome.action = ACTION_HUMAN_REVIEW
                outcome.notes.append(
                    _truncate(f"repair apply failed: {e}", 200)
                )
                return False, repaired_plan.final, repaired_gen
        elif apply_auto_approved:
            outcome.action = ACTION_HUMAN_REVIEW
            outcome.notes.append(reason)
            return False, repaired_plan.final, repaired_gen
        else:
            outcome.action = ACTION_DRAFT_ONLY
            return False, repaired_plan.final, repaired_gen

    # Still HUMAN_REVIEW or REJECT after this cycle. Update action to
    # match the new verdict so the caller can decide whether to keep
    # going.
    if repaired_plan.final.final == "REJECT":
        outcome.action = ACTION_REJECTED
    elif repaired_plan.final.final == "HUMAN_REVIEW":
        outcome.action = ACTION_HUMAN_REVIEW
    return False, repaired_plan.final, repaired_gen


def run_one_article(
    article: dict,
    *,
    articles_dir: pathlib.Path,
    summaries_dir: pathlib.Path,
    minimax_api_key: Optional[str],
    minimax_model: str,
    max_retries: int,
    article_budget_usd: float,
    primary_spec: Optional[vs.VerifierSpec],
    secondary_spec: Optional[vs.VerifierSpec],
    do_verify: bool,
    dry_run: bool,
    apply_auto_approved: bool,
    require_dual_verifier_for_apply: bool = True,
    # DeepSeek fallback config (PR I plumbing). Defaults disable the
    # fallback entirely so existing call sites and tests stay unchanged.
    enable_fallback_on_undersize: bool = False,
    fallback_provider: str = "deepseek",
    fallback_model: str = "deepseek-v4-flash",
    fallback_max_attempts: int = 1,
    fallback_api_key: Optional[str] = None,
    # Repair loop (PR L). Defaults disable the loop entirely.
    enable_verifier_repair_loop: bool = False,
    max_repair_cycles: int = 1,
    repair_provider: str = "minimax",
    repair_model: Optional[str] = None,
    repair_on: Optional[frozenset[str]] = None,
) -> ArticleOutcome:
    """Run the full pipeline for one article. Always returns an outcome."""
    outcome = ArticleOutcome(
        folder=article["folder"],
        slug=article.get("slug", ""),
        title=article.get("title", ""),
    )

    if article_budget_usd <= 0:
        outcome.action = ACTION_SKIPPED_COST_CAP
        outcome.notes.append("budget exhausted before generation")
        return outcome

    body = bs._read_article_body(article["folder"])
    if not body:
        outcome.action = ACTION_GENERATION_FAILED
        outcome.gen_error = "no article body"
        outcome.notes.append("article body missing or empty")
        return outcome

    if dry_run:
        outcome.gen_gate_status = "DRY_RUN"
        outcome.action = ACTION_DRAFT_ONLY
        outcome.notes.append("dry-run: no generation, no verification, no writes")
        return outcome

    if minimax_api_key is None:
        outcome.action = ACTION_GENERATION_FAILED
        outcome.gen_error = "MINIMAX_API_KEY not set"
        outcome.notes.append("missing MiniMax key (no value printed)")
        return outcome

    # ---- Generation phase ----
    gen = bs._generate_with_retries(
        article_text=body,
        model=minimax_model,
        max_retries=max_retries,
        max_cost_usd=article_budget_usd,
        api_key=minimax_api_key,
        enable_fallback_on_undersize=enable_fallback_on_undersize,
        fallback_provider=fallback_provider,
        fallback_model=fallback_model,
        fallback_max_attempts=fallback_max_attempts,
        fallback_api_key=fallback_api_key,
    )
    outcome.gen_gate_status = getattr(gen["gate_status"], "value", str(gen["gate_status"]))
    outcome.gen_retries = gen.get("retries_used", 0)
    outcome.gen_cost_usd = float(gen.get("total_cost_usd") or 0.0)
    outcome.fallback_attempts_used = int(gen.get("fallback_attempts_used") or 0)
    outcome.fallback_provider_used = gen.get("fallback_provider_used")
    outcome.fallback_model_used = gen.get("fallback_model_used")
    outcome.fallback_skipped_reason = gen.get("fallback_skipped_reason") or ""
    if gen.get("gate_issues"):
        outcome.notes.extend(_truncate(i, 160) for i in gen["gate_issues"][:3])

    summaries = gen.get("summaries")
    if summaries is None:
        outcome.action = ACTION_GENERATION_FAILED
        outcome.gen_error = "generation produced no summaries"
        return outcome

    # Always write the draft review file — even on RETRYABLE/HUMAN_REVIEW the
    # operator wants to see what the model produced.
    review_path = bs._build_review_path(summaries_dir, outcome.slug or outcome.folder)
    bs._write_review_file(
        review_path,
        article,
        summaries,
        provider="minimax",
        model=minimax_model,
        gate_meta=gen,
    )

    # ---- Verification phase ----
    if do_verify and primary_spec is not None:
        remaining_for_verifier = max(0.0, article_budget_usd - outcome.gen_cost_usd)
        plan = vs.verify_one(
            review_path=review_path,
            articles_dir=articles_dir,
            primary_spec=primary_spec,
            secondary_spec=secondary_spec,
            fallback_spec=None,
            allow_network=True,
            single_verifier=(secondary_spec is None),
            max_cost_usd=remaining_for_verifier,
        )
        if plan.final is not None:
            outcome.final_verdict = plan.final.final
            outcome.single_verifier = plan.final.single_verifier
            outcome.secondary_skipped_cost_cap = plan.final.secondary_skipped_cost_cap
            outcome.verifier_cost_usd = float(plan.final.total_cost_usd or 0.0)
            if plan.final.primary is not None:
                outcome.primary_verdict = plan.final.primary.verdict
                if plan.final.primary.top_issue and not outcome.top_issue:
                    outcome.top_issue = _truncate(plan.final.primary.top_issue, 200)
            if plan.final.secondary is not None:
                outcome.secondary_verdict = plan.final.secondary.verdict
                if plan.final.secondary.top_issue and not outcome.top_issue:
                    outcome.top_issue = _truncate(plan.final.secondary.top_issue, 200)
            elif plan.final.secondary_skipped_cost_cap:
                outcome.secondary_verdict = "skipped (cost cap)"

            # Always write the verification block when verification ran.
            block = vs.render_verification_block(plan.final)
            vs.write_verification_to_file(review_path, block)

    # ---- Action selection ----
    if outcome.final_verdict == "REJECT":
        outcome.action = ACTION_REJECTED
    elif outcome.final_verdict == "AUTO_APPROVE":
        eligible, reason = can_auto_apply(
            plan.final if do_verify and primary_spec is not None else None,
            require_dual_verifier=require_dual_verifier_for_apply,
        )
        if apply_auto_approved and eligible:
            try:
                _promote_draft_to_approved(review_path)
                review_data = bs._parse_review_file(review_path)
                bs._apply_review_to_metadata(
                    outcome.folder, review_data, allow_partial=False
                )
                outcome.action = ACTION_AUTO_APPLIED
                outcome.notes.append(reason)
            except Exception as e:  # noqa: BLE001 — surface the failure in the report
                outcome.action = ACTION_HUMAN_REVIEW
                outcome.notes.append(_truncate(f"apply failed: {e}", 200))
        elif apply_auto_approved:
            outcome.action = ACTION_HUMAN_REVIEW
            outcome.notes.append(reason)
        else:
            outcome.action = ACTION_DRAFT_ONLY
    elif outcome.final_verdict == "HUMAN_REVIEW":
        outcome.action = ACTION_HUMAN_REVIEW
    else:
        # No verdict (verifier did not run or failed)
        outcome.action = ACTION_DRAFT_ONLY

    # ---- Verifier-feedback repair loop (PR L) ----
    #
    # Repair runs only when:
    #   * --enable-verifier-repair-loop is set, AND
    #   * the first dual-verify pass did not auto-apply, AND
    #   * the first pass produced a HUMAN_REVIEW or soft-REJECT verdict
    #     in an eligible failure category, AND
    #   * the article-level budget has headroom.
    #
    # Repair NEVER weakens the dual-verifier AUTO_APPROVE boundary —
    # the repaired output must clear the deterministic gate AND both
    # repaired verifier verdicts must be AUTO_APPROVE before any
    # metadata write.
    repair_cap = _clamp_max_repair_cycles(max_repair_cycles)
    if (
        enable_verifier_repair_loop
        and repair_cap > 0
        and do_verify
        and primary_spec is not None
        and minimax_api_key is not None
        and outcome.action in (ACTION_HUMAN_REVIEW, ACTION_REJECTED)
        and outcome.final_verdict in ("HUMAN_REVIEW", "REJECT")
    ):
        outcome.repair_loop_enabled = True
        # Snapshot the pre-repair state so the report can quantify lift.
        outcome.pre_repair_final_verdict = outcome.final_verdict
        outcome.pre_repair_top_issue = outcome.top_issue

        active_repair_on = repair_on if repair_on is not None else bs.REPAIR_ON_DEFAULT

        eligible, repair_reason = bs._is_repair_eligible(
            gate_status=gen.get("gate_status"),
            gate_issues=gen.get("gate_issues") or [],
            final_verdict=outcome.final_verdict,
            primary_verdict=outcome.primary_verdict,
            primary_top_issue=(
                plan.final.primary.top_issue
                if plan.final is not None and plan.final.primary is not None
                else ""
            ),
            secondary_verdict=outcome.secondary_verdict,
            secondary_top_issue=(
                plan.final.secondary.top_issue
                if plan.final is not None and plan.final.secondary is not None
                else ""
            ),
            repair_on=active_repair_on,
        )

        if not eligible:
            outcome.repair_skipped_reason = repair_reason
        else:
            outcome.repair_reason = repair_reason
            effective_repair_model = repair_model or minimax_model
            last_plan_final = plan.final if plan is not None else None
            cycles_remaining = repair_cap
            while cycles_remaining > 0 and outcome.action != ACTION_AUTO_APPLIED:
                budget_remaining = max(
                    0.0,
                    article_budget_usd
                    - outcome.gen_cost_usd
                    - outcome.verifier_cost_usd
                    - outcome.repair_cost_usd,
                )
                if budget_remaining <= 0:
                    outcome.repair_skipped_reason = (
                        outcome.repair_skipped_reason
                        or "budget exhausted before repair"
                    )
                    break

                applied, repaired_final, repaired_gen = _run_repair_cycle(
                    outcome=outcome,
                    article=article,
                    body=body,
                    review_path=review_path,
                    articles_dir=articles_dir,
                    minimax_api_key=minimax_api_key,
                    repair_model=effective_repair_model,
                    primary_spec=primary_spec,
                    secondary_spec=secondary_spec,
                    article_budget_remaining=budget_remaining,
                    apply_auto_approved=apply_auto_approved,
                    require_dual_verifier_for_apply=require_dual_verifier_for_apply,
                    gen=gen,
                    last_plan_final=last_plan_final,
                )

                gen = repaired_gen
                last_plan_final = repaired_final

                if applied:
                    break

                # If the repair attempt itself failed (the cycle counter
                # advanced but no verifier plan came back), do not keep
                # spinning — the next cycle would use the same feedback
                # and likely fail the same way.
                if repaired_final is None:
                    break

                cycles_remaining -= 1

    return outcome


# =============================================================================
# Report
# =============================================================================

def repo_head_sha(repo_root: pathlib.Path) -> str:
    """Best-effort HEAD lookup. Returns 'unknown' if anything fails."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:  # pragma: no cover - defensive
        pass
    return "unknown"


def render_report(
    *,
    started_at: datetime.datetime,
    head_sha: str,
    args_summary: dict[str, Any],
    selected: list[dict],
    outcomes: list[ArticleOutcome],
    cumulative_cost: float,
    args: argparse.Namespace,
) -> str:
    lines: list[str] = []
    lines.append(f"# Summary batch report — {started_at.isoformat()}")
    lines.append("")
    lines.append("Generated by `tools/run_summary_batch.py`. Report lives outside the repository.")
    lines.append("")
    lines.append("## Run parameters")
    lines.append(f"- Repo HEAD: `{head_sha}`")
    for key, label in (
        ("limit", "limit"),
        ("missing_only", "missing_only"),
        ("slug", "slug"),
        ("provider", "generator_provider"),
        ("model", "generator_model"),
        ("primary_verifier", "primary_verifier"),
        ("primary_model", "primary_model"),
        ("secondary_verifier", "secondary_verifier"),
        ("secondary_model", "secondary_model"),
        ("allow_network", "allow_network"),
        ("max_budget_usd", "max_budget_usd"),
        ("max_retries", "max_retries"),
        ("verify", "verify"),
        ("apply_auto_approved", "apply_auto_approved"),
        ("enable_fallback_on_undersize", "enable_fallback_on_undersize"),
        ("fallback_provider", "fallback_provider"),
        ("fallback_model", "fallback_model"),
        ("fallback_max_attempts", "fallback_max_attempts"),
        ("dry_run", "dry_run"),
    ):
        if key in args_summary:
            lines.append(f"- {label}: `{args_summary[key]}`")
    lines.append("")

    lines.append("## Selected articles")
    if not selected:
        lines.append("- (none)")
    for art in selected:
        lines.append(f"- `{art['folder']}` — {redact(art.get('title') or '')}")
    lines.append("")

    lines.append("## Per-article results")
    lines.append("")
    header = (
        "| folder | gate | retries | primary | secondary | final | action | "
        "gen $ | verif $ | top issue |"
    )
    sep = "|" + "|".join(["---"] * 10) + "|"
    lines.append(header)
    lines.append(sep)
    for o in outcomes:
        lines.append(
            "| `{folder}` | {gate} | {retries} | {primary} | {secondary} | "
            "{final} | {action} | ${gen:.6f} | ${vfy:.6f} | {issue} |".format(
                folder=o.folder,
                gate=o.gen_gate_status,
                retries=o.gen_retries,
                primary=o.primary_verdict or "-",
                secondary=o.secondary_verdict or "-",
                final=o.final_verdict or "-",
                action=o.action,
                gen=o.gen_cost_usd,
                vfy=o.verifier_cost_usd,
                issue=_truncate(o.top_issue, 60) or "-",
            )
        )
    lines.append("")

    # Per-article notes block (multi-line, harder to fit in the table).
    has_notes = any(o.notes for o in outcomes)
    if has_notes:
        lines.append("### Per-article notes")
        lines.append("")
        for o in outcomes:
            if not o.notes:
                continue
            lines.append(f"- `{o.folder}`:")
            for note in o.notes:
                lines.append(f"  - {redact(note)}")
        lines.append("")

    lines.append("## Totals")
    counts = {
        "generated": 0,
        "verified": 0,
        "auto_approve": 0,
        "human_review": 0,
        "reject": 0,
        "applied": 0,
        "exceptions": 0,
        "fallback_attempts_total": 0,
        "fallback_articles_invoked": 0,
        "fallback_articles_skipped": 0,
    }
    repair_counts = {
        "repair_loop_enabled": bool(getattr(args, "enable_verifier_repair_loop", False)),
        "repair_max_cycles": _clamp_max_repair_cycles(
            getattr(args, "max_repair_cycles", 1)
        ),
        "repair_candidates": 0,
        "repair_attempts": 0,
        "repair_successes": 0,
        "repair_failures": 0,
        "repair_skipped": 0,
        "repair_converted_to_auto_approve": 0,
    }
    fallback_skip_reasons: dict[str, int] = {}
    repair_skip_reasons: dict[str, int] = {}
    repair_reasons: dict[str, int] = {}
    total_repair_cost = 0.0
    for o in outcomes:
        if o.gen_gate_status not in ("n/a", "DRY_RUN"):
            counts["generated"] += 1
        if o.final_verdict is not None:
            counts["verified"] += 1
        if o.final_verdict == "AUTO_APPROVE":
            counts["auto_approve"] += 1
        elif o.final_verdict == "HUMAN_REVIEW":
            counts["human_review"] += 1
        elif o.final_verdict == "REJECT":
            counts["reject"] += 1
        if o.action == ACTION_AUTO_APPLIED:
            counts["applied"] += 1
        if o.action in (
            ACTION_HUMAN_REVIEW,
            ACTION_REJECTED,
            ACTION_SKIPPED_COST_CAP,
            ACTION_GENERATION_FAILED,
        ):
            counts["exceptions"] += 1
        if o.fallback_attempts_used:
            counts["fallback_attempts_total"] += o.fallback_attempts_used
            counts["fallback_articles_invoked"] += 1
        if o.fallback_skipped_reason:
            counts["fallback_articles_skipped"] += 1
            fallback_skip_reasons[o.fallback_skipped_reason] = (
                fallback_skip_reasons.get(o.fallback_skipped_reason, 0) + 1
            )
        # Repair metrics. A candidate is any article where the first
        # pass landed in HUMAN_REVIEW/REJECT and repair was enabled;
        # attempts is the per-cycle counter; success means converted to
        # AUTO_APPROVE during the repair loop.
        if o.repair_loop_enabled:
            counts_or_skip = bool(o.repair_skipped_reason) or o.repair_cycles_used > 0
            if counts_or_skip:
                repair_counts["repair_candidates"] += 1
            if o.repair_skipped_reason:
                repair_counts["repair_skipped"] += 1
                repair_skip_reasons[o.repair_skipped_reason] = (
                    repair_skip_reasons.get(o.repair_skipped_reason, 0) + 1
                )
            if o.repair_cycles_used > 0:
                repair_counts["repair_attempts"] += o.repair_cycles_used
                if o.repair_succeeded:
                    repair_counts["repair_successes"] += 1
                    repair_counts["repair_converted_to_auto_approve"] += 1
                else:
                    repair_counts["repair_failures"] += 1
            if o.repair_reason:
                repair_reasons[o.repair_reason] = (
                    repair_reasons.get(o.repair_reason, 0) + 1
                )
            total_repair_cost += float(o.repair_cost_usd or 0.0)

    for k, v in counts.items():
        lines.append(f"- {k}: {v}")
    lines.append(f"- cumulative_cost_usd: {cumulative_cost:.6f}")
    lines.append(f"- max_budget_usd: {args.max_budget_usd}")
    if fallback_skip_reasons:
        lines.append("- fallback_skipped_reasons:")
        for reason, n in sorted(fallback_skip_reasons.items(), key=lambda kv: -kv[1]):
            lines.append(f"  - {redact(reason)}: {n}")

    # Repair-loop metrics block. Emitted whenever the loop is enabled so
    # the report records both candidates considered and skips applied.
    if repair_counts["repair_loop_enabled"]:
        lines.append("- repair_loop_enabled: true")
        for k in (
            "repair_max_cycles",
            "repair_candidates",
            "repair_attempts",
            "repair_successes",
            "repair_failures",
            "repair_skipped",
            "repair_converted_to_auto_approve",
        ):
            lines.append(f"- {k}: {repair_counts[k]}")
        lines.append(f"- repair_cost_usd: {total_repair_cost:.6f}")
        if repair_reasons:
            lines.append("- repair_reasons:")
            for r, n in sorted(repair_reasons.items(), key=lambda kv: -kv[1]):
                lines.append(f"  - {redact(r)}: {n}")
        if repair_skip_reasons:
            lines.append("- repair_skipped_reasons:")
            for r, n in sorted(repair_skip_reasons.items(), key=lambda kv: -kv[1]):
                lines.append(f"  - {redact(r)}: {n}")
    lines.append("")

    lines.append("## Next command suggestion")
    if counts["applied"] > 0 and not args.rebuild_artifacts:
        lines.append(
            "- One or more articles were auto-applied to metadata. "
            "Rebuild generated artifacts before opening a content PR:"
        )
        lines.append("  ```")
        lines.append("  python3 tools/rebuild_local.py && python3 tools/update_docs.py")
        lines.append("  python3 tools/check_generated_artifacts.py")
        lines.append("  ```")
    elif counts["human_review"] > 0 or counts["reject"] > 0:
        lines.append(
            "- Exceptions remain. Inspect the draft `summaries/<slug>.review.md` "
            "files listed above and decide manually."
        )
    elif counts["auto_approve"] > 0 and not args.apply_auto_approved:
        lines.append(
            "- Articles cleared dual-verifier AUTO_APPROVE. Re-run with "
            "`--apply-auto-approved` to write metadata.json."
        )
    else:
        lines.append("- Nothing required.")
    lines.append("")
    return "\n".join(lines)


def write_report(report_path: pathlib.Path, content: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")


# =============================================================================
# CLI
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_summary_batch",
        description=(
            "Automated summary pipeline. Default behaviour is dry-run "
            "(no network, no writes). Live calls require --batch AND "
            "--allow-network AND --max-budget-usd > 0. Metadata writes "
            "additionally require --apply-auto-approved."
        ),
    )
    p.add_argument("--batch", action="store_true",
                   help="Required for any live batch run.")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--missing-only", action="store_true", default=True)
    p.add_argument("--no-missing-only", dest="missing_only", action="store_false",
                   help="Override default --missing-only.")
    p.add_argument("--slug", default=None)
    p.add_argument("--summaries-dir", default=str(DEFAULT_SUMMARIES_DIR))
    p.add_argument("--report-path", default=None,
                   help="Default: /tmp/articles-summary-batch-<stamp>.md. "
                        "Must resolve outside the repository.")
    p.add_argument("--provider", choices=["minimax"], default="minimax")
    p.add_argument("--model", default="MiniMax-M2")
    p.add_argument("--primary-verifier", choices=["openai"], default="openai")
    p.add_argument("--primary-model", default="gpt-5.4-mini")
    p.add_argument("--secondary-verifier", choices=["anthropic", "none"], default="anthropic")
    p.add_argument("--secondary-model", default="claude-haiku-4-5-20251001")
    p.add_argument("--allow-network", action="store_true")
    p.add_argument("--max-budget-usd", type=float, default=1.00)
    p.add_argument("--max-retries", type=int, default=2)
    p.add_argument("--verify", action="store_true", default=True)
    p.add_argument("--no-verify", dest="verify", action="store_false")
    p.add_argument("--apply-auto-approved", action="store_true", default=False,
                   help="Required for any metadata write. Only final "
                        "AUTO_APPROVE results with dual-verifier confidence are "
                        "ever auto-applied.")
    p.add_argument("--rebuild-artifacts", action="store_true", default=False,
                   help="Flag-only in PR F: the runner emits a next-command hint "
                        "instead of running the rebuild. Keeps generated-artifact "
                        "diffs out of automation PRs.")
    # DeepSeek fallback (PR I plumbing — implemented in build_summaries.py
    # via PR H). Disabled by default; live activation requires the same
    # triple gate as the generator + a DEEPSEEK_API_KEY in env.
    p.add_argument("--enable-fallback-on-undersize", action="store_true", default=False,
                   help="When the primary generator (MiniMax) exhausts undersize "
                        "retries and the only deterministic-gate failure is "
                        "summary_long below the 430-word minimum, route ONE "
                        "additional generation attempt through the fallback "
                        "provider (DeepSeek). Output still passes the same "
                        "deterministic gate and dual verifier; no auto-approval "
                        "boundary change.")
    p.add_argument("--fallback-provider", choices=["deepseek"], default="deepseek",
                   help="Fallback provider name. Default: deepseek.")
    p.add_argument("--fallback-model", default="deepseek-v4-flash",
                   help="Fallback model id. Default: deepseek-v4-flash.")
    p.add_argument("--fallback-max-attempts", type=int, default=1,
                   help="Hard cap on fallback attempts per article. "
                        "Effectively pinned to 1 by the build_summaries layer.")
    # Verifier-feedback repair loop (PR L). Optional pass that feeds
    # structured deterministic-gate + verifier feedback back into a
    # bounded repair generation, then re-runs the same gate and dual
    # verifier. Disabled by default; live activation requires the same
    # triple gate as the generator. Repair never weakens the dual-verifier
    # AUTO_APPROVE boundary.
    p.add_argument("--enable-verifier-repair-loop", action="store_true",
                   default=False,
                   help="After a first-pass dual-verify HUMAN_REVIEW (or "
                        "REJECT in safe categories only), run a bounded "
                        "repair pass that feeds structured feedback into a "
                        "regeneration. Re-runs the deterministic gate and "
                        "BOTH verifiers; auto-apply still requires both "
                        "repaired verdicts to be AUTO_APPROVE.")
    p.add_argument("--max-repair-cycles", type=int, default=1,
                   help="Cap on repair cycles per article. Default 1, "
                        "hard cap 2. Higher values are clamped to 2.")
    p.add_argument("--repair-provider", choices=["minimax"], default="minimax",
                   help="Repair provider. Defaults to the primary generator "
                        "provider. Only minimax is supported in this release.")
    p.add_argument("--repair-model", default=None,
                   help="Repair model id. Defaults to --model.")
    p.add_argument("--repair-on", default="deterministic_gate,human_review",
                   help="Comma-separated list of failure categories that "
                        "trigger repair. Choices: deterministic_gate, "
                        "human_review, reject. Default: "
                        "deterministic_gate,human_review. Including "
                        "'reject' is opt-in and only applies to soft "
                        "rejects; hard-reject categories (invented facts, "
                        "named entities, pricing, compliance claims) are "
                        "always excluded.")
    p.add_argument("--dry-run", action="store_true", default=False,
                   help="Force dry-run even if --allow-network is set.")
    p.add_argument("--articles-dir", default=str(ARTICLES_DIR))
    p.add_argument("--index-path", default=str(INDEX_PATH))
    return p


def _is_live(args: argparse.Namespace) -> bool:
    return bool(
        args.batch
        and args.allow_network
        and not args.dry_run
        and args.max_budget_usd is not None
        and args.max_budget_usd > 0
    )


def _print_plan_header(
    args: argparse.Namespace,
    selected: list[dict],
    live: bool,
) -> None:
    print(
        f"[batch] live={live} apply_auto_approved={args.apply_auto_approved} "
        f"limit={args.limit} slug={args.slug or '-'} "
        f"summaries_dir={args.summaries_dir} "
        f"max_budget_usd=${args.max_budget_usd:.2f} "
        f"selected={len(selected)} "
        f"fallback_enabled={args.enable_fallback_on_undersize}"
    )
    if args.enable_fallback_on_undersize:
        print(
            f"[batch] fallback_provider={args.fallback_provider} "
            f"fallback_model={args.fallback_model} "
            f"fallback_max_attempts={args.fallback_max_attempts}"
        )


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    # Resolve report path first so a bad path stops us before any heavy work.
    try:
        report_path = resolve_report_path(args.report_path)
    except ValueError as e:
        print(f"[batch] ERROR: {e}", file=sys.stderr)
        return 2

    articles_dir = pathlib.Path(args.articles_dir)
    summaries_dir = pathlib.Path(args.summaries_dir)
    index_path = pathlib.Path(args.index_path)

    selected = select_articles(
        index_path=index_path,
        articles_dir=articles_dir,
        missing_only=args.missing_only,
        slug=args.slug,
        limit=args.limit,
    )

    live = _is_live(args)
    _print_plan_header(args, selected, live)

    if args.apply_auto_approved and not live:
        print(
            "[batch] ERROR: --apply-auto-approved requires --batch --allow-network "
            "--max-budget-usd > 0. Refusing to write metadata in dry-run mode.",
            file=sys.stderr,
        )
        return 2

    # Resolve verifier specs (only needed for live + verify).
    primary_spec: Optional[vs.VerifierSpec] = None
    secondary_spec: Optional[vs.VerifierSpec] = None
    if args.verify and live:
        try:
            primary_spec = vs._resolve_verifier(args.primary_model, args.primary_verifier)
            if args.secondary_verifier != "none":
                secondary_spec = vs._resolve_verifier(
                    args.secondary_model, args.secondary_verifier
                )
        except ValueError as e:
            print(f"[batch] ERROR: {e}", file=sys.stderr)
            return 2

    # Resolve generator key once. Detection only — never print the value.
    minimax_api_key: Optional[str] = None
    fallback_api_key: Optional[str] = None
    if live:
        minimax_api_key = os.environ.get("MINIMAX_API_KEY", "").strip() or None
        if minimax_api_key is None:
            print(
                "[batch] ERROR: MINIMAX_API_KEY required for live generation "
                "(value not printed).",
                file=sys.stderr,
            )
            return 2
        if primary_spec is not None:
            if not os.environ.get(primary_spec.env_var, "").strip():
                print(
                    f"[batch] ERROR: {primary_spec.env_var} required for the "
                    f"primary verifier (value not printed).",
                    file=sys.stderr,
                )
                return 2
        # DeepSeek fallback key — only required when the fallback flag is
        # set on a live run. Presence-only check; never print the value.
        if args.enable_fallback_on_undersize and args.fallback_provider == "deepseek":
            fallback_api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip() or None
            if fallback_api_key is None:
                print(
                    "[batch] ERROR: DEEPSEEK_API_KEY required when "
                    "--enable-fallback-on-undersize is set with fallback provider "
                    "'deepseek' (value not printed).",
                    file=sys.stderr,
                )
                return 2

    cumulative_cost = 0.0
    outcomes: list[ArticleOutcome] = []
    started_at = datetime.datetime.now()

    for art in selected:
        per_article_budget = max(0.0, args.max_budget_usd - cumulative_cost)
        if live and per_article_budget <= 0:
            outcomes.append(ArticleOutcome(
                folder=art["folder"],
                slug=art.get("slug", ""),
                title=art.get("title", ""),
                action=ACTION_SKIPPED_COST_CAP,
                notes=["cumulative budget exhausted before article"],
            ))
            continue

        outcome = run_one_article(
            article=art,
            articles_dir=articles_dir,
            summaries_dir=summaries_dir,
            minimax_api_key=minimax_api_key,
            minimax_model=args.model,
            max_retries=args.max_retries,
            article_budget_usd=per_article_budget,
            primary_spec=primary_spec,
            secondary_spec=secondary_spec,
            do_verify=args.verify,
            dry_run=not live,
            apply_auto_approved=args.apply_auto_approved,
            enable_fallback_on_undersize=args.enable_fallback_on_undersize,
            fallback_provider=args.fallback_provider,
            fallback_model=args.fallback_model,
            fallback_max_attempts=args.fallback_max_attempts,
            fallback_api_key=fallback_api_key,
            enable_verifier_repair_loop=args.enable_verifier_repair_loop,
            max_repair_cycles=_clamp_max_repair_cycles(args.max_repair_cycles),
            repair_provider=args.repair_provider,
            repair_model=args.repair_model,
            repair_on=_parse_repair_on(args.repair_on),
        )
        cumulative_cost += outcome.total_cost_usd()
        outcomes.append(outcome)
        print(
            f"[batch] {art['folder']}: gate={outcome.gen_gate_status} "
            f"final={outcome.final_verdict or '-'} action={outcome.action} "
            f"cost=${outcome.total_cost_usd():.6f} "
            f"cumulative=${cumulative_cost:.6f}"
        )

    head_sha = repo_head_sha(REPO_ROOT)
    args_summary = {
        "limit": args.limit,
        "missing_only": args.missing_only,
        "slug": args.slug,
        "provider": args.provider,
        "model": args.model,
        "primary_verifier": args.primary_verifier,
        "primary_model": args.primary_model,
        "secondary_verifier": args.secondary_verifier,
        "secondary_model": args.secondary_model,
        "allow_network": args.allow_network,
        "max_budget_usd": args.max_budget_usd,
        "max_retries": args.max_retries,
        "verify": args.verify,
        "apply_auto_approved": args.apply_auto_approved,
        "enable_fallback_on_undersize": args.enable_fallback_on_undersize,
        "fallback_provider": args.fallback_provider,
        "fallback_model": args.fallback_model,
        "fallback_max_attempts": args.fallback_max_attempts,
        "enable_verifier_repair_loop": args.enable_verifier_repair_loop,
        "max_repair_cycles": _clamp_max_repair_cycles(args.max_repair_cycles),
        "repair_provider": args.repair_provider,
        "repair_model": args.repair_model or args.model,
        "repair_on": sorted(_parse_repair_on(args.repair_on)),
        "dry_run": not live,
    }
    report = render_report(
        started_at=started_at,
        head_sha=head_sha,
        args_summary=args_summary,
        selected=selected,
        outcomes=outcomes,
        cumulative_cost=cumulative_cost,
        args=args,
    )
    write_report(report_path, report)
    print(f"[batch] report: {report_path}")

    if args.rebuild_artifacts:
        # Flag-only in PR F: print the rebuild hint, do not execute. Keeps
        # generated-artifact diffs out of automation runs by default.
        print(
            "[batch] --rebuild-artifacts is flag-only in this release; run the "
            "rebuild manually after inspecting the report:"
        )
        print("  python3 tools/rebuild_local.py && python3 tools/update_docs.py")
        print("  python3 tools/check_generated_artifacts.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
