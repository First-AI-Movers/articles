# Branch Protection Expectations

This document describes the intended branch protection rules for `main`. Repository owners should configure these in **Settings → Branches**.

## Rationale

This repository uses an **automation-friendly owner/operator workflow**:

- AI/operator opens a PR.
- Required status checks run automatically.
- If checks are green, the operator can merge without waiting for a manual approval.
- Manual reviews are encouraged for risky or architectural changes, but they are not a hard blocker for every trusted-owner PR because the same operator often creates and merges the PR.

This model prioritises velocity while keeping `main` safe from direct pushes, force pushes, deletions, and broken CI.

## Required rules

| Rule | Setting | Rationale |
|---|---|---|
| **Require a pull request before merging** | ✅ Enabled | No direct pushes to `main`. All changes must go through a PR so checks run. |
| **Require status checks to pass** | `test`, `e2e`, `gitleaks`, `check` | The four **universal** checks — they report on every PR class (docs-only, workflow-only, Dependabot, ingestion, worker), so requiring them never deadlocks a PR. The four path-conditional checks (`geo-audit`, `readability`, `vale`, `lychee`) are intentionally NOT branch-protection required — see "Required check inventory" below. |
| **Require approving review** | ❌ Disabled | Green CI is the merge gate. Manual reviews are encouraged but not required for trusted-owner automation. |
| **Require review from CODEOWNERS** | ❌ Disabled | CODEOWNERS is a documented ownership signal, not a hard merge blocker. |
| **Require linear history** | ✅ Enabled | Keeps history clean and bisectable. Use squash-merge or rebase-merge. |
| **Require signed commits** | Optional | Recommended if contributors use GPG/SSH signing. |
| **Include administrators** | ✅ Enabled | Rules apply to everyone, including repo admins. |
| **Restrict pushes that create files larger than 100 MiB** | ✅ Enabled | Prevents accidental large-file commits. |

## Required check inventory

There are **two tiers**:

- **Branch-protection required** — the four *universal* checks that report on
  **every** PR class (docs-only, workflow-only, Dependabot, ingestion, worker).
  These are enforced by `main` branch protection. A required context that is
  *absent* for a PR class blocks that class forever, so only universal checks
  may live here.
- **Auto-merger additional** — four more checks that are path-conditional
  (`paths-ignore: [ROADMAP.md, docs/**]`), so they are absent on docs-only PRs
  and therefore CANNOT be branch-protection required. The ingestion auto-merger
  (`tools/auto_merge_ingestion_pr.py` → `REQUIRED_CHECKS`) additionally waits for
  all eight, which is safe because every ingestion PR touches `articles/` and so
  triggers all eight.

Each check is its own workflow file so a failure pinpoints the cause quickly.

| Check name | Tier | Workflow file | What it gates |
|---|---|---|---|
| `test` | branch-protection required | `.github/workflows/tests.yml` | Python unit tests (`pytest tools/tests`), changelog freshness on PRs, duplicate-title gate, errata validation. Runs on every PR. |
| `e2e` | branch-protection required | `.github/workflows/e2e.yml` | Playwright browser tests against the freshly built static site. Single-workflow design (N6-H): the `e2e` job always reports — on pure-docs PRs it skips the Playwright run internally but still reports SUCCESS. |
| `gitleaks` | branch-protection required | `.github/workflows/gitleaks.yml` | Secret scanning across the full repo (no `paths-ignore` — secrets can land anywhere). |
| `check` | branch-protection required | `.github/workflows/generated-artifacts.yml` | Runs `tools/check_generated_artifacts.py`: rebuild + diff against committed `index.json`, `sitemap.xml`, `feed.xml`, `feed.json`, `llms.txt`, `llms-full.txt`, `llms-recent.txt`, `README.md`. The `check` job runs on every PR (heavy drift check, or a no-op skip step for the safe-maintenance allowlist) and always reports. |
| `geo-audit` | auto-merger additional | `.github/workflows/geo-audit.yml` | GEO score per article. `paths-ignore: [ROADMAP.md, docs/**]` — absent on docs-only PRs, so NOT branch-protection required. |
| `readability` | auto-merger additional | `.github/workflows/article-quality.yml` (job: `readability`) | Flesch / Flesch-Kincaid scoring. Path-conditional (`paths-ignore`), so NOT branch-protection required. |
| `vale` | auto-merger additional | `.github/workflows/article-quality.yml` (job: `vale`) | Prose linting via Vale. Soft gate (`continue-on-error: true`) + path-conditional. |
| `lychee` | auto-merger additional | `.github/workflows/article-quality.yml` (job: `lychee`) | Dead-link scanning. Soft gate + path-conditional. |

If you add or remove a check, keep these in sync:

1. `tools/auto_merge_ingestion_pr.py` → `REQUIRED_CHECKS` — all eight (the
   ingestion-PR wait-set).
2. This document (both tables above).
3. **Settings → Branches → main → Required status checks** — the four
   *universal* checks only (`test`, `e2e`, `gitleaks`, `check`). Never add a
   path-conditional check here; it would deadlock the PR classes that skip it.
   (Manual; only an admin can change it.)

The check `test_branch_protection_lists_all_required_checks` in
`tools/tests/test_workflows_ci_audit_followup.py` asserts (2) lists every name
in (1). (3) is enforced manually.

## Forbidden actions

- **Force push** to `main` — disabled.
- **Delete `main`** — disabled.

## Verification

To verify current settings via GitHub CLI:

```bash
gh api repos/First-AI-Movers/articles/branches/main/protection
```

> Note: Only repository owners and admins can view or modify branch protection settings.
