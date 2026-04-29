# Article Summaries

## Overview

Each article can have three optional summaries of different lengths:

- **Short** (~50 words): Single-paragraph punchline. Used for JSON-LD `description`, Open Graph tags, and social preview cards.
- **Medium** (~200 words): Structured synthesis for LLM context windows and newsletter snippets.
- **Long** (~500 words): Comprehensive overview for research briefs and citation digests.

## Review Workflow

Summaries are generated into review files (`summaries/<slug>.review.md`) with **Status: draft**. A human reviewer must:

1. Read the review file
2. Edit summaries for accuracy, tone, and voice
3. Change `Status: draft` to `Status: approved`
4. Run `--apply-approved` to write the summaries into `metadata.json`

Only approved summaries are published. Draft summaries are never used by the build.

## Usage

```bash
# Dry-run preview (default, no writes)
python3 tools/build_summaries.py --dry-run --slug my-article

# Generate review files with the mock provider (no API key needed)
python3 tools/build_summaries.py --write-review-files --limit 5 --provider mock

# Apply approved review files to metadata.json
python3 tools/build_summaries.py --apply-approved --slug my-article

# Apply even if some lengths are missing
python3 tools/build_summaries.py --apply-approved --slug my-article --allow-partial
```

## Providers

- `mock` — deterministic synthetic summaries for testing. No API key.
- `manual` — paste your own summaries into the review file.
- `anthropic` / `openai` — live LLM calls (stubs; requires SDK + API key + `--allow-network`).

## File Layout

```
articles/
  2026-04-01-my-article/
    metadata.json   ← updated by --apply-approved
    article.md
summaries/
  my-article.review.md   ← created by --write-review-files, reviewed by human
```

## Safety

- `--dry-run` (default) never writes files or calls the network.
- Real LLM calls require `--write-review-files`, a provider, an API key, and `--allow-network`.
- Metadata writes are atomic via `_atomic_io.atomic_write_json`.
- No article metadata is modified during the infrastructure phase.
