# E39b Implementation Plan — 1 Article × 5 Languages Pilot

**Status:** Awaiting approval before any code is written or DeepL calls are made.
**Date:** 2026-04-29
**Pilot article:** `eu-ai-act-conformity-assessment-guide-european-smes-2026`
**SEO strategy:** Option B (approved for pilot only)

---

## 1. Executive summary

E39b is a controlled 1-article × 5-language pilot. It tests the full translation workflow end-to-end without committing to a top-20 rollout.

**Approved scope:**
- 1 pilot article: EU AI Act Conformity Assessment (~13,435 chars)
- 5 languages: Spanish (es), French (fr), German (de), Dutch (nl), Portuguese (pt)
- Estimated DeepL cost: ~67,175 source characters (~13% of monthly Free budget)
- SEO: Option B — translated pages are `index, follow` + self-canonical; English stays `noindex` + external canonical

**What E39b does NOT do:**
- No top-20 rollout
- No automated CI translation
- No changes to unrelated epics
- No modification of existing `metadata.json` schema
- No live deploy until after review and approval

---

## 2. Exact files to create / change

### New files (9)

| # | Path | Purpose |
|---|------|---------|
| 1 | `tools/translate_articles.py` | Translation CLI: dry-run, write-review-files, apply-approved, mock/deepl/manual providers |
| 2 | `tools/translations_schema.json` | JSON Schema for `translations.json` sidecar |
| 3 | `tools/check_translations.py` | Validates `translations.json` sidecars across all article folders |
| 4 | `tools/translation_glossary.json` | Mandated terminology equivalents per language |
| 5 | `tools/tests/test_translate_articles.py` | Tests for translation CLI |
| 6 | `tools/tests/test_multilingual_pages.py` | Tests for translated page rendering |
| 7 | `docs/TRANSLATIONS.md` | Runbook for the translation workflow |
| 8 | `translations/reviews/eu-ai-act-conformity-assessment-guide-european-smes-2026.es.review.md` | Generated review file (DeepL draft, human-reviewed) |
| 9 | `articles/2026-04-24-eu-ai-act-conformity-assessment-guide-european-smes-202/translations.json` | Review status sidecar |

### Modified files (5)

| # | Path | Change |
|---|------|--------|
| 1 | `templates/base.html.j2` | `<html lang="{{ lang|default('en') }}">` + `{% block hreflang %}{% endblock %}` |
| 2 | `templates/article.html.j2` | JSON-LD `inLanguage` dynamic; alternate hreflang links; robots/canonical per language |
| 3 | `tools/rebuild_local.py` | Detect `translations.json` + `article.<lang>.md`; render per-language pages; update `index.json`; update `llms-full.txt` |
| 4 | `docs/OPERATIONS.md` | Add translation workflow section |
| 5 | `docs/CHANGELOG.md` | Auto-updated via `build_changelog.py` |

### Generated during E39b (not committed until approved)

| # | Path | How created |
|---|------|-------------|
| 1 | `articles/2026-04-24-.../article.es.md` | `--apply-approved` from approved review file |
| 2 | `articles/2026-04-24-.../article.fr.md` | Same |
| 3 | `articles/2026-04-24-.../article.de.md` | Same |
| 4 | `articles/2026-04-24-.../article.nl.md` | Same |
| 5 | `articles/2026-04-24-.../article.pt.md` | Same |

---

## 3. Exact translation review file format

**Path:** `translations/reviews/<slug>.<lang>.review.md`

**Filename example:** `translations/reviews/eu-ai-act-conformity-assessment-guide-european-smes-2026.es.review.md`

**Format:**

```markdown
# Translation Review — EU AI Act Conformity Assessment: A Practical Guide for European SMEs

- **Slug:** eu-ai-act-conformity-assessment-guide-european-smes-2026
- **Language:** es
- **Target language name:** Spanish
- **Original title:** EU AI Act Conformity Assessment: A Practical Guide for European SMEs
- **Translated title:** Evaluación de conformidad con la Ley de IA de la UE: Guía práctica para las PYME europeas
- **Source URL:** https://articles.firstaimovers.com/articles/eu-ai-act-conformity-assessment-guide-european-smes-2026/
- **Canonical URL:** https://articles.firstaimovers.com/es/articles/eu-ai-act-conformity-assessment-guide-european-smes-2026/
- **Model:** deepl-free
- **Generated at:** 2026-04-29

## Terminology check

| Term | Expected ES | Found |
|---|---|---|
| EU AI Act | Ley de IA de la UE | [ ] |
| GDPR | RGPD | [ ] |
| SME | PYME | [ ] |
| conformity assessment | evaluación de conformidad | [ ] |
| high-risk AI system | sistema de IA de alto riesgo | [ ] |

## Translated body

<full translated markdown body>

## Review status

Status: draft
Reviewer:
Reviewed at:

## Reviewer notes

<free-form notes>
```

**Field rules:**
- `Status:` must be `draft` or `approved`. Default is `draft`.
- `Reviewer:` required when `Status: approved`.
- `Reviewed at:` ISO date `YYYY-MM-DD`, required when `Status: approved`.
- `Translated title:` required when `Status: approved`.
- `Terminology check` section must be completed before approval.

---

## 4. Exact translations.json schema

**Path:** `articles/<folder>/translations.json`

**Schema file:** `tools/translations_schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Article Translations Sidecar",
  "type": "object",
  "patternProperties": {
    "^(es|fr|de|nl|pt)$": {
      "type": "object",
      "required": ["status"],
      "properties": {
        "status": {
          "type": "string",
          "enum": ["draft", "published"]
        },
        "title": {
          "type": "string",
          "minLength": 1
        },
        "reviewed_at": {
          "type": "string",
          "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
        },
        "reviewer": {
          "type": "string",
          "minLength": 1
        },
        "model": {
          "type": "string"
        },
        "source_chars": {
          "type": "integer",
          "minimum": 1
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

**Validation rules enforced by `check_translations.py`:**
- `status: published` requires `title`, `reviewed_at`, `reviewer`
- `status: draft` allows null/omitted optional fields
- Language codes restricted to `es|fr|de|nl|pt`
- `reviewed_at` must be `YYYY-MM-DD`
- Unknown language codes rejected

**Example `translations.json` for the pilot:**

```json
{
  "es": {
    "status": "published",
    "title": "Evaluación de conformidad con la Ley de IA de la UE: Guía práctica para las PYME europeas",
    "reviewed_at": "2026-04-29",
    "reviewer": "Dr. Hernani Costa",
    "model": "deepl-free",
    "source_chars": 13435
  },
  "fr": {
    "status": "published",
    "title": "Évaluation de conformité à la Loi sur l'IA de l'UE: Guide pratique pour les PME européennes",
    "reviewed_at": "2026-04-29",
    "reviewer": "Dr. Hernani Costa",
    "model": "deepl-free",
    "source_chars": 13435
  },
  "de": {
    "status": "published",
    "title": "Konformitätsbewertung nach dem EU-KI-Gesetz: Ein praktischer Leitfaden für europäische KMU",
    "reviewed_at": "2026-04-29",
    "reviewer": "Dr. Hernani Costa",
    "model": "deepl-free",
    "source_chars": 13435
  },
  "nl": {
    "status": "published",
    "title": "Conformiteitsbeoordeling onder de EU AI-verordening: Een praktische gids voor Europese mkb's",
    "reviewed_at": "2026-04-29",
    "reviewer": "Dr. Hernani Costa",
    "model": "deepl-free",
    "source_chars": 13435
  },
  "pt": {
    "status": "published",
    "title": "Avaliação de conformidade com a Lei da IA da UE: Guia prático para as PME europeias",
    "reviewed_at": "2026-04-29",
    "reviewer": "Dr. Hernani Costa",
    "model": "deepl-free",
    "source_chars": 13435
  }
}
```

---

## 5. Exact glossary entries

**Path:** `tools/translation_glossary.json`

```json
{
  "EU AI Act": {
    "es": "Ley de IA de la UE",
    "fr": "Loi sur l'IA de l'UE",
    "de": "EU-KI-Verordnung",
    "nl": "EU AI-verordening",
    "pt": "Lei da IA da UE"
  },
  "GDPR": {
    "es": "RGPD",
    "fr": "RGPD",
    "de": "DSGVO",
    "nl": "AVG",
    "pt": "RGPD"
  },
  "SME": {
    "es": "PYME",
    "fr": "PME",
    "de": "KMU",
    "nl": "MKB",
    "pt": "PME"
  },
  "conformity assessment": {
    "es": "evaluación de conformidad",
    "fr": "évaluation de conformité",
    "de": "Konformitätsbewertung",
    "nl": "conformiteitsbeoordeling",
    "pt": "avaliação de conformidade"
  },
  "high-risk AI system": {
    "es": "sistema de IA de alto riesgo",
    "fr": "système d'IA à haut risque",
    "de": "Hochrisiko-KI-System",
    "nl": "hoogrisico-AI-systeem",
    "pt": "sistema de IA de alto risco"
  },
  "AI governance": {
    "es": "gobernanza de IA",
    "fr": "gouvernance de l'IA",
    "de": "KI-Governance",
    "nl": "AI-governance",
    "pt": "governança de IA"
  },
  "risk management": {
    "es": "gestión de riesgos",
    "fr": "gestion des risques",
    "de": "Risikomanagement",
    "nl": "risicobeheer",
    "pt": "gestão de riscos"
  },
  "data sovereignty": {
    "es": "soberanía de datos",
    "fr": "souveraineté des données",
    "de": "Datensouveränität",
    "nl": "datasoevereiniteit",
    "pt": "soberania de dados"
  }
}
```

**Glossary enforcement:**
- Review file includes a `Terminology check` table
- Post-translation lint scans `article.<lang>.md` for glossary terms
- If a glossary term appears in English form, lint warns: `[glossary] "GDPR" should be "RGPD" in es`
- Human reviewer must tick the `[ ]` boxes before approval

---

## 6. Exact build behavior for Option B

### 6.1 `index.json` behavior

For the pilot article only, `build_index()` adds a `"translations"` key:

```json
{
  "folder": "2026-04-24-eu-ai-act-conformity-assessment-guide-european-smes-202",
  "slug": "eu-ai-act-conformity-assessment-guide-european-smes-2026",
  "title": "EU AI Act Conformity Assessment: A Practical Guide for European SMEs",
  "translations": {
    "es": { "title": "Evaluación de conformidad...", "published": true },
    "fr": { "title": "Évaluation de conformité...", "published": true },
    "de": { "title": "Konformitätsbewertung...", "published": true },
    "nl": { "title": "Conformiteitsbeoordeling...", "published": true },
    "pt": { "title": "Avaliação de conformidade...", "published": true }
  }
}
```

**Rule:** Only languages with `translations.json` `status: "published"` are included.

### 6.2 Per-article page rendering

For each article with published translations:

**English page** (`/articles/<slug>/index.html`):
- `<html lang="en">` (default)
- `noindex, follow`
- canonical -> external source (`canonical_url`)
- JSON-LD `"inLanguage": "en"`
- hreflang alternate links to all published translations:
  ```html
  <link rel="alternate" hreflang="es" href="https://articles.firstaimovers.com/es/articles/<slug>/" />
  <link rel="alternate" hreflang="fr" href="https://articles.firstaimovers.com/fr/articles/<slug>/" />
  ...
  <link rel="alternate" hreflang="x-default" href="https://articles.firstaimovers.com/articles/<slug>/" />
  ```

**Translated page** (`/es/articles/<slug>/index.html`, etc.):
- `<html lang="es">`
- `index, follow` <- **this is the Option B change**
- canonical -> self (`https://articles.firstaimovers.com/es/articles/<slug>/`)
- JSON-LD `"inLanguage": "es"`
- hreflang alternate links back to English and other translations
- Archive notice preserved: "Archive copy — read original at [external URL]"
- License and attribution preserved

**Template implementation:**

```jinja2
{# templates/base.html.j2 #}
<html lang="{{ lang|default('en') }}" data-theme="dark">
...
{% block hreflang %}{% endblock %}
```

```jinja2
{# templates/article.html.j2 #}
{% block robots %}
{% if lang and lang != 'en' %}
<meta name="robots" content="index, follow">
{% else %}
<meta name="robots" content="noindex, follow">
{% endif %}
{% endblock %}

{% block canonical %}
{% if lang and lang != 'en' %}
<link rel="canonical" href="{{ site_url }}/{{ lang }}/articles/{{ slug }}/">
{% else %}
<link rel="canonical" href="{{ canonical_url }}">
{% endif %}
{% endblock %}

{% block hreflang %}
{% if translations %}
<link rel="alternate" hreflang="en" href="{{ site_url }}/articles/{{ slug }}/" />
{% for lang_code, t in translations.items() %}
<link rel="alternate" hreflang="{{ lang_code }}" href="{{ site_url }}/{{ lang_code }}/articles/{{ slug }}/" />
{% endfor %}
<link rel="alternate" hreflang="x-default" href="{{ site_url }}/articles/{{ slug }}/" />
{% endif %}
{% endblock %}

{# JSON-LD #}
"inLanguage": {{ (lang or 'en')|tojson }},
```

### 6.3 Sitemap behavior

- **No change to main `sitemap.xml`.** Translated pages are NOT added.
- If desired later, language-specific sitemaps (`sitemap-es.xml`) can be generated. Out of scope for E39b.

### 6.4 Feed behavior

- **No change.** Translations excluded from `feed.xml` and `feed.json`.
- Rationale: subscribers expect English.

### 6.5 `llms-full.txt` behavior

After each English article block, append published translations with language markers:

```markdown
---

# Evaluación de conformidad con la Ley de IA de la UE: Guía práctica para las PYME europeas

- **Published:** 2026-04-24
- **Language:** es
- **Original:** https://articles.firstaimovers.com/articles/eu-ai-act-conformity-assessment-guide-european-smes-2026/
- **URL:** https://articles.firstaimovers.com/es/articles/eu-ai-act-conformity-assessment-guide-european-smes-2026/
- **Topics:** EU AI Act, AI Governance, European SME AI, AI Risk Management, AI Strategy

<body>
```

### 6.6 `rebuild_local.py` changes

**In `build_index()`:**
- After reading `metadata.json`, check for `translations.json` in the same folder
- Parse it; validate with `translations_schema.json`
- Only include languages with `status: "published"`
- Add `"translations"` dict to the article entry

**In `build_site()`:**
- After rendering the English article page, check `a.get("translations", {})`
- For each published language:
  - Read `article.<lang>.md`
  - Render body via `_render_markdown`
  - Compute `output_relpath = f"{lang}/articles/{slug}/index.html"`
  - Call `_render("article.html.j2", output_relpath, lang=lang, translations=translations, ...)`
  - Pass all English article context plus `lang` and `translations`

**In `build_llms_full()` / `build_llms_recent()`:**
- After each English article, check for published translations
- Append translation blocks with language headers

---

## 7. Exact tests

### `tools/tests/test_translate_articles.py`

```python
class TestTranslateArticles:
    """Translation CLI: dry-run, review files, apply-approved, mock provider."""

    def test_dry_run_writes_nothing(self, monkeypatch, tmp_path):
        ...

    def test_mock_provider_creates_review_file(self, monkeypatch, tmp_path):
        ...

    def test_review_file_contains_draft_status(self, monkeypatch, tmp_path):
        ...

    def test_apply_approved_creates_article_lang_md(self, monkeypatch, tmp_path):
        ...

    def test_draft_does_not_apply(self, monkeypatch, tmp_path):
        ...

    def test_character_budget_report(self, monkeypatch, tmp_path):
        ...

    def test_invalid_language_rejected(self, monkeypatch, tmp_path):
        ...

    def test_no_network_in_tests(self, monkeypatch, tmp_path):
        ...

    def test_no_original_mutation(self, monkeypatch, tmp_path):
        ...

    def test_glossary_enforcement(self, monkeypatch, tmp_path):
        ...

    def test_deepl_provider_requires_api_key(self, monkeypatch, tmp_path):
        ...

    def test_deepl_provider_requires_allow_network(self, monkeypatch, tmp_path):
        ...
```

### `tools/tests/test_multilingual_pages.py`

```python
class TestMultilingualPages:
    """Translated page rendering: routes, hreflang, canonical, inLanguage."""

    def test_unapproved_translation_does_not_render(self, monkeypatch, tmp_path):
        ...

    def test_approved_translation_renders_route(self, monkeypatch, tmp_path):
        ...

    def test_english_page_has_hreflang_alternates(self, monkeypatch, tmp_path):
        ...

    def test_translated_page_has_hreflang_alternates(self, monkeypatch, tmp_path):
        ...

    def test_english_page_is_noindex_external_canonical(self, monkeypatch, tmp_path):
        ...

    def test_translated_page_is_index_self_canonical(self, monkeypatch, tmp_path):
        ...

    def test_jsonld_inlanguage_is_dynamic(self, monkeypatch, tmp_path):
        ...

    def test_html_lang_is_dynamic(self, monkeypatch, tmp_path):
        ...

    def test_archive_notice_preserved(self, monkeypatch, tmp_path):
        ...

    def test_license_attribution_preserved(self, monkeypatch, tmp_path):
        ...

    def test_orphan_translation_no_route(self, monkeypatch, tmp_path):
        ...

    def test_malformed_translation_skipped(self, monkeypatch, tmp_path):
        ...
```

### `tools/tests/test_check_translations.py`

```python
class TestCheckTranslations:
    """Sidecar validator: schema, required fields, status gate."""

    def test_valid_published_translation_passes(self):
        ...

    def test_published_without_title_fails(self):
        ...

    def test_published_without_reviewer_fails(self):
        ...

    def test_published_without_reviewed_at_fails(self):
        ...

    def test_draft_without_optional_fields_passes(self):
        ...

    def test_invalid_language_code_fails(self):
        ...

    def test_unknown_property_fails(self):
        ...
```

---

## 8. Exact validation commands

```bash
# 1. Validate translations sidecars
python3 tools/check_translations.py

# 2. Run translation tests
python3 -m pytest tools/tests/test_translate_articles.py -v
python3 -m pytest tools/tests/test_multilingual_pages.py -v
python3 -m pytest tools/tests/test_check_translations.py -v

# 3. Dry-run translation tool (no writes, no network)
python3 tools/translate_articles.py --dry-run --slug eu-ai-act-conformity-assessment-guide-european-smes-2026 --lang es --provider mock

# 4. Generate mock review files
python3 tools/translate_articles.py --write-review-files --slug eu-ai-act-conformity-assessment-guide-european-smes-2026 --lang es --provider mock

# 5. Apply approved translations
python3 tools/translate_articles.py --apply-approved --slug eu-ai-act-conformity-assessment-guide-european-smes-2026 --lang es

# 6. Build site
python3 tools/rebuild_local.py

# 7. Standard health checks
python3 tools/normalize_tags.py --dry-run
python3 tools/check_duplicate_titles.py
python3 tools/build_changelog.py --check
python3 tools/check_errata.py
python3 tools/check_series.py --strict
python3 tools/build_citation_graph.py --check

# 8. Full test suite
python3 -m pytest tools/tests -q

# 9. E2E tests
npm run test:e2e

# 10. Verify no unintended changes
git diff -- articles | head -200
git diff -- templates | head -200
git diff -- tools/rebuild_local.py | head -200
git status --short
```

---

## 9. Mock vs DeepL: which ships first?

**Recommendation: Ship mock review files first.**

**Reasoning:**
1. The mock provider creates deterministic, reviewable review files without any API key or network call.
2. This lets us validate the full workflow (generate -> review -> apply -> build -> test) before spending DeepL quota.
3. The mock review files become fixtures for `test_translate_articles.py`.
4. Only after the mock workflow passes all tests do we run DeepL to generate real draft review files.

**Sequence:**
1. Implement `tools/translate_articles.py` with mock provider
2. Generate mock review files for the pilot article
3. Run full test suite with mock fixtures
4. **Approval gate:** User reviews mock output, approves the tool design
5. Run DeepL to generate real draft review files (`--provider deepl --allow-network`)
6. Human reviews each language
7. Change `Status: draft` -> `Status: approved`
8. Run `--apply-approved`
9. Build site, run tests, merge

---

## 10. Risk controls and approval gates

### Approval gate 1: Tool design review (before any DeepL calls)

**Trigger:** After mock provider is implemented and mock review files are generated.
**Decision:** Does the review file format, glossary, and CLI interface look correct?
**Action if approved:** Proceed to generate real DeepL draft review files.
**Action if rejected:** Iterate on tool design, no DeepL quota spent.

### Approval gate 2: DeepL draft review (before human review)

**Trigger:** After `--write-review-files --provider deepl --allow-network`.
**Decision:** Are the draft translations quality enough to warrant human review time?
**Action if approved:** Assign human reviewer per language.
**Action if rejected:** Tune glossary/prompt, regenerate, or abort E39b.

### Approval gate 3: Build preview (before PR)

**Trigger:** After `--apply-approved` and `rebuild_local.py`.
**Decision:** Do the translated pages render correctly? Is hreflang valid? Is canonical correct?
**Action if approved:** Open PR.
**Action if rejected:** Fix build integration, re-test.

### Risk controls

| Risk | Control |
|---|---|
| DeepL quota surprise | Character budget report before every `--write-review-files` call |
| Unreviewed translation ships | `status: published` required; build ignores draft; tests enforce |
| Original article mutated | `--apply-approved` only creates sibling `article.<lang>.md`; tests assert original unchanged |
| API key committed | `gitleaks` CI gate; env-only key; stub exits with clear error if missing |
| Hallucinated facts in translation | Prompt guard: "Do not invent facts"; glossary enforcement; human review |
| Broken hreflang | Tests assert alternate links present and reciprocal |
| SEO penalty from duplicate content | Option B: translated pages self-canonical, English stays external canonical |
| Build time explosion | Pilot is 1 article x 5 pages = +5 pages; measure before scaling |
| Malformed translation crashes build | Build skips malformed files with stderr warning |

---

## 11. `tools/translate_articles.py` CLI design

```bash
# Dry-run preview (default)
python3 tools/translate_articles.py --dry-run --slug <slug> --lang <lang> --provider mock

# Generate review files
python3 tools/translate_articles.py --write-review-files --slug <slug> --lang <lang> --provider mock
python3 tools/translate_articles.py --write-review-files --slug <slug> --lang <lang> --provider deepl --allow-network

# Apply approved translations
python3 tools/translate_articles.py --apply-approved --slug <slug> --lang <lang>

# Batch: all languages for one slug
python3 tools/translate_articles.py --write-review-files --slug <slug> --provider mock

# Batch: specific languages
python3 tools/translate_articles.py --write-review-files --slug <slug> --lang es,fr,de --provider mock
```

**Arguments:**
- `--dry-run` (default true): Preview without writes or network
- `--write-review-files`: Generate review files
- `--apply-approved`: Create `article.<lang>.md` from approved review files
- `--provider`: `mock|deepl|manual`
- `--slug`: Target article slug
- `--lang`: Comma-separated language codes (default: `es,fr,de,nl,pt`)
- `--allow-network`: Required for real DeepL calls
- `--translations-dir`: Review file output dir (default: `translations/reviews`)
- `--glossary`: Path to glossary JSON (default: `tools/translation_glossary.json`)

---

## 12. Pilot execution checklist

- [ ] Create `tools/translate_articles.py` with mock provider
- [ ] Create `tools/translations_schema.json`
- [ ] Create `tools/check_translations.py`
- [ ] Create `tools/translation_glossary.json`
- [ ] Create `tools/tests/test_translate_articles.py`
- [ ] Create `tools/tests/test_multilingual_pages.py`
- [ ] Create `tools/tests/test_check_translations.py`
- [ ] Modify `templates/base.html.j2` (lang block, hreflang block)
- [ ] Modify `templates/article.html.j2` (dynamic robots, canonical, inLanguage, hreflang)
- [ ] Modify `tools/rebuild_local.py` (detect translations, render per-language pages)
- [ ] Generate mock review files for pilot article
- [ ] **Approval gate 1:** User reviews mock output
- [ ] Generate DeepL draft review files for pilot article
- [ ] **Approval gate 2:** User reviews draft quality
- [ ] Human review: edit translations, mark `Status: approved`
- [ ] Run `--apply-approved`
- [ ] Build site
- [ ] **Approval gate 3:** User previews translated pages
- [ ] Run full test suite + e2e
- [ ] Create `docs/TRANSLATIONS.md`
- [ ] Update `docs/OPERATIONS.md`
- [ ] Open PR, wait for CI, merge

---

## 13. What E39b does NOT change

- `tools/article_schema.json` — `additionalProperties: false` preserved; no translation fields added
- `metadata.json` for any article — translations live in sidecar
- `mcp-server/` — no changes
- `og-worker/` — no changes
- Ask page — no changes
- Existing workflows — no new CI workflows for translation
- `articles/*/article.md` originals — never modified
- No top-20 rollout
- No automated DeepL in CI
