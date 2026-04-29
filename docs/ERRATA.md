# Errata and Correction Protocol

An academic-style correction protocol for the First AI Movers article archive. Articles remain immutable records; corrections are appended as structured errata.

## Purpose

Increase trust, scholarly posture, and editorial accountability. Readers can see when a factual correction, source update, clarification, or retraction has been issued while preserving archive integrity.

## Immutable article-body principle

Article Markdown files (`articles/*/article.md`) are **never edited after publication**. This is a core archive invariant (see `CONTRIBUTING.md`). Errata live in a separate file per article and are rendered as an aside on the article page.

## When to issue an erratum

| Type | When to use |
|---|---|
| `correction` | A factual error was discovered (wrong date, wrong number, misattributed quote). |
| `clarification` | The original text was technically correct but misleading or ambiguous. |
| `source-update` | A referenced link, report, or source is no longer available; replaced with archived or current version. |
| `retraction` | The article contains a significant error that undermines its conclusion. Rare. |
| `editorial-note` | A meta-level note about context, follow-up, or related later work. |

## When NOT to issue an erratum

- **Stylistic rewrites** — grammar, phrasing, tone.
- **SEO rewrites** — keyword stuffing, title tuning.
- **Republishing an improved version** — publish a new article instead.

## File format

Create `articles/YYYY-MM-DD-slug/errata.md`:

```markdown
# Errata

## 2026-04-29 — Source link updated

Type: source-update
Status: published
Editor: Dr. Hernani Costa

The original source link for the referenced report no longer resolved. It was replaced with an archived or current source link.

Affected section: Sources
```

### Rules

- File must start with `# Errata`.
- Each entry must use `## YYYY-MM-DD — Title`.
- Each entry must include `Type:`, `Status:`, and `Editor:`.
- Only `published` entries render publicly.
- `draft` entries are allowed but do not render.
- Allowed types: `correction`, `clarification`, `source-update`, `retraction`, `editorial-note`.
- Allowed statuses: `draft`, `published`.

## Validation

```bash
python3 tools/check_errata.py
```

Exits 0 when valid or when no errata files exist. Exits nonzero for malformed errata.

JSON output (optional):

```bash
python3 tools/check_errata.py --json
```

## Rendering

Published errata render as an `<aside class="errata">` near the bottom of the article page, before the article footer. Articles without `errata.md` render unchanged.

## Review process

1. Draft the erratum in `articles/<folder>/errata.md` with `Status: draft`.
2. Run `python3 tools/check_errata.py` to validate.
3. Switch to `Status: published` when approved.
4. Run `python3 tools/rebuild_local.py` to regenerate the static site.
5. Open a PR. CI validates errata format automatically.

## Rollback / removal

- To unpublish an erratum, change its status to `draft`.
- To remove all errata for an article, delete `articles/<folder>/errata.md`.
- Errata do not affect `index.json`, `sitemap.xml`, or canonical URLs.

## Relationship to other epics

| Epic | Relationship |
|---|---|
| **E30 Article Quality CI** | Errata are a quality signal; they do not trigger quality gates |
| **E23/E34 DOIs** | Errata may be referenced in per-article DOI metadata in future versions |
| **E36 Citation graph** | Errata could be linked as corrections in a future citation graph |

## Local development

```bash
# Validate all errata files
python3 tools/check_errata.py

# Build site and see errata rendered
python3 tools/rebuild_local.py
# Open site/articles/<slug>/index.html in a browser
```
