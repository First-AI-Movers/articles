# Zizmor Advisory Rollout — Articles

Advisory GitHub Actions workflow-security scan (`ARTICLES-ZIZMOR-SCOPED-ADVISORY-A`), the
workflow-security layer of the org scanner stack, propagated from agent-toolkit /
public-innovation-eu (#180) / radar.engine (#474). **Evidence only — advisory / non-required;
no promotion, no required-gate proposal, no ruleset change is made or recommended here.** No
secret values or raw payloads appear in this report.

## What landed
- **`.github/workflows/zizmor-advisory.yml`** — `pull_request` (path-scoped to `.github/workflows/**` + `.github/zizmor.yml`) + `workflow_dispatch`; `contents: read`; concurrency-guarded; `actions/checkout@v6` / `setup-python@v6` / `upload-artifact@v7` (Articles' governed `@vN` pins — **not** SHA); `persist-credentials: false`. Installs **`zizmor==1.25.2`** from PyPI, runs **`--offline`** (no token, no online audits, no Docker). Findings are advisory (exit 0); a tool/exec failure (no JSON report) exits non-zero so a broken pilot is visible — the job is non-required, so a red run still never blocks a merge.
- **`.github/zizmor.yml`** — sets `unpinned-uses` to **`ref-pin`** so zizmor accepts Articles' governed major-version tag pins instead of demanding hash pins (see below). Every other audit stays active.

## Why a scoped config (the `@vN` governance question)
Articles **governs** action pinning by **major-version tag** (`@v4`/`@v5`/`@v6`…), Dependabot-managed, per `SECURITY.md` §"Dependencies" and the workflow-pin tests in `tools/tests/`. That is a deliberate, test-enforced policy. zizmor's `unpinned-uses` audit defaults to requiring **hash** pins, so it flagged **68** `@vN` pins as High — which would bury the real signal and conflict with the documented policy. **We did not convert any action to a SHA pin.** Instead `.github/zizmor.yml` sets `unpinned-uses → ref-pin` (tag/ref pins are policy here), aligning zizmor with Articles' convention. If Articles ever adopts SHA pins, tighten the pattern to `hash-pin`.

## First-run results + classification ledger (2026-06-22, local dogfood, `--offline`)
Baseline (no config): **87 surfaced** — `unpinned-uses` 68, `template-injection` 9, `excessive-permissions` 5, `dependabot-cooldown` 3, `artipacked` 2.
**With `.github/zizmor.yml`: 19 surfaced** (0 informational-only delta) — `unpinned-uses` cleared to **0**; the genuine workflow-security signal remains.

| Finding | Count | Severity | Where | Disposition |
|---|---:|---|---|---|
| `unpinned-uses` | 68 → **0** | High | all workflows (`@vN` tags) | **ACCEPTED — governed policy.** Articles pins actions by `@vN` major tag + Dependabot (SECURITY.md). `ref-pin` policy in `.github/zizmor.yml`. Not converted to SHA. |
| `template-injection` | 9 | High ×7, Info ×2 | `ingest-airtable-dispatch.yml` ×4, `wayback-snapshot.yml` ×3, `e2e.yml` ×1, `generated-artifacts.yml` ×1 | **FOLLOW-UP (advisory; not fixed here).** Pre-existing `${{ … }}` interpolation in `run:` blocks. Each needs per-finding triage (trusted-context vs real); the fix is the `env:`-mapping pattern. Across 4 workflows = beyond this scanner-add scope. |
| `excessive-permissions` | 5 | High | `build-and-deploy.yml` ×2, cookiecutter template `build-and-deploy.yml` ×3 | **FOLLOW-UP.** Add explicit minimal job-level `permissions:`. The cookiecutter ones are in a **generated-repo template** (lower priority — they harden archives created from it). |
| `dependabot-cooldown` | 3 | Medium | `.github/dependabot.yml` | **FOLLOW-UP (low).** Add a `cooldown:` to the 3 ecosystems (zizmor default expects ≥7 days). Touching `dependabot.yml` while many Dependabot PRs are open is best done deliberately. |
| `artipacked` | 2 | Medium | cookiecutter template `build-and-deploy.yml` + `tests.yml` | **FOLLOW-UP.** `persist-credentials: false` on the template's checkouts (generated-repo hardening). |

**0 findings introduced by this PR.** All 19 are pre-existing Articles workflow hardening opportunities; this PR only *adds the scanner* + accepts the governed `@vN` policy.

## Recommended follow-up (separate)
**`ARTICLES-WORKFLOW-SECURITY-HARDENING-A`** — work the 19 advisory findings: `template-injection` (env-mapping pattern, the proven fix from radar.engine #477), `excessive-permissions` (explicit minimal `permissions:`), `dependabot-cooldown` (cooldown block), `artipacked` (template `persist-credentials: false`). A focused hardening pass, kept out of this scanner-add PR (and out of any "broad workflow refactor").

## Promotion decision
- Runs observed: 1 (local dogfood) + CI runs to accrue. · Findings introduced: **0**. · Accepted-by-policy: 68 `unpinned-uses`. · Open hardening follow-ups: 19.
- **Verdict: KEEP_ADVISORY_MORE_DATA_NEEDED.** Advisory/non-required; folds into the cross-repo scanner evidence-window ledger. Promotion is a separate governed decision.

## Safety
No required-check / ruleset change · no `pull_request_target` · GitHub-hosted only · no SARIF / `security-events` / GHAS dependency · no Docker · no secrets/tokens · `--offline` (no network) · advisory/classify-only (no auto-remediation) · **no action converted from `@vN` to SHA** (governed policy preserved).
