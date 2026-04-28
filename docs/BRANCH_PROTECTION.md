# Branch Protection Expectations

This document describes the intended branch protection rules for `main`. Repository owners should configure these in **Settings → Branches**.

## Required rules

| Rule | Setting | Rationale |
|---|---|---|
| **Require a pull request before merging** | ✅ Enabled | No direct pushes to `main`. All changes must be reviewed. |
| **Require status checks to pass** | `test`, `e2e`, `gitleaks` | Python tests, browser E2E, and secret scanning must all pass. |
| **Require review from CODEOWNERS** | ✅ Enabled | Owner approval is required for `/articles/`, `/tools/`, `/templates/`, `/static/`, `/.github/`, and package files. |
| **Require linear history** | ✅ Enabled | Keeps history clean and bisectable. Use squash-merge or rebase-merge. |
| **Require signed commits** | Optional | Recommended if contributors use GPG/SSH signing. |
| **Include administrators** | ✅ Enabled | Rules apply to everyone, including repo admins. |
| **Restrict pushes that create files larger than 100 MiB** | ✅ Enabled | Prevents accidental large-file commits. |

## Forbidden actions

- **Force push** to `main` — disabled.
- **Delete `main`** — disabled.

## Verification

To verify current settings via GitHub CLI:

```bash
gh api repos/First-AI-Movers/articles/branches/main/protection
```

> Note: Only repository owners and admins can view or modify branch protection settings.
