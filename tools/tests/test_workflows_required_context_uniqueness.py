"""Guard: each branch-protection required status-check context has exactly ONE producer.

GitHub warns that "using the same job name in multiple workflows can cause
ambiguous status check results and block pull requests from being merged."
When two jobs across two workflows resolve to the same check-run context name,
a required-context gate can be satisfied by whichever check reports last — a
red producer can be masked by a green same-named producer (false green on a
required check).

`e2e.yml` was already consolidated to a single `e2e` producer for exactly this
reason (see its header). This guard extends the same invariant to every
branch-protection required context so the `test` collision that this test was
added to fix (mcp-server.yml's Node `test` job vs tests.yml's pytest `test`
job) cannot regress or recur for `test`, `e2e`, or `gitleaks`.

The set of required contexts is authoritative in branch protection:
`gh api repos/First-AI-Movers/articles/branches/main/protection` →
required_status_checks.contexts == ["test", "e2e", "gitleaks"].
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

# Branch-protection required status-check contexts (see module docstring).
REQUIRED_CONTEXTS = {"test", "e2e", "gitleaks"}


def _context_producers() -> dict[str, list[str]]:
    """Map each check-context name → list of "<workflow>:<job-id>" that produce it.

    A job's reported check-context is its `name:` if set, else its job id.
    Matrix/expression names are out of scope for this repo (none of the
    required-context producers use them); a job whose `name` is a non-string
    (e.g. a matrix expression) is keyed by its job id defensively.
    """
    producers: dict[str, list[str]] = {}
    for wf_path in sorted(WORKFLOWS.glob("*.yml")):
        data = yaml.safe_load(wf_path.read_text(encoding="utf-8")) or {}
        jobs = data.get("jobs") or {}
        for job_id, job in jobs.items():
            job = job or {}
            name = job.get("name")
            context = name if isinstance(name, str) else job_id
            producers.setdefault(context, []).append(f"{wf_path.name}:{job_id}")
    return producers


def test_required_contexts_have_single_producer():
    producers = _context_producers()
    offenders = {
        ctx: producers.get(ctx, [])
        for ctx in sorted(REQUIRED_CONTEXTS)
        if len(producers.get(ctx, [])) != 1
    }
    assert not offenders, (
        "Every branch-protection required status-check context must be produced "
        "by exactly one job across all workflows, else the required gate is "
        f"ambiguous (GitHub picks the last reporter). Offenders: {offenders}. "
        "Rename the colliding job (mirror og-worker.yml's `og-worker` job id) so "
        "each required context has a single producer."
    )
