# Test Suite

Tests for the article archive tooling scripts.

## Structure

Tests are organized by production module / feature area:

| File | What it tests |
|---|---|
| `test_add_tldr.py` | TL;DR detection and injection (`add_tldr.py`) |
| `test_atomic_io.py` | Atomic file-write helpers (`_atomic_io.py`) |
| `test_check_duplicate_titles.py` | Duplicate-title detection gate |
| `test_feed.py` | Atom feed, JSON Feed, byte-stability |
| `test_index_build.py` | `index.json` schema and shape |
| `test_ingest_airtable.py` | Airtable ingestion script, schema, workflow |
| `test_llms_corpus.py` | `llms-full.txt`, `llms-recent.txt`, determinism |
| `test_normalize_tags.py` | Tag normalization to canonical topics |
| `test_per_article_pages.py` | Per-article HTML rendering (E6/E7) |
| `test_quick_reads.py` | TL;DR extraction and Quick Reads rendering |
| `test_rebuild_local.py` | Site build, sitemap, topic hubs, accessibility, SEO |
| `test_search_index.py` | Client-side search over `index.json` |
| `test_security_tooling.py` | gitleaks config, Dependabot, content scrubber |
| `test_submit_indexnow.py` | IndexNow submission script |
| `test_topic_intros.py` | `topic_intros.json` loader and content |
| `test_xss_safety.py` | XSS resistance (title, summary, body, JSON-LD) |

## Shared fixtures

- `conftest.py` — pytest configuration (`sys.path` insert so test modules can import `tools/`).
- `_fixtures.py` — shared test constants (`SAMPLE_INDEX`, `SAMPLE_ARTICLE`, etc.).

## Running tests

```bash
# Full suite
python3 -m pytest tools/tests -v

# One file
python3 -m pytest tools/tests/test_ingest_airtable.py -v

# One test class
python3 -m pytest tools/tests/test_rebuild_local.py::TestAccessibility -v

# Quick summary
python3 -m pytest tools/tests -q
```

## Adding new tests

1. Create a new file named `test_<module>.py` in this directory.
2. Import shared constants from `_fixtures.py` if needed.
3. Keep tests focused on one production module when possible.
4. Do not add new tests to a removed monolith — use focused files.
