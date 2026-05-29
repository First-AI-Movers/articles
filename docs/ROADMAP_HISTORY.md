# Roadmap history

Completed sprints, epic-by-epic completion notes, the shipped-PR snapshot, the suggested execution order, and resolved hardening follow-ups for the First AI Movers article archive.

The active roadmap lives in [`../ROADMAP.md`](../ROADMAP.md). This file is hand-maintained — it records what was done, why, and where the artifacts landed, so a future contributor can decode commit messages and PR titles without re-deriving the history from `git log`.

## Phase 1 — Content depth (highest SEO/GEO impact)

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E1~~ | ~~Topic narratives — top 10 topics~~ | ✅ **Done.** Intro + key themes + why-it-matters for the 10 highest-volume topics. | 📱 | M |
| ~~E2~~ | ~~Topic narratives — mid 25 topics~~ | ✅ **Done.** Same pattern for the next 25 topics (15-50 articles each). | 📱 | M |
| ~~E3~~ | ~~Topic narratives — final 42 topics~~ | ✅ **Done.** All 77 topic hubs with ≥5 articles now have curated intros. Remaining 34 canonical topics have <5 articles and do not render hub pages. | 📱 | M |
| ~~E4~~ | ~~Topic-page TL;DR digest blocks~~ | ✅ **Done.** "Quick reads" section on 67 of 77 topic hub pages using existing article TL;DRs only. Hidden when no TL;DRs available. | 📱 | S |

## Phase 2 — Visual & social presence

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E5~~ | ~~JSON Feed + social footer + social metadata plumbing~~ | ✅ **Done.** `/feed.json` in JSON Feed 1.1 format, visible author social-links footer (LinkedIn / podcast / YouTube), conditional `og:image` template plumbing — no generated images. | 📱 | M |

## Phase 3 — V2 site features (per-article pages)

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E6~~ | ~~Per-article HTML pages — renderer~~ | ✅ **Done.** `/articles/<slug>/` for every article. `<meta name=robots content="noindex,follow">` + `<link rel=canonical>` to external canonical. Schema.org `Article` JSON-LD per page. Raw-HTML safety audit passed. | 📱 | L |
| ~~E7~~ | ~~Per-article enhancements~~ | ✅ **Done.** Related-articles strip (topic overlap), table of contents, reading-time chip, breadcrumb. | 📱 | M |

## Phase 4 — Hardening & ops

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E8~~ | ~~Test coverage + duplicate-title CI gate + atomic writes~~ | ✅ **Done.** Feed + JSON Feed byte-stability tests, llms-full + llms-recent byte-stability tests, XSS resistance tests (title, summary, topic intro, JSON-LD), atomic metadata writes via `tools/_atomic_io.py`, Jinja2 autoescape fix for `.j2` templates. Duplicate-title gate (`tools/check_duplicate_titles.py`) is now **blocking** after E19 resolved the 6 historical pairs. | 📱 | M |
| ~~E9~~ | ~~Docs + workflow polish~~ | ✅ **Done.** `CONTRIBUTING.md`, `.github/pull_request_template.md`, `SECURITY.md`, workflow renamed to `build-and-deploy.yml`. | 📱 | S |

## Phase 5 — Optional value-add

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E10~~ | ~~Client-side internal search~~ | ✅ **Done.** JS-only fuzzy search over `index.json`. Search box on home + topics index. No backend. | 📱 | M |
| ~~E11~~ | ~~Accessibility audit + fixes~~ | ✅ **Done.** Skip link on all pages, `<main id="main-content">` landmark, visible `:focus-visible` states for links/buttons, theme toggle `aria-pressed`, breadcrumb `aria-label`, primary nav label, dark-mode muted contrast fix, `prefers-reduced-motion` support. | 📱 | S |
| *(deferred)* | Harvest canonical publisher OG images | Where canonical article pages already have OG images, harvest and reference them in archive topic pages. Requires MacBook + publisher API access. | 💻 | M |

## Phase 6 — User-side (you, on MacBook)

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E12~~ | ~~GSC cross-domain verification + sitemap re-submission~~ | ✅ **Done for `articles.firstaimovers.com`.** GSC sitemap resubmitted (80 URLs discovered). Bing sitemap submitted. IndexNow key live. Search Visibility Sprint PRs A/B/C/D/#41 merged. **External platforms (Radar/Hashnode, www/Beehiiv) are paused constraints** — see External platform follow-ups in `ROADMAP.md`. | 💻 | S |
| ~~E13~~ | ~~Live-site QA + Lighthouse + spot-check~~ | ✅ **Done.** Key file returns 200 with exact body. IndexNow dry-run returns 80 URLs. Live IndexNow submission returned 202 (accepted). Bot checks: articles=200 for Googlebot/Bingbot; Radar=429 (Hashnode platform); www=403 to Bingbot (Beehiiv platform). Lighthouse / PageSpeed already run during sprint. | 💻 | S |

## Phase 7 — Professionalization (portfolio-grade hardening)

The first six phases delivered the archive. This phase made the repository read as a professional, defensible, contributor-ready project: secret-scanning gates, a non-monolithic test suite + browser-level E2E, a documentation pipeline that stays current automatically, a deliberate visual layer, explicit governance for a public-but-protected repo with a documented external content-push path, and a self-hosted ingestion pipeline that retired the Make.com dependency.

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E14~~ | ~~Security tooling & supply-chain hygiene~~ | ✅ **Done.** `gitleaks` workflow on PR + push with `.gitleaks.toml` allowlist; `dependabot.yml` (weekly, pip + Actions); content scrubber `tools/scrub_presigned_urls.py` (dry-run, targets Beehiiv `<audio>` blocks with S3 presigned URLs); SECURITY.md updated with "Supported security tooling" section. Scrubber found 1 article with a presigned URL but has not been run live yet — tracked as follow-up. | 📱 | S |
| ~~E15a~~ | ~~Unit-test refactor~~ | ✅ **Done.** Split `tools/tests/test_tools.py` (4,188 lines) into 16 focused test files by production module; added `conftest.py` and `_fixtures.py` for shared constants; added `tools/tests/README.md`; updated CI/workflows/docs references to `pytest tools/tests`. No test logic changed, no production code changed. | 📱 | M |
| ~~E15b~~ | ~~Playwright E2E suite~~ | ✅ **Done.** 32 browser-level tests across home, topics, article pages, search, feeds/sitemap, and accessibility semantics. Runs against built `site/` via local static server. Separate `.github/workflows/e2e.yml` (PR + push + nightly). Trace + HTML report artifacts on failure. Axe-core and visual baselines deferred. | 📱 | M |
| ~~E16~~ | ~~Documentation pipeline + dynamic docs~~ | ✅ **Done.** `docs/ARCHITECTURE.md` with Mermaid dataflow diagrams; `docs/OPERATIONS.md` runbooks; `tools/build_changelog.py` generating `docs/CHANGELOG.md` (manual snapshot, not CI-generated); `tools/update_docs.py` with `<!-- BEGIN/END auto:operational-state -->` marker patching for ROADMAP.md; optional `--readme`/`--llms` flags; `--check` mode; 28 new tests. `rebuild_local.py` and `build-and-deploy.yml` untouched. | 📱 | M |
| ~~E17~~ | ~~Design overhaul~~ | ✅ **Done.** **(a) CSS polish:** spacing scale (`--space-xs` to `--space-xl`), font tokens (`--font-body`, `--font-ui`, `--font-mono`), WCAG AA accent colour (`#b5450f`), theme toggle `aria-pressed` fix, `tabindex="-1"` on `<main>` for skip-link focus, card hover state, search input icon, table overflow guard, medium breakpoint, all inline styles removed. **(b) Font system:** self-hosted Inter + JetBrains Mono (SIL OFL 1.1) under `static/fonts/` (no Google Fonts / no CDN); `@font-face` with `font-display: swap`; `docs/DESIGN.md` shipped. **(c) Visual regression:** 4 Playwright `toHaveScreenshot()` baselines (home, topic-with-intro, per-article, about) with cross-platform tolerance. **(d) Decisions:** Pico.css not vendored — custom CSS layer retained as sufficient; Lighthouse CI deferred — manual Lighthouse acceptable for release checks. | 📱 | M |
| ~~E18~~ | ~~Governance + dual content-push paths~~ | ✅ **Done.** **(1) Repo policy:** `LICENSE-CODE` (Apache-2.0) for tooling/templates/static/workflows; `README.md` + `CONTRIBUTING.md` + `SECURITY.md` updated with dual-license split. `.github/CODEOWNERS` requiring owner approval on `/articles/`, `/tools/`, `/templates/`, `/static/`, `/.github/`, `/tests-e2e/`, package files. Issue templates (`bug.yml`, `content-correction.yml`, `security.yml`). `docs/BRANCH_PROTECTION.md` documenting expected rules (PR required, CI green, linear history, no force-push). **(2) External content-push (Flow B):** `.github/workflows/ingest-article.yml` listens on `repository_dispatch` `new-article`; `tools/ingest_article.py` validates payload against `tools/article_schema.json`, writes `articles/<slug>/{article.md,metadata.json}`, opens a PR via `peter-evans/create-pull-request@v6`; optional `ARTICLE_INGESTION_PR_TOKEN` for automatic CI on ingestion PRs. `docs/EXTERNAL_PUBLISHING.md` with payload contract, example curl, sender token scopes, rollback notes. **(3) Showcase polish:** README badges (tests, E2E, code license), Mermaid "How this works" diagram, license split callout. No `v1.0` tag yet — deferred to E23/E35 pipeline maturity. | 📱 | M |
| ~~E19~~ | ~~Resolve duplicate-title soft gate~~ | ✅ **Done.** Editorial pass on the 6 historical duplicate title pairs — append date or property qualifier ("… (April 2026)" / "… — Radar") per the existing recommendation. `continue-on-error: true` removed from `Check for duplicate article titles` step in `.github/workflows/tests.yml`. Gate is now blocking. | 📱 | XS |
| ~~E20a~~ | ~~Self-hosted Airtable ingestion (cron, replaces Make.com)~~ | ✅ **Scaffold + dry-run validated.** `tools/ingest_airtable.py` reads `AIRTABLE_PAT` / `AIRTABLE_BASE_ID` / `AIRTABLE_TABLE_NAME` from GitHub Encrypted Secrets; uses `requests` to fetch records modified in the last **72 h**; validates against `tools/article_schema.json`; maps real Airtable fields (`Title`, `slug`, `Pub Date`, `GUID`, `Content HTML`, `tags`); derives missing slugs from `GUID` canonical URL; normalizes ISO timestamps to `YYYY-MM-DD`; deduplicates against existing `articles/<slug>/` folders. Workflow `.github/workflows/ingest-airtable.yml` runs on `schedule` (`17 6 * * *`) + `workflow_dispatch`; dry-run by default (`INGEST_DRY_RUN=1`); write mode gated behind repository variable. Opens PRs via `peter-evans/create-pull-request@v6`; never pushes directly to `main`. **Dry-run validated:** run 25062480810 classified 67/67 records cleanly (0 invalid, 67 skipped as existing). **Write mode remains disabled** pending controlled single-record write test approval. | 📱 | M |
| ~~E20b~~ | ~~Push-based Airtable trigger (sub-second latency, optional follow-up)~~ | ✅ **Done.** `.github/workflows/ingest-airtable-dispatch.yml` listens on `repository_dispatch` (`airtable-record-updated`) and `workflow_dispatch` (`record_id` input). Calls `tools/ingest_airtable.py --record-id <id>` to fetch a single record. Coexists with E20a: push is the fast path (seconds), cron is the safety net for missed pushes. Record ID validated in workflow (`rec` + 14+ alphanumeric). Dry-run by default (`INGEST_DRY_RUN` gating). PR via `peter-evans/create-pull-request@v6` with `ARTICLE_INGESTION_PR_TOKEN` fallback. Docs updated in `docs/airtable-ingestion.md`, `docs/EXTERNAL_PUBLISHING.md`, `SECURITY.md`, `docs/OPERATIONS.md`. 13 new workflow contract tests. | 📱 | S |

## Phase 8 — Reach, permanence, and AI-native distribution

Phase 8 took the archive from "professionally maintained" (Phase 7) to "forward-looking AI-native artifact": expose the corpus to AI agents directly via MCP, mint Zenodo DOIs for academic permanence, ship a small RAG embedding index for downstream LLM consumers, harden GEO/AI-citation surface, and add the human-reader polish (offline reading, comments, analytics) that signals seriousness. Each epic was independent and shipped as its own PR.

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E21~~ | ~~MCP server exposing the archive~~ | ✅ **Done.** `mcp-server/` directory with TypeScript MCP server on `@modelcontextprotocol/sdk` v1.26.0, stateless `WebStandardStreamableHTTPServerTransport` on `/mcp`. 5 tools (`search_articles`, `get_article`, `list_topics`, `get_topic_intro`, `get_quick_reads`) + 3 resources (`corpus`, `article`, `topic`). Lexical search with optional semantic fallback via Workers AI (`@cf/baai/bge-small-en-v1.5`). Bundled `archive-data.json` (~1.6 MB raw / 355 KB gzipped); `embeddings.json` fetched at runtime. `tools/export_mcp_data.py` generates Worker-friendly JSON from `index.json` + article Markdown. CI workflow `.github/workflows/mcp-server.yml` with type check, tests, dry-run build, and gated deployment. `docs/MCP_SERVER.md` runbook. **Deployment gated** behind `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, and `MCP_DEPLOY_ENABLED=1`. Live deployment pending credential configuration. | 📱 | M |
| ~~E22~~ | ~~RAG embedding index (Parquet + FAISS)~~ | ✅ **Done.** `tools/build_embeddings.py` generates embeddings via `BAAI/bge-small-en-v1.5` using `fastembed` (ONNX-based, no PyTorch, MIT-licensed). Input text per article: title + topics + TL;DR/summary + first 500 body chars. Writes `embeddings.parquet` (~1.97 MB for 829 articles, 384-dim float32 fixed-size list) at repo root as a sibling artifact to `llms-full.txt`. Deterministic ordering by `published_date` desc. `tools/embeddings_sample.py` demonstrates NumPy cosine-similarity retrieval in ~10 lines — FAISS deferred to v2 if scale demands it. `.github/workflows/build-embeddings.yml` triggers on `workflow_dispatch` and weekly cron (Sundays 03:17 UTC), caches model via `actions/cache`, uploads artifact, and opens PR via `create-pull-request` if parquet changes. Not required in branch protection. 23 tests in `tools/tests/test_embeddings.py` using mocked embedder + synthetic vectors; no model download in tests. Powers E21's `search_articles` and E33's RAG retrieval. | 📱 | M |
| ~~E23~~ | ~~Zenodo DOI + Citation File Format release pipeline~~ | ✅ **Done.** `CITATION.cff` hardened with `type: dataset`, `repository-code`, `abstract`, and commented DOI placeholder. `docs/CITATION.md` ships APA, BibTeX, and CSL JSON examples (before/after DOI). `docs/ZENODO_RELEASE.md` documents one-time Zenodo setup, `vYYYY.MM.DD` tag convention, release checklist, and sandbox warning. `tools/check_citation.py` validates CITATION.cff locally (no network). `.github/workflows/release-citation-check.yml` runs on `workflow_dispatch`. README Citation section links to docs and marks DOI as pending. 23 tests. No DOI minted yet — ready for first release. | 📱 | S |
| ~~E24~~ | ~~Privacy-respecting analytics~~ | ✅ **Done.** GoatCounter script with SRI-versioned `count.v5.js` and `window.goatcounter.path` override added to `templates/base.html.j2`. The override ensures local archive paths (`/articles/<slug>/`, `/topics/<slug>/`) are tracked instead of external canonical URLs. Cookieless, no fingerprinting, no cookie banner. `docs/ANALYTICS.md` documents endpoint, privacy posture, path rationale, verification, and rollback. 12 tests in `tools/tests/test_analytics.py`. Free non-commercial hosted plan. | 📱 | XS |
| ~~E25~~ | ~~Wayback Machine auto-snapshots~~ | ✅ **Done.** `tools/wayback_snapshot.py` selects 8 deterministic URLs (home, sitemap, topics index, 5 stable topic hubs) and submits to Internet Archive Save Page Now. Dry-run by default; `--submit` for live submission with polite sleep between requests. Graceful handling of timeouts, rate limits, and connection errors. `.github/workflows/wayback-snapshot.yml` triggers on `release` published and `workflow_dispatch` (manual). Not scheduled automatically in v1. Not a required check. `docs/WAYBACK.md` documents URL list, usage, and rollback. 13 tests. No credentials. No article changes. | 📱 | XS |
| ~~E26~~ | ~~Giscus comments via GitHub Discussions~~ | ✅ **Done.** `tools/comments_config.json` drives the integration with an `enabled` master switch (defaults to `false`) so the site builds safely before GitHub Discussions + Giscus app are configured. `templates/partials/giscus.html.j2` renders the official Giscus `<script>` only when enabled and both `repo_id` and `category_id` are non-empty. `templates/article.html.j2` includes the partial at the bottom of the article block. `tools/rebuild_local.py` loads the config into the Jinja2 context. No per-article metadata changes required. `docs/COMMENTS.md` documents prerequisites (enable Discussions, install Giscus app, obtain IDs), privacy posture (no local DB, no ad-tech, comments live in GitHub Discussions), and rollback. 18 tests in `tools/tests/test_comments.py`. **Blocked from enabling** until user enables GitHub Discussions, installs the Giscus app, and fills in real `repo_id`/`category_id`. | 📱 | S |
| ~~E27~~ | ~~PWA + offline reading mode~~ | ✅ **Done.** `static/manifest.webmanifest` with 192×192 and 512×512 PNG icons (`static/icons/icon-{192,512}.png`). Hand-authored `static/sw.js` (no Workbox) with precache for shell pages/CSS/JS/fonts/icons and stale-while-revalidate for `index.json`/`feed.json`. Network-first navigation with `/offline/` fallback. `static/pwa.js` registers the service worker. `templates/offline.html.j2` extends base with `noindex` and skip-link. 32 Python contract tests + 5 Playwright E2E tests. `docs/PWA.md` shipped. | 📱 | M |
| ~~E28~~ | ~~GEO audit CI gate~~ | ✅ **Done.** `tools/geo_audit.py` scores every article on six deterministic structural checks (single H1, heading hierarchy, TL;DR, outbound source link, numerical signal, metadata completeness) for a 100-point scale. Generates `geo_audit_report.json` and `geo_audit_report.md`. Baseline on 829 articles: average 65.1, pass 360, warn 191, fail 278. Top gaps: TL;DR (637 missing), single H1 (435), numeric signal (307). `.github/workflows/geo-audit.yml` runs on PR/push as a soft/non-blocking gate uploading artifact reports. `docs/GEO_AUDIT.md` documents criteria, local usage, and soft-gate policy. 27 tests. No LLM or external API calls. No article content edited. | 📱 | S |
| ~~E29~~ | ~~AI training-data clarity manifest~~ | ✅ **Done.** `<meta name="ai-training" content="permitted; license=CC-BY-4.0; attribution-required">` injected in `templates/base.html.j2` so all rendered pages carry it. "AI Training License" header block prepended to `llms-full.txt` and `llms-recent.txt` with CC BY 4.0 attribution to Dr. Hernani Costa / First AI Movers. Rationale comment appended to `robots.txt` documenting the allow-everyone stance. `docs/AI_TRAINING_POLICY.md` covers scope, attribution, license split, and bot handling. 10 tests in `tools/tests/test_ai_training_manifest.py`. Pre-positions for **EU AI Act Article 50** (Aug 2026) machine-readable disclosure requirements. | 📱 | XS |
| ~~E30~~ | ~~Article quality CI (vale + readability + dead-link)~~ | ✅ **Done.** `tools/readability.py` computes Flesch Reading Ease and Flesch-Kincaid Grade Level for every article, stripping front matter/code blocks/markdown. `.vale.ini` + `.vale/styles/FAM/{Hype,WeakPhrases,Terminology}.yml` provide conservative prose linting. `.lychee.toml` configures dead-link checking with exclusions for noisy domains (LinkedIn, Twitter/X, Hashnode). `.github/workflows/article-quality.yml` runs three parallel jobs (readability + soft Vale + soft Lychee) on PR/push/weekly cron, uploading artifacts. `docs/ARTICLE_QUALITY_CI.md` documents the soft-gate policy. 42 tests across `test_readability.py` and `test_article_quality_ci.py`. No articles edited. | 📱 | S |
| ~~E31~~ | ~~Article series / learning-path metadata~~ | ✅ **Done.** New optional `series` (string slug) + `series_order` (int) fields in `metadata.json`. Registry (`tools/series_registry.json`) + validator (`tools/check_series.py`). Per-article page renders a series chip + prev/next navigation. Topic hubs gain a "Series in this topic" section. JSON-LD `isPartOf` relation per series. **PR #100** shipped infrastructure; **PR #101** activated 2 approved series (`prompt-engineering-10-day`, `ai-model-guide-smbs-2026`) across 12 articles. Rejected/pending candidates left untouched. | 📱 | M |
| ~~E32~~ | ~~*(research stub)* C2PA Content Credentials for written articles~~ | ✅ **Done (research-only).** `docs/C2PA_RESEARCH.md` covers the C2PA spec v2.4 (Apr 2026), supported formats, EU AI Act Article 50 obligations, tooling landscape (`c2patool`, SDKs, verifiers), gap analysis for static text archives, and a decision register. `docs/decisions/adr-001-c2pa-content-credentials.md` records the formal decision to **defer** adoption: no signing, no manifests, no dependencies, no article/template changes. `tools/tests/test_c2pa_research.py` enforces the research-only constraint with 17 governance tests. Pointers added to `docs/OPERATIONS.md` and `CONTRIBUTING.md`. Revisit no earlier than 2 Aug 2026 or when CLI tooling for Markdown/HTML manifests stabilises. | 📱 | research |
| ~~E33~~ | ~~"Ask the archive" chatbot (proof of concept)~~ | ✅ **POC scaffold shipped.** `POST /api/ask` on the E21 MCP Worker validates requests, retrieves articles via lexical search, builds a citation-required prompt, and calls Workers AI (`@cf/meta/llama-3.1-8b-instruct`) when binding is available. Static `/ask/` page with accessible form, loading/error/answer/citations states, and graceful fallback when endpoint is unavailable. **PR #103** shipped backend, frontend, build integration, E2E tests, and docs. **Live deployment deferred** pending Cloudflare credentials (`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`) and rate-limit setup. Semantic retrieval compatibility with E22 embeddings unverified without live deployment; lexical search is v1 default. | 📱 | M |

## Phase 9 — Top-notch curatorial layer

Phase 9 lifted the archive from "very good" (the 95th percentile after Phase 8) into the genuinely top-notch tier — academic-publishing rigor (per-article DOIs, erratum protocol), AI-citation craft (multi-length summaries, citation graph), curatorial reach (multilingual variants, custom OG images), and the multi-property pattern that prevents scope drift. Each epic shipped as its own PR.

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E34~~ | ~~Per-article DOIs~~ | ✅ **Done as infrastructure.** Optional `doi` field support, dry-run/sandbox-capable `tools/mint_dois.py`, Zenodo bucket upload flow, article snapshot generation, DOI-only citation rendering, and JSON-LD DOI fields shipped in **PR #112**. No production DOI records minted; production minting requires explicit Zenodo approval and permanent-DOI flag. | 📱 | S |
| ~~E35~~ | ~~Multi-length structured summaries — infrastructure + pilot~~ | ✅ **E35a infrastructure done in PR #114.** Optional `summary_short`, `summary_medium`, `summary_long`, `summary_reviewed_at`, `summary_model` fields in `metadata.json` and `article_schema.json`. `tools/build_summaries.py` with mock/anthropic/openai/manual providers, `--dry-run` (default), `--write-review-files`, `--apply-approved`, `--allow-partial`, and `--allow-network` safety gate. Human review workflow via `summaries/<slug>.review.md` (draft → approved). Build integration: `index.json` passthrough, JSON-LD `description`, `llms-full.txt` headers. 30 tests. `docs/SUMMARIES.md` shipped. **E35b reviewed pilot done in PR #116.** 5 representative articles received approved summaries: EU AI Act Conformity Assessment, The European CEO's 12-Month AI Agenda, Agentic AI for European SME Operators, Stop Making Claude Prompts More Complicated Than the Work, and Why Your Company Needs a Sovereign Media Engine. 5 approved review files committed. No article bodies edited. Full-corpus rollout remains pending separate approval. | 📱 | M |
| ~~E36~~ | ~~Citation graph between articles~~ | ✅ **Done.** New `tools/build_citation_graph.py` parses every `articles/*/article.md` for internal links to other articles in this archive (regex against `articles.firstaimovers.com/articles/<slug>/`, `radar.firstaimovers.com/<slug>` etc., plus topic-overlap hints). Emits `citation_graph.json` (nodes = articles, edges = "references"). Per-article page renders "References these N articles" + "Referenced by these M articles" footers. JSON-LD gains a `citation` array. Renders the archive as a scholarly resource rather than scattered blog posts. | 📱 | S |
| ~~E37~~ | ~~Erratum / correction protocol~~ | ✅ **Done.** Optional `articles/<slug>/errata.md` with timestamped, signed entries (correction, clarification, source-update, retraction, editorial-note). `tools/check_errata.py` validates schema. `rebuild_local.py` ingests published entries into per-article HTML pages as `<aside class="errata">`. Draft entries are validated but not rendered. New docs in `docs/ERRATA.md` and `CONTRIBUTING.md`. **PR #105** shipped validator, rendering, docs, tests, and CI integration. No real errata added to historical articles. | 📱 | XS |
| ~~E38~~ | ~~Custom OG image renderer (closes E5's empty plumbing)~~ | ✅ **Done as scaffold/integration.** PR #118 added `og-worker/` (Cloudflare Worker with Hono, SVG template rendering, input validation, XML escaping, and CDN caching), disabled-by-default `tools/og_config.json`, article/topic OG template wiring in `templates/article.html.j2` and `templates/topic.html.j2`, and 7 Python integration tests plus 26 TypeScript worker tests. Current output is **SVG primary**; PNG via `@resvg/resvg-wasm` remains wired in `src/render.ts` but not enabled pending runtime verification. Bundle: 87.47 KiB raw / 21.52 KiB gzipped. No live deployment or DNS changes yet. | 📱 | M |
| ~~E40~~ | ~~Multi-property archive pattern (`docs/MULTI_PROPERTY_PATTERN.md` + cookiecutter)~~ | ✅ **Done.** `docs/MULTI_PROPERTY_PATTERN.md` documents the rationale (topical authority, canonical clarity, citation/license cleanliness, LLM ingestion, analytics isolation) and includes a 12-item fork-and-customize checklist. `cookiecutter-archive-template/` at repo root provides a minimal starter with sample article, basic templates, static assets, build tooling stubs, CI workflows, and license split (CC BY 4.0 / Apache-2.0). Template intentionally omits mature features (MCP, chatbot, embeddings, PWA, comments, analytics, DOI, errata, series, quality CI). **PR #107** shipped pattern doc, template scaffold, docs updates, and 25 tests. No external property content migrated. | 📱 | XS |

E39 (multilingual variants) is still active in the growth layer; see [`../ROADMAP.md`](../ROADMAP.md#active-multilingual-rollout-e39c).

## Suggested execution order (as completed)

1. ~~E1 → E2 → E3 → E4~~ — ✅ **Phase 1 complete.** All 77 topic hub pages have curated intros; 67 have Quick reads.
2. ~~E5~~ — JSON Feed + social footer + OG image plumbing. ✅ Done.
3. ~~E6~~ — per-article HTML pages renderer. ✅ Done.
4. ~~E7~~ — per-article enhancements (related articles, TOC, reading time, breadcrumbs). ✅ Done.
5. ~~E8~~ — test coverage + duplicate-title gate + atomic writes. ✅ Done.
6. ~~E9~~ — docs + workflow polish. ✅ Done.
7. ~~E10~~ — client-side internal search. ✅ Done.
8. ~~E11~~ — accessibility audit + fixes. ✅ Done.
9. ~~E12 → E13~~ — Search visibility setup for `articles.firstaimovers.com`. ✅ Done. External platforms paused.
10. ~~E14~~ — security tooling + supply-chain hygiene. ✅ Done.
11. ~~E19~~ — resolve duplicate-title soft gate. ✅ Done.
12. ~~E20a~~ — self-hosted Airtable cron ingestion; retires Make.com. ✅ **Scaffold + dry-run validated.** Write mode disabled pending controlled single-record write test.
13. ~~E15a~~ — split the test monolith. ✅ Done.
14. ~~E15b~~ — Playwright E2E suite locking in everything that's shipped. ✅ Done.
15. ~~E18~~ — governance + external content-push (Flow B via `repository_dispatch` → PR; never direct main push). ✅ Done.
16. ~~E16~~ — dynamic docs pipeline so the new docs from E18 stay current automatically. ✅ Done.
17. ~~E20b~~ — optional push-based Airtable trigger for sub-second ingestion latency (reuses E18's `repository_dispatch` plumbing). ✅ Done.
18. ~~E17~~ — design overhaul, ship last so E15b screenshot baselines stick. ✅ Done.
19. ~~E28~~ — GEO audit CI gate (S, compounds with every new article — moved earlier from prior position #23 to maximize lifetime audited inventory). ✅ Done.
20. ~~E25~~ — Wayback snapshots (XS, set-and-forget; ship anytime). ✅ Done.
21. ~~E29~~ — AI-training manifest. ✅ Done.
22. ~~E24~~ — GoatCounter analytics. ✅ Done.
23. ~~E23~~ — Zenodo DOI + CITATION.cff release pipeline. ✅ Done.
24. ~~E26~~ — Giscus comments. ✅ Done.
25. ~~E22~~ — RAG embedding index. ✅ Done.
26. ~~E21~~ — MCP server on Cloudflare Workers. ✅ **Scaffold shipped; deployment gated pending Cloudflare credentials.**
27. ~~E27~~ — PWA offline reading. ✅ Done.
28. ~~E30~~ — article quality CI: vale + lychee + readability. ✅ Done.
29. ~~E31~~ — article series / learning-path metadata. ✅ Done. Infrastructure PR #100; activation PR #101.
30. ~~E33~~ — "Ask the archive" chatbot POC. ✅ POC scaffold shipped in PR #103. Live deployment deferred pending Cloudflare credentials + rate-limit setup.
31. ~~E37~~ — erratum / correction protocol. ✅ Done. PR #105.
32. ~~E40~~ — multi-property pattern doc + cookiecutter template. ✅ Done. PR #107.
33. ~~E36~~ — citation graph between articles. ✅ Done.*
34. ~~E32~~ — *(research only)* C2PA research note + deferred ADR. ✅ Done.
35. ~~E34~~ — per-article DOIs infrastructure. ✅ Done in PR #112.
36. ~~E35~~ — multi-length structured summaries (M, batched LLM-generated + human review). ✅ E35a infrastructure in PR #114; E35b 5-article reviewed pilot in PR #116. Full-corpus rollout pending separate approval.
37. ~~E38~~ — custom OG image renderer on Cloudflare Workers (M, closes E5 plumbing). ✅ Done in PR #118.
38. **E39** — multilingual variants. **E39b pilot (1 article × 5 languages) done in PR #123** (human-reviewed). **E39c mini-pilot Batch 1 done in PR #129** (1 article × 5 languages, DeepL + AI-QA). E39c top-20 rollout remains pending (awaits traffic data or citation-graph fallback).
39. **E12 / E13** — owner-side, anytime after Phase 7 shipped.

## Completed "Next" candidates

| # | Track | Outcome |
|---|---|---|
| ~~N1~~ | ~~Duplicate-title remediation~~ | ✅ **Done in E19.** 6 historical pairs disambiguated; gate is now blocking. |
| ~~N2~~ | ~~Live IndexNow workflow switch~~ | ✅ **Done.** PR #178 flipped `.github/workflows/build-and-deploy.yml` from `submit_indexnow.py --dry-run` to live submission; job depends on `deploy` and remains `continue-on-error: true`. **Live verified 2026-05-15** (run [25928942642](https://github.com/First-AI-Movers/articles/actions/runs/25928942642) on `main @ 608d728`): `IndexNow: submitted 80 URLs → 200 https://api.indexnow.org/indexnow` at `16:27:08Z`. Key not logged. `tools/tests/test_workflows_ci_audit.py::test_indexnow_step_does_not_use_dry_run` + `test_indexnow_step_is_non_blocking` both pass. |
| ~~N6~~ | ~~Scope docs-only workflow skips~~ | ✅ **Done.** PR #183 scoped the `paths-ignore` on `article-quality.yml`, `e2e.yml`, and `geo-audit.yml` so article markdown changes still trigger the heavy gates while pure-docs `.md` edits continue to skip. PR #184 hardened the N6 required-check context. Surfaced during N2 verification 2026-05-15. |

## E41 shipped rows

The E41 epic is the staged rollout of autonomous Airtable publishing. Rows below are the shipped sub-letters; pending design (E41c) and dry-run implementation (E41d) live in [`../ROADMAP.md`](../ROADMAP.md#e41--autonomous-airtable-publishing-post-v1).

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E41a~~ | ~~Airtable status mapping fix + write-mode plan~~ | ✅ **Done** in PR #147. Field map updated `Status` → `FAIM Status`; 7 new tests; `docs/AUTONOMOUS_AIRTABLE_PUBLISHING_PLAN.md` shipped. | 📱 | XS |
| ~~E41a'~~ | ~~Posted-only gate + cron token-fallback~~ | ✅ **Done** in PR #148. `ALLOWED_STATUSES = {"posted"}`; status normalized to lowercase on write; cron uses `ARTICLE_INGESTION_PR_TOKEN \|\| GITHUB_TOKEN`. | 📱 | XS |
| ~~E41a''~~ | ~~rebuild_local funnel-None coercion~~ | ✅ **Done** in PR #149. Discovered when first ingestion run crashed sorting `{None: 1, "top": 5}.items()`. Fix at aggregation + sort site; 2 regression tests. | 📱 | XS |
| ~~E41a'''~~ | ~~update_docs.py runs before pytest~~ | ✅ **Done** in PR #150. Both ingestion workflows now patch ROADMAP marker between rebuild and pytest. | 📱 | XS |
| ~~E41a''''~~ | ~~ROADMAP.md added to ingestion add-paths~~ | ✅ **Done** in PR #153. The in-runner ROADMAP patch now reaches the generated PR. | 📱 | XS |
| ~~E41b~~ | ~~Controlled single-record write test~~ | ✅ **Done** 2026-05-03 in PR #154. First autonomous Airtable→PR→CI→merge ingestion (`rec6nsPU1kHTcKYXF`, 829 → 830). Pipeline proven; incident #151 (PAT scope) opened then resolved. | 📱 | XS |
| ~~E41e~~ | ~~Bounded daily cron write mode + incident logging~~ | ✅ **Done.** `INGEST_MAX_RECORDS` (default 20) + `INGEST_MAX_CREATED` (default 5) cap each cron run. `--max-created` added to `tools/ingest_airtable.py` with 5 new tests. Incident-issue step on cron-write failure. | 📱 | S |
| ~~E41g~~ | ~~List-fetch sort by `Date Added` desc (issue #164)~~ | ✅ **Done.** `_fetch_records` adds `sort[0][field]=Date Added&sort[0][direction]=desc` so newly-added Posted records cannot be hidden behind the lexically-oldest 20 record IDs that re-saves keep refreshing. Record-id dispatch path unaffected. 8 new tests. | 📱 | XS |
| ~~E41f~~ | ~~Gated auto-merge for ingestion PRs~~ | ✅ **Done.** `tools/auto_merge_ingestion_pr.py` runs after PR-create. Verifies branch prefix `ingest/airtable-`, exact PR title, file allowlist, mergeability, and required-check success. Squash-merges on pass; opens `E41 auto-merge blocked` issue on any block. Default OFF via `AUTO_MERGE_INGESTION_PRS=0`. 49 unit tests. | 📱 | S |
| ~~E41h~~ | ~~Skip PR creation when no articles created~~ | ✅ **Done.** `tools/ingest_airtable.py` emits `ingest-summary.json`; workflow gates rebuild/PR/auto-merge on `created != '0'`. Eliminates daily noise PRs (incident: PR #169). 13 new tests. | 📱 | XS |

**Closeout PRs:** #137 E39c re-scope, #138 artifact drift check, #139 release readiness, #141 AI-QA wording restore, #142 security review, #143 CI/Pages proof, #144 final audit harness, #145 archive v1 freeze.

## Status snapshot — completed PRs (chronological)

What already shipped (22 PRs through the v1 build, all merged):

- **PR #2** Auto-rebuild CI workflow
- **PR #3** Sitemap canonical fix (per-article canonical, allowlist)
- **PR #4** Atom feed (`/feed.xml`)
- **PR #5** `llms-full.txt` (full corpus)
- **PR #6** Firecrawl orphan cleanup
- **PR #7** Tooling consolidation + tests CI
- **PR #8** Tag normalization (3,686 raw tags → 102 canonical topics) + static site v1 (75 topic hubs)
- **PR #9** SEO + GEO + security audit follow-up (14 fixes including jinja2 CVE pin, robots.txt LLM opt-in, BreadcrumbList, 107 metadata whitespace cleanups)
- **PR #10** `llms-recent.txt` (30-day rolling slice)
- **PR #11** Topic narratives E2 — mid 25 topics
- **PR #12** Topic narratives E3 — final 42 topics
- **PR #13** Topic narratives E3 — final 42 topic intros (continuation)
- **PR #14** Topic-page Quick reads E4 — TL;DR digest blocks
- **PR #16** JSON Feed (`/feed.json`) + social footer + `og:image` template plumbing — E5
- **PR #18** Per-article HTML pages renderer + raw-HTML safety audit — E6
- **PR #19** ROADMAP cleanup + raw-HTML sanitizer follow-up
- **PR #20** Dark mode default + light toggle
- **PR #21** Per-article enhancements: TOC, reading time, breadcrumbs, related articles — E7
- **PR #23** E8 archive hardening: duplicate-title gate, atomic writes, feed/LLMS byte-stability tests, XSS coverage, Jinja2 autoescape fix — E8
- **PR #25** E9 workflow polish: `CONTRIBUTING.md`, `SECURITY.md`, PR template, workflow rename — E9
- **PR #27** E11 accessibility polish: skip link, focus states, theme toggle semantics, breadcrumb labels — E11
- **PR #29** E10 client-side search: vanilla-JS search over `index.json`, search box on home + topics index, 16 tests — E10
- **PR #32** Search Visibility Sprint A — sitemap cleanup: removed 702 cross-host canonicals and 10 data files; sitemap now 80 URLs
- **PR #33** Search Visibility Sprint B — IndexNow integration: key file, `tools/submit_indexnow.py`, CI dry-run step, 12 tests
- **PR #36** Search Visibility Sprint C — topic hub SEO/GEO: CollectionPage JSON-LD, per-topic lastmod, article→hub links, 9 tests
- **PR #37** Search Visibility Sprint D — monitoring docs: `docs/search-visibility-monitoring.md`
- **PR #41** IndexNow env migration: moved keys from committed `.indexnow-key` to Doppler/GitHub secret `INDEXNOW_API_KEY_ARTICLES_FAIM`, host-aware tooling, 17 tests
- **PR #43** E14 security tooling: gitleaks workflow + `.gitleaks.toml`, Dependabot config, content scrubber, SECURITY.md updates, 10 tests
- **PR #55** E19 duplicate-title remediation: disambiguated 6 historical pairs, removed `continue-on-error: true`, gate is now blocking
- **PR #58** E20a scaffold: `tools/ingest_airtable.py`, `tools/article_schema.json`, `.github/workflows/ingest-airtable.yml`, `docs/airtable-ingestion.md`, `TestAirtableIngestion` (17 tests)
- **PR #60** E20a field mapping fix: real Airtable fields (`slug`, `Pub Date`, `GUID`, `Content HTML`, `tags`), date normalization, `--allow-no-status-gate` in dry-run only
- **PR #61** E20a slug derivation: `_slug_from_canonical_url()` fallback when Airtable `slug` is missing, 7 new tests
- **PR #63** E15a unit-test refactor: split 4,188-line monolith into 16 focused test files; added `conftest.py`, `_fixtures.py`, `tools/tests/README.md`
- **PR #65** E15b Playwright E2E suite: 32 browser tests, `tests-e2e/` specs, `playwright.config.ts`, `.github/workflows/e2e.yml`, `package.json`
- **PR #67** E18 governance + external publishing: `LICENSE-CODE`, `.github/CODEOWNERS`, issue templates, `docs/BRANCH_PROTECTION.md`, `docs/EXTERNAL_PUBLISHING.md`, `tools/ingest_article.py`, `.github/workflows/ingest-article.yml`, 27 new tests
- **PR #69** E16 documentation pipeline + dynamic docs: `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`, `tools/build_changelog.py`, `docs/CHANGELOG.md`, `tools/update_docs.py`, ROADMAP.md `auto:operational-state` marker, 28 new tests
- **PR #71** E20b Airtable dispatch trigger: `.github/workflows/ingest-airtable-dispatch.yml`, `tools/tests/test_airtable_dispatch.py`, docs updates across `airtable-ingestion.md`, `EXTERNAL_PUBLISHING.md`, `SECURITY.md`, `OPERATIONS.md`
- **PR #89** E26: Giscus comments scaffold (disabled by default)
- **PR #90** E26 closure: mark Giscus comments as done in ROADMAP
- **PR #91** E22: RAG embedding index (`tools/build_embeddings.py`, `embeddings.parquet`, `tools/embeddings_sample.py`, `.github/workflows/build-embeddings.yml`, 23 tests)
- **PR #92** E22 closure: mark RAG embedding index as done in ROADMAP
- **PR #93** E21: MCP server on Cloudflare Workers (`mcp-server/` TypeScript scaffold, 5 tools + 3 resources, `tools/export_mcp_data.py`, `.github/workflows/mcp-server.yml`, `docs/MCP_SERVER.md`, 30 tests)
- **PR #96** E27: PWA offline reading mode (`static/manifest.webmanifest`, `static/icons/icon-{192,512}.png`, hand-authored `static/sw.js`, `static/pwa.js`, `templates/offline.html.j2`, `tools/build_pwa_icons.py`, `docs/PWA.md`, 32 Python tests + 5 Playwright E2E tests)
- **PR #98** E30: Article quality CI (`tools/readability.py`, `.vale.ini` + `.vale/styles/FAM/`, `.lychee.toml`, `.github/workflows/article-quality.yml`, `docs/ARTICLE_QUALITY_CI.md`, 42 tests)

## Hardening follow-up — resolved in E19

The duplicate-title CI gate (`tools/check_duplicate_titles.py`) is now **blocking** — `continue-on-error: true` was removed after all 6 historical pairs were disambiguated with date/property qualifiers:

| # | Original title | Disambiguation | Folders |
|---|---|---|---|
| 1 | AI Consulting in Amsterdam for European SMEs | April 2026 version got `(April 2026)` qualifier | `2026-04-03-ai-consulting-amsterdam-european-smes-1` |
| 2 | AI Readiness vs. AI Consulting | April 2026 version got `(April 2026)` qualifier | `2026-04-03-ai-readiness-vs-ai-consulting` |
| 3 | The CEO Playbook for the First 90 Days of AI Adoption | April 2026 version got `(April 2026)` qualifier | `2026-04-03-ceo-playbook-first-90-days-ai-adoption-1` |
| 4 | What GitHub's Coding Agent Changes for Product Teams | April 2026 version got `(April 2026)` qualifier | `2026-04-03-github-coding-agent-product-teams-1` |
| 5 | Why Your Company Needs a Sovereign Media Engine | Radar republication got `— Radar` qualifier | `2026-03-26-sovereign-media-engine-owned-audience-2026` |
| 6 | Your Website Is Answering the Wrong Questions | Radar republication got `— Radar` qualifier | `2026-02-09-content-strategy-funnel-architecture-guide` |

## 2026-05 maintenance + hardening session

A focused session merged 10 small PRs aimed at operational hygiene and Node.js 24 readiness ahead of the 2026-06-02 runner cutover:

- **#187** — `peter-evans/create-pull-request` v6 → v8. Also resolved the upstream "Duplicate header: Authorization" regression that had broken the May 21–27 cron-write cluster.
- **#186** — `actions/setup-node` v4 → v6 (Node 24 runtime).
- **#185** — `actions/upload-artifact` v4 → v7 (Node 24 runtime). Verified that every consuming workflow uses a unique artifact name per job, so v5+ per-name immutability does not break any existing upload pattern.
- **#188** — `actions/cache` v4 → v5 (Node 24 runtime).
- **#203** — Auto-close stale `E41 cron ingestion incident:` issues on the next successful schedule-triggered cron-write run. The step is gated on `success() && env.INGEST_DRY_RUN != '1' && github.event_name == 'schedule'` so dry-runs and `workflow_dispatch` runs never touch incident state.
- **#204** — Hardened `.github/workflows/ingest-article.yml`. The `repository_dispatch` payload now flows through `env: CLIENT_PAYLOAD_JSON` and is parsed in a single-quoted Python heredoc — the dispatch payload is no longer interpolated into a shell command string.
- **#200** — `openai` Python range bump (`>=2.36.0` → `>=2.38.0`). The repo's `_provider_openai` is a documented stub gated behind a CLI flag; this is a metadata-only update.
- **#190** — `Pillow` range bump (`>=10.0.0` → `>=12.2.0`). Used only by `tools/build_pwa_icons.py` (as a `cairosvg`-unavailable fallback) and `tools/tests/test_pwa.py`. Stable `Image.new` / `ImageDraw.Draw` / `Image.open` APIs unchanged.
- **#199** — `numpy` range bump (`>=2.0.0` → `>=2.4.6`). Direct usage lives only in `tools/embeddings_sample.py` and `tools/tests/test_embeddings.py` with deterministic-seed RNG; the passing pytest suite under the new pin is the behavioral verification.
- **#208** — Generated-artifacts drift check now skips PRs whose only changed files are `tools/requirements.txt`, `.github/workflows/<name>.yml`, or `.github/dependabot.yml`. Any other path still runs the full drift check, and every push to `main` runs it unconditionally. An audit test extracts the literal allowlist regex and asserts it equals exactly that set, so any future broadening forces an explicit safety review.
