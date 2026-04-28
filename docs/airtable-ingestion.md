# Airtable Ingestion

This document describes the Airtable-to-archive ingestion pipeline (E20a).

## Purpose

Replace the Make.com-based article ingestion with a native GitHub Actions workflow that:

1. Fetches approved article records from Airtable.
2. Validates them against `tools/article_schema.json`.
3. Writes new `articles/<folder>/{article.md, metadata.json}`.
4. Normalizes tags, rebuilds derived artifacts, and opens a PR.

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
| `Slug` | `slug` | ✅ |
| `Published Date` | `published_date` | ✅ |
| `Canonical URL` | `canonical_url` | ✅ |
| `Article Markdown` | `article_markdown` | ✅ |
| `Author` | `author` | ❌ (default: Dr. Hernani Costa) |
| `Author URL` | `author_url` | ❌ |
| `Company` | `company` | ❌ |
| `Company URL` | `company_url` | ❌ |
| `Tags` | `tags` | ❌ |
| `Funnel Stage` | `funnel_stage` | ❌ |
| `First AI Movers Services` | `first_ai_movers_services` | ❌ |
| `Status` | `status` | ❌ (strongly recommended) |
| `Word Count` | `word_count` | ❌ |
| `Read Time` | `read_time_minutes` | ❌ |
| `License` | `license` | ❌ |

If your Airtable base uses different field names, edit `AIRTABLE_FIELD_MAP` in `tools/ingest_airtable.py`.

## Status gate

Only records with status `published`, `ready`, or `approved` are ingested by default.
Records with `draft`, `needs review`, or `archived` are skipped.

If your base does not have a `Status` field:
- Dry-run will warn.
- Write mode requires `--allow-no-status-gate`.

## Workflow

`.github/workflows/ingest-airtable.yml` runs:

- **Trigger:** `workflow_dispatch` (manual) or scheduled cron (`17 6 * * *`)
- **Default mode:** `INGEST_DRY_RUN=1` (reports candidates, writes nothing)
- **Write mode:** Set repository variable `INGEST_DRY_RUN=0` to enable PR creation

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

## Cutover plan from Make.com

1. **Ship E20a** with `INGEST_DRY_RUN=1`.
2. **Run side-by-side** with Make.com for 1 week. Compare incoming articles.
3. **Flip to write mode** (`INGEST_DRY_RUN=0`) when dry-run output is clean.
4. **Observe 14 days.** Monitor PRs, failures, and duplicate titles.
5. **Delete Make.com scenario** when confident.

## Rollback / disable

- Set repository variable `INGEST_DRY_RUN=1` to revert to dry-run.
- Delete the workflow file `.github/workflows/ingest-airtable.yml` to stop ingestion entirely.
- Revoke the Airtable PAT if needed.

## Failure visibility

When write mode is enabled and ingestion fails:
- The workflow run will show a red status.
- Check the Actions tab for the `Ingest articles from Airtable` workflow.
- Errors include Airtable API failures, schema validation failures, and duplicate title blocks.

## Security

- The Airtable PAT is stored as a GitHub Encrypted Secret — never committed.
- The workflow never logs the PAT or article body content.
- gitleaks is configured to scan for accidental secret commits.
