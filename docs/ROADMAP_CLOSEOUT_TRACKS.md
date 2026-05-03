# Roadmap Closeout — Parallel Execution Tracks

**Status:** Planning artifact — no implementation, no article changes.  
**Date:** 2026-05-01  
**Scope:** Canonicalize all remaining archive work into two parallel tracks plus a final audit phase.  
**Label key:** `VERIFIED` = repo-grounded fact; `INFERRED` = reasonable projection; `UNRESOLVED` = requires owner decision.

---

## 1. Verified current state

### What is complete

| Item | Evidence | Certainty |
|---|---|---|
| **829 articles** ingested, indexed, and site-rendered | `index.json` `"total_articles": 829` | VERIFIED |
| **103 canonical topics**, 77 rendered topic hubs | `README.md` operational-state snapshot | VERIFIED |
| **Phase 1–8 epics** (E1–E38) shipped | `ROADMAP.md` strike-through list through E38 | VERIFIED |
| **E39b translation pilot** — 1 article × 5 languages | `articles/2026-04-24-eu-ai-act-conformity-assessment-guide-european-smes-202/translations.json` with 5 `published` entries, `approval_method: human` | VERIFIED |
| **E39c mini-pilot Batch 1** — 1 article × 5 languages | `articles/2026-03-25-claude-prompt-architecture-vs-complexity-2026/translations.json` with 5 `published` entries, `approval_method: ai_qa`, `ai_generated: true` | VERIFIED |
| **Test suite** — ~303 Python unit/integration + 32 Playwright E2E | `docs/OPERATIONS.md` Test Suite Quick Reference | VERIFIED |
| **CI gates** — tests, E2E, duplicate titles, errata, gitleaks | `.github/workflows/tests.yml`, `e2e.yml`, `gitleaks.yml` | VERIFIED |
| **Soft-gate audits** — GEO, article quality (readability/Vale/Lychee) | `.github/workflows/geo-audit.yml`, `article-quality.yml` | VERIFIED |
| **Ingestion scaffolding** — E18 dispatch, E20a cron, E20b push | `.github/workflows/ingest-article.yml`, `ingest-airtable.yml`, `ingest-airtable-dispatch.yml` | VERIFIED |
| **Build & deploy** — GitHub Pages with artifact commit | `.github/workflows/build-and-deploy.yml` | VERIFIED |
| **Embeddings pipeline** — weekly parquet generation | `.github/workflows/build-embeddings.yml` | VERIFIED |
| **MCP server scaffolding** — TypeScript Worker, 5 tools + 3 resources | `mcp-server/`, `.github/workflows/mcp-server.yml` | VERIFIED |
| **Citation graph** — 829 nodes, 1,245 edges | `citation_graph.json` | VERIFIED |
| **E35a summaries infrastructure + E35b 5-article pilot** | `tools/build_summaries.py`, 5 approved review files | VERIFIED |
| **E34 per-article DOI infrastructure** | `tools/mint_dois.py`, schema support | VERIFIED |
| **AI-QA translation checker** | `tools/check_translation_quality.py`, deterministic offline checks | VERIFIED |

### What is partially complete

| Item | What ships | What remains | Certainty |
|---|---|---|---|
| **E39c top-20 translation rollout** | E39b pilot done (1 article, human-reviewed). E39c Batch 1 done (6 articles, AI-QA approved). 7 articles × 5 languages = 35 translated pages total. Tooling, tests, docs, batch plan ready. | 13 remaining articles × 5 languages = 65 translation entries pending AI-QA approval and `--apply-approved`. Quota-paced at ~1 article/month on DeepL Free. | VERIFIED |
| **E20a Airtable ingestion** | Dry-run validated (67/67 records clean); field mapping correct | Write mode disabled; controlled single-record write test not done; Make.com not retired | VERIFIED |
| **E21 MCP server** | Code, tests, data export, docs shipped | Live deployment gated — `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `MCP_DEPLOY_ENABLED=1` not configured | VERIFIED |
| **E33 Ask the Archive** | Backend (`/api/ask`), frontend (`/ask/`), tests, docs shipped | Live deployment gated — Cloudflare credentials + rate-limit setup pending | VERIFIED |
| **E35 multi-length summaries** | Infrastructure + 5-article reviewed pilot | Full-corpus rollout pending separate owner approval | VERIFIED |
| **E38 OG image renderer** | Worker scaffold, template wiring, tests shipped | SVG primary output only; PNG via resvg-wasm not enabled; no live deployment or DNS | VERIFIED |
| **IndexNow** | Key file, submission tool, CI dry-run step, tests shipped | Live submission still `--dry-run` in `build-and-deploy.yml` | VERIFIED |
| **Giscus comments** | Scaffold, template wiring, tests, docs shipped | Disabled by default; `repo_id`/`category_id` empty; GitHub Discussions not enabled | VERIFIED |

### What is pending

| Item | Why pending | Blocker |
|---|---|---|
| **E39c quota-paced continuation** | Optional post-v1 growth layer. Awaiting owner go-ahead on DeepL quota + AI-QA threshold. Default pace ~1 article × 5 languages per month. | Owner decision |
| **E39c hreflang/SEO strategy confirmation** | Option B approved for pilot and Batch 1; re-confirmation needed for continued rollout | Owner decision |
| **N2 Live IndexNow switch** | CI step still `--dry-run` | Owner decision (low risk, reversible) |
| **N3 Topic hub CTR optimization** | Requires 2–4 weeks of GSC data | GoatCounter data not yet available (~3 days since E24) |
| **N4 WordPress/Hetzner migration checklist** | External platform work, not archive blocker | Owner timeline |
| **E23 Zenodo DOI minting** | Infrastructure ready; no release created yet | Owner decision |
| **E34 Per-article DOI minting** | Infrastructure ready; no sandbox or production records created | Owner decision |

### What is blocked by credentials, platform access, or owner decisions

| Blocker | Affected items | Certainty |
|---|---|---|
| **Cloudflare credentials** (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`) | E21 MCP deploy, E33 Ask deploy, E38 OG renderer deploy | VERIFIED |
| **DeepL API key + owner approval** | E39c translation generation | VERIFIED |
| **GitHub Discussions + Giscus app install** | E26 comments enablement | VERIFIED |
| **Zenodo account linking + release decision** | E23 corpus DOI, E34 per-article DOIs | VERIFIED |
| **`MCP_DEPLOY_ENABLED=1` repository variable** | E21 auto-deploy on push | VERIFIED |
| **`INGEST_DRY_RUN=0` repository variable** | E20a/E20b live write mode | VERIFIED |
| **AI-QA tolerance threshold** | E39c `--apply-approved` gate (`check_translation_quality.py` strictness) | UNRESOLVED |

---

## 2. Two-track execution model

### Track A — Finish the visible product

**Purpose:** Complete the reader-facing layer so the archive is maximally useful before final audit and owner focus shifts.

**In scope:**

| Work item | Why Track A | Size | Owner |
|---|---|---|---|
| **A1 — E39c next article translation** (~1 article × 5 languages) | Continue AI-QA approved rollout at quota pace | M | Content/Translation |
| **A4 — README.md stats refresh** | Ensure badges and counts match `index.json` | XS | Docs |
| **A5 — N2 Live IndexNow switch** (optional) | If owner approves, remove `--dry-run` from `build-and-deploy.yml` indexnow step | XS | Automation |

**Track A avoids:**
- Broad workflow rewrites
- Automation architecture changes (MCP deploy, chatbot deploy, OG deploy)
- Final audit changes
- Unrelated docs restructuring
- E35 full-corpus summary rollout (separate owner decision)

### Track B — Automation, hardening, and audit readiness

**Purpose:** Close automation gaps, harden docs/consistency, and build the scaffolding for the final audit so the archive can be frozen as a stable v1.

**In scope:**

| Work item | Why Track B | Size | Owner |
|---|---|---|---|
| **B1 — Canonical closeout tracks doc** (this doc) | Single source of truth for remaining work | S | Planning |
| **B2 — Automation readiness audit** | Verify every workflow runs, every gate behaves, every credential is documented | M | Automation |
| **B3 — Workflow/doc consistency pass** | Ensure `docs/OPERATIONS.md`, `README.md`, `CONTRIBUTING.md`, and workflow comments are consistent with current code | S | Docs |
| **B4 — Generated artifact policy** | Document which artifacts are committed vs gitignored vs CI-generated; verify `build-and-deploy.yml` commit list is complete | XS | Automation |
| **B5 — CI/Pages proof** | Verify `build-and-deploy.yml` deploys cleanly; verify Pages URL returns 200 | S | Automation | `docs/CI_PAGES_PROOF.md` |
| **B6 — Release/DOI/MCP/embeddings readiness checklist** | Consolidate E21/E22/E23/E34/E38 gated items into one readiness matrix | S | Automation | `docs/RELEASE_EXTERNAL_READINESS.md` |
| **B7 — Final audit harness/checklist** | Create the checklist and scripts for the final large audit (Section 6) | M | Planning |
| **B8 — Security/secrets review** | Verify `.gitleaks.toml` coverage, confirm no secrets in history, document rotation schedule | S | Automation | `docs/SECURITY_SECRETS_REVIEW.md` |

**Track B avoids:**
- Article translation rollout
- Article content editing
- Changes to E39 translation files unless needed for planning docs
- DeepL API calls
- Live Cloudflare deployments (credential-dependent)

---

## 3. Dependency graph

| Work item | Track | Dependency | Can run now? | Risk | Done evidence |
|---|---|---|---|---|---|
| B1 Closeout tracks doc | B | None | **Yes** | Low | This document |
| B3 Doc consistency pass | B | B1 | **Yes** | Low | PR diff only |
| B4 Generated artifact policy | B | B1 | **Yes** | Low | Doc + verify list |
| B2 Automation readiness audit | B | B1, B3 | **Yes** | Low | Workflow run logs |
| B5 CI/Pages proof | B | B2 | After B2 | Low | Live URL 200 |
| B6 Release/DOI/MCP readiness | B | B2 | **Yes** | Low | `docs/RELEASE_EXTERNAL_READINESS.md` |
| B8 Security/secrets review | B | B2 | After B2 | Low | gitleaks green |
| B7 Final audit harness | B | B2, B5, B6 | After B5 | Medium | Checklist doc + scripts |
| A4 README stats refresh | A | None | **Yes** | Low | `rebuild_local.py` output |
| A5 Live IndexNow | A | Owner approval | **Yes** (if approved) | Low | CI step removes `--dry-run` |
| A1 E39c next translation | A | Owner approves quota + AI-QA threshold | **Yes** (if approved) | Medium | `translations.json` entries |
| **Final large audit** | Final | B1–B8 (A1–A5 optional) | After Track B complete | Medium | Section 6 checklist |
| **Archive closeout PR** | Final | Final audit green | After audit | Low | `ROADMAP.md` marks archive v1 |

**What can run in parallel immediately:**
- B1, B3, B4, B6, B8 (all doc/planning work)
- A4 (small docs fix)
- A1 next translation (if owner approves DeepL + AI-QA threshold now)

**What must wait for Track A:**
- Nothing in Track B is blocked by Track A. They are intentionally decoupled.
- E39c translation continuation is optional and does not block the final audit.

**What must wait for Track B:**
- Final audit harness (B7) needs automation readiness verified first.

**What must happen only during the final audit:**
- Cross-cutting integrity checks (article count, metadata, URLs, canonicals, licensing)
- Browser-level verification of translated pages
- Full test suite + E2E run on a clean checkout
- Pages deployment verification
- secrets/attribution/licensing proof

---

## 4. Suggested branch/PR sequence

```
Independent (parallel):
├── PR B1  → docs(roadmap): canonical closeout tracks
└── PR A4  → docs(readme): refresh stats from latest index

After B1 merges:
├── PR B2  → docs(ops): workflow/doc consistency pass
├── PR B4  → docs(ops): generated artifact policy
└── PR B8  → ci(sec): secrets review + gitleaks coverage check

After A4 merges:
├── PR A5  → ci(indexnow): switch to live submission (owner-approved)
└── PR A1  → feat(translations): E39c next article × 5 languages (AI-QA, quota-paced)

After B2 + B4 + B8 merge:
├── PR B5  → ci(pages): verify deploy health + URL proof
├── PR B6  → docs(ops): release/DOI/MCP/embeddings readiness matrix
└── PR B7  → docs(audit): final audit harness and checklist

After Track B complete (A1 optional):
├── PR FINAL → docs(closeout): archive v1 freeze — CHANGELOG.md, CITATION.cff
```

**Naming convention:**
- `docs(...)` — planning, runbook, README changes
- `feat(translations)` — new `article.<lang>.md` + `translations.json`
- `ci(...)` — workflow or automation changes
- `fix(...)` — correction to existing behavior

---

## 5. No-touch zones / collision prevention

### File ownership by track

| Zone | Track A may touch | Track B may touch | Neither may touch without coordination |
|---|---|---|---|
| **Translation content** | `articles/<slug>/article.{es,fr,de,nl,pt}.md`, `articles/<slug>/translations.json` | — | `article.md`, `metadata.json` |
| **Translation review files** | `translations/reviews/<slug>.<lang>.review.md` | — | — |
| **Planning docs** | `docs/E39*.md` (updates after batches) | `docs/ROADMAP_CLOSEOUT_TRACKS.md`, `docs/OPERATIONS.md`, `docs/ARCHITECTURE.md` | — |
| **ROADMAP.md** | Track A owns content-status updates (E39 progress) | **Do not touch** — PR #130 already aligned E39 wording; future updates belong to Track A or the final closeout PR only | Both — edit in separate PRs, never simultaneously |
| **README.md** | Stats refresh | License/dual-license wording | — |
| **Workflows** | — (except A5 with owner approval) | `.github/workflows/*.yml` (consistency pass only) | `build-and-deploy.yml` commit logic |
| **Generated artifacts** | `translations.json` | `index.json`, `sitemap.xml`, `feed.xml`, `feed.json`, `llms*.txt` | Only via `rebuild_local.py` in CI |
| **Templates** | — | `templates/*.j2` (doc references only) | Template logic changes |
| **Tools** | `tools/translate_articles.py` (bug fixes only) | `tools/*.py` (doc references, schema checks) | Core ingestion/build logic |

### Merge sequencing rule

1. **ROADMAP.md** must be touched by one PR at a time. Track B does not touch `ROADMAP.md` — PR #130 already aligned E39 wording. If Track A needs to mark E39c progress, open a dedicated PR.
2. **No PR may both translate articles AND change CI workflows.** Split them.
3. **Translation PRs must include:** `python3 tools/check_translations.py` passing, `python3 tools/check_translation_quality.py` passing, plus the relevant pytest modules.
4. **Doc-only PRs must include:** `python3 tools/build_citation_graph.py --check` passing, `python3 tools/check_duplicate_titles.py` passing.

---

## 6. Final large audit design

The final audit is a **dedicated phase** after both Track A and Track B are complete. It is not part of either track. Treat it as a "release candidate" review before freezing v1.

### Audit scope

| Layer | What to verify | Proof label | How |
|---|---|---|---|
| **Repo structure** | 829 article folders, each with `article.md` + `metadata.json`; no orphaned folders | `Metadata-reviewed` | `find articles -type d | wc -l` + schema validation |
| **Article/metadata integrity** | All `metadata.json` valid against `article_schema.json`; no duplicate titles | `Metadata-reviewed` | `pytest tools/tests/test_article_schema.py` + `check_duplicate_titles.py` |
| **Generated artifacts** | `index.json`, `sitemap.xml`, `feed.xml`, `feed.json`, `llms*.txt`, `README.md` are current and committed | `Generated-artifact-proven` | `git status` clean after `rebuild_local.py` |
| **Translation sidecars** | All `translations.json` valid; published translations render correctly; AI-QA checker passes | `Content-reviewed` | `check_translations.py` + `check_translation_quality.py` + build preview |
| **AI-QA disclosure** | AI-generated translations carry visible disclosure; `ai_generated: true` in sidecar | `Content-reviewed` | E2E test + file grep |
| **AI-training disclosure** | `<meta name="ai-training">` present on all rendered pages; `llms-full.txt` license header intact | `Content-reviewed` | E2E test + file grep |
| **Sitemap/feed/llms** | `sitemap.xml` = 80 URLs; `feed.xml` = 50 entries; `llms.txt` discoverable | `Generated-artifact-proven` | Count + validate XML |
| **README/ABOUT/CITATION/LICENSE** | Stats current; ORCID/affiliation links work; `CITATION.cff` valid; dual-license clear | `Content-reviewed` | Manual review + `check_citation.py` |
| **Workflows** | All 13 workflows have up-to-date references; no dead steps | `CI-proven` | Read every `.github/workflows/*.yml` |
| **CI** | `pytest tools/tests` green; `npm run test:e2e` green; gitleaks green | `Test-proven`, `CI-proven` | Run full suite on clean checkout |
| **Pages/browser proof** | `https://articles.firstaimovers.com/` returns 200; key pages render; no 404s on CSS/JS | `Browser/Pages-proven` | Playwright E2E + manual spot-check |
| **Canonical URLs** | English pages = `noindex,follow` + external canonical; translated pages = `index,follow` + self-canonical | `URL/canonical-proven` | E2E assertion + view-source |
| **SEO/robots/hreflang** | `robots.txt` valid; `sitemap.xml` advertised; hreflang clusters present on translated pages | `URL/canonical-proven` | E2E + XML validation |
| **Accessibility** | Skip link, focus states, landmarks, aria labels present per E11 | `Browser/Pages-proven` | Playwright E2E + axe-core (if available) |
| **Analytics** | GoatCounter script present with path override; no cookie banner needed | `Browser/Pages-proven` | View-source + network tab |
| **MCP/embeddings/DOI/release readiness** | Readiness matrix from B6 confirms each gated item is either deployed or documented as deferred | `CI-proven` | Checklist review |
| **Security/secrets** | `gitleaks` green; no credentials in repo; Dependabot active | `Test-proven`, `CI-proven` | `gitleaks detect` + `.gitleaks.toml` review |
| **Licensing/attribution** | Every page has CC BY 4.0 footer; `LICENSE` + `LICENSE-CODE` present; `CITATION.cff` valid | `Content-reviewed` | grep + manual review |

### Audit process

1. **Create a clean checkout** in a temp directory.
2. **Run the automated harness** (B7 will produce a script):
   ```bash
   python3 tools/rebuild_local.py
   python3 -m pytest tools/tests -q
   npm run test:e2e
   python3 tools/check_duplicate_titles.py
   python3 tools/normalize_tags.py --dry-run
   python3 tools/build_citation_graph.py --check
   python3 tools/check_translations.py
   python3 tools/check_translation_quality.py
   python3 tools/check_errata.py
   python3 tools/check_citation.py
   ```
3. **Manual verification checklist** (owner or trusted reviewer):
   - Open 5 random article pages in browser; verify canonical, JSON-LD, footer
   - Open 1 translated page per language; verify `lang`, `inLanguage`, hreflang, AI-generated disclosure
   - Verify `sitemap.xml` opens and parses
   - Verify `feed.xml` opens and parses
   - Check GitHub Actions history for any red runs in the last 14 days
4. **Sign-off:** Issue a GitHub Discussion or PR comment with the checklist results.
5. **Freeze:** Merge the final closeout PR; tag `v2026.05.XX` if Zenodo DOI is desired.

---

## 7. Remaining decisions for owner

These are **true owner decisions**, not implementation details. They determine scope, timing, and cost.

| # | Decision | Options | Suggested default | Consequence of delay |
|---|---|---|---|---|
| D1 | **E39c scope:** Finish only planned top-20 or expand later to top-50? | Top-20 only; or top-20 now + top-50 later | **Top-20 only for v1 freeze** | None — expansion is documented as future growth layer |
| D2 | **E39c canonical strategy:** Re-confirm Option B for full rollout? | Option B (status quo); or architect Option C | **Option B** | Blocks Batch 2 if not confirmed |
| D3 | **AI-QA tolerance threshold:** Confirm `check_translation_quality.py` strictness for E39c? | Default lenient; or `--strict` for higher bar | **Default lenient** | Blocks `--apply-approved` if threshold is undefined |
| D4 | **DeepL quota exhaustion:** If Free tier runs out mid-batch, upgrade to Pro or pause until next month? | Upgrade Pro ($5.49/mo + $25/M chars); or pause | **Pause until next month** | 1-month delay per affected batch |
| D5 | **Enable comments/Giscus?** Enable GitHub Discussions, install Giscus app, fill IDs? | Enable now; or leave disabled for v1 | **Leave disabled for v1** | None — safe to enable later |
| D6 | **Mint production DOI now or defer?** Corpus-level Zenodo DOI + per-article DOIs | Mint corpus DOI at v1 tag; or defer all | **Mint corpus DOI at v1 tag** | Citation metadata stays "pending" |
| D7 | **Deploy MCP/Ask live now or leave scaffolded?** Requires Cloudflare credentials + rate limits | Deploy now; or leave scaffolded for v2 | **Leave scaffolded for v1** | None — all code is ready |
| D8 | **Live IndexNow now or keep dry-run?** Switch `build-and-deploy.yml` from `--dry-run` | Switch to live; or keep dry-run | **Switch to live** (low risk, reversible) | Bing may index slower |
| D9 | **Treat E39 completion as archive closeout blocker or optional growth layer?** | Blocker for v1 tag; or optional post-v1 | **Optional growth layer** | If blocker, v1 freezes in ~3 months; if optional, v1 can freeze now |

---

## 8. Recommended fastest path

The fastest responsible closeout that leaves the archive in a professional, defensible, contributor-ready state:

1. **Merge B1** (this doc) immediately.
2. **Merge A4** (README stats refresh) in parallel.
3. **Owner decides D1–D9** (can be async via PR comments or Issues).
4. **If owner approves E39c continuation:**
   - Run A1 next translation at quota pace (~1 article/month).
   - Run B2–B8 automation readiness in parallel.
   - Run final audit after Track B is complete.
   - Freeze/archive as stable v1 with E39c documented as an ongoing growth layer.
5. **If owner defers E39c:**
   - Run B2–B8 in parallel.
   - Run final audit after Track B is complete.
   - Freeze/archive as stable v1 with E39c documented as a future growth layer.
6. **Post-freeze:** All optional growth items (E39c expansion, E35 full-corpus summaries, MCP deploy, Ask deploy, OG deploy, Giscus enable) live in `docs/` as documented backlog. They do not block the archive from being cited, referenced, or reused. The archive may continue receiving E39c translations at quota pace after v1 freeze.

**Why this is responsible:**
- It does not leave automation in a half-broken state.
- It does not overcommit to unapproved translation work.
- It produces a verifiable v1 artifact that academics, LLMs, and contributors can trust.
- It documents all deferred work so future agents can pick up where this closeout leaves off.

---

## Validation

Before merging the PR that adds this document, verify:

```bash
# Only planning doc changes expected
git diff -- docs/ROADMAP_CLOSEOUT_TRACKS.md ROADMAP.md

# Translation validator still passes
python3 tools/check_translations.py

# AI-QA checker still passes
python3 tools/check_translation_quality.py

# Tag normalization is clean (may take time on 829 articles)
python3 tools/normalize_tags.py --dry-run

# Citation graph is current
python3 tools/build_citation_graph.py --check

# Working tree is clean
git status --short
```

If you only add this planning doc, a full `rebuild_local.py` run is optional because no articles, metadata, or templates changed.

---

## Evidence summary

| Claim | Evidence type | Location |
|---|---|---|
| 829 articles indexed | Repo-grounded | `index.json` `"total_articles": 829` |
| E39b pilot complete | Code-reviewed, content-reviewed, test-proven | `articles/2026-04-24-eu-ai-act-conformity-assessment-guide-european-smes-202/translations.json` |
| E39c mini-pilot Batch 1 complete | Code-reviewed, content-reviewed, test-proven | `articles/2026-03-25-claude-prompt-architecture-vs-complexity-2026/translations.json` |
| AI-QA checker shipped | Code-reviewed, test-proven | `tools/check_translation_quality.py` |
| E39c plan ready | Planning artifact | `docs/E39C_ROLLOUT_PLAN.md` |
| E20a dry-run clean | CI log | `ROADMAP.md` E20a follow-ups table |
| MCP/Ask/OG deployment gated | Code-reviewed | `docs/RELEASE_EXTERNAL_READINESS.md` §7 |
| IndexNow dry-run | CI-reviewed | `docs/RELEASE_EXTERNAL_READINESS.md` §7 |
| Test suite counts | Doc reference | `docs/OPERATIONS.md` Test Suite Quick Reference |
| All workflows listed | Repo-grounded | `.github/workflows/` (13 files) |
