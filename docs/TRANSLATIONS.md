# Translations

Runbook for the review-gated article translation workflow (E39).

## Overview

The archive supports human-reviewed translations of articles into European languages. The workflow mirrors the E35 summaries pattern:

1. **Generate** — translation tool creates draft review files.
2. **Review** — human editor reviews terminology and marks `Status: approved`.
3. **Apply** — approved review files create `article.<lang>.md` sidecars and update `translations.json`.
4. **Build** — `rebuild_local.py` renders translated pages when `translations.json` has `status: published`.

## Gate 1: Tool design review

No DeepL calls until the mock workflow passes all tests and the user approves the review file format.

## Gate 2: DeepL draft quality

After Gate 1 approval, run DeepL to generate real draft review files. Abort if quality is insufficient.

## Gate 3: Build preview

After human review and `--apply-approved`, verify translated pages render correctly before opening PR.

**Status:** Completed for pilot article `eu-ai-act-conformity-assessment-guide-european-smes-2026` in 5 languages (es, fr, de, nl, pt).

### Pilot generated files

```
articles/2026-04-24-eu-ai-act-conformity-assessment-guide-european-smes-202/
  article.md              # original English (immutable)
  article.es.md           # Spanish translation
  article.fr.md           # French translation
  article.de.md           # German translation
  article.nl.md           # Dutch translation
  article.pt.md           # Portuguese translation
  translations.json       # sidecar with published status
```

### Translated page routes

- `/es/articles/eu-ai-act-conformity-assessment-guide-european-smes-2026/`
- `/fr/articles/eu-ai-act-conformity-assessment-guide-european-smes-2026/`
- `/de/articles/eu-ai-act-conformity-assessment-guide-european-smes-2026/`
- `/nl/articles/eu-ai-act-conformity-assessment-guide-european-smes-2026/`
- `/pt/articles/eu-ai-act-conformity-assessment-guide-european-smes-2026/`

## Supported languages

- `es` — Spanish
- `fr` — French
- `de` — German
- `nl` — Dutch
- `pt` — Portuguese

Language codes are restricted to this set. Adding a language requires updating:
- `tools/translations_schema.json`
- `tools/translate_articles.py` (`LANG_NAMES`, `VALID_LANGS`)
- `tools/translation_glossary.json`
- `tools/check_translations.py` (`VALID_LANGS`)

## File model

Translations live beside the original article, never inside `metadata.json`:

```
articles/<folder>/
  article.md           # original English
  article.es.md        # Spanish translation (created by --apply-approved)
  article.fr.md        # French translation
  metadata.json        # unchanged
  translations.json    # sidecar with status gating
```

## Review file format

Path: `translations/reviews/<slug>.<lang>.review.md`

Each review file contains:
- Article metadata (slug, language, original title, translated title, URLs)
- Terminology check table (glossary enforcement)
- Full translated markdown body
- Review status block (`Status: draft` → human review → `Status: approved`)
- Reviewer notes

**Rules:**
- `Status:` must be `draft` or `approved`.
- `Reviewer:` and `Reviewed at:` required when `Status: approved`.
- `Translated title:` required when `Status: approved`.
- Terminology check boxes must be completed before approval.

## Glossary

`tools/translation_glossary.json` defines mandated terminology per language. The review file includes a terminology check table. Post-translation lint warns if a glossary term appears in English form.

Current terms: EU AI Act, GDPR, SME, conformity assessment, high-risk AI system, AI governance, risk management, data sovereignty.

## CLI commands

### Dry-run preview (no writes, no network)

```bash
python3 tools/translate_articles.py --dry-run --slug <slug> --lang es --provider mock
```

### Generate review files (mock)

```bash
python3 tools/translate_articles.py --write-review-files --slug <slug> --lang es --provider mock
```

### Generate review files (DeepL)

```bash
python3 tools/translate_articles.py --write-review-files --slug <slug> --lang es --provider deepl --allow-network
```

### Apply approved translations

```bash
python3 tools/translate_articles.py --apply-approved --slug <slug> --lang es
```

### Validate translations sidecars

```bash
python3 tools/check_translations.py
```

## SEO strategy (Option B)

For the pilot (1 article × 5 languages):

- **English pages** remain `noindex, follow` with external canonical.
- **Translated pages** get `index, follow` with self-canonical (`/es/articles/<slug>/`).
- **hreflang** alternate links added for discovery.
- Translated pages are **not** added to `sitemap.xml`.
- Translated pages are **not** added to `feed.xml` / `feed.json`.

This is approved for the pilot only. Full-corpus canonical strategy is deferred.

## Invariants

1. **Original articles are immutable.** `article.md` and `metadata.json` are never modified by the translation tool.
2. **No automated CI translation.** DeepL calls are human-gated only.
3. **No top-20 rollout without pilot approval.** The pilot is 1 article × 5 languages.
4. **Review files are editorial artifacts.** Mock review files are workflow test fixtures, not editorial content.
5. **Translations.json is the source of truth.** Only `status: published` entries are rendered by the build.
6. **No secrets in repo.** API keys are env-only; `gitleaks` enforces this.

## Validation commands

Run these before any translation PR:

```bash
python3 tools/check_translations.py
python3 -m pytest tools/tests/test_translate_articles.py -v
python3 -m pytest tools/tests/test_check_translations.py -v
python3 -m pytest tools/tests/test_multilingual_pages.py -v
```

## Rollback

To remove a published translation from the build without deleting review files:

1. Edit `articles/<folder>/translations.json` and change the language `status` from `"published"` to `"draft"`.
2. Run `python3 tools/rebuild_local.py` to regenerate the site.
3. The translated HTML pages will no longer be rendered, but `article.<lang>.md` and review files remain for future re-approval.

To fully remove a translation:

1. Delete `article.<lang>.md`.
2. Remove the language entry from `translations.json`.
3. Rebuild the site.

## Troubleshooting

### "DEEPL_API_KEY required"

Set `DEEPL_API_KEY` in your environment. Never commit it.

### "Provider 'deepl' requires --allow-network"

Add `--allow-network` to the command, or use `--provider mock` for testing.

### "Review status is not 'approved'"

The review file must have `Status: approved` before `--apply-approved` will create `article.<lang>.md`.

### Unknown language code

Only `es`, `fr`, `de`, `nl`, `pt` are supported. Use comma-separated for multiple: `--lang es,fr,de`.
