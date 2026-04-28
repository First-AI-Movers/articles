# External Publishing

This document describes the generic external content-push path (Flow B) for adding articles to the archive from external publishing platforms.

## Overview

External platforms can push new articles to this repository via GitHub's `repository_dispatch` event. The payload is validated, files are written, artifacts are rebuilt, and a pull request is opened for owner review. **No direct push to `main` ever occurs.**

## Relationship to other ingestion paths

| Path | Trigger | Scope |
|---|---|---|
| **E18 Flow B** (this doc) | Generic `repository_dispatch` with `new-article` type | Any external platform that can POST to GitHub API with a full article payload |
| **E20a** | Airtable cron polling | Scheduled batch ingestion from Airtable (safety net) |
| **E20b** | Airtable automation → `repository_dispatch` with `airtable-record-updated` type | Single-record push from Airtable (fast path). Reuses E20a's fetch/validate/PR logic; does **not** accept a full payload here. |
| **Manual PR** | Human contributor | Direct Git-based contribution |

### E18 vs E20b: when to use which dispatch path

| | E18 (`new-article`) | E20b (`airtable-record-updated`) |
|---|---|---|
| **Payload** | Full article JSON (`title`, `slug`, `article_markdown`, etc.) | Single `record_id` string |
| **Sender** | Any external platform (Radar, Hashnode, custom CMS) | Airtable automation only |
| **Recipient workflow** | `.github/workflows/ingest-article.yml` | `.github/workflows/ingest-airtable-dispatch.yml` |
| **Validation** | Schema validation against `tools/article_schema.json` | Fetch from Airtable, then schema validation |
| **Use case** | Platforms that already have the full article and want to push it | Airtable is the source of truth; trigger ingestion on row change |

Do not send full article payloads to the E20b endpoint, and do not send bare record IDs to the E18 endpoint. They are separate plumbing for separate sources.

## Payload schema

Articles must conform to `tools/article_schema.json`:

```json
{
  "title": "string (required)",
  "slug": "string, lowercase alphanumeric with hyphens (required)",
  "published_date": "YYYY-MM-DD (required)",
  "canonical_url": "URI (required)",
  "article_markdown": "string (required)",
  "author": "string (default: Dr. Hernani Costa)",
  "author_url": "URI (default: https://drhernanicosta.com)",
  "company": "string (default: First AI Movers)",
  "company_url": "URI (default: https://firstaimovers.com)",
  "tags": ["array", "of", "strings"],
  "funnel_stage": "top | middle | bottom",
  "first_ai_movers_services": ["array", "of", "strings"],
  "status": "published | ready | approved",
  "word_count": 1234,
  "read_time_minutes": 5,
  "license": "CC BY 4.0"
}
```

See [`tools/article_schema.json`](../tools/article_schema.json) for the authoritative schema.

## Example `repository_dispatch` call

```bash
curl -X POST \
  -H "Authorization: token <sender-pat>" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/First-AI-Movers/articles/dispatches \
  -d '{
    "event_type": "new-article",
    "client_payload": {
      "title": "Example Article Title",
      "slug": "example-article-title",
      "published_date": "2026-04-28",
      "canonical_url": "https://firstaimovers.com/example-article",
      "article_markdown": "# Example\n\nThis is the article body.",
      "tags": ["AI strategy", "European SME"],
      "funnel_stage": "top"
    }
  }'
```

## Sender token requirements

The sender needs a **fine-grained personal access token** or **GitHub App token** with:

- Repository access: `First-AI-Movers/articles` only
- Permissions:
  - `contents:read` — to verify the repo
  - `actions:write` — to trigger `repository_dispatch`

Do **not** use a classic PAT with broad `repo` scope if you can avoid it.

## Recipient workflow behavior

`.github/workflows/ingest-article.yml` handles the dispatch:

1. Receives `repository_dispatch` event type `new-article`.
2. Writes `client_payload` to a temporary JSON file.
3. Runs `tools/ingest_article.py --payload-file <file> --write`.
4. Runs `tools/normalize_tags.py`.
5. Runs `tools/rebuild_local.py`.
6. Runs `tools/check_duplicate_titles.py`.
7. Runs `python3 -m pytest tools/tests -v`.
8. Opens a PR via `peter-evans/create-pull-request`.

The PR title includes the article slug. The PR body includes:
- Source: `repository_dispatch`
- Validation summary
- A reminder not to merge until CI is green and the diff is reviewed

## Review and merge process

1. Owner receives the automated PR.
2. Review the diff (article text, metadata, generated artifacts).
3. Verify CI passes.
4. Merge if acceptable.

## Rollback

If an incorrect article is ingested:

1. Close the PR without merging — no files are changed.
2. If already merged, open a **new** PR that removes the article folder. Article text is immutable, but accidental folders can be removed before they are indexed by search engines.

## Security notes

- **No secrets in payload.** Never pass `AIRTABLE_PAT`, `GITHUB_TOKEN`, or other secrets inside `client_payload`.
- **Secrets live in GitHub Encrypted Secrets only.**
- **PRs created with `GITHUB_TOKEN` do not trigger downstream CI.** If you need automatic test runs on ingestion PRs, configure the optional `ARTICLE_INGESTION_PR_TOKEN` secret.
- **Validation happens before PR creation.** Invalid payloads are rejected without creating files.

## Local testing

Test the ingester locally with the fixture payload:

```bash
python3 tools/ingest_article.py \
  --payload-file tools/fixtures/external_article_payload.json \
  --dry-run
```

To test with a custom payload:

```bash
python3 tools/ingest_article.py \
  --payload-file my-payload.json \
  --dry-run
```

Use `--write` only when you intend to create files.
