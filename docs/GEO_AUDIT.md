# GEO Audit

The GEO (Generative Engine Optimization) audit scores every archived article for structural signals that AI answer engines and search systems favour. It is **diagnostic only** — it does not rewrite article content.

## Purpose

- Create a repeatable baseline for AI-citation friendliness.
- Prioritise editorial effort using data instead of intuition.
- Track improvement over time as the corpus grows.

## Scoring model

Each article is scored out of **100 points** across six deterministic, local checks:

| Criterion | Points | What it checks |
|---|---|---|
| Single H1 present | 20 | Exactly one markdown `# ` heading in the article body (front-matter title is ignored). |
| Sequential heading hierarchy | 20 | No heading-level jumps (e.g., `##` → `####` without `###`). Articles with no subheadings receive partial credit (10). |
| TL;DR present | 20 | Detects `> **TL;DR:**` blockquote or a `## TL;DR` / `### TL;DR` heading. |
| Outbound source link | 15 | At least one external HTTP(S) link that is not an internal First AI Movers domain or mailto. |
| Numerical/statistical signal | 15 | At least one percentage, monetary value, scale word (`million`, `billion`), or multiplier (`3.5x`). |
| Metadata completeness | 10 | Required fields (`title`, `published_date`, `canonical_url`) plus optional fields (`tags`, `author`, `word_count`, etc.). |

### Status thresholds

| Status | Score range |
|---|---|
| Pass | ≥ 80 |
| Warn | 60 – 79 |
| Fail | < 60 |

## Running locally

```bash
python3 tools/geo_audit.py
```

Options:

```bash
python3 tools/geo_audit.py --articles-dir articles --json-out geo_audit_report.json --md-out geo_audit_report.md
python3 tools/geo_audit.py --min-score 70 --fail-below-threshold
```

Default behaviour exits 0 even if scores are low. Use `--fail-below-threshold` to exit non-zero.

## Reading the reports

- `geo_audit_report.json` — machine-readable full results with per-article check breakdowns.
- `geo_audit_report.md` — human-readable executive summary, weakest articles, and recurring missing checks.

## Current soft-gate status

The GEO audit runs on every PR and push to `main` as a separate workflow (`.github/workflows/geo-audit.yml`). It uploads reports as artifacts. It is **not a required check** and does not block merges. It may be upgraded to a hard gate after the baseline is stable and editorial processes are in place.

## Improving scores

This audit measures structure, not quality. To raise a score:

- Add a single markdown `# Title` in the article body if missing.
- Ensure heading levels progress sequentially.
- Add a `> **TL;DR:** ...` blockquote near the top.
- Include at least one outbound source link.
- Add a statistic, percentage, or monetary figure where relevant.

**Do not rewrite historical articles purely to chase a score without editorial approval.**

## Why no LLM or external APIs

The audit is intentionally local and deterministic:

- No API keys or rate limits.
- No model drift.
- Fully reproducible across environments.
- Fast enough to run on 800+ articles in seconds.

## Relationship to E30 article quality CI

E30 (planned) adds `vale` prose linting, `lychee` dead-link checking, and Flesch-Kincaid readability. GEO audit is structural; E30 is editorial. They complement each other.
