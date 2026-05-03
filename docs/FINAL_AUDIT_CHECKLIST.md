# Final Audit Checklist — Archive v1 Freeze

**Status:** Active — ready for final closeout execution  
**Date:** 2026-05-03  
**Scope:** Pre-freeze health verification of the `First-AI-Movers/articles` archive (829 articles, 103 canonical topics).  
**Label key:** `VERIFIED` = repo-grounded fact; `KNOWN_ISSUE` = documented pre-existing condition that does not block v1.

---

## 1. What this document is

This checklist defines the **exit criteria** for declaring the archive "v1 stable." It is used in two ways:

1. **Automated harness** — `tools/final_audit.py` runs the deterministic, machine-verifiable checks.
2. **Manual sign-off** — A human reviewer completes the browser-level and judgment-based checks that cannot be automated.

Both must be satisfied before the final closeout PR is merged and the archive is frozen.

---

## 2. Automated harness (`tools/final_audit.py`)

Run the harness before any manual review:

```bash
# Default mode: required checks must pass; optional warnings are shown but non-blocking
python3 tools/final_audit.py

# Strict mode: optional checks are treated as required (for CI or pre-tag verification)
python3 tools/final_audit.py --strict

# Skip local-only checks (CHANGELOG freshness, full pytest suite) when running in CI or on a fresh clone without optional deps
python3 tools/final_audit.py --skip-local
```

### 2.1 Required checks (must all pass)

| # | Check | What it verifies | Command / Evidence |
|---|-------|------------------|-------------------|
| R1 | **Repo structure** | 829 article folders, each with `article.md` + `metadata.json`; no orphaned folders | `find articles -type d` + file existence |
| R2 | **Generated artifacts current** | `index.json`, `sitemap.xml`, `feed.xml`, `feed.json`, `llms*.txt`, `README.md`, `CHANGELOG.md` are committed and match the rebuild output | `python3 tools/check_generated_artifacts.py` |
| R3 | **No duplicate titles** | All article titles are unique | `python3 tools/check_duplicate_titles.py` |
| R4 | **CITATION.cff valid** | CFF file parses without errors and contains required fields | `python3 tools/check_citation.py` |
| R5 | **Errata valid** | No malformed or orphaned errata entries | `python3 tools/check_errata.py` |
| R6 | **Translations valid** | All `translations.json` files are schema-valid; `published` entries have matching HTML files | `python3 tools/check_translations.py` |
| R7 | **Translation QA** | AI-generated translations pass deterministic quality gates (tag coverage, heading presence, URL count, length ratio, word-for-word check) | `python3 tools/check_translation_quality.py` |
| R8 | **Citation graph current** | `citation_graph.json` is up to date with the current article corpus | `python3 tools/build_citation_graph.py --check` |
| R9 | **Tags normalized** | No tag normalization drift across the corpus | `python3 tools/normalize_tags.py --dry-run` |
| R10 | **Sitemap parseable** | `sitemap.xml` is well-formed XML with the expected number of URLs | XML parse + count |
| R11 | **LLMS files present** | `llms-full.txt` and `llms-recent.txt` exist, have license headers, and contain articles | File existence + header grep |
| R12 | **Feed files present** | `feed.xml` and `feed.json` exist and are well-formed | File existence + parse |

**Current state (as of 2026-05-03):**
- All 12 required checks: **PASS** ✅

### 2.2 Optional checks (warnings allowed; use `--strict` to promote to required)

| # | Check | What it verifies | Why optional |
|---|-------|------------------|-------------|
| O1 | **CHANGELOG.md current** | `CHANGELOG.md` is up to date with the latest commits | `KNOWN_ISSUE` — CHANGELOG is intentionally maintained manually and may lag. The stale state is documented in `ROADMAP.md` and does not affect archive integrity. |
| O2 | **pytest tools/tests** | Full Python test suite passes (including optional-deps tests like embeddings) | `KNOWN_ISSUE` — `numpy` is an optional dependency for `test_embeddings.py`. This test passes in CI (`tests.yml`) where dependencies are installed. Local runs without `numpy` skip this test gracefully. |

**Current state (as of 2026-05-03):**
- O1: **FAIL** (CHANGELOG stale — pre-existing, documented)
- O2: **FAIL** locally (missing `numpy` — CI covers it)
- Both are non-blocking for v1 freeze.

### 2.3 Harness output example

```
======================================================================
FINAL ARCHIVE AUDIT
======================================================================
Check                                     Req     Status        Notes
----------------------------------------------------------------------
Repo structure                            YES       PASS
Generated artifacts current               YES       PASS
No duplicate titles                       YES       PASS
CITATION.cff valid                        YES       PASS
Errata valid                              YES       PASS
Translations valid                        YES       PASS
Translation QA                            YES       PASS
Citation graph current                    YES       PASS
Tags normalized                           YES       PASS
Sitemap parseable                         YES       PASS
LLMS files present                        YES       PASS
Feed files present                        YES       PASS
CHANGELOG.md current                       no       FAIL [changelog] ...
pytest tools/tests                         no       FAIL ...
----------------------------------------------------------------------
Results: 12/14 checks passed
Optional failures: 2
======================================================================
AUDIT PASSED with optional warnings.
```

---

## 3. Manual sign-off checklist

Complete these checks in a browser before declaring the audit complete. They verify rendering, UX, and policy compliance that automated scripts cannot assess.

### 3.1 Article rendering (5 random articles)

Open 5 articles chosen at random from the index. For each, verify:

- [ ] Page loads without 404s on CSS, JS, or fonts
- [ ] `<title>` matches the article headline
- [ ] JSON-LD `Article` schema is present in `<head>`
- [ ] Canonical URL is correct
- [ ] CC BY 4.0 footer is visible with license link
- [ ] `<meta name="ai-training">` is present
- [ ] Author attribution is correct
- [ ] Publication date is correct
- [ ] Topic tags link to valid topic hubs
- [ ] No console JavaScript errors

### 3.2 Translated pages (1 per language)

Open one translated article for each of the 5 languages (DE, ES, FR, IT, PT). Suggested: the E39b pilot article (`eu-ai-act-conformity-assessment-guide-european-smes-2026`). For each, verify:

- [ ] `<html lang="xx">` is correct
- [ ] JSON-LD `inLanguage` matches the page language
- [ ] Hreflang cluster links are present in `<head>`
- [ ] AI-generated disclosure is visible (if `ai_generated: true`)
- [ ] Human-reviewed disclosure is visible (if `approval_method: human`)
- [ ] Canonical is self-referencing (translated pages are `index,follow`)
- [ ] Content is fully translated (no mixed-language paragraphs)
- [ ] Navigation links return to the English original correctly

### 3.3 Core pages

- [ ] **Homepage** (`/`) loads; hero, article grid, topic cloud, and footer render
- [ ] **About page** (`/about/`) loads; licensing and attribution are clear
- [ ] **Ask the Archive** (`/ask/`) loads; search input is functional
- [ ] **Topic hub** (pick any topic, e.g., `/topics/artificial-intelligence/`) loads; article list is present
- [ ] **404 page** (`/nonexistent/`) returns proper 404 with navigation preserved

### 3.4 SEO / discoverability

- [ ] `robots.txt` is accessible and allows all user-agents
- [ ] `sitemap.xml` is accessible and parses as valid XML (80 URLs as of v1)
- [ ] `feed.xml` is accessible and parses as valid Atom (50 entries as of v1)
- [ ] `llms.txt` is linked from the footer and accessible
- [ ] `manifest.webmanifest` is accessible

### 3.5 Analytics / trust

- [ ] GoatCounter script is present in `<head>` with path override
- [ ] No cookie banner is displayed (GoatCounter is cookie-less)
- [ ] No tracking pixels from third parties other than GoatCounter

### 3.6 Accessibility (spot check)

- [ ] Skip-to-content link is present and keyboard-focusable
- [ ] Focus states are visible on interactive elements
- [ ] Landmark regions (`<main>`, `<nav>`, `<footer>`) are present
- [ ] Images have `alt` text (spot-check 3 articles)
- [ ] Color contrast is acceptable (WCAG 2.1 AA — spot-check with browser dev tools)

### 3.7 CI / Actions health

- [ ] GitHub Actions shows all green runs in the last 14 days
- [ ] No `gitleaks` failures in the last 30 days
- [ ] `build-and-deploy.yml` last run succeeded and Pages URL is live
- [ ] `tests.yml` last run passed
- [ ] `e2e.yml` last run passed

---

## 4. Known issues that do NOT block v1

These are documented, pre-existing conditions. They are tracked as post-v1 growth work.

| Issue | Why it doesn't block v1 | Where it's documented |
|-------|------------------------|----------------------|
| CHANGELOG.md may be slightly stale | Maintained manually; freshness does not affect archive integrity or reader experience | `ROADMAP.md` §E38 follow-ups |
| `test_embeddings.py` requires `numpy` | Optional dependency; CI covers it; local runs without numpy skip gracefully | `docs/OPERATIONS.md` |
| E39c translation rollout is incomplete (7/20 articles) | Optional growth layer; existing 35 translations are fully reviewed and published | `docs/E39C_ROLLOUT_PLAN.md` |
| MCP server not deployed live | Requires Cloudflare credentials; all code, tests, and docs are complete | `docs/RELEASE_EXTERNAL_READINESS.md` §7 |
| Ask the Archive not deployed live | Requires Cloudflare credentials; all code, tests, and docs are complete | `docs/RELEASE_EXTERNAL_READINESS.md` §7 |
| OG image renderer not deployed live | Requires Cloudflare credentials; SVG output works locally | `docs/RELEASE_EXTERNAL_READINESS.md` §7 |
| Giscus comments disabled | Requires GitHub Discussions + app install; safe to enable later | `docs/RELEASE_EXTERNAL_READINESS.md` §7 |
| IndexNow still `--dry-run` | Low-risk reversible switch; owner decision pending | `docs/RELEASE_EXTERNAL_READINESS.md` §7 |
| Zenodo DOI not minted | Requires release creation; infrastructure is ready | `docs/RELEASE_EXTERNAL_READINESS.md` §7 |

---

## 5. Sign-off process

1. **Run the automated harness:**
   ```bash
   python3 tools/final_audit.py
   ```
   Confirm all required checks pass.

2. **Complete the manual checklist** (Section 3) in a browser.

3. **Record the result.** Options:
   - Open a GitHub Discussion with the checklist pasted and checked off.
   - Post a PR comment on the final closeout PR with the results.
   - Update this file with the sign-off date and reviewer name.

4. **Merge the final closeout PR.** This PR should:
   - Update `ROADMAP.md` to mark the archive as v1 frozen.
   - Refresh `CHANGELOG.md` if desired (optional).
   - Update `CITATION.cff` `version` and `date-released` fields.
   - Tag the merge commit as `v2026.05.XX` if a Zenodo DOI is desired.

---

## 6. Quick reference

| Artifact | Count / State |
|----------|---------------|
| Articles | 829 |
| Canonical topics | 103 (77 rendered hubs) |
| Translations | 35 pages (7 articles × 5 languages) |
| Sitemap URLs | 80 |
| Feed entries | 50 |
| Citation graph | 829 nodes, 1,245 edges |
| CI workflows | 14 |
| Python tests | ~303 unit/integration + 32 Playwright E2E |
| Test pass rate (required) | 12/12 (100%) |
| Test pass rate (with optional) | 12/14 (85.7%) — non-blocking |

---

## Evidence

| Claim | Evidence | Location |
|-------|----------|----------|
| Automated harness exists | Code-reviewed, test-proven | `tools/final_audit.py` |
| Harness tests exist | pytest green (9/9) | `tools/tests/test_final_audit.py` |
| Audit design documented | Planning artifact | `docs/ROADMAP_CLOSEOUT_TRACKS.md` §6 |
| Required checks all pass | Run on 2026-05-03 | This document §2.1 |
| Optional check behavior documented | Known-issue table | This document §4 |
| Manual checklist defined | Human-verifiable steps | This document §3 |
