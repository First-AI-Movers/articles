# E39 Translation Plan — Multilingual Article Variants

**Status:** Planning document — no implementation, no translations generated.  
**Date:** 2026-04-29  
**DeepL docs retrieval date:** 2026-04-29 (developers.deepl.com/docs/resources/usage-limits)

---

## 1. Executive recommendation

**Do not translate anything yet.**

E39 should ship in three phases:

- **E39a (now):** Readiness + architecture. This document, plus any schema/tool stubs needed for the build pipeline. No translated files.
- **E39b (after approval):** 1-article × 5-language pilot. Validate the full workflow end-to-end with a single high-value article.
- **E39c (after E39b review workflow proves itself):** Top-20 rollout, batched per month to stay inside DeepL Free character limits.

**Why wait:**
1. GoatCounter has only ~1 day of traffic data (E24 shipped 2026-04-28). The ROADMAP originally assumed ~30 days of data.
2. The canonical/noindex SEO decision (Section 7) has strategic implications and needs explicit owner approval before any build changes.
3. DeepL API Free is sufficient for a pilot but would require ~2.5 months for a full top-20 × 5-language rollout.

**Fallback if owner wants to proceed immediately:** Use citation-graph centrality + E35b pilot provenance as the candidate-selection heuristic. This is defensible and data-driven.

---

## 2. Analytics readiness verdict

| Question | Answer |
|---|---|
| Is GoatCounter data available in the repo? | **No.** Only the integration script (`templates/base.html.j2`), tests (`tools/tests/test_analytics.py`), and docs (`docs/ANALYTICS.md`) exist. No export files, CSVs, or JSON dumps. |
| Can we programmatically export top pages? | **Not without manual dashboard action.** GoatCounter has a JSON API, but no API key is stored in the repo or CI. `docs/ANALYTICS.md` explicitly excludes "Analytics API ingestion" and "Automated reporting" from E24 scope. |
| Do we have 30 days of data yet? | **No — approximately 1 day.** E24 shipped on 2026-04-28. The current date is 2026-04-29. We are ~29 days short of the threshold the ROADMAP assumed. |
| Fallback selection method | **Citation graph centrality + E35b pilot provenance.** `citation_graph.json` (1,245 edges across 829 articles) is already generated. Articles with the most inbound citations are structurally central to the corpus. Cross-reference with E35b's 5 reviewed-summary articles (proven high editorial value). |

---

## 3. Candidate-selection method

**Preferred method (after 30 days of GoatCounter data):**
Top 20 by GoatCounter pageviews on `/articles/<slug>/` paths.

**Fallback method (available now):**
Composite heuristic, ranked by priority:

1. **E35b pilot articles** (5 articles with human-reviewed summaries = proven editorial value).
2. **Inbound citation count** from `citation_graph.json` (structurally central articles).
3. **Topic overlap** with core themes: EU AI Act, AI governance, AI strategy, AI agents, prompt engineering, sovereign media.
4. **Recency** (2026 articles preferred; tie-breaker).
5. **Exclude** city/location-specific pages unless analytics prove demand.

---

## 4. Top-20 candidate table

| # | Folder | Slug | Title | Date | Topics | ~Chars | Reason Selected | Trans. Risk |
|---|--------|------|-------|------|--------|--------|-----------------|-------------|
| 1 | 2026-04-24-eu-ai-act-conformity-assessment-guide-european-smes-202 | eu-ai-act-conformity-assessment-guide-european-smes-2026 | EU AI Act Conformity Assessment: A Practical Guide for European SMEs | 2026-04-24 | EU AI Act, AI Governance, European SME AI, AI Risk Management, AI Strategy | 13,435 | E35b pilot; flagship regulatory guide | Low — formal terms have established equivalents |
| 2 | 2026-03-26-the-european-ceos-12-month-ai-agenda | the-european-ceos-12-month-ai-agenda | The European CEO's 12-Month AI Agenda | 2026-03-26 | AI Strategy, AI Governance, European SME AI, AI Workflow Automation, AI Productivity Tools, AI Risk Management | 12,369 | E35b pilot; C-suite execution framework | Low — business language |
| 3 | 2026-04-15-agentic-ai-smes-european-operators-guide-2026 | agentic-ai-smes-european-operators-guide-2026 | Agentic AI for European SME Operators: What Actually Changes in Your Workflows | 2026-04-15 | EU AI Act, AI Governance, European SME AI, Agentic Workflows, AI Workflow Automation, AI Strategy | 15,314 | E35b pilot; foundational agentic AI explainer | Medium — "agentic" is emergent terminology |
| 4 | 2026-03-25-claude-prompt-architecture-vs-complexity-2026 | claude-prompt-architecture-vs-complexity-2026 | Stop Making Claude Prompts More Complicated Than the Work | 2026-03-25 | AI Agents, AI Strategy | 9,535 | E35b pilot; strongest prompt-engineering guidance | Low — practical/tutorial tone |
| 5 | 2026-01-28-sovereign-media-engine-for-your-company | sovereign-media-engine-owned-audience-2026 | Why Your Company Needs a Sovereign Media Engine | 2026-01-28 | Data Sovereignty, Sovereign AI Infrastructure, European SME AI | 10,479 | E35b pilot; owned-media thesis | Medium — "sovereign media" is brand coinage |
| 6 | 2026-03-26-europes-ai-operating-shift-executive-guide | europes-ai-operating-shift-executive-guide | Europe's AI Operating Shift: The Executive Guide to Sovereignty, Token Economics, and Organizational Redesign | 2026-03-26 | Sovereign AI Infrastructure, AI Governance, European SME AI, AI Strategy | 12,365 | Broad C-level sovereignty lens | Medium — token economics is niche |
| 7 | 2026-04-18-ai-agents-vs-workflow-automation-sme-guide-2026 | ai-agents-vs-workflow-automation-sme-guide-2026 | AI Agents vs Workflow Automation: What European SME Operators Need to Know in 2026 | 2026-04-18 | AI Agents, AI Workflow Automation, AI Governance, European SME AI, AI Strategy | 14,109 | High topic overlap (5); directly compares agents vs automation | Low — comparative framing |
| 8 | 2026-04-24-ai-agent-swarms-european-smes-2026 | ai-agent-swarms-european-smes-2026 | AI Agent Swarms: What European SMEs Need to Know in 2026 | 2026-04-24 | EU AI Act, AI Governance, European SME AI, AI Agents, Multi-Agent Systems, AI Workflow Automation | 14,085 | Cutting-edge multi-agent coverage | Medium — "swarms" is emergent |
| 9 | 2026-03-12-eu-ai-act-audit-governance-model-guide | eu-ai-act-audit-governance-model-guide | EU AI Act for Growing Companies: Do You Need a Compliance Audit, a Governance Setup, or a Full AI Operating Model? | 2026-03-12 | EU AI Act, AI Governance, European SME AI, AI Risk Management, AI Strategy, AI Literacy | 14,309 | High-value EU AI Act governance depth | Low — formal regulatory language |
| 10 | 2026-03-26-ai-native-engineering-playbook-european-smes | ai-native-engineering-playbook-european-smes | The AI-Native Engineering Playbook for European SMEs | 2026-03-26 | European SME AI, AI Strategy, EU AI Act, AI Governance, AI Workflow Automation, AI Literacy | 10,442 | Strong 2026 playbook | Low — engineering terminology is stable |
| 11 | 2026-04-17-ai-roi-business-case-european-smes-2026 | ai-roi-business-case-european-smes-2026 | How to Build an AI ROI Business Case Your Board Will Actually Approve | 2026-04-17 | AI Strategy, AI Governance, European SME AI, AI Workflow Automation, AI Productivity Tools, AI Risk Management | 14,096 | Finance/board angle | Low — business case language |
| 12 | 2026-03-26-local-ai-for-european-smes-privacy-sovereignty | local-ai-for-european-smes-privacy-sovereignty | Local AI for European Companies: Privacy, Sovereignty, and Control Without the Hype | 2026-03-26 | European SME AI, GDPR & Data Privacy, Data Sovereignty, Sovereign AI Infrastructure, AI Strategy, B2B SaaS Growth | 14,848 | Sovereignty + privacy; complements #5 | Low — privacy terminology is stable |
| 13 | 2026-02-11-ai-agent-breakthroughs-sme-procurement-governance | ai-agent-breakthroughs-sme-procurement-governance | Five AI Agent Breakthroughs That Change How SMEs Should Buy, Build, and Govern Autonomous Systems | 2026-02-11 | AI Agents, EU AI Act, AI Governance, European SME AI, Multi-Agent Systems | 15,407 | Procurement + governance angle | Medium — procurement terms vary by jurisdiction |
| 14 | 2026-04-01-openai-agent-stack-consulting-need | openai-agent-stack-consulting-need | OpenAI Just Made Coding Agents More Practical. Most Companies Still Need Help Turning That Into Results | 2026-04-01 | AI Agents, AI Governance, European SME AI, AI Strategy, AI Workflow Automation, AI Coding Tools | 9,483 | Timely 2026 OpenAI angle; shorter = lower cost | Low — news/commentary tone |
| 15 | 2026-03-26-mcp-for-teams-ai-integration-layer-2026 | mcp-for-teams-ai-integration-layer-2026 | MCP for Teams: The Integration Layer AI-Native Companies Need | 2026-03-26 | Model Context Protocol, AI Strategy, AI Workflow Automation, European SME AI, Context Engineering, AI Governance | 11,688 | Hot infrastructure topic (MCP) | Medium — "MCP" is brand-new acronym |
| 16 | 2026-04-18-ai-search-visibility-generative-engine-optimization-sme | ai-search-visibility-generative-engine-optimization-sme | GEO for European SMEs: How to Be Found in ChatGPT, Gemini, and Perplexity | 2026-04-18 | AI Content Strategy, AI Search Visibility, GEO, European SME AI, B2B SaaS Growth | 14,713 | GEO/AI-search visibility | Medium — "GEO" is brand coinage |
| 17 | 2026-03-20-agentic-ai-systems-vs-scripts-2026 | agentic-ai-systems-vs-scripts-2026 | Stop Treating Agentic AI Like a Script | 2026-03-20 | AI Governance, European SME AI, Agentic Workflows, AI Strategy, AI Workflow Automation | 11,868 | Complements #3 with paradigm argument | Medium — "agentic" is emergent |
| 18 | 2026-02-09-living-website-content-engine-programmatic-seo | living-website-content-engine-programmatic-seo | The Living Website: How to Build a Content Engine That Works While You Sleep | 2026-02-09 | AI Content Strategy, Programmatic SEO, European SME AI, B2B SaaS Growth, AI Workflow Automation | 11,987 | Owned-media ops alternative | Low — marketing ops language |
| 19 | 2026-01-23-the-human-element-in-ai-what-every-european-sme-must-pr | the-human-element-in-ai-what-every-european-sme-must-pr | The Human Element in AI: What Every European SME Must Preserve as AI Scales | 2026-01-23 | EU AI Act, AI Governance, European SME AI, AI Strategy, Responsible AI | 16,994 | Ethics + governance; longest but high-value | Low — ethics language is universal |
| 20 | 2026-03-26-sovereign-ai-europe-companies-control-model-2026 | sovereign-ai-europe-companies-control-model-2026 | Sovereign AI for European Companies: What It Actually Means in Practice | 2026-03-26 | Data Sovereignty, Sovereign AI Infrastructure, AI Governance, AI Investment, AI Strategy | 17,698 | Deepest sovereignty coverage | Medium — "sovereign AI" is brand coinage |

**Total source characters for top 20:** ~248,500  
**Corpus-wide sample stats:** mean ~10,275 chars, median ~10,539 chars, max ~34,434 chars.

---

## 5. Character-budget estimate

DeepL API Free constraints (verified 2026-04-29):
- **500,000 source characters per month** (hard cap, no rollover)
- **Total request size:** 128 KiB (131,072 bytes) per request
- **Header size:** 16 KiB per request
- Billing counts source characters only; each target language = separate API call
- Target language codes: `ES`, `FR`, `DE`, `NL`, `PT`

| Scenario | Source chars | 5-lang cost | % of monthly budget | Months on Free |
|---|---|---|---|---|
| 1 article × 5 languages (avg) | ~12,379 | ~61,895 | ~12% | 1 |
| **5 articles × 5 languages (E35b pilot set)** | **61,132** | **305,660** | **~61%** | **1** |
| 10 articles × 5 languages | ~123,790 | ~618,950 | ~124% | 2 |
| 20 articles × 5 languages | ~248,500 | ~1,242,500 | ~249% | ~3 (or API Pro) |

**Recommended pilot:** 5 articles × 5 languages = 305,660 chars (~61% of monthly budget). Leaves ~194K chars for re-translation, glossary tuning, or 1–2 extra short articles.

**Request-size note:** Typical article body (10K–15K chars ≈ 10–15 KB raw, ~30–45 KB URL-encoded) fits well within 128 KiB. Longest articles (~34K chars, ~100 KB URL-encoded) still fit but with reduced margin. Chunking by H2/H3 section (~2K–4K chars each) is recommended for error isolation and retry safety.

---

## 6. Recommended file/metadata model

### 6.1 File structure (Model A — recommended)

```
articles/<folder>/
  article.md              ← original English
  article.es.md           ← Spanish translation (created by --apply-approved)
  article.fr.md           ← French translation
  article.de.md           ← German translation
  article.nl.md           ← Dutch translation
  article.pt.md           ← Portuguese translation
  metadata.json           ← unchanged; no translation bloat
  translations.json       ← review status + metadata sidecar
```

**Why Model A wins:**
- Translations live with source for review context
- No metadata.json bloat
- Build pipeline already scans article folders for sidecars (`errata.md`)
- Follows established `metadata.json` + `article.md` separation

### 6.2 `translations.json` sidecar schema

```json
{
  "es": {
    "status": "published",
    "reviewed_at": "2026-04-29",
    "reviewer": "Dr. Hernani Costa",
    "model": "deepl-free",
    "title": "Evaluación de conformidad con la Ley de IA de la UE: Guía práctica para las PYME europeas"
  },
  "fr": {
    "status": "draft",
    "reviewed_at": null,
    "reviewer": null,
    "model": null,
    "title": null
  }
}
```

**Schema rules:**
- Top-level keys: BCP-47 language codes (`es`, `fr`, `de`, `nl`, `pt`)
- `status`: enum `["draft", "published"]` (required)
- `title`: string, required for `published`
- `reviewed_at`: ISO date string, required for `published`
- `reviewer`: string, required for `published`
- `model`: string, optional (translator/model identifier)
- Only `published` translations render in the build

### 6.3 What NOT to do

- Do NOT add translation fields to `metadata.json` (schema has `additionalProperties: false`)
- Do NOT use a `translations/` top-level directory (separates from source, harder to review)
- Do NOT generate translated HTML only (breaks review-gated workflow)

---

## 7. SEO/hreflang decision options

### Current state
- Local English article pages: `noindex, follow` + canonical → external source (Radar/Beehiiv/etc.)
- Sitemap: excludes per-article pages (only home, about, topics index, topic hubs)
- `inLanguage`: hardcoded `"en"` in JSON-LD
- `<html lang="en">` hardcoded in base template

### The critical decision

Google's hreflang documentation states that **all pages in an hreflang cluster should be indexable**. Our English local pages are `noindex`, which creates a structural tension.

| Option | English | Translations | hreflang | Sitemap | SEO value |
|---|---|---|---|---|---|
| **A** | `noindex` + external canonical | `noindex` + external canonical | Ignored by Google | None | Zero — translations invisible |
| **B** *(recommended for E39)* | `noindex` + external canonical *(status quo)* | `index` + self-canonical | Add anyway for discovery | Language-specific sitemaps only | Translations rank independently; English stays mirrored |
| **C** | `index` + self-canonical | `index` + self-canonical | Full valid cluster | All pages in sitemap | Maximum authority; **massive strategic shift** |

### Recommendation

**Choose Option B for E39**, with an explicit architectural note that Option C is the long-term target after the WordPress/Hetzner migration.

- **Translated pages:** `index, follow` + self-canonical (`/es/articles/<slug>/`, etc.)
- **English local pages:** keep `noindex` + external canonical (status quo)
- **hreflang:** Add `<link rel="alternate" hreflang="...">` tags anyway — helps crawlers discover variants even if the cluster isn't perfect
- **Sitemap:** Do NOT add translated pages to main `sitemap.xml`. Create language-specific sitemaps later if needed.
- **JSON-LD `inLanguage`:** Dynamic per language (`"es"`, `"fr"`, etc.)
- **`<html lang>`:** Dynamic per language

**This decision requires explicit owner approval before implementation.**

---

## 8. Translation/review workflow

### 8.1 Tool design (`tools/translate_articles.py`)

Follows the E35 (`build_summaries.py`) review-gated pattern exactly:

```bash
# Dry-run preview (default, no writes, no network)
python3 tools/translate_articles.py --dry-run --slug my-article --lang es

# Generate review files with mock provider (no API key needed)
python3 tools/translate_articles.py --write-review-files --limit 5 --lang es --provider mock

# Generate review files with DeepL (requires DEEPL_API_KEY + --allow-network)
python3 tools/translate_articles.py --write-review-files --slug my-article --lang es --provider deepl --allow-network

# Apply approved review files to create article.<lang>.md + translations.json
python3 tools/translate_articles.py --apply-approved --slug my-article --lang es
```

**Required behavior:**
- `--dry-run` is default; never writes files or calls network
- Real API calls require `--write-review-files`, provider, API key, and `--allow-network`
- Atomic writes via `tools/_atomic_io.py`
- Character-budget report produced after processing
- Request chunking under DeepL request-size limits
- No metadata/article writes from unreviewed machine output

### 8.2 Review file model

```
translations/reviews/<slug>.<lang>.review.md
```

Structure (mirrors E35 review files):

```markdown
# Translation Review: <slug> → <lang>

- **Original title:** ...
- **Translated title:** ...
- **Source URL:** ...
- **Language:** es
- **Model:** deepl-free
- **Generated at:** 2026-04-29T12:00:00Z
- **Status:** draft
- **Reviewer:**
- **Reviewed at:**

## Terminology check

| Term | Expected ES |
|---|---|
| EU AI Act | Ley de IA de la UE |
| GDPR | RGPD |
| SME | PYME |

## Translated body

<translated markdown>
```

**Status gate:**
- `draft` → never renders, never included in build
- `approved` → human edits translation, changes Status, fills Reviewer/Reviewed at, runs `--apply-approved`

### 8.3 Quality guards

**Tone protection:**
- Prompt instruction: "Preserve the author's voice, tone, and nuance. The author is Dr. Hernani Costa, a senior AI strategist. Translations must sound authoritative, clear, and practitioner-oriented, not generic."

**No-hallucination policy:**
- Prompt instruction: "Translate ONLY the provided article text. Do not invent facts, numbers, citations, quotes, or section headings that do not exist in the original. Do not add editorial commentary."

**Glossary/terminology guard:**
- Create `tools/translation_glossary.json` with mandated equivalents:
  - "EU AI Act" → ES: "Ley de IA de la UE", FR: "Loi sur l'IA de l'UE", DE: "EU-KI-Verordnung", NL: "EU AI-verordening", PT: "Lei da IA da UE"
  - "GDPR" → ES/FR/PT: "RGPD", NL: "AVG", DE: "DSGVO"
  - "SME" → ES/PT: "PYME", FR: "PME", DE: "KMU", NL: "MKB"
- Review file includes a Terminology check section
- Post-translation lint validates glossary terms appear in mandated forms

---

## 9. Build integration plan

### 9.1 `index.json`

After reading `metadata.json`, check for `translations.json`:
- Only include languages with `status: "published"`
- Add `"translations"` key to article entry:

```json
{
  "slug": "...",
  "title": "...",
  "translations": {
    "es": { "title": "Título traducido" },
    "fr": { "title": "Titre traduit" }
  }
}
```

### 9.2 Per-article page rendering

For each article with published translations:
- Read `article.<lang>.md`
- Render into `site/<lang>/articles/<slug>/index.html`
- Pass `lang = "<lang>"` to template context

### 9.3 Template changes

- `base.html.j2`: `<html lang="{{ lang|default('en') }}">`
- `article.html.j2`: JSON-LD `"inLanguage": "{{ lang|default('en') }}"`
- Add `{% block hreflang %}{% endblock %}` populated with alternate links when translations exist

### 9.4 Sitemap

**Keep translated pages out of main `sitemap.xml`.** If Option B is approved, consider language-specific sitemaps later (`sitemap-es.xml`, etc.) only for translated pages.

### 9.5 Feeds

**Exclude translations from `feed.xml` and `feed.json`.** Rationale: subscribers expect English. If inclusion is desired later, create separate language feeds.

### 9.6 `llms-full.txt` / `llms-recent.txt`

**Include translations with language markers.** After each English article, append published translations:

```markdown
---

# Título traducido

- **Published:** 2026-04-01
- **Language:** es
- **URL:** https://articles.firstaimovers.com/es/articles/<slug>/
- **Topics:** ...

<body>
```

This preserves the corpus as a multilingual resource for LLM training.

---

## 10. Test plan

### `tools/tests/test_translate_articles.py`

1. **Language code validation** — reject invalid codes (`"xx"`, `"EN"`, `"español"`)
2. **Dry-run writes nothing** — no files, no network
3. **Mock provider creates deterministic review file** — contains original title, translated body, `Status: draft`
4. **Character budget report produced** — shows total chars, remaining budget, per-article breakdown
5. **Request chunking respects limit** — long articles split or error clearly
6. **No live network calls in tests** — all tests use `--provider mock` or monkeypatch
7. **No original article.md mutation** — mtime and content unchanged after any operation
8. **Approved translation applies atomically** — `article.es.md` created on `--apply-approved` with `Status: approved`
9. **Draft translation does not apply** — `article.es.md` NOT created for draft
10. **Hallucination guard in prompt** — assert prompt contains prohibitions against inventing facts
11. **Glossary enforcement** — mock article with "GDPR" + glossary → review file contains mandated term

### `tools/tests/test_multilingual_pages.py`

1. **Unapproved translation does not render** — no hreflang link, no `/es/` directory
2. **Approved translation renders route** — `/es/articles/<slug>/index.html` exists with translated title/body
3. **Hreflang links generated correctly** — alternate links present on English and translated pages
4. **Canonical/noindex behavior explicit** — translated pages carry `noindex, follow` + external canonical (if Option B) or self-canonical (if Option C)
5. **JSON-LD `inLanguage` set** — `"es"` on Spanish page, `"en"` on English
6. **`<html lang>` set correctly** — `<html lang="es">` on Spanish page
7. **Archive notice preserved** — "Archive copy" notice still points to original canonical
8. **License and attribution preserved** — CC BY 4.0 footer, Dr. Hernani Costa attribution
9. **No orphan translation routes** — stale `article.fr.md` without approved status creates no route
10. **Malformed translation file handled gracefully** — build skips with warning, does not crash

---

## 11. Rollout phases

### E39a — Readiness + architecture (PR #120/#121)

- [x] `docs/E39_TRANSLATION_PLAN.md` (this document)
- [x] `tools/translations_schema.json` — JSON schema for `translations.json`
- [x] `tools/check_translations.py` — sidecar validator (mirrors `check_errata.py`)
- [x] `tools/tests/test_translate_articles.py` + `test_multilingual_pages.py` — 39 tests total
- [x] `tools/translation_glossary.json` — initial glossary
- [x] Update `ROADMAP.md` with E39a/E39b/E39c breakdown
- [x] Build changes shipped in E39b (E39a + E39b merged into one delivery stream)

### E39b — Pilot (1 article × 5 languages) ✅ Done in PR #123

- [x] Pick 1 pilot article from top-5 candidate list
- [x] Implement `tools/translate_articles.py` scaffold
- [x] Generate review files with mock provider
- [x] Human review in all 5 languages
- [x] `--apply-approved` to create `article.{es,fr,de,nl,pt}.md`
- [x] Build integration: render translated pages, hreflang, `inLanguage`
- [x] Tests: `test_translate_articles.py` (27), `test_multilingual_pages.py` (12)
- [x] Validate with full test suite + e2e
- [x] PR review and merge

### E39c — Top-20 rollout (pending)

- [ ] Wait for GoatCounter 30-day data OR proceed with citation-graph fallback
- [ ] Batch translations per month to stay inside DeepL Free 500K chars
- [ ] Human review per language (batched quarterly if needed)
- [ ] Expand glossary based on review findings
- [ ] Language-specific sitemaps (if Option C canonical strategy adopted)
- [ ] Update `docs/TRANSLATIONS.md` runbook

---

## 12. Risks and open decisions

| Risk | Mitigation | Owner decision needed? |
|---|---|---|
| **Canonical/noindex strategy** (Section 7) affects whether translations have any SEO value | Document Option B vs C clearly | **YES** — Dr. Costa must approve Option B before build changes |
| DeepL Free 500K chars/month is tight for 20 × 5 languages | Pilot first; budget monthly; API Pro is $5.49/mo + $25/M chars if needed | No — operational decision during rollout |
| Machine translation quality without human review damages brand | Review-gated workflow: no publish without approval | No — workflow enforces this |
| Terminology inconsistency across languages | Glossary + lint + review checklist | No — tooling enforces this |
| GoatCounter data may never materialize for top-20 selection | Citation-graph fallback is defensible and already available | No — fallback is ready |
| Build time increase from 911 → ~1,000+ pages | Measure during E39b pilot; optimize if needed | No — measure first |
| hreflang cluster is technically broken under Option B | Accept as pragmatic intermediate; architect for Option C migration | **YES** — acknowledge in plan |
| Sending article text to DeepL may raise privacy questions | Content is CC BY 4.0 and already public; document in plan | No — license permits this |
| Translated pages may compete with original external canonical | Translations are `noindex` if Option A, or self-canonical if Option B/C | Yes — part of canonical decision |

---

## 13. Sources used

| Source | Date accessed | What it confirmed |
|---|---|---|
| `developers.deepl.com/docs/resources/usage-limits` | 2026-04-29 | 500K chars/month Free, 128 KiB request size, 16 KiB header size, language codes |
| `support.deepl.com/hc/en-us/articles/360020685720` | 2026-04-29 | Billing per source characters, exact count for API Free |
| `docs/ANALYTICS.md` (repo) | 2026-04-29 | GoatCounter is dashboard-only, no API ingestion, no repo data |
| `tools/rebuild_local.py` (repo) | 2026-04-29 | Build pipeline, sitemap exclusions, sidecar conventions (errata) |
| `tools/article_schema.json` (repo) | 2026-04-29 | `additionalProperties: false` — cannot add translation fields to metadata.json |
| `templates/base.html.j2` (repo) | 2026-04-29 | `<html lang="en">` hardcoded, canonical/robots defaults |
| `templates/article.html.j2` (repo) | 2026-04-29 | `noindex` + external canonical override, JSON-LD `inLanguage: "en"` hardcoded |
| `citation_graph.json` (repo) | 2026-04-29 | 1,245 edges across 829 articles; inbound citation counts for candidate ranking |
| E35b pilot articles (repo) | 2026-04-29 | 5 articles with human-reviewed summaries = proven editorial value |
| ROADMAP.md (repo) | 2026-04-29 | E39 scope, DeepL assumption, 30-day analytics dependency |
