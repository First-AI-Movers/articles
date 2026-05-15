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
| **Require status checks to pass** | `check`, `e2e`, `geo-audit`, `gitleaks`, `lychee`, `readability`, `test`, `vale` | All eight required checks must pass before merge. The auto-merger uses this exact set (`tools/auto_merge_ingestion_pr.py` → `REQUIRED_CHECKS`). See "Required check inventory" below. |
| **Require approving review** | ❌ Disabled | Green CI is the merge gate. Manual reviews are encouraged but not required for trusted-owner automation. |
| **Require review from CODEOWNERS** | ❌ Disabled | CODEOWNERS is a documented ownership signal, not a hard merge blocker. |
| **Require linear history** | ✅ Enabled | Keeps history clean and bisectable. Use squash-merge or rebase-merge. |
| **Require signed commits** | Optional | Recommended if contributors use GPG/SSH signing. |
| **Include administrators** | ✅ Enabled | Rules apply to everyone, including repo admins. |
| **Restrict pushes that create files larger than 100 MiB** | ✅ Enabled | Prevents accidental large-file commits. |

## Required check inventory

The eight checks named above map to specific workflow jobs. Each is its own
workflow file so a failure pinpoints the cause quickly.

| Check name | Workflow file | What it gates |
|---|---|---|
| `test` | `.github/workflows/tests.yml` | Python unit tests (`pytest tools/tests`), changelog freshness on PRs, duplicate-title gate, errata validation. |
| `e2e` | `.github/workflows/e2e.yml` | Playwright browser tests against the freshly built static site. Skipped for docs-only PRs via `paths-ignore`. |
| `gitleaks` | `.github/workflows/gitleaks.yml` | Secret scanning across the full repo (no `paths-ignore` — secrets can land anywhere). |
| `check` | `.github/workflows/generated-artifacts.yml` | Runs `tools/check_generated_artifacts.py`: rebuild + diff against committed `index.json`, `sitemap.xml`, `feed.xml`, `feed.json`, `llms.txt`, `llms-full.txt`, `llms-recent.txt`, `README.md`, `ROADMAP.md`. |
| `geo-audit` | `.github/workflows/geo-audit.yml` | GEO score per article. Skipped for docs-only PRs. |
| `readability` | `.github/workflows/article-quality.yml` (job: `readability`) | Flesch / Flesch-Kincaid scoring. |
| `vale` | `.github/workflows/article-quality.yml` (job: `vale`) | Prose linting via Vale. Soft gate (`continue-on-error: true`). |
| `lychee` | `.github/workflows/article-quality.yml` (job: `lychee`) | Dead-link scanning. Soft gate. |

If you add or remove a required check, update **three** places in lockstep so
the auto-merger, the docs, and the GitHub Settings stay in sync:

1. `tools/auto_merge_ingestion_pr.py` → `REQUIRED_CHECKS`
2. This table (`docs/BRANCH_PROTECTION.md`)
3. **Settings → Branches → main → Required status checks** (manual; only an
   admin can change it)

The check `test_branch_protection_lists_all_required_checks` in
`tools/tests/test_workflows_ci_audit_followup.py` enforces (1) ↔ (2)
consistency. (3) is enforced manually.

## Forbidden actions

- **Force push** to `main` — disabled.
- **Delete `main`** — disabled.

## Verification

To verify current settings via GitHub CLI:

```bash
gh api repos/First-AI-Movers/articles/branches/main/protection
```

> Note: Only repository owners and admins can view or modify branch protection settings.
