# Autonomous Airtable Publishing Plan

Post-v1 plan for unblocking daily Airtable-to-PR automation safely. This document
covers the staged rollout of Airtable write mode, optional Anthropic-based
polish, and gated auto-merge. Each stage is its own PR; nothing here is
activated until the prior stage has shipped and been observed.

**Status:** E41a status-mapping fix landed in this PR; nothing else is enabled.

## Current Airtable configuration (verified)

| Item | Value | Source of truth |
|---|---|---|
| Base name | `Pubs` | Airtable workspace |
| Base ID | `apphbuWvlyV6KM4Hr` | Airtable API (read-only verification) |
| Table name | `beehiiv` | Airtable base |
| Table ID | `tbluKwm5UcUhRmyNq` | Airtable base |
| View | _none required_ | `ROADMAP.md` line 233 |
| Required schema fields | `Title`, `slug`, `Pub Date`, `GUID`, `Content HTML` | All present in the table |
| Editorial status field | `FAIM Status` (singleSelect) | Live values: `Ready`, `Posted` |
| Cron schedule | `17 6 * * *` | `.github/workflows/ingest-airtable.yml` |
| Push trigger | `repository_dispatch` `airtable-record-updated` | `.github/workflows/ingest-airtable-dispatch.yml` |

The original E20a scaffold mapped `"status" → "Status"`. The live Pubs/beehiiv
table has no literal `Status` field, so write mode would have skipped every
record with `[SKIP] no Status field`. E41a remapped `"status" → "FAIM Status"`.

E41b corrected the lifecycle interpretation: archive ingestion gates on
`FAIM Status = Posted`. `Posted` means the article is already live upstream
(canonical URL resolves; post-publication edits unlikely), which is the only
state where mirroring into the canonical archive is safe. `Ready` means the
record is prepared for upstream publication but NOT yet posted — its canonical
URL may not yet resolve, so the archive must not mirror it.

`ALLOWED_STATUSES` is therefore `{"posted"}` (case-insensitive). The script
also lowercases the value when writing `metadata.json`, so newly-ingested
records carry `"status": "posted"`, matching the convention used by the
existing 829 archive records (which all carry lowercase `"published"`).

## Doppler / GitHub secret-sync recommendation

**Recommendation:** Use Doppler's first-party GitHub Actions integration to
sync project `articles-git`, config `dev` into GitHub repository secrets.

- The existing workflows reference `${{ secrets.AIRTABLE_PAT }}` etc.
  Doppler-managed sync keeps that contract unchanged.
- No Doppler CLI step in CI. No new dependencies.
- Single source of truth in Doppler; rotation propagates automatically.
- GitHub Actions still consumes plain encrypted secrets — no token
  exfiltration surface beyond Doppler's existing sync.

**Required Doppler values (project `articles-git`, config `dev`):**

| Key | Value | Notes |
|---|---|---|
| `AIRTABLE_PAT` | _secret_ | Personal Access Token; read-only scope to base `apphbuWvlyV6KM4Hr` |
| `AIRTABLE_BASE_ID` | `apphbuWvlyV6KM4Hr` | Pubs base |
| `AIRTABLE_TABLE_NAME` | `tbluKwm5UcUhRmyNq` | Use the table ID rather than the name `beehiiv` for rename resilience |
| `AIRTABLE_VIEW_NAME` | _unset_ | View not required; cron's `--since-hours 72` plus folder dedupe is the gate |
| `INDEXNOW_API_KEY_ARTICLES_FAIM` | _existing_ | Used by `tools/submit_indexnow.py` and `rebuild_local.py` |
| `DEEPL_API_KEY` | _existing_ | Translation pipeline |

**Do not put** in Doppler/GitHub yet:

- `ANTHROPIC_API_KEY` — defer until E41c.
- Any auto-merge token — defer until E41f.

**Operational rules:**

1. Never print the PAT or any token in CI logs, PR descriptions, or comments.
2. Do not commit `.env` files at any layer.
3. Rotation cadence: rotate `AIRTABLE_PAT` immediately if the base sharing
   surface changes; otherwise on a 90-day schedule.
4. Doppler audit log is the authoritative record of secret access.

## Write-mode rollout stages

| Stage | What ships | Gate | Status |
|---|---|---|---|
| E41a | Status mapping fix (`Status` → `FAIM Status`); tests; this plan | None — code-only | ✅ shipped (PR #147) |
| E41a' | Posted-only gate correction; cron token-fallback | Code-only | ✅ shipped (PR #148) |
| E41a'' | rebuild_local funnel-None coercion | Code-only | ✅ shipped (PR #149) |
| E41a''' | update_docs.py runs before pytest in both ingestion workflows | Workflow-only | ✅ shipped (PR #150) |
| E41a'''' | ROADMAP.md added to ingestion add-paths | Workflow-only | ✅ shipped (PR #153) |
| E41b | Controlled single-record write test (one Posted record, dispatch path) | Owner approval; `INGEST_DRY_RUN=0` transient | ✅ proven 2026-05-03: PR #154 ingested `rec6nsPU1kHTcKYXF` end-to-end with machine gates |
| E41e | Bounded daily cron write mode + incident logging | Repo variables flip after PR merge | ✅ shipping (this PR) |
| E41g | List-fetch sort by `Date Added` desc (newest-first) | Code-only; issue #164 root cause | ✅ shipped (PR #166) |
| E41f | Gated auto-merge for `ingest/airtable-*` branches | Required CI green; default OFF via `AUTO_MERGE_INGESTION_PRS` | 🚧 this PR (code shipped, activation gated) |
| E41c | Anthropic polish design (provider, prompt contract, dry-run plan) | Owner approval; ADR | ❌ no |
| E41d | Anthropic polish dry-run implementation behind feature flag | Provider gated; opt-in env var; no live calls in CI | ❌ no |

Nothing in this plan changes the workflow's "PR-only, never push to main"
contract. `peter-evans/create-pull-request` remains the single integration
point for both `ingest-airtable.yml` and `ingest-airtable-dispatch.yml`.

## E41e — bounded daily cron write mode (active)

The cron at `17 6 * * *` UTC scans Airtable for `FAIM Status = Posted`
records modified in the last 72 h, runs the same pipeline that E41b
proved (ingest → normalize tags → dedupe-title → rebuild → patch
ROADMAP marker → pytest → PR), and opens an `ingest/airtable-articles`
branch. The PR is **not** auto-merged — that's E41f.

### Production safety bounds

The cron is gated by three repo variables. Defaults in the workflow YAML
are conservative; tune via `gh variable set` once steady-state is observed.

| Variable | Default | Purpose |
|---|---|---|
| `INGEST_DRY_RUN` | `1` (workflow fallback) | Master kill switch. Set to `0` to enable write-mode. Set back to `1` to instantly stop creating PRs. |
| `INGEST_MAX_RECORDS` | `20` | Caps how many records the script PAGES from Airtable in one run. |
| `INGEST_MAX_CREATED` | `5` | Caps how many article folders the script actually CREATES per run. Skips and dedupes don't count. |

**Activation procedure (after this PR merges):**

```bash
gh variable set INGEST_DRY_RUN     --body 0  -R First-AI-Movers/articles
gh variable set INGEST_MAX_RECORDS --body 20 -R First-AI-Movers/articles
gh variable set INGEST_MAX_CREATED --body 5  -R First-AI-Movers/articles
```

**Kill switch (revert to dry-run):**

```bash
gh variable set INGEST_DRY_RUN --body 1 -R First-AI-Movers/articles
```

The next cron tick reads the variable; no workflow restart needed.

### Incident logging

If a write-mode cron run fails (any step exits non-zero), a final step
in the job opens a GitHub issue titled
`E41 cron ingestion incident: workflow run <id> failed`, including:

- workflow run URL
- commit SHA
- ref
- INGEST_DRY_RUN / INGEST_MAX_RECORDS / INGEST_MAX_CREATED state
- trigger event

The step uses `${{ secrets.ARTICLE_INGESTION_PR_TOKEN || secrets.GITHUB_TOKEN }}`
and never echoes secret values. The step is skipped on dry-run runs and
on success — only writes-that-fail are logged.

### Duplicate detection (E41e' — issue #156 fix)

The first E41e cron run (workflow run 25312661954) admitted a record
whose archive twin existed under a Make.com-truncated folder name with
slightly different title typography (em-dash vs ASCII hyphen). pytest
caught it before PR creation, the new incident-issue step opened
[#156](https://github.com/First-AI-Movers/articles/issues/156)
automatically, and the kill switch was activated.

The fix (PR after #155) strengthens ingest-time duplicate detection:

- `_normalize_title()` — Unicode NFKC, dash/quote variants → ASCII,
  whitespace collapse, casefold. Used by `_title_exists()`.
- `_normalize_canonical_url()` — strip + lowercase scheme/host + strip
  trailing slash. Used by new `_canonical_url_exists()` defense-in-
  depth check, which catches duplicates even when title drifted beyond
  what title normalization can recover.
- `_write_article()` evaluates folder, title, and canonical URL gates
  in that order; any match ⇒ silent idempotent skip.

The standalone `tools/check_duplicate_titles.py` and the index-level
test stay on `.lower()` to avoid surfacing legacy smart-quote pairs as
hard CI failures; that cleanup is editorial-scope follow-up.

### List-fetch ordering (E41g — issue #164)

The 2026-05-05 cron and 2026-05-06 manual dispatch both observed the
same 20 already-archived records (`rec01miXg…rec1gSdd`) skipped as
duplicates, with `Ingested 0 article(s)`. Root cause:
`tools/ingest_airtable.py::_fetch_records` sent no `sort=` parameter,
so Airtable returned records in default order — by record ID, lexically
ascending — which is by construction the oldest cohort of records.
With `INGEST_MAX_RECORDS=20`, the entire scan budget was consumed on
records that already existed in the archive; new Posted records with
lexically-larger IDs were never seen.

E41g pins the list path to:

```text
sort[0][field]=Date Added
sort[0][direction]=desc
```

This is the field that records when an article record *entered*
Airtable, which is the right ordering signal for archive ingestion.
Modification time is not used because re-saves of long-archived
records would otherwise float to the top. Pub Date is not used because
it tracks upstream publication, which can drift from when the record
arrived in Airtable.

`maxRecords` and `--since-hours 72` are unchanged. The `--record-id`
dispatch path is unaffected — single-record fetch never sorts.

### Generated artifacts covered by ingestion PRs

Both ingestion workflows' `add-paths` cover the full set of files
touched by `rebuild_local.py` + `update_docs.py`:

- `articles/*` (new article folders)
- `index.json`
- `sitemap.xml`
- `feed.xml`, `feed.json`
- `llms.txt`, `llms-full.txt`, `llms-recent.txt`
- `README.md`
- `ROADMAP.md` (added in E41a'''')

## Controlled single-record write test (E41b checklist)

This is the only acceptable path to first production write. It must NOT run
until the owner explicitly approves the listed record.

**Pre-flight**

- [ ] E41a is merged.
- [ ] Doppler `articles-git/dev` populated as above.
- [ ] Doppler → GitHub sync verified by inspecting GitHub Settings → Secrets
      (presence only; never reveal values).
- [ ] `INGEST_DRY_RUN` is `1` or unset at start.
- [ ] One Airtable record selected by the owner with:
  - `FAIM Status = Posted`
  - `Source` consistent with `articles.firstaimovers.com` archive scope
  - Slug NOT already present under `articles/<YYYY-MM-DD>-<slug>/`
  - Title NOT already present in `index.json`

**Execution**

- [ ] Set repo variable `INGEST_DRY_RUN=0`. Note the timestamp.
- [ ] Run `Actions → Ingest Airtable dispatch (E20b) → Run workflow` with
      the chosen `record_id`.
- [ ] Confirm the workflow run is green: ingest, normalize tags, duplicate
      check, rebuild, pytest.
- [ ] Open the auto-generated PR. Confirm:
  - [ ] Branch name matches `ingest/airtable-record-<recId>`.
  - [ ] Changed files are limited to `articles/<folder>/article.md`,
        `articles/<folder>/metadata.json`, `index.json`, `sitemap.xml`,
        `feed.xml`, `feed.json`, `llms.txt`, `llms-full.txt`,
        `llms-recent.txt`, `README.md`.
  - [ ] Front matter renders correctly (YAML-quoted title, ISO date, license).
  - [ ] No secrets are echoed in the workflow logs.
  - [ ] CI on the PR is green (or, if PR was created with `GITHUB_TOKEN`,
        close-and-reopen to trigger checks).
- [ ] Spot-check the rendered article on the PR preview / local rebuild.

**Post-flight**

- [ ] Immediately set `INGEST_DRY_RUN=1` again.
- [ ] Merge the PR after CODEOWNERS approval.
- [ ] Verify the article is present at `articles.firstaimovers.com` after
      `build-and-deploy.yml` runs.
- [ ] If anything looks wrong, revert via a follow-up PR; do not force-push.
- [ ] Capture the run number, PR number, and any anomalies in `ROADMAP.md`
      under the E41b row.

## AI polish (E41c / E41d) — deferred

- Provider: Anthropic (`claude-sonnet-4-6` or current latest).
- Scope: TL;DR, multi-length summary refinement, headline tightening — never
  body rewrite.
- Mode: dry-run by default; outputs to `articles/<folder>/.polish.draft.json`,
  not the canonical files.
- Activation: separate ADR + owner sign-off + cost guardrails (per-article
  token cap, monthly cap).
- Out of scope for this PR: no Anthropic SDK dependency, no API key, no
  prompt files, no schema changes.

## Auto-merge (E41f) — shipped, default OFF

`tools/auto_merge_ingestion_pr.py` runs after `peter-evans/create-pull-request`
in `.github/workflows/ingest-airtable.yml`. It is gated by:

- `INGEST_DRY_RUN != '1'` — the cron's existing kill switch (workflow-level
  `if:` on every write step). Flipping `INGEST_DRY_RUN=1` instantly disables
  ingestion *and* auto-merge.
- `AUTO_MERGE_INGESTION_PRS == '1'` — E41f-specific repo variable. Default `0`.

When both are on, the script enforces, in order:

1. Open PR exists with head ref starting with `ingest/airtable-`.
2. PR title equals exactly `ingest(articles): add articles from Airtable`.
3. Every changed path matches the allowlist:
   - `articles/<folder>/article.md`
   - `articles/<folder>/metadata.json`
   - `README.md`, `ROADMAP.md`, `index.json`, `sitemap.xml`, `feed.xml`,
     `feed.json`, `llms.txt`, `llms-full.txt`, `llms-recent.txt`
   - No nested article subdirs, no other top-level files.
4. `mergeable == "MERGEABLE"`.
5. All required CI checks finish with `conclusion == "SUCCESS"`:
   - `check` (Generated artifacts)
   - `e2e` (E2E tests)
   - `geo-audit` (GEO audit)
   - `gitleaks` (Secret scanning)
   - `lychee`, `readability`, `vale` (Article quality audit, three checks)
   - `test` (Run tests)

   The script polls with a configurable timeout (default 900s / 30s interval).

When all gates pass, the script squash-merges the PR and deletes the head
branch. Any block (allowlist violation, failed check, timeout, mergeability
failure) opens an `E41 auto-merge blocked: <reason>` issue with the PR URL,
workflow run, changed-file list, and the failed-check classification. No
secret values are recorded.

**Activation procedure (after this PR merges and is observed for ≥ 1 cron
tick under the default OFF setting):**

```bash
gh variable set AUTO_MERGE_INGESTION_PRS --body 1 -R First-AI-Movers/articles
```

**Kill switches (either reverts auto-merge):**

```bash
# E41f-specific — auto-merge off, cron still opens PRs for human review
gh variable set AUTO_MERGE_INGESTION_PRS --body 0 -R First-AI-Movers/articles

# Whole-cron kill switch — also disables PR creation
gh variable set INGEST_DRY_RUN --body 1 -R First-AI-Movers/articles
```

The next cron tick reads both variables; no workflow restart needed.

The auto-merge step never pushes to `main` directly. Squash-merge goes
through the standard GitHub merge path; branch protection rules continue
to apply (the merging token is `ARTICLE_INGESTION_PR_TOKEN` if provisioned
with the right scope, otherwise `GITHUB_TOKEN`). If branch protection
requires CODEOWNERS approval and the token has no review-bypass, the
merge will fail and an incident issue will be filed — that's the desired
safety property.

## Cost estimates

Assumption-based, not commitments.

### GitHub Actions (current scope, no LLM)

| Surface | Frequency | Avg minutes/run | Monthly minutes | Notes |
|---|---|---|---|---|
| `ingest-airtable.yml` (cron) | 1×/day | ~4 | ~120 | Includes rebuild + tests on PR-creating runs |
| `ingest-airtable-dispatch.yml` | ~1–3×/day | ~4 | ~360 | Burst-bound by Airtable changes |
| Per-PR CI (tests, e2e, quality) | 1× per ingestion PR | ~12 | ~360 | Triggered when PR is created with a CI-eligible token |
| **Total ingestion-related** | | | **~840 min/mo** | Well within the 2,000-minute Free tier and the 3,000-minute Pro tier on private repos; effectively free on public repos |

Per-article: ~16 min of Actions time end-to-end (ingest + downstream CI).
Per-100 articles: ~1,600 min (~27 hr). Public-repo Actions minutes are not
billed; private-repo overage would be ~$8/100-articles at $0.008/min.

### Anthropic (E41c/E41d projection)

Assumes Claude Sonnet 4.6 list pricing (~$3 / 1M input tokens, $15 / 1M output
tokens) and prompt caching for system+style context.

| Polish task | Input tokens | Output tokens | $/article (no cache) | $/article (90% cache hit) |
|---|---|---|---|---|
| TL;DR refinement | ~3,500 | ~250 | ~$0.014 | ~$0.0028 |
| Multi-length summary refinement | ~6,000 | ~1,200 | ~$0.036 | ~$0.0085 |
| Headline tightening | ~1,200 | ~80 | ~$0.005 | ~$0.0011 |
| **All three** | ~10,700 | ~1,530 | ~$0.055 | ~$0.012 |

Per 100 articles (worst case, no cache): ~$5.50.
Per 100 articles (with prompt caching): ~$1.20.
Monthly cap recommended at $20 to absorb retries/regressions. Hard cap and
`max_tokens` ceiling go in the polish script in E41d, not now.

## Scope guardrails for this PR

This PR is E41a only. The following are explicitly **out of scope**:

- No write-mode activation (`INGEST_DRY_RUN` stays default `1`).
- No call to the Airtable API at any layer.
- No Anthropic SDK, API key, or prompt content.
- No auto-merge mechanism.
- No workflow behavior changes — `ingest-airtable.yml` and
  `ingest-airtable-dispatch.yml` are read-only references in the new tests.
- No article body edits.
- No hand-edits to generated artifacts (`index.json`, `sitemap.xml`, etc.).
- No translation work.
- No deployment changes.
- No secret creation, rotation, or printing.

## Validation checklist for E41a

- [x] `python3 -m pytest tools/tests/test_ingest_airtable.py -q` — 51 tests
      pass (44 pre-existing + 7 new FAIM Status tests).
- [x] Field map mutation is the only behavioral change in
      `tools/ingest_airtable.py`.
- [x] No workflow YAML modified.
- [x] No secret printed; no Airtable record fetched at runtime by this PR.
