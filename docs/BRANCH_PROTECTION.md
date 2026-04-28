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
| **Require status checks to pass** | `test`, `e2e`, `gitleaks` | Python tests, browser E2E, and secret scanning must all pass. |
| **Require approving review** | ❌ Disabled | Green CI is the merge gate. Manual reviews are encouraged but not required for trusted-owner automation. |
| **Require review from CODEOWNERS** | ❌ Disabled | CODEOWNERS is a documented ownership signal, not a hard merge blocker. |
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
