# Airtable Ingestion

This document describes the Airtable-to-archive ingestion pipeline (E20a and E20b).

## Purpose

Replace the Make.com-based article ingestion with a native GitHub Actions workflow that:

1. Fetches approved article records from Airtable.
2. Validates them against `tools/article_schema.json`.
3. Writes new `articles/<folder>/{article.md, metadata.json}`.
4. Normalizes tags, rebuilds derived artifacts, and opens a PR.

## Validated dry-run state

| Run | Result |
|---|---|
| **Run ID** | `25062480810` |
| **Total seen** | 67 records |
| **Skipped** | 67 (already exist in archive) |
| **Invalid** | 0 |
| **Would create** | 0 |

The dry-run scaffold is validated. Field mapping, date normalization, slug derivation, and deduplication all work correctly. **Write mode remains disabled** pending a controlled single-record write test.

## Required secrets

Configure these in the repository Settings → Secrets and variables → Actions:

| Secret | Description |
|---|---|
| `AIRTABLE_PAT` | Airtable Personal Access Token with read access to the base |
| `AIRTABLE_BASE_ID` | Airtable base ID (e.g. `appXXXXXXXXXXXXXX`) |
| `AIRTABLE_TABLE_NAME` | Table name or ID (e.g. `Articles` or `tblXXXXXXXXXXXXXX`) |
| `AIRTABLE_VIEW_NAME` | *(Optional)* View name or ID to filter records |

## Airtable field mapping

The ingestion script maps Airtable fields to article payload fields via `AIRTABLE_FIELD_MAP` in `tools/ingest_airtable.py`:

| Airtable field (default) | Article payload key | Required |
|---|---|---|
| `Title` | `title` | ✅ |
| `slug` | `slug` | ✅ (falls back to `GUID` if missing) |
| `Pub Date` | `published_date` | ✅ |
| `GUID` | `canonical_url` | ✅ |
| `Link` | — | ❌ ignored (image/Beehiiv assets) |
| `Content HTML` | `article_markdown` | ✅ |
| `Author` | `author` | ❌ (default: Dr. Hernani Costa) |
| `Author URL` | `author_url` | ❌ |
| `Company` | `company` | ❌ |
| `Company URL` | `company_url` | ❌ |
| `tags` | `tags` | ❌ |
| `Funnel Stage` | `funnel_stage` | ❌ |
| `First AI Movers Services` | `first_ai_movers_services` | ❌ |
| `Status` | `status` | ❌ (strongly recommended) |
| `Word Count` | `word_count` | ❌ |
| `Read Time` | `read_time_minutes` | ❌ |
| `License` | `license` | ❌ |

If your Airtable base uses different field names, edit `AIRTABLE_FIELD_MAP` in `tools/ingest_airtable.py`.

## Duplicate detection

Two-layer defense, in order of evaluation per record:

1. **Folder collision** — `articles/<YYYY-MM-DD>-<slug>/` already exists.
2. **Title duplicate** — any existing `metadata.json.title` matches after
   `_normalize_title()`. Normalization (driven by E41e issue #156):
   - Unicode NFKC.
   - Em/en/minus/horizontal-bar/non-breaking-hyphen → ASCII hyphen.
   - Curly single/double quotes → ASCII apostrophe / double-quote.
   - Whitespace runs → single space; non-breaking space → regular.
   - `casefold()`.
3. **Canonical URL duplicate** — any existing `metadata.json.canonical_url`
   matches after `_normalize_canonical_url()`. Normalization:
   - Strip whitespace, drop trailing slash, lowercase scheme + host.
   - Path/query/fragment preserved case-sensitively.

Any of the three returning True ⇒ the record is silently skipped (no PR,
no incident — idempotent dedupe).

The standalone `tools/check_duplicate_titles.py` and the
`test_no_duplicate_titles_in_index` test stay on simpler `.lower()`
comparison to avoid breaking on a small set of legacy smart-quote pairs
that predate the strict gate; cleanup of those is tracked separately.

## Status gate

Only records with `FAIM Status = Posted` are ingested.

`Posted` means the article is already live in the upstream publishing system
(Hashnode/Beehiiv/Medium/etc.) and its canonical URL resolves. Mirroring it
into the archive is therefore safe.

`Ready` means the article is prepared for upstream publication but has NOT
yet been posted. The canonical URL may not yet resolve and post-publication
edits may still occur, so `Ready` records must NOT be archived.

Records with any other `FAIM Status` value (e.g. `Draft`, `Failed`, blank)
are skipped.

If a record is missing `FAIM Status` entirely:
- Dry-run allows missing status for discovery (passes `--allow-no-status-gate`).
- Write mode requires `--allow-no-status-gate` to be set explicitly.

If a record is missing `slug` but has `GUID`:
- The ingestion script derives the slug from the last path segment of `GUID`.
- If `slug` is present in Airtable, it is used directly and never overridden.

## Workflow

`.github/workflows/ingest-airtable.yml` runs:

- **Trigger:** `workflow_dispatch` (manual) or scheduled cron (`17 6 * * *`)
- **Default mode:** `INGEST_DRY_RUN=1` (reports candidates, writes nothing)
- **Write mode:** Set repository variable `INGEST_DRY_RUN=0` to enable PR creation
- **Batch caps (E41e):**
  - `INGEST_MAX_RECORDS` (default `20`) — pages this many records from
    Airtable per run.
  - `INGEST_MAX_CREATED` (default `5`) — caps successful folder creations
    per run. Skips and dedupes do not consume the budget.
  - Both can be tuned with `gh variable set NAME --body N`.
- **Incident logging:** A final workflow step opens a GitHub issue if any
  prior step in a write-mode run fails. Title format:
  `E41 cron ingestion incident: workflow run <id> failed`. Skipped on
  dry-run and on success. No secret values are recorded.

### Dry-run (default)

```bash
# CI runs this automatically
python3 tools/ingest_airtable.py --dry-run --since-hours 72
```

### Local dry-run

```bash
AIRTABLE_PAT=patXXX AIRTABLE_BASE_ID=appXXX AIRTABLE_TABLE_NAME=Articles \
  python3 tools/ingest_airtable.py --dry-run --limit 5
```

### Local write (test only)

```bash
AIRTABLE_PAT=patXXX AIRTABLE_BASE_ID=appXXX AIRTABLE_TABLE_NAME=Articles \
  python3 tools/ingest_airtable.py --write --since-hours 72
```

## Push-based trigger (E20b)

E20b adds a **fast-path, sub-second trigger** that complements the E20a cron job. Instead of waiting for the next scheduled run, an Airtable automation fires on row create or update and dispatches a `repository_dispatch` event to this repository.

### E20a vs E20b

| Aspect | E20a (cron) | E20b (push) |
|---|---|---|
| **Trigger** | Scheduled cron (`17 6 * * *`) | Airtable automation on row create / update |
| **Latency** | Up to ~24 h (daily batch) | Seconds (sub-second dispatch) |
| **Scope** | All records modified in last 72 h | Single record by ID |
| **Role** | Safety net — catches missed or failed pushes | Fast path — immediate ingestion |
| **Workflow** | `.github/workflows/ingest-airtable.yml` | `.github/workflows/ingest-airtable-dispatch.yml` |

### How the push works

1. An Airtable automation watches for row creates or updates.
2. On change, it sends a `repository_dispatch` event to GitHub with:
   - `event_type`: `airtable-record-updated`
   - `client_payload.record_id`: the Airtable record ID (e.g. `recXXXXXXXXXXXXXX`)
3. `.github/workflows/ingest-airtable-dispatch.yml` receives the dispatch and runs:
   ```bash
   python3 tools/ingest_airtable.py --record-id <id>
   ```
4. The same validation, deduplication, tag normalization, rebuild, and PR steps from E20a run for that single record.

> **The Airtable automation sends only the record ID.** The workflow fetches the full record using the existing `AIRTABLE_PAT` secret. Do **not** put the Airtable PAT inside the Airtable automation.

### Dry-run gate still applies

E20b respects the same `INGEST_DRY_RUN` repository variable as E20a:

- If `INGEST_DRY_RUN` is unset or `1`, the dispatch workflow runs in dry-run mode even when triggered by Airtable.
- Set `INGEST_DRY_RUN=0` to enable write mode and PR creation.

This means you can safely wire up the Airtable automation while keeping write mode disabled.

### Manual testing via `workflow_dispatch`

Test the E20b workflow manually without touching Airtable:

1. Go to **Actions → Ingest Airtable dispatch (E20b) → Run workflow**.
2. Enter a record ID (e.g. `recXXXXXXXXXXXXXX`).
3. The workflow runs with the same dry-run/write logic as the cron job.

Local equivalent:

```bash
AIRTABLE_PAT=patXXX AIRTABLE_BASE_ID=appXXX AIRTABLE_TABLE_NAME=Articles \
  python3 tools/ingest_airtable.py --write --record-id recXXXXXXXXXXXXXX
```

### Rollback / disable E20b

- **Disable the Airtable automation** in Airtable → Automations to stop pushes without changing repository code.
- **Delete or disable** `.github/workflows/ingest-airtable-dispatch.yml` to stop processing dispatches.
- **Set `INGEST_DRY_RUN=1`** to revert both E20a and E20b to dry-run instantly.

## Cutover plan from Make.com

1. **Ship E20a** with `INGEST_DRY_RUN=1`.
2. **Run side-by-side** with Make.com for 1 week. Compare incoming articles.
3. **Flip to write mode** (`INGEST_DRY_RUN=0`) when dry-run output is clean.
4. **Observe 14 days.** Monitor PRs, failures, and duplicate titles.
5. **Delete Make.com scenario** when confident.

## Rollback / disable

- Set repository variable `INGEST_DRY_RUN=1` to revert both E20a and E20b to dry-run instantly.
- Delete `.github/workflows/ingest-airtable.yml` to stop cron ingestion (E20a).
- Delete `.github/workflows/ingest-airtable-dispatch.yml` to stop push ingestion (E20b).
- Revoke the Airtable PAT if needed.

## Failure visibility

When write mode is enabled and ingestion fails:
- The workflow run will show a red status.
- Check the Actions tab for the `Ingest articles from Airtable` (E20a) or `Ingest Airtable dispatch` (E20b) workflow.
- Errors include Airtable API failures, schema validation failures, and duplicate title blocks.

## Security

- The Airtable PAT is stored as a GitHub Encrypted Secret — never committed.
- The workflow never logs the PAT or article body content.
- gitleaks is configured to scan for accidental secret commits.
