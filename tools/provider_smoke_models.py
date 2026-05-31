"""Model registry for tools/provider_smoke.py.

Default and experimental models are split so that operators can run the harness
against the recommended production set without accidentally invoking models
that smoke evidence shows are unsuitable for bulk structured-summary workloads.

The split is informed by the 2026-05-31 smoke + addendum runs (see operator's
local diagnostic files); it must be revisited once a larger benchmark sample
exists. The harness's `--include-experimental-models` flag explicitly opts in
to the EXPERIMENTAL_MODELS set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ModelSpec:
    """A single model in the smoke-test registry.

    Attributes:
        model_id: Vendor-specific identifier passed in the API request body.
        provider: Provider key matching the dispatcher in provider_smoke.py
            (one of: "deepseek", "minimax", "anthropic").
        endpoint: Full HTTPS endpoint URL for chat-completion-style calls.
        env_var: Environment-variable name carrying the API key. The harness
            reads only presence; values never leave the request payload.
        default_role: Default pipeline role suggested by smoke evidence.
            Used by the report writer to seed the production-recommendation
            column. Operators can override at call time.
        pricing_in_usd_per_million: Estimated input-token price. Source must
            be the operator's billing dashboard or vendor pricing page; the
            value lives here only to populate the report's cost column and
            should be treated as a directional estimate, not as a contract.
        pricing_out_usd_per_million: Estimated output-token price.
        notes: One-paragraph operator-facing note appended to the report
            when the model appears in a run.
    """

    model_id: str
    provider: str
    endpoint: str
    env_var: str
    default_role: str
    pricing_in_usd_per_million: Optional[float] = None
    pricing_out_usd_per_million: Optional[float] = None
    notes: str = ""


DEFAULT_MODELS: dict[str, ModelSpec] = {
    "deepseek-v4-flash": ModelSpec(
        model_id="deepseek-v4-flash",
        provider="deepseek",
        endpoint="https://api.deepseek.com/v1/chat/completions",
        env_var="DEEPSEEK_API_KEY",
        default_role="bulk_primary",
        pricing_in_usd_per_million=0.27,
        pricing_out_usd_per_million=1.10,
        notes=(
            "Bulk-primary candidate. Fast (~0.5 s in smoke) and cheap. "
            "Must run behind a different-family verifier on every call: in the "
            "2026-05-31 smoke (N=2), v4-flash hallucinated on the risk-heavy "
            "article. The 2026-05-31 addendum (N=4) saw the failure shape "
            "suppressed by an explicit anti-fabrication prompt, but the "
            "verifier gate remains load-bearing."
        ),
    ),
    "MiniMax-M2": ModelSpec(
        model_id="MiniMax-M2",
        provider="minimax",
        endpoint="https://api.minimax.io/v1/text/chatcompletion_v2",
        env_var="MINIMAX_API_KEY",
        default_role="risk_heavy_primary",
        pricing_in_usd_per_million=0.30,
        pricing_out_usd_per_million=1.20,
        notes=(
            "Risk-heavy primary candidate. Slower (~15 s in smoke) but the "
            "only model in either smoke run to hit all three word-count "
            "bands cleanly on at least one article. Use on operator-tagged "
            "risk-heavy articles, and as bulk fallback when DeepSeek "
            "verifier-REJECTs."
        ),
    ),
    "claude-haiku-4-5-20251001": ModelSpec(
        model_id="claude-haiku-4-5-20251001",
        provider="anthropic",
        endpoint="https://api.anthropic.com/v1/messages",
        env_var="ANTHROPIC_API_KEY",
        default_role="verifier",
        pricing_in_usd_per_million=1.00,
        pricing_out_usd_per_million=5.00,
        notes=(
            "Verifier primary. Catches substantive issues (fabrication, "
            "voice drift, schema problems). Smoke evidence shows it is "
            "unreliable on word-count arithmetic — pair every Haiku verdict "
            "with the deterministic Python word-count gate in this harness. "
            "Generator-of-last-resort if both DeepSeek and MiniMax fail."
        ),
    ),
}


EXPERIMENTAL_MODELS: dict[str, ModelSpec] = {
    "deepseek-v4-pro": ModelSpec(
        model_id="deepseek-v4-pro",
        provider="deepseek",
        endpoint="https://api.deepseek.com/v1/chat/completions",
        env_var="DEEPSEEK_API_KEY",
        default_role="reject_production",
        pricing_in_usd_per_million=0.55,
        pricing_out_usd_per_million=2.19,
        notes=(
            "Experimental, not default. Accessible on the operator's key but "
            "in the 2026-05-31 addendum (N=4) produced 0/4 valid JSON at "
            "max_tokens=4000 — the model emits chain-of-thought before any "
            "JSON and consumed the full output budget on reasoning. Not "
            "recommended for bulk structured-summary generation at sensible "
            "token budgets. Override via --include-experimental-models AND a "
            "much higher --max-tokens (>=12000)."
        ),
    ),
    "MiniMax-M2.7": ModelSpec(
        model_id="MiniMax-M2.7",
        provider="minimax",
        endpoint="https://api.minimax.io/v1/text/chatcompletion_v2",
        env_var="MINIMAX_API_KEY",
        default_role="fallback_only",
        pricing_in_usd_per_million=0.40,
        pricing_out_usd_per_million=1.60,
        notes=(
            "Experimental, not default. Accessible on the operator's key but "
            "in the 2026-05-31 addendum (N=4) did not beat MiniMax-M2: same "
            "JSON-validity rate, different failure shape (tends to overshoot "
            "the short-summary upper bound rather than M2's undershoots). "
            "Keep as experiment only until N>=10 evidence supports promotion."
        ),
    ),
}


# Hard-coded folders already summarised in Batches 001-003 (PRs #220, #221,
# #222). Excluded from benchmark sampling so the comparison runs only on
# articles still missing summary metadata. Update when later batches land.
BATCH_001_002_003_FOLDERS: frozenset[str] = frozenset({
    # Batch 001 (PR #220)
    "2026-05-24-claude-code-remote-control-dispatch-multi-device-guide-2026-v2",
    "2026-05-11-evaluate-mcp-servers-enterprise-workflows-2026",
    "2026-05-11-local-first-ai-stack-privacy-trade-offs-2026",
    "2026-05-11-map-data-flows-local-first-ai-assistant-2026",
    "2026-05-11-skills-memory-agent-harnesses-next-ai-layer-2026",
    # Batch 002 (PR #221)
    "2026-05-11-tune-maintainer-health-rubric-thresholds-dependency-tier-2026",
    "2026-05-10-30-day-pilot-open-source-ai-coding-agent-2026",
    "2026-05-10-automate-maintainer-health-rubric-ci-ai-tools-2026",
    "2026-05-10-github-stars-bad-procurement-metric-ai-tools-2026",
    "2026-05-10-kimi-2-6-ai-engineering-auditor-best-use-cases-2026",
    # Batch 003 (PR #222)
    "2026-05-10-maintainer-health-matters-more-than-github-stars-2026",
    "2026-05-10-open-source-ai-repos-european-engineering-teams-2026",
    "2026-05-10-open-source-ai-tool-security-checklist-european-scale-ups-2026",
    "2026-05-10-premium-reasoning-low-cost-ai-development-stack-2026",
    "2026-05-09-local-first-ai-assistants-enterprise-privacy-2026",
})


# Risk-bucket classification thresholds for the stratified sampler. Each
# bucket has a list of case-insensitive regex patterns; an article is
# assigned to whichever bucket has the highest hit-count above its
# minimum threshold. Ties broken by RISK_BUCKETS order (first wins).
RISK_BUCKETS: tuple[str, ...] = (
    "vendor_pricing",
    "legal_regulatory",
    "technical",
    "normal",
)


# Pattern lists are intentionally narrow so the classification stays
# inspectable in a code review. Re-tune after the first 12-article live run.
BUCKET_PATTERNS: dict[str, tuple[tuple[str, int], ...]] = {
    "vendor_pricing": (
        (r"\$[0-9]", 1),
        (r"per\s+million\s+tokens", 1),
        (r"\bpricing\b", 1),
        (r"\bMAU\b", 1),
        (r"\brevenue\b", 1),
        (r"\b(?:Anthropic|OpenAI|DeepSeek|MiniMax|Moonshot|NVIDIA|Cursor|Claude|GPT-?\d|Gemini)\b", 1),
    ),
    "legal_regulatory": (
        (r"\bGDPR\b", 1),
        (r"\bDORA\b", 1),
        (r"\bEU AI Act\b", 1),
        (r"\bArticle\s+\d+\b", 1),
        (r"\bconformity\b", 1),
        (r"\bliability\b", 1),
        (r"\bcopyright\b", 1),
    ),
    "technical": (
        (r"\bGitHub Actions\b", 1),
        (r"\bCI/CD\b", 1),
        (r"\bAPI\b", 1),
        (r"\bSBOM\b", 1),
        (r"\bSLSA\b", 1),
        (r"\bOpenSSF\b", 1),
        (r"\bRAG\b", 1),
    ),
    "normal": (
        # Catch-all bucket; the sampler assigns articles here when no other
        # bucket clears its threshold. The patterns below boost the score
        # for clearly editorial / leadership pieces.
        (r"\bengineering leader", 1),
        (r"\bCTO\b", 1),
        (r"\bplaybook\b", 1),
    ),
}


# Minimum hits required for an article to be assigned to a non-"normal"
# bucket. Articles that fail every minimum land in "normal".
BUCKET_MIN_HITS: dict[str, int] = {
    "vendor_pricing": 8,
    "legal_regulatory": 6,
    "technical": 8,
    "normal": 0,
}


@dataclass(frozen=True)
class ResolvedModelSet:
    """Result of resolving the operator's --models flag against the registry."""

    selected: tuple[ModelSpec, ...]
    experimental_requested: tuple[str, ...] = field(default_factory=tuple)


def resolve_models(
    requested_ids: list[str] | None,
    include_experimental: bool,
) -> ResolvedModelSet:
    """Resolve a list of model IDs against the registry.

    Args:
        requested_ids: Operator-provided list of model IDs, or None to use
            DEFAULT_MODELS in registration order.
        include_experimental: If False, requesting an experimental model by
            ID raises ValueError. If True, experimental models are allowed
            and their notes are surfaced in the report.

    Raises:
        ValueError: If any requested ID is unknown or is experimental but
            include_experimental is False.
    """
    if requested_ids is None:
        return ResolvedModelSet(selected=tuple(DEFAULT_MODELS.values()))

    selected: list[ModelSpec] = []
    experimental_used: list[str] = []
    for mid in requested_ids:
        mid = mid.strip()
        if not mid:
            continue
        if mid in DEFAULT_MODELS:
            selected.append(DEFAULT_MODELS[mid])
        elif mid in EXPERIMENTAL_MODELS:
            if not include_experimental:
                raise ValueError(
                    f"Model '{mid}' is experimental. Pass "
                    f"--include-experimental-models to opt in. See the "
                    f"docstring of provider_smoke_models.py for the "
                    f"evidence behind the default/experimental split."
                )
            selected.append(EXPERIMENTAL_MODELS[mid])
            experimental_used.append(mid)
        else:
            known = sorted(set(DEFAULT_MODELS) | set(EXPERIMENTAL_MODELS))
            raise ValueError(
                f"Unknown model '{mid}'. Known model IDs: {', '.join(known)}"
            )

    return ResolvedModelSet(
        selected=tuple(selected),
        experimental_requested=tuple(experimental_used),
    )
