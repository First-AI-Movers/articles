# Article Quality CI

The article quality CI layer audits style, readability, and dead links across the archive. It is **diagnostic only** — it does not rewrite article content.

## Purpose

- Catch style drift (hype words, weak filler, inconsistent terminology) before it accumulates.
- Surface readability risks so editorial effort can be data-driven.
- Identify dead or broken outbound links before readers encounter them.
- Complement the [GEO audit](GEO_AUDIT.md) (structural scoring) with editorial and linguistic checks.

## What is checked

| Layer | Tool | Scope | What it looks for |
|---|---|---|---|
| **Style** | [Vale](https://vale.sh/) | `articles/**/*.md`, `docs/**/*.md`, `README.md` | Unsupported hype words, weak filler phrases, inconsistent terminology. |
| **Dead links** | [Lychee](https://lychee.cli.rs/) | `articles/**/*.md`, `docs/**/*.md`, `README.md` | Broken or unreachable HTTP(S) links. |
| **Readability** | `tools/readability.py` | `articles/**/*.md` | Flesch Reading Ease, Flesch-Kincaid Grade Level, sentence length, syllable density. |

## Why checks are soft in v1

All three layers run on every PR and push, but **none block merges**:

- The archive contains 800+ historical articles written before these rules existed.
- Mass-rewriting historical content requires editorial approval and is out of scope.
- Vale and Lychee can produce false positives (transient 403/429, context-dependent word choice).
- The goal is **visibility**, not enforcement.

Branch protection remains unchanged: only `test` and `e2e` are required.

## Running locally

### Readability

```bash
python3 tools/readability.py
```

Options:

```bash
python3 tools/readability.py --articles-dir articles --json-out readability_report.json --md-out readability_report.md
python3 tools/readability.py --min-reading-ease 40 --max-grade 16 --fail-on-threshold
```

Default behaviour exits 0 even if scores are extreme. Use `--fail-on-threshold` to exit non-zero.

### Vale

Install Vale (macOS example):

```bash
brew install vale
```

Run:

```bash
vale articles docs README.md
```

Vale reads `.vale.ini` and the `.vale/styles/FAM/` rules automatically.

### Lychee

Install Lychee (macOS example):

```bash
brew install lychee
```

Run:

```bash
lychee --config .lychee.toml
```

## How to read reports

- `readability_report.json` — machine-readable full results with per-article metrics.
- `readability_report.md` — human-readable executive summary, hardest-to-read articles, and articles over threshold.
- Vale output — per-file line-level alerts (suggestion / warning levels).
- Lychee output — list of broken links with status codes.

## How to improve an article

1. Check the readability report for your article's grade level and sentence length.
2. Break long sentences into shorter ones.
3. Replace passive constructions with active voice where possible.
4. Remove filler phrases flagged by Vale.
5. Verify all outbound links with Lychee.

## Editorial approval for historical rewrites

**Do not rewrite historical articles purely to chase a score without editorial approval.** Article text is immutable once published per `CONTRIBUTING.md`. Corrections and updates are handled by publishing a new article.

## How to update Vale terms

Edit `.vale/styles/FAM/Terminology.yml` to add or change preferred terms. Follow the existing `extends: substitution` pattern.

## How to handle dead-link false positives

If Lychee flags a link that is actually valid (e.g., a site that blocks automated requests):

1. Verify the link manually in a browser.
2. If it is a known noisy domain, add it to `.lychee.toml` `exclude_path` with a comment explaining why.
3. Do not suppress links without verification.

## Relationship to E28 GEO audit

| | GEO audit (E28) | Article quality CI (E30) |
|---|---|---|
| **Focus** | Structural signals (H1, headings, TL;DR, outbound links, numerics, metadata) | Editorial quality (style, readability, dead links) |
| **Tooling** | Pure Python, no external deps | Vale + Lychee + Python |
| **Blocking** | No | No |
| **Edits content** | No | No |

They complement each other. Run both locally before opening a PR:

```bash
python3 tools/geo_audit.py
python3 tools/readability.py
vale articles docs README.md
lychee --config .lychee.toml
```

## Workflow behaviour

`.github/workflows/article-quality.yml` runs three parallel jobs:

1. **readability** — always runs; uploads reports as artifacts.
2. **vale** — best-effort; `continue-on-error: true` so a missing Vale binary does not fail the workflow.
3. **lychee** — best-effort; `continue-on-error: true` so a missing Lychee binary or transient network errors do not fail the workflow.

On `schedule` (weekly Sundays 04:17 UTC), the full corpus is checked. On `pull_request`, the same jobs run against the PR branch.

## Risks and noise controls

- Vale rules are intentionally conservative. They flag *suggestions* and *warnings*, not errors.
- Lychee excludes LinkedIn, Twitter/X, and Hashnode/Radar domains that block automated requests.
- Readability defaults are lenient (`min-reading-ease: 30`, `max-grade: 18`) to avoid flagging the entire historical corpus.
- All three jobs upload artifacts so humans can inspect results without blocking CI.
