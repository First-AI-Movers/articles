# CI and Pages Proof

**Status:** Track B5 complete — CI health and Pages deployment verified.  
**Date:** 2026-05-03  
**Scope:** Verify the archive deploy pipeline is healthy after recent closeout changes.  
**Label key:** `VERIFIED` = repo-grounded fact; `INFERRED` = reasonable projection; `UNRESOLVED` = requires owner decision.  

---

## 1. Executive verdict

**Verdict: `ready`** — The CI pipeline and Pages deployment are healthy.

- All required checks pass on current `main`. VERIFIED
- Build & deploy workflow runs successfully through all stages. VERIFIED
- Pages site serves correctly with HTTP 200. VERIFIED
- Public artifacts (index.json, sitemap.xml, feed.xml, llms.txt, llms-full.txt, llms-recent.txt) are reachable. VERIFIED
- Translated pages render correctly with proper lang, canonical, hreflang, and AI-generated disclosure. VERIFIED
- IndexNow remains `--dry-run`. VERIFIED
- No direct push to protected `main` occurs in CI. VERIFIED

**No v1 blockers identified.**

---

## 2. Current main SHA

| Property | Value |
|---|---|
| **SHA** | `0c55f520be2dde497eef5ba708bcf223c7f42849` |
| **Commit** | `docs(sec): add security and secrets closeout review (#142)` |
| **Date** | 2026-05-03 |
| **B8 merged** | PR #142 |

---

## 3. CI proof table

Checks on `main` SHA `0c55f52` (push event):

| Workflow | Status | Duration | Evidence |
|---|---|---|---|
| Secret scanning (gitleaks) | success | 8s | `.github/workflows/gitleaks.yml` |
| Run tests | success | 55s | `.github/workflows/tests.yml` |
| E2E tests | success | 1m24s | `.github/workflows/e2e.yml` |
| GEO audit | success | 24s | `.github/workflows/geo-audit.yml` |
| Article quality audit | success | 21s | `.github/workflows/article-quality.yml` |
| Generated artifacts | success | 27s | `.github/workflows/generated-artifacts.yml` |
| **Build & deploy** | **success** | **~2m** | **Triggered via `workflow_dispatch` (see Section 4)** |

Stale failures on older commits (not blockers):

| Workflow | SHA | Status | Reason |
|---|---|---|---|
| Ingest articles from Airtable | `7b63a16` | failure | Scheduled cron; optional secrets not configured |
| Build embedding index | `7b63a16` | failure | Scheduled cron; optional dependency issue |

---

## 4. Build & deploy proof table

Workflow: `.github/workflows/build-and-deploy.yml`  
Run: `workflow_dispatch` on `main` (SHA `0c55f52`)  
Run ID: `25277083452`

| Stage | Step | Status | Notes |
|---|---|---|---|
| **build** | Checkout | success | `actions/checkout@v4` |
| **build** | Setup Python | success | `actions/setup-python@v5` (3.11) |
| **build** | Install dependencies | success | `pip install -r tools/requirements.txt` |
| **build** | Normalize tags | success | `python3 tools/normalize_tags.py` |
| **build** | Rebuild site | success | `python3 tools/rebuild_local.py` |
| **build** | Configure Pages | success | `actions/configure-pages@v4` |
| **build** | Upload artifact | success | `actions/upload-pages-artifact@v3` (path: `site/`) |
| **deploy** | Deploy Pages | success | `actions/deploy-pages@v4` |
| **indexnow** | Checkout | success | `actions/checkout@v4` |
| **indexnow** | Setup Python | success | `actions/setup-python@v5` (3.11) |
| **indexnow** | IndexNow dry-run | success | `python3 tools/submit_indexnow.py --dry-run` |

**Key observations:**
- The workflow uses `contents: read` (not `write`), so it cannot push directly to protected `main`. VERIFIED
- `build-and-deploy.yml` did **not** auto-trigger on SHA `0c55f52` because the changed files (`docs/*`, `README.md`, regenerated artifacts) do not match the workflow path filters (`articles/**`, `tools/**`, `templates/**`, `static/**`, etc.). This is expected behavior.
- A manual `workflow_dispatch` was triggered to prove the pipeline still works end-to-end on the current `main`.

---

## 5. Public URL proof table

All URLs tested with `curl -I` on 2026-05-03.

| URL | HTTP Status | Content-Type | Last-Modified |
|---|---|---|---|
| `https://articles.firstaimovers.com/` | **200** | `text/html; charset=utf-8` | Sat, 02 May 2026 12:37:28 GMT |
| `https://articles.firstaimovers.com/index.json` | **200** | `application/json; charset=utf-8` | Sat, 02 May 2026 12:37:28 GMT |
| `https://articles.firstaimovers.com/sitemap.xml` | **200** | `application/xml` | Sat, 02 May 2026 12:37:28 GMT |
| `https://articles.firstaimovers.com/feed.xml` | **200** | `application/xml` | Sat, 02 May 2026 12:37:29 GMT |
| `https://articles.firstaimovers.com/llms.txt` | **200** | `text/plain; charset=utf-8` | Sat, 02 May 2026 12:37:28 GMT |
| `https://articles.firstaimovers.com/llms-full.txt` | **200** | `text/plain; charset=utf-8` | Sat, 02 May 2026 12:37:28 GMT |
| `https://articles.firstaimovers.com/llms-recent.txt` | **200** | `text/plain; charset=utf-8` | Sat, 02 May 2026 12:37:28 GMT |
| `https://articles.firstaimovers.com/robots.txt` | **200** | `text/plain; charset=utf-8` | Sat, 02 May 2026 12:37:28 GMT |
| `https://articles.firstaimovers.com/topics/ai-strategy/` | **200** | `text/html; charset=utf-8` | Sat, 02 May 2026 12:37:29 GMT |

---

## 6. Translated page proof

Tested URL: `https://articles.firstaimovers.com/es/articles/claude-prompt-architecture-vs-complexity-2026/`

| Property | Expected | Found | Status |
|---|---|---|---|
| `html lang` | `es` | `es` | ✅ |
| `meta robots` | `index, follow` | `index, follow` | ✅ |
| Self-canonical | Present | `https://articles.firstaimovers.com/es/articles/claude-prompt-architecture-vs-complexity-2026/` | ✅ |
| hreflang en | Present | Link to English version | ✅ |
| hreflang es | Present | Link to Spanish version | ✅ |
| hreflang fr | Present | Link to French version | ✅ |
| hreflang de | Present | Link to German version | ✅ |
| hreflang nl | Present | Link to Dutch version | ✅ |
| hreflang pt | Present | Link to Portuguese version | ✅ |
| hreflang x-default | Present | Link to English version | ✅ |
| AI-generated disclosure | Present | _This page is an AI-generated translation of the original English article by Dr. Hernani Costa / First AI Movers._ | ✅ |
| HTTP status | 200 | 200 | ✅ |

---

## 7. IndexNow dry-run proof

From Build & deploy run `25277083452`, indexnow job log:

```
--- DRY RUN ---
Endpoint: https://api.indexnow.org/indexnow
Host: articles.firstaimovers.com
Key source: INDEXNOW_API_KEY_ARTICLES_FAIM
Key (redacted): ee4c...e996
Key location: https://articles.firstaimovers.com/***.txt
Sitemap URLs: 80
Filtered to articles.firstaimovers.com indexable: 80
```

**Confirmed:** IndexNow remains `--dry-run`. No live submission occurred.

---

## 8. Known non-blockers

| # | Item | Severity | Status | Why not a blocker |
|---|---|---|---|---|
| N1 | Ingest Airtable cron fails on older SHA | Low | Expected | Optional workflow; secrets not configured; does not affect archive v1 |
| N2 | Build embedding index fails on older SHA | Low | Expected | Optional workflow; optional dependency; does not affect archive v1 |
| N3 | Build & deploy did not auto-trigger on `0c55f52` | None | Expected | Path filters correctly excluded docs-only changes; manual dispatch proved pipeline health |

---

## 9. Final B5 verdict

The archive CI pipeline and Pages deployment are **healthy and ready for v1 freeze**.

| Layer | Proof | Status |
|---|---|---|
| Required CI checks | All 6 green on current `main` | ✅ |
| Build & deploy | Full run successful (build → deploy → dry-run) | ✅ |
| Pages URL | `articles.firstaimovers.com` returns 200 | ✅ |
| Public artifacts | All 7 URLs return 200 with correct content types | ✅ |
| Translated pages | Proper lang, canonical, hreflang, AI disclosure | ✅ |
| IndexNow | Remains `--dry-run` | ✅ |
| No direct push | `contents: read` in build job | ✅ |

---

## 10. Evidence summary

| Claim | Evidence type | Location |
|---|---|---|
| Current main SHA | Repo-grounded | `git log --oneline -1 origin/main` → `0c55f52` |
| All CI green | CI proven | GitHub Actions runs on SHA `0c55f52` |
| Build & deploy success | CI proven | Run `25277083452` — build, deploy, indexnow all success |
| Pages URL 200 | Live test | `curl -I https://articles.firstaimovers.com/` → HTTP 200 |
| Public artifacts 200 | Live test | `curl -I` on 7 URLs → all HTTP 200 |
| Translated page correct | Live test | `curl` on ES article → lang, robots, canonical, hreflang, AI disclosure |
| IndexNow dry-run | CI log | Run `25277083452` indexnow job → `--dry-run` output |
| No direct push | Code-reviewed | `build-and-deploy.yml` `contents: read` |
