# Generated-Artifact Drift Check — Stability Closeout (2026-06-22)

**Status:** observation window **closed — stable** · **Closes:** [GENERATED_ARTIFACT_DRIFT_REFRESH_2026_06_21.md](GENERATED_ARTIFACT_DRIFT_REFRESH_2026_06_21.md) (PR #266, merge `bbd73a63f`).

## Background

PR #266 (`ARTICLES-GENERATED-ARTIFACT-DRIFT-REFRESH-A`) removed a recurring **false failure** in the advisory `Generated artifacts` check (`generated-artifacts.yml` → `tools/check_generated_artifacts.py`): it compared committed artifacts byte-for-byte against a fresh `rebuild_local.py` regeneration, so a **build-date-only** change (no content change) registered as drift and failed docs/maintenance PRs. #266 **date-normalizes the four generation-timestamp fields** before comparing, leaving all other content compared byte-for-byte.

This note closes the observation window opened by that change.

## Observation window

**2026-06-21 (post-merge of #266) → 2026-06-22.**

| Signal | Result |
|---|---|
| `generated-artifacts` runs in the window | **50 / 50 success, 0 failures** |
| **False failures** (build-date-only drift failing a PR) | **0** |
| Distinct **non-dependabot** PR branches that ran the check (heavy / non-allowlisted path) | **5** — `docs/articles-ir-runbook-scann…`, `security/articles-workflow-sec…`, `security/articles-zizmor-advis…`, `security/articles-dependabot-r…`, `security/articles-dependabot-t…` — all **passed** |
| Real content drift still protected | **yes** (see below) |

The five non-dependabot branches are the meaningful signal: they ran the **full rebuild-and-compare** (not the safe-maintenance allowlist short-circuit) on real docs/security changes and did **not** false-fail.

## Real content drift remains protected

The fix normalized **only** the four generation-date fields; every other byte is still compared. This is locked by unit tests in `tools/tests/test_check_generated_artifacts.py`:

- `test_drift_exits_nonzero` — a real content change still **fails** the check;
- `test_report_lists_changed_artifact`, `test_missing_artifact_reported`, `test_new_artifact_reported` — content changes / missing / new artifacts are detected and reported;
- `test_no_drift_exits_zero` — a clean tree passes.

So the normalization closed the false-positive without weakening genuine drift detection.

## Conclusion

The date-normalized generated-artifact drift check is **stable**: zero false failures across 50 runs and 5 distinct heavy-path PRs since #266, with real content drift still caught. The observation window is **closed**.

## Safety

Docs-only closeout. `generated-artifacts.yml` remains **advisory / non-required**; no workflow, ruleset, required-check, settings, secret, billing, or deploy change. Public repo (`articles`) only.
