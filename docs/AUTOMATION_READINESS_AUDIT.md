# Automation Readiness Audit

**Status:** Planning artifact — no implementation, no workflow changes, no production behavior modified.  
**Date:** 2026-05-01  
**Scope:** Audit every automation surface in the First AI Movers article archive to identify gaps before final closeout.  
**Source of truth:** `docs/ROADMAP_CLOSEOUT_TRACKS.md` (merged PR #131).

---

## 1. Executive summary

The archive has **13 CI workflows**, **2 Dependabot ecosystems**, and **8 external-integration surfaces**. Most are healthy. Four critical gaps must be addressed before the archive can be frozen as a stable v1:

1. **Generated artifact drift** — `build-and-deploy.yml` no longer auto-commits derived files (`index.json`, `sitemap.xml`, feeds, LLMS corpus, `README.md`) after commit `14ba82b9`. These committed files can drift from the actual build output.
2. **IndexNow permanently dry-run** — The submission step in `build-and-deploy.yml` always uses `--dry-run`. There is no documented switch to live mode.
3. **Airtable ingestion permanently dry-run** — `INGEST_DRY_RUN` defaults to `1`. There is no controlled write-mode enablement procedure documented.
4. **CHANGELOG.md stale** — `build_changelog.py --check` reports the changelog is out of date.

Everything else is either `ready`, `ready but gated` (awaiting credentials/owner decisions), or `deferred` by design.

---

## 2. Classification legend

| Class | Meaning |
|---|---|
| `ready` | Runs automatically, no secrets missing, no owner decision pending. |
| `ready but gated` | Code and CI are complete; activation requires a secret, a repository variable, or an explicit owner decision. |
| `manual only` | Infrastructure shipped; no automation path exists. Requires human action. |
| `broken` | Fails in CI, has a logic error, or is known to produce incorrect output. |
| `deferred` | Intentionally not enabled for v1; documented as future work. |

---

## 3. Master audit table

| Surface | Files | Current state | Required secrets/vars | Trigger | Risk | Next action | Proof |
|---|---|---|---|---|---|---|---|
| **tests** | `.github/workflows/tests.yml` | ready | None | PR + push to `main` | Low | None | CI green on every PR |
| **E2E** | `.github/workflows/e2e.yml` | ready | None | PR + push + nightly cron | Low | None | CI green; 32 tests pass |
| **gitleaks** | `.github/workflows/gitleaks.yml`, `.gitleaks.toml` | ready | None | PR + push to `main` | Low | None | CI green; allowlist documented |
| **GEO audit** | `.github/workflows/geo-audit.yml`, `tools/geo_audit.py` | ready | None | PR + push + manual | Low | None | CI green; soft gate uploads artifacts |
| **Article quality** | `.github/workflows/article-quality.yml`, `tools/readability.py`, `.vale.ini`, `.lychee.toml` | ready | None | PR + push + weekly cron | Low | None | CI green; readability always runs, Vale/Lychee best-effort |
| **Build & deploy** | `.github/workflows/build-and-deploy.yml`, `tools/rebuild_local.py` | ready | `INDEXNOW_API_KEY_ARTICLES_FAIM` | Push to `main` (filtered paths) + manual | **Medium** | Fix generated-artifact drift (see Section 4) | Pages deploys; site builds |
| **IndexNow** | `tools/submit_indexnow.py` (called from build-and-deploy) | ready but gated | `INDEXNOW_API_KEY_ARTICLES_FAIM` | After every Pages deploy | Low | Owner approves live switch (remove `--dry-run`) | Dry-run returns 80 URLs |
| **External ingestion** | `.github/workflows/ingest-article.yml`, `tools/ingest_article.py` | ready | `ARTICLE_INGESTION_PR_TOKEN` (optional) | `repository_dispatch` + manual | Low | Sender token not yet configured; documented in `EXTERNAL_PUBLISHING.md` | Fixture payload tested in CI |
| **Airtable cron** | `.github/workflows/ingest-airtable.yml`, `tools/ingest_airtable.py` | ready but gated | `AIRTABLE_PAT`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_NAME`, `AIRTABLE_VIEW_NAME` (optional) | Daily cron + manual | Medium | Controlled write test before enabling `INGEST_DRY_RUN=0` | Dry-run clean (67/67 records) |
| **Airtable dispatch** | `.github/workflows/ingest-airtable-dispatch.yml` | ready but gated | Same as Airtable cron | `repository_dispatch` + manual | Medium | Same controlled write test as cron | Record ID validation works |
| **Embeddings** | `.github/workflows/build-embeddings.yml`, `tools/build_embeddings.py` | ready | None | Weekly cron + manual | Low | None | CI green; opens PR if parquet changes |
| **MCP server** | `.github/workflows/mcp-server.yml`, `mcp-server/` | ready but gated | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | PR (filtered paths) + push + manual | Low | Owner adds secrets + sets `MCP_DEPLOY_ENABLED=1` | Type check, tests, build green |
| **Ask endpoint** | `mcp-server/src/ask.ts` | ready but gated | Same as MCP server | Deployed with MCP Worker | Low | Same as MCP server | Local dev server works |
| **OG worker** | `og-worker/` | deferred | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | No CI workflow | Low | Worker scaffold shipped; no deployment automation | Tests exist; not wired to CI |
| **Zenodo / DOI** | `docs/ZENODO_RELEASE.md`, `tools/mint_dois.py`, `tools/check_citation.py` | manual only | `ZENODO_API_TOKEN`, `ZENODO_SANDBOX_API_TOKEN` | Manual release + manual minting | Low | Owner creates Zenodo release when ready | Citation check passes; release checklist documented |
| **Giscus comments** | `templates/partials/giscus.html.j2`, `tools/comments_config.json` | deferred | `repo_id`, `category_id` (in config) | No CI workflow | Low | Enable GitHub Discussions + install Giscus app + fill IDs | Scaffold renders safely when disabled |
| **Wayback snapshots** | `.github/workflows/wayback-snapshot.yml`, `tools/wayback_snapshot.py` | ready | None | Release published + manual | Low | None | Dry-run works; no release has triggered it yet |
| **Dependabot** | `.github/dependabot.yml` | ready | None | Weekly (Monday 09:00 Europe/Lisbon) | Low | None | Config valid; pip + github-actions ecosystems |

---

## 4. Detailed findings

### 4.1 Critical — generated artifact drift

**Finding:** Commit `14ba82b9` ("fix(workflows): avoid direct generated-artifact push to protected main") removed the "Commit regenerated artifacts if changed" step from `build-and-deploy.yml`. Permissions were changed from `contents: write` to `contents: read`.

**Impact:** The following files are committed to the repo but are NO LONGER auto-updated when `build-and-deploy.yml` runs:

| File | Gitignored? | Auto-updated before 14ba82b9? | Current risk |
|---|---|---|---|
| `index.json` | No | Yes | **Drift** — article count, dates, topics may become stale |
| `sitemap.xml` | No | Yes | **Drift** — URL count, lastmod dates may become stale |
| `feed.xml` | No | Yes | **Drift** — entries, dates may become stale |
| `feed.json` | No | **No** | **Drift** — was never in the auto-commit list |
| `llms-full.txt` | No | Yes | **Drift** — corpus size, stats may become stale |
| `llms-recent.txt` | No | Yes | **Drift** — window, article count may become stale |
| `llms.txt` | No | Yes | **Drift** — stats may become stale |
| `README.md` | No | Yes | **Drift** — badges, counts, dates may become stale |
| `citation_graph.json` | No | N/A | **Drift** — only updated by manual `build_citation_graph.py` |
| `embeddings.parquet` | No | N/A | **Drift** — only updated by `build-embeddings.yml` PR |

**Mitigation in place:** `build-and-deploy.yml` still builds the site and deploys `site/` to Pages. The **deployed site** is correct. The **committed repo files** may lag.

**Recommended fix (Track B — B4):**
1. Document the new "source vs. generated" policy explicitly: committed artifacts are maintained via manual/local rebuild + PR, not CI auto-commit.
2. Add a CI check (not auto-commit) that fails if `rebuild_local.py` would change any committed artifact. This makes drift visible without bypassing branch protection.
3. Include `feed.json` in the artifact policy.

### 4.2 Critical — IndexNow permanently dry-run

**Finding:** The `indexnow` job in `build-and-deploy.yml` always runs `python3 tools/submit_indexnow.py --dry-run`. There is no conditional to switch to live submission.

**Impact:** Search engines are not notified of new/deployed content automatically.

**Recommended fix (Track A — A5 or Track B):**
- Add a repository variable `INDEXNOW_LIVE=1` and gate the `--dry-run` flag behind it, or
- Remove `--dry-run` entirely (low risk — the tool has polite rate limiting and the key is already configured).

### 4.3 Critical — Airtable ingestion permanently dry-run

**Finding:** `INGEST_DRY_RUN` defaults to `1` in both `ingest-airtable.yml` and `ingest-airtable-dispatch.yml`. There is no documented "controlled single-record write test" procedure beyond a mention in `ROADMAP.md`.

**Impact:** Airtable ingestion is validated but never writes. Make.com is still the active ingestion path.

**Recommended fix (Track B — B6):**
- Document the exact write-mode enablement procedure in `docs/OPERATIONS.md`.
- Include a checklist: verify one record via `--write --record-id <id>` locally, then set `INGEST_DRY_RUN=0`, then observe one cron run, then run side-by-side for 1 week.

### 4.4 High — CHANGELOG.md stale

**Finding:** `python3 tools/build_changelog.py --check` reports `CHANGELOG.md would change`.

**Impact:** The changelog freshness check on PRs will fail until the changelog is updated. This is a required check on PRs (not on main push).

**Recommended fix (Track B — B3):**
- Run `python3 tools/build_changelog.py` locally, review the diff, open a PR to refresh `CHANGELOG.md`.

### 4.5 Medium — feed.json missing from artifact commit list (historical)

**Finding:** Even before `14ba82b9`, `feed.json` was not included in the auto-commit list in `build-and-deploy.yml`. The list only covered `feed.xml`.

**Impact:** `feed.json` may be stale relative to `feed.xml`.

**Recommended fix (Track B — B4):**
- Include `feed.json` in the generated artifact policy.

### 4.6 Medium — MCP server deploy silently skips

**Finding:** The deploy job in `mcp-server.yml` silently exits `0` when credentials are missing or `MCP_DEPLOY_ENABLED` is not set. This is safe but means the deploy step provides no signal that deployment is not happening.

**Impact:** An owner might believe MCP is deployed when it is not.

**Recommended fix (Track B — B6):**
- Document the deployment status clearly in `docs/MCP_SERVER.md`.
- Consider adding a non-blocking "deployment skipped" annotation in the workflow.

### 4.7 Low — OG worker has no CI workflow

**Finding:** `og-worker/` contains a Cloudflare Worker with tests, but there is no `.github/workflows/og-worker.yml`.

**Impact:** OG worker changes are not tested in CI.

**Recommended fix:** Deferred to v2. The OG worker is not a v1 blocker.

### 4.8 Low — Giscus comments fully manual

**Finding:** No automation exists to enable Giscus. It requires: enable GitHub Discussions → install Giscus app → obtain `repo_id` and `category_id` → fill `tools/comments_config.json`.

**Impact:** None for v1. Deferred by design.

### 4.9 Low — Zenodo release fully manual

**Finding:** There is no `.github/workflows/zenodo-release.yml`. The release checklist in `docs/ZENODO_RELEASE.md` is entirely manual.

**Impact:** None for v1. A manual release process is acceptable for an archive that releases infrequently.

### 4.10 Low — Wayback snapshot not triggered by any release yet

**Finding:** The Wayback snapshot workflow triggers on `release: published`. No release has been published yet.

**Impact:** None. The workflow is ready and will trigger correctly when the first release is created.

---

## 5. Secrets and variables inventory

| Secret / Variable | Used by | Status | Documented in |
|---|---|---|---|
| `GITHUB_TOKEN` | All workflows | ✅ Auto-provided | N/A |
| `INDEXNOW_API_KEY_ARTICLES_FAIM` | `build-and-deploy.yml`, `ingest-airtable.yml`, `ingest-airtable-dispatch.yml`, `ingest-article.yml` | ✅ Configured | `docs/OPERATIONS.md` |
| `AIRTABLE_PAT` | `ingest-airtable.yml`, `ingest-airtable-dispatch.yml` | ✅ Configured | `docs/OPERATIONS.md` |
| `AIRTABLE_BASE_ID` | `ingest-airtable.yml`, `ingest-airtable-dispatch.yml` | ✅ Configured | `docs/OPERATIONS.md` |
| `AIRTABLE_TABLE_NAME` | `ingest-airtable.yml`, `ingest-airtable-dispatch.yml` | ✅ Configured | `docs/OPERATIONS.md` |
| `AIRTABLE_VIEW_NAME` | `ingest-airtable.yml`, `ingest-airtable-dispatch.yml` | Optional | `docs/OPERATIONS.md` |
| `ARTICLE_INGESTION_PR_TOKEN` | `ingest-article.yml`, `ingest-airtable-dispatch.yml` | Optional | `docs/OPERATIONS.md`, `EXTERNAL_PUBLISHING.md` |
| `CLOUDFLARE_API_TOKEN` | `mcp-server.yml` | ❌ Not configured | `docs/MCP_SERVER.md` |
| `CLOUDFLARE_ACCOUNT_ID` | `mcp-server.yml` | ❌ Not configured | `docs/MCP_SERVER.md` |
| `ZENODO_API_TOKEN` | `tools/mint_dois.py` | ❌ Not configured | `docs/ZENODO_RELEASE.md` |
| `ZENODO_SANDBOX_API_TOKEN` | `tools/mint_dois.py` | ❌ Not configured | `docs/ZENODO_RELEASE.md` |
| `MCP_DEPLOY_ENABLED` | `mcp-server.yml` | ❌ Not set | `docs/MCP_SERVER.md` |
| `INGEST_DRY_RUN` | `ingest-airtable.yml`, `ingest-airtable-dispatch.yml` | ✅ Unset (safe default = dry-run) | `docs/OPERATIONS.md` |

**No secrets are committed to the repo.** `gitleaks` enforces this.

---

## 6. Minimum Track B follow-up PRs from this audit

| PR | Title | Scope | Why |
|---|---|---|---|
| **B3** | `docs(ops): refresh CHANGELOG.md and workflow consistency pass` | Refresh `CHANGELOG.md`, update `docs/OPERATIONS.md` to mention AI-QA workflow, verify all docs reference current workflow names | Changelog is stale; docs should reflect AI-QA approval |
| **B4** | `docs(ops): generated artifact policy + drift detection` | Add `docs/GENERATED_ARTIFACTS.md` documenting which files are committed vs. gitignored vs. CI-generated; add a non-blocking CI check that warns if `rebuild_local.py` would change committed artifacts; include `feed.json` | Close the drift gap identified in Section 4.1 |
| **B6** | `docs(ops): release/DOI/MCP/embeddings readiness matrix` | Consolidate gated items into one doc; document exact Airtable write-mode enablement procedure; document MCP deployment verification | Close the enablement-gap documentation |
| **B8** | `ci(sec): verify gitleaks coverage and secrets inventory` | Verify `.gitleaks.toml` covers all known secret patterns; confirm no secrets in history; document rotation schedule | Security hygiene before v1 freeze |

**Explicitly NOT recommended as PRs:**
- Do NOT add auto-commit back to `build-and-deploy.yml` — it bypasses branch protection.
- Do NOT switch IndexNow to live without owner approval.
- Do NOT enable Airtable write mode without a controlled test.
- Do NOT create an OG worker CI workflow — deferred to v2.
- Do NOT create a Zenodo release workflow — manual process is acceptable.

---

## 7. Collision prevention with Track A

This audit document and its follow-up PRs adhere to Track B ownership rules:

- **No translation files touched** — `articles/<slug>/article.{es,fr,de,nl,pt}.md`, `translations.json`, and `translations/reviews/` are untouched.
- **No article content edited** — No `article.md` or `metadata.json` changes.
- **No `ROADMAP.md` edited** — PR #130 already aligned E39 wording.
- **No DeepL calls made** — This is a read-only audit.
- **No workflow behavior changed** — Findings are documented; fixes are proposed as separate PRs.
- **No generated artifacts modified** — Only read to verify state.

Track A may proceed with E39c Batch 2–4 in parallel with B3/B4/B6/B8.

---

## 8. E39c safe defaults (for Track A reference)

Per `docs/ROADMAP_CLOSEOUT_TRACKS.md` owner decisions, the fastest safe defaults for E39c continuation are:

| Decision | Default |
|---|---|
| Scope | Top-20 only (18 remaining articles) |
| Canonical strategy | Option B (English = `noindex` + external canonical; translations = `index` + self-canonical) |
| Approval method | AI-QA (`check_translation_quality.py`) — strict mode |
| DeepL quota | Pause until next month if Free tier exhausted |
| Human/native-language review | Not required for E39c rollout |

---

## 9. Validation

Run these before merging the PR that adds this document:

```bash
# Translation validators
python3 tools/check_translations.py
python3 tools/check_translation_quality.py

# Tag normalization (may take time)
python3 tools/normalize_tags.py --dry-run

# Citation graph current
python3 tools/build_citation_graph.py --check

# Only the new audit doc should appear
git diff -- docs/AUTOMATION_READINESS_AUDIT.md
git status --short
```

**Expected results:**
- `check_translations.py`: `OK: 2 file(s), 10 entries, 0 errors`
- `check_translation_quality.py`: `checked=10 passed=10 warnings=3 errors=0`
- `git status --short`: `?? docs/AUTOMATION_READINESS_AUDIT.md` only

---

## 10. Evidence summary

| Claim | Evidence | Location |
|---|---|---|
| 13 workflows exist | Repo-grounded | `.github/workflows/*.yml` |
| Generated artifact commit removed | Commit diff | `14ba82b9` — `build-and-deploy.yml` `-14` lines removing commit step |
| `feed.json` never auto-committed | Historical code review | Pre-`14ba82b9` `build-and-deploy.yml` commit list |
| IndexNow dry-run | Code-reviewed | `.github/workflows/build-and-deploy.yml` line 80 |
| Airtable dry-run gated | Code-reviewed | `.github/workflows/ingest-airtable.yml` line 13 |
| MCP deploy gated | Code-reviewed | `.github/workflows/mcp-server.yml` lines 92–99 |
| Changelog stale | Tool output | `python3 tools/build_changelog.py --check` → "would change" |
| All CI green on main | CI logs | `gh run list --branch main` — all `conclusion: success` |
| No secrets committed | CI proven | `gitleaks` workflow green on every PR/push |
| Dependabot active | Config file | `.github/dependabot.yml` |
