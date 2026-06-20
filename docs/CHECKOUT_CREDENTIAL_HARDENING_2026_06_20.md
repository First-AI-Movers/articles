# Checkout Credential Hardening + Action-Pinning Decision — Article Archive

**Created:** 2026-06-20 (ARTICLES-WORKFLOW-ACTION-PINNING-A) · **Lane:** Security
**Scope:** disables checkout credential persistence across all workflows (the non-conflicting half of the workflow-hardening mission), and **records why SHA action-pinning was NOT applied** — it conflicts with this repo's deliberate, test-enforced major-tag pinning convention.

## What landed

**`persist-credentials: false` on all 22 `actions/checkout` steps.** This stops the `GITHUB_TOKEN` (or a passed PAT) from being persisted into `.git/config`, where a later step or compromised action could read it. Verified safe:

- **No workflow does `git push` / `git commit` / `git add`** — none relies on the persisted credential.
- The PR-creating workflows (`ingest-airtable`, `ingest-article`, `ingest-airtable-dispatch`, `summary-auto-apply`, `build-embeddings`) authenticate `peter-evans/create-pull-request` via an **explicit `token:` input** (`ARTICLE_INGESTION_PR_TOKEN || GITHUB_TOKEN`), not the checkout credential.
- The Pages deploy uses the `deploy-pages` **OIDC** action, not git.
- Existing `with:` inputs (`fetch-depth`, `token`) are preserved.

The repo's own workflow-structure tests (`tools/tests/test_workflows_summary_{apply,monitor,smoke}.py`) pass with this change (74 passed).

## Why SHA action-pinning was NOT applied (decision: deferred to operator)

The mission's primary ask was to pin actions to full commit SHAs. **This repo has a deliberate, documented, test-enforced convention to pin actions to MAJOR TAGS (`@vN`) instead**, and SHA-pinning conflicts with it:

- **`SECURITY.md` §Dependency and supply-chain security:** *"GitHub Actions use pinned major versions (`@v4`, `@v5`)."* — the documented policy is major-tag pinning.
- **`.github/dependabot.yml`** runs the `github-actions` ecosystem weekly — the repo relies on **Dependabot** to bump action major tags. SHA-pinning would suppress those updates (Dependabot can update SHA pins but the repo's model + tests are built around `@vN`).
- **`tools/tests/test_workflows_summary_{apply,monitor,smoke}.py::test_action_pins*`** are **CI gates** that assert every workflow pins `actions/checkout@v6`, `actions/setup-python@v6`, `peter-evans/create-pull-request@v8`, etc. SHA pins fail them (7 failures observed).
- **`docs/SECURITY_SECRETS_REVIEW.md`:** the supply-chain posture is recorded as "@vN + Dependabot, VERIFIED."

Forcing SHA pins would require rewriting the documented policy, removing/rewriting three test files, and reconfiguring Dependabot — a **governance tradeoff (SHA immutability vs. Dependabot-managed major-tag updates)** that this repo has already decided. That decision is the operator's to revisit, not a unilateral autopilot change, so the SHA-pinning sub-goal is **HALTED and surfaced** rather than forced.

**Recommended operator decision (a separate governed mission if pursued):** either (a) keep `@vN` + Dependabot (accept tag-retargeting risk is mitigated by the consistency tests + Dependabot review) — the status quo; or (b) move to SHA pins **and** update `SECURITY.md`, the `test_action_pins*` tests, and the Dependabot config together. Until then, `@vN` is preserved.

## Safety

No publishing, Pages-deploy, ingestion/PR, scanner, required-check, ruleset, or secret change. Action version refs are unchanged (`@vN` preserved per repo policy). YAML valid; the repo's workflow-structure tests pass.
