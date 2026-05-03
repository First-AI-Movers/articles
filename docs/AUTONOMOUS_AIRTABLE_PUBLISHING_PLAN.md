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
record with `[SKIP] no Status field`. E41a remaps `"status" → "FAIM Status"`.
Allowed statuses remain `{published, ready, approved}` (case-insensitive).
`Ready` is eligible; `Posted` is intentionally excluded — Posted records have
already been published downstream and re-ingesting them is undesirable.

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

| Stage | What ships | Gate | This PR? |
|---|---|---|---|
| E41a | Status mapping fix (`Status` → `FAIM Status`); tests; this plan | None — code-only | ✅ yes |
| E41b | Controlled single-record write test with one known `Ready` record | Owner approval; `INGEST_DRY_RUN=0` set transiently for one dispatch run | ❌ no |
| E41c | Anthropic polish design (provider, prompt contract, dry-run plan) | Owner approval; ADR | ❌ no |
| E41d | Anthropic polish dry-run implementation behind feature flag | Provider gated; opt-in env var; no live calls in CI | ❌ no |
| E41e | Daily write-mode PR creation enabled via `INGEST_DRY_RUN=0` | E41b green; observation window ≥ 14 days | ❌ no |
| E41f | Gated auto-merge for ingestion PRs | All required CI checks green; CODEOWNERS approval; explicit allowlist | ❌ no |

Nothing in this plan changes the workflow's "PR-only, never push to main"
contract. `peter-evans/create-pull-request` remains the single integration
point for both `ingest-airtable.yml` and `ingest-airtable-dispatch.yml`.

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
  - `FAIM Status = Ready`
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

## Auto-merge (E41f) — deferred

- Eligible only if all of the following are true on the ingestion PR:
  - `tests.yml`, `e2e.yml`, `gitleaks.yml`, `geo-audit.yml` all green.
  - `check_duplicate_titles.py` and `check_generated_artifacts.py` green.
  - PR has exactly one CODEOWNERS approval.
  - Branch is `ingest/airtable-*`; no other paths touched.
- Mechanism: GitHub native auto-merge (squash). No third-party action.
- Out of scope for this PR.

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
