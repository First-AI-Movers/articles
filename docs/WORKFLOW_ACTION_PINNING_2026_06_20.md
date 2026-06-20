# Workflow Action Pinning + Credential Hardening — Article Archive

**Created:** 2026-06-20 (ARTICLES-WORKFLOW-ACTION-PINNING-A) · **Lane:** Security
**Scope:** pins every non-local GitHub Action to a full commit SHA and disables checkout credential persistence — closing the supply-chain tag-retargeting risk flagged in [`INCIDENT_RESPONSE_RUNBOOK.md`](INCIDENT_RESPONSE_RUNBOOK.md) §7. Follows the agent-toolkit / PI-EU / Radar pinning pattern. **No publishing, Pages-deploy, ingestion/PR, scanner, required-check, ruleset, or secret change.**

## What changed

1. **Action pinning (59 refs → 0 unpinned).** Every non-local action pinned to a full commit SHA at its **current major** (no behavior upgrade), with a `# vX.Y.Z` comment:

   | Action | SHA | Tag |
   |---|---|---|
   | `actions/checkout` | `df4cb1c069e1874edd31b4311f1884172cec0e10` | v6.0.3 |
   | `actions/setup-python` | `a309ff8b426b58ec0e2a45f0f869d46889d02405` | v6.2.0 |
   | `actions/setup-node` | `48b55a011bda9f5d6aeb4c2d9c7362e8dae4041e` | v6.4.0 |
   | `actions/upload-artifact` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | v7.0.1 |
   | `actions/cache` | `27d5ce7f107fe9357f9df03efb73ab90386fccae` | v5.0.5 |
   | `actions/configure-pages` | `45bfe0192ca1faeb007ade9deae92b16b8254a0d` | v6.0.0 |
   | `actions/upload-pages-artifact` | `fc324d3547104276b827a68afc52ff2a11cc49c9` | v5.0.0 |
   | `actions/deploy-pages` | `cd2ce8fcbc39b97be8ca5fce6e763baed58fa128` | v5.0.0 |
   | `peter-evans/create-pull-request` | `5f6978faf089d4d20b00c7766989d076bb2fc7f1` | v8.1.1 |
   | `lycheeverse/lychee-action` | `8646ba30535128ac92d33dfc9133794bfdd9b411` | v2.8.0 |

   No local actions exist to (incorrectly) pin.
2. **Checkout credentials.** `persist-credentials: false` added to **all 22 `actions/checkout` steps**. Verified safe: **no workflow does `git push` / `git commit` / `git add`**; the PR-creating workflows (`ingest-airtable`, `ingest-article`, `ingest-airtable-dispatch`, `summary-auto-apply`, `build-embeddings`) authenticate `peter-evans/create-pull-request` via an **explicit `token:` input** (`ARTICLE_INGESTION_PR_TOKEN || GITHUB_TOKEN`), not the checkout's persisted credential; and the Pages deploy uses the `deploy-pages` OIDC action, not git. `fetch-depth` / `token` inputs on existing `with:` blocks are preserved.
3. **Permissions — unchanged.** Every workflow already declares per-workflow permissions, each justified and preserved: the PR-creators keep `contents: write` + `pull-requests: write`; `build-and-deploy` keeps `pages: write` + `id-token: write`; the rest keep their declared scopes. **Zero permission lines changed.**
4. **Artifacts — unchanged.** Upload paths are already scoped (`upload-pages-artifact` → `site/`; the others → specific report/metric paths); none upload the workspace, `.git/`, secrets, or raw provider logs.

## Safety

No live publish, no Pages-deploy semantics change (same OIDC deploy), no ingestion/PR-creation change (same `peter-evans` + token), no scanner change, no required-check or ruleset change, no secret read, no `pull_request_target`, no self-hosted PR job. Same action majors, same triggers/schedules → no behavior change. YAML validated for all workflows; `git diff --check` clean.

## Known advisory caveat (pre-existing, not from this PR)

The advisory **`check` (generated-artifacts drift)** job may be red on the **pre-existing date-stamp drift** documented in the IR mission (committed site artifacts embed the `2026-06-06` build date; a rebuild re-stamps to today). That job is **non-required** (required = `test` / `e2e` / `gitleaks`) and this PR changes only workflow YAML — it does not touch generated artifacts. A periodic artifact refresh is a separate maintenance task and is **not** bundled here.
