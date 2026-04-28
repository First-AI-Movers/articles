# Roadmap

Remaining work on the First AI Movers article archive, broken into single-session epics. Each epic is sized to ship in one focused session.

## Tag legend

- 📱 — doable from cold cloud env (this Claude Code session, no special access needed)
- 💻 — needs MacBook + accounts/devices (Search Console clicks, live-site QA, design-tool review)
- **Hybrid** — primary work is 📱; verification step is 💻

Effort (rough): **XS** = ≤30 min, **S** = ~1h, **M** = ~2h, **L** = ~4h. All are sized to fit one session.

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
| ~~E8~~ | ~~Test coverage + duplicate-title CI gate + atomic writes~~ | ✅ **Done.** Feed + JSON Feed byte-stability tests, llms-full + llms-recent byte-stability tests, XSS resistance tests (title, summary, topic intro, JSON-LD), atomic metadata writes via `tools/_atomic_io.py`, Jinja2 autoescape fix for `.j2` templates. Duplicate-title gate is implemented (`tools/check_duplicate_titles.py`) but currently **soft** (`continue-on-error: true` in CI) because 6 historical duplicate title pairs exist — see Known hardening follow-up below. | 📱 | M |
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
| ~~E12~~ | ~~GSC cross-domain verification + sitemap re-submission~~ | ✅ **Done for `articles.firstaimovers.com`.** GSC sitemap resubmitted (80 URLs discovered). Bing sitemap submitted. IndexNow key live. Search Visibility Sprint PRs A/B/C/D/#41 merged. **External platforms (Radar/Hashnode, www/Beehiiv) are paused constraints** — see External platform follow-ups below. | 💻 | S |
| ~~E13~~ | ~~Live-site QA + Lighthouse + spot-check~~ | ✅ **Done.** Key file returns 200 with exact body. IndexNow dry-run returns 80 URLs. Live IndexNow submission returned 202 (accepted). Bot checks: articles=200 for Googlebot/Bingbot; Radar=429 (Hashnode platform); www=403 to Bingbot (Beehiiv platform). Lighthouse / PageSpeed already run during sprint. | 💻 | S |

## Phase 7 — Professionalization (portfolio-grade hardening)

The first six phases delivered the archive. This phase makes the repository read as a professional, defensible, contributor-ready project: secret-scanning gates, a non-monolithic test suite + browser-level E2E, a documentation pipeline that stays current automatically, a deliberate visual layer, explicit governance for a public-but-protected repo with a documented external content-push path, and a self-hosted ingestion pipeline that retires the Make.com dependency.

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| ~~E14~~ | ~~Security tooling & supply-chain hygiene~~ | ✅ **Done.** `gitleaks` workflow on PR + push with `.gitleaks.toml` allowlist; `dependabot.yml` (weekly, pip + Actions); content scrubber `tools/scrub_presigned_urls.py` (dry-run, targets Beehiiv `<audio>` blocks with S3 presigned URLs); SECURITY.md updated with "Supported security tooling" section. Scrubber found 1 article with a presigned URL but has not been run live yet — tracked as follow-up. | 📱 | S |
| **E15a** | Unit-test refactor | Split `tools/tests/test_tools.py` (3,029 lines) into per-module test files (`test_index_build.py`, `test_sitemap.py`, `test_feed.py`, `test_llms_corpus.py`, `test_site_build.py`, `test_topic_intros.py`, `test_quick_reads.py`, `test_per_article_pages.py`, `test_atomic_io.py`, `test_normalize_tags.py`, `test_check_duplicate_titles.py`, `test_search_index.py`); shared fixtures in `conftest.py`; `tools/tests/README.md` documenting layout; CI flips from `pytest -v` to `pytest -W error -ra --tb=short`; redundancy triage. | 📱 | M |
| **E15b** | Playwright E2E suite | `tests-e2e/` with Playwright Test using `getByRole`/`getByLabel`; ~12-15 specs covering golden paths (home → topics → topic-page intro/fallback, per-article TOC + reading-time + breadcrumb, 404 noindex, theme toggle persistence, search box, feed/sitemap parse, About JSON-LD, skip-link reachability); `axe-playwright` accessibility checks; runs against built `site/` via local static server in CI; new `.github/workflows/e2e.yml` (PR + nightly); trace + HTML report artifacts on failure. | 📱 | M |
| **E16** | Documentation pipeline + dynamic docs | New `docs/` folder with `ARCHITECTURE.md` (Mermaid dataflow), `OPERATIONS.md` (runbooks), `CHANGELOG.md` (auto-built from squash-merge titles via `tools/build_changelog.py`); centralizes README/ROADMAP/ABOUT stat-patches into `tools/update_docs.py` with `<!-- BEGIN/END auto -->` markers; idempotency tested; wired into `build-and-deploy.yml` before commit. | 📱 | M |
| **E17** | Design overhaul (Pico.css + self-hosted fonts) | Vendor Pico.css under `static/vendor/` (no CDN — reproducible builds); thin custom layer keeps existing `.topic-intro` / `.quick-reads` / `.card` overrides; self-host Inter + JetBrains Mono (OFL) under `static/fonts/` (no Google Fonts call); typography rhythm fixes; `lighthouse-ci` step in CI uploading report as PR artifact (non-blocking initially); 4 Playwright `expect(page).toHaveScreenshot()` baselines (home, topic-with-intro, per-article, about) — added in E15b; `docs/DESIGN.md` documenting tokens, scale, breakpoints. | 📱 | M |
| **E18** | Governance + dual content-push paths | **(1) Repo policy:** add `LICENSE-CODE` (Apache-2.0) for `tools/`, `templates/`, `static/`, `.github/`; keep `LICENSE` (CC BY 4.0) for `articles/`; `README.md` + `CONTRIBUTING.md` updated to clarify the split (Kubernetes-style). `.github/CODEOWNERS` requiring owner approval on `/articles/`, `/tools/`, `/templates/`, `/static/`, `/.github/`. Issue templates (`bug.yml`, `content-correction.yml`, `security.yml`). Documented branch-protection rules (PR required, CI green, linear history, no force-push). **(2) External content-push (Flow B):** `.github/workflows/ingest-article.yml` listening on `repository_dispatch` event `new-article`; `tools/ingest_article.py` validates payload against new `tools/article_schema.json`, writes `articles/<slug>/{article.md,metadata.json}`, opens a PR via `peter-evans/create-pull-request@v6` (preserves "only owners merge" rule); fine-grained PAT in sender repo, `contents:write` + `actions:read` scoped to this repo only; `docs/EXTERNAL_PUBLISHING.md` with copy-pasteable payload + sender setup; round-trip test (payload fixture → ingester writes valid files → `rebuild_local.py` succeeds). **(3) Showcase polish:** README badges (article count, tests passing, license, last build, Lighthouse score), 3-line elevator pitch, screenshot, "How this works" diagram. Tag `v1.0` release with auto-generated notes from `CHANGELOG.md`. | 📱 | M |
| **E19** | Resolve duplicate-title soft gate | Editorial pass on the 6 historical duplicate title pairs (see Known hardening follow-up below) — append date or property qualifier ("… (April 2026)" / "… — Radar") per the existing recommendation. Remove `continue-on-error: true` from `Check for duplicate article titles` step in `.github/workflows/tests.yml`. Test confirming the gate is now blocking. | 📱 | XS |
| **E20a** | Self-hosted Airtable ingestion (cron, replaces Make.com) | New `tools/ingest_airtable.py` reads `AIRTABLE_PAT` / `AIRTABLE_BASE_ID` / `AIRTABLE_TABLE_NAME` from GitHub Encrypted Secrets (no Doppler — 3 secrets in 1 repo isn't worth the extra integration); uses `pyairtable` to fetch records modified in the last **72 h** via `filterByFormula=IS_AFTER(LAST_MODIFIED_TIME(), DATEADD(NOW(), -72, 'hours'))`; validates each record against `tools/article_schema.json` (schema authored in a follow-up Claude Code session with Airtable read access — schema is stable, no field churn expected); deduplicates against existing `articles/<slug>/` folders; writes new article folders only. New `.github/workflows/ingest-airtable.yml` runs `on: schedule: - cron: "17 6 * * *"` (off-peak UTC to dodge top-of-hour delays) + `on: workflow_dispatch:` for manual runs; opens a PR via `peter-evans/create-pull-request@v6`. **Auto-merge enabled** when CI is green AND the PR's diff touches only `articles/` paths (any tools/templates/.github/ mutation requires a human). On-failure step opens a GitHub Issue (label `ingest-failure`) with the workflow run URL — silent failures impossible. **Cost: $0** — public repos get unlimited free GitHub-hosted minutes. **Migration plan:** ship behind `INGEST_DRY_RUN=1` env var, run side-by-side with Make.com for 1 week, cut over, observe 14 days, delete the Make.com scenario. **Tests:** mocked-`pyairtable` unit tests, idempotency (same record twice → zero diff), schema validation (malformed record reported, not crashed on), round-trip (payload fixture survives `rebuild_local.py`). | 📱 | M |
| **E20b** | Push-based Airtable trigger (sub-second latency, optional follow-up) | Airtable automation fires on row create/edit and POSTs to `/repos/{owner}/{repo}/dispatches` with `event_type: "new-article"` and the record ID in `client_payload`. New `.github/workflows/ingest-airtable-dispatch.yml` listens on `repository_dispatch`; calls `ingest_airtable.py --record-id <id>` to fetch just that one record. Coexists with E20a: push is the fast path (seconds), cron is the safety net for missed pushes. Reuses E20a's ingester, validator, and PR-creation step — pure trigger addition. | 📱 | S |

## Phase 8 — Reach, permanence, and AI-native distribution

Phase 8 takes the archive from "professionally maintained" (Phase 7) to "forward-looking AI-native artifact": expose the corpus to AI agents directly via MCP, mint Zenodo DOIs for academic permanence, ship a small RAG embedding index for downstream LLM consumers, harden GEO/AI-citation surface, and add the human-reader polish (offline reading, comments, analytics) that signals seriousness. Each epic is independent and ships as its own PR — no bundling.

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E21** | MCP server exposing the archive | New `mcp-server/` directory: TypeScript MCP server (built on `@modelcontextprotocol/sdk`) deployed to Cloudflare Workers (free tier). Tools: `search_articles(query)`, `get_article(slug)`, `list_topics()`, `get_topic_intro(topic)`, `get_quick_reads(topic)`. Resources: each article and topic hub exposed as MCP resources. Powers Claude Code, Cursor, Continue, Zed, and any MCP-aware client to browse the archive natively. Auto-deploys via `wrangler` on `main` push. README documents the MCP endpoint URL + connection snippet for client config. **Almost no archive sites have this in 2026 — early-mover signal.** Pairs with E22 (uses the embedding index for `search_articles`). | 📱 | M |
| **E22** | RAG embedding index (Parquet + FAISS) | Nightly GitHub Actions job runs `tools/build_embeddings.py`: streams `articles/*/article.md`, generates embeddings via `bge-small-en-v1.5` (MIT-licensed, runs locally on the Actions runner — no API key), writes `embeddings.parquet` (columns: `slug`, `title`, `topic`, `published_date`, `embedding` 384-float, `summary`). Sibling artifact to `llms-full.txt` at repo root. `tools/embeddings_sample.py` demonstrates `pyarrow + faiss` retrieval in 10 lines. Powers E21's `search_articles` tool and any downstream RAG consumer. | 📱 | M |
| **E23** | Zenodo DOI + Citation File Format release pipeline | Enable Zenodo↔GitHub integration so every `v*` tag mints a DOI for that snapshot of the archive. Update `CITATION.cff` (already exists) on every release with `version`, `date-released`, and the Zenodo-issued DOI. Add a "Cite this archive" badge to README. Document citation in `docs/CITATION.md` with BibTeX, APA, and CSL JSON examples. **Transforms the repo from "GitHub project" to "academic artifact"** — citable, ORCID-linked, indexed in OpenAIRE/EOSC. | 📱 | S |
| **E24** | Privacy-respecting analytics (GoatCounter hosted free tier) | One `<script async src="https://gc.zgo.at/count.js" data-goatcounter="https://firstaimovers.goatcounter.com/count">` tag in `templates/base.html.j2`. Cookieless, ~3.5 KB script, GDPR/CCPA/PECR-compliant out of the box. Free non-commercial hosted plan — no VPS, no extra ops. Public-readable dashboard if desired. Shows which topic hubs and articles actually get traffic, evidence-basing future content choices. | 📱 | XS |
| **E25** | Wayback Machine auto-snapshots | New `.github/workflows/wayback-snapshot.yml` using the `caltechlibrary/waystation` action triggered on `release` events. Pings Internet Archive's Save Page Now for the home page, sitemap, and a sample of 5 topic hubs. Archive permanence beyond GitHub Pages SLA — even if the project ever moves, the URLs live forever in the Wayback Machine. Free. | 📱 | XS |
| **E26** | Giscus comments via GitHub Discussions | Enable Discussions on the repo; add `templates/partials/giscus.html.j2` with the Giscus `<script>` block; include it conditionally on per-article pages (`E6` output) behind a `comments_enabled: true` metadata flag. Comments stored as GitHub Discussions. Ad-free, cookie-free, requires GitHub login to comment (acceptable for technical audience). Light moderation via the Discussions UI. | 📱 | S |
| **E27** | PWA + offline reading mode | `static/sw.js` generated from a Workbox 7 build step in `tools/build_service_worker.py`. Cache-first for HTML/CSS/JS/fonts; stale-while-revalidate for `index.json` and `embeddings.parquet`. Custom offline page (`templates/offline.html.j2`). `static/manifest.webmanifest` enables "Install" on supporting browsers. Long-form articles + offline reading = real UX win for an archive. Lighthouse PWA score target: 90+. | 📱 | M |
| **E28** | GEO audit CI gate (per-article AI-citation friendliness) | New `tools/geo_audit.py` runs on PR + post-merge: per-article 0-100 score on Princeton-validated signals — single H1, sequential heading hierarchy (no h2→h4 jumps), ≥1 stat or numerical citation, ≥1 outbound source link, presence of TL;DR. Outputs `geo_audit_report.json` and a Markdown summary. Soft-gate at first (warning), upgradeable to a hard gate after baseline established. Cited tactics: ChatGPT/Perplexity/Claude all favor structured content with sources. | 📱 | S |
| **E29** | AI training-data clarity manifest | **Partially absorbed by Search Visibility Sprint** (`robots.txt` on `main` already declares 15+ explicit per-bot allow rules: GPTBot, ChatGPT-User, OAI-SearchBot, ClaudeBot, Claude-Web, anthropic-ai, PerplexityBot, Perplexity-User, Google-Extended, Bingbot, Applebot, Applebot-Extended, CCBot, etc.). Remaining E29 scope: (1) `<meta name="ai-training" content="permitted; license=CC-BY-4.0; attribution-required">` injection in `templates/base.html.j2` so all rendered pages carry it; (2) "AI Training License" header block prepended to `llms-full.txt` and `llms-recent.txt`; (3) one-paragraph rationale comment appended to `robots.txt` documenting the allow-everyone stance. Pre-positions for **EU AI Act Article 50** (Aug 2026) machine-readable disclosure requirements. | 📱 | XS |
| **E30** | Article quality CI (vale + readability + dead-link) | `vale` Markdown lint with a custom style guide under `.vale/styles/FAM/` (banned hype words, sentence length, terminology consistency). `lychee` for dead-link checking on `articles/**/article.md` + `templates/`. Flesch-Kincaid readability score per article via `tools/readability.py`. Runs on PR; warnings, not blockers. Keeps content quality consistent at scale. | 📱 | S |
| **E31** | Article series / learning-path metadata | New optional `series` (string slug) + `series_order` (int) fields in `metadata.json`. Per-article page renders a series breadcrumb chip + "Continue reading →" footer. Topic hubs gain a "Series in this topic" section above the article list. Lets multi-part frameworks (CEO Playbook, AI Roadmap, sovereign-media-engine pieces) read as a structured journey. JSON-LD `isPartOf` relation added per series. | 📱 | M |
| **E32** | *(research stub)* C2PA Content Credentials for written articles | EU AI Act Article 50 enforcement starts Aug 2026 — machine-readable AI-involvement disclosure becomes mandatory. C2PA is the de facto standard but tooling for written content is still maturing through 2026 (visual-first ecosystem; C2PA G+LAM working group white paper Feb 2026). Track the spec, revisit when CLI tools for signing Markdown manifests stabilize. **Not a build commitment yet — research-only.** | 📱 | research |
| **E33** | "Ask the archive" chatbot (proof of concept) | Single-page chat UI under `templates/ask.html.j2` POSTs to a Cloudflare Workers function (free tier, same worker as E21's MCP server). Worker performs RAG against `embeddings.parquet` (E22) for top-5 articles, then prompts a small open-weight model via Cloudflare Workers AI free allowance (Llama 3.1 8B Instruct or DeepSeek-V2 small). Per-IP rate limit via Cloudflare's free Rate Limiting Rules (e.g., 10 requests/hour). Auto-disables itself if the free-tier quota is approached. Streams answer with citations linking back to source articles. **POC scope, not production** — depends on E21 + E22 shipping first. | 📱 | M |

## Phase 9 — Top-notch curatorial layer

Phase 9 lifts the archive from "very good" (the 95th percentile after Phase 8) into the genuinely top-notch tier — academic-publishing rigor (per-article DOIs, erratum protocol), AI-citation craft (multi-length summaries, citation graph), curatorial reach (multilingual variants, custom OG images), and the multi-property pattern that prevents scope drift. Each epic ships as its own PR. **Six rows is a phase. Twenty rows is a wishlist.**

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E34** | Per-article DOIs | Extends E23 from corpus-level DOI to one DOI per article. Each `articles/<slug>/metadata.json` gains a `doi` field once minted. New `tools/mint_dois.py` calls Zenodo's REST API for any article without a DOI, deposits a record (title, author, publication date, abstract = TL;DR, license = CC BY 4.0, related-identifier pointing back to canonical_url + this archive entry), records the issued DOI back into `metadata.json`. Articles render a "Cite this article" block with BibTeX/APA/CSL JSON. Sitemap and JSON-LD pick up the DOI as `identifier` / `sameAs`. **Each article becomes individually citable in academic work** — the strongest "Wikipedia for serious AI strategy" upgrade. | 📱 | S |
| **E35** | Multi-length structured summaries | New `tools/build_summaries.py` produces three pre-computed summaries per article: 50-word (single-paragraph, ChatGPT-quote-shaped), 200-word (Claude-synthesis-shaped), 500-word (Perplexity/research-shaped). Generated via Claude Sonnet/Haiku in batches, human-reviewed via a `summaries/<slug>.review.md` workflow before commit. New fields in `metadata.json`: `summary_short`, `summary_medium`, `summary_long`. Exposed in `index.json`, JSON-LD `description`, and `llms-full.txt` headers. **AI-citation gold standard** — different platforms get the right-shaped summary served. | 📱 | M |
| **E36** | Citation graph between articles | New `tools/build_citation_graph.py` parses every `articles/*/article.md` for internal links to other articles in this archive (regex against `articles.firstaimovers.com/articles/<slug>/`, `radar.firstaimovers.com/<slug>` etc., plus topic-overlap hints). Emits `citation_graph.json` (nodes = articles, edges = "references"). Per-article page renders "References these N articles" + "Referenced by these M articles" footers. JSON-LD gains a `citation` array. Renders the archive as a scholarly resource rather than scattered blog posts. | 📱 | S |
| **E37** | Erratum / correction protocol | Articles are immutable per E18 (CONTRIBUTING invariant) — but a top-notch archive needs a published correction process. New optional `articles/<slug>/errata.md` file: timestamped, signed entries describing factual corrections, source-link updates, and (rare) retractions. Per-article page renders an `<aside class="errata">` at the bottom when present. New section in `CONTRIBUTING.md` documenting when to write erratum vs republish-as-new vs do-nothing. Tooling: `tools/check_errata.py` validates schema, `rebuild_local.py` ingests errata into the per-article HTML pages. Academic-publishing-grade. | 📱 | XS |
| **E38** | Custom OG image renderer (closes E5's empty plumbing) | Cloudflare Worker (free tier; can colocate with E21's MCP worker or run separately) renders a PNG per article on-demand from an SVG template at `https://og.firstaimovers.com/<slug>.png?topic=...&date=...&title=...`. Template includes title (auto-fitted), topic chip, published date, author byline, brand mark. Worker caches via Cloudflare's CDN (free, indefinite). E5's existing `og:image` meta-tag plumbing in templates wires up to the new endpoint per-page. Closes the social-share visual loop without local image storage. | 📱 | M |
| **E39** | Multilingual variants for top-20 articles (ES/FR/DE/NL/PT) | After E24's GoatCounter analytics establishes which articles get most traffic (~30 days of data), pick the top 20 and machine-translate to Spanish, French, German, Dutch, Portuguese — the European SME audience the writing targets. Pipeline: `tools/translate_articles.py` calls DeepL API (free tier 500K chars/month) → produces `articles/<slug>/article.{es,fr,de,nl,pt}.md` → human review on a per-language basis (could be batched per quarter). Adds `hreflang` markup, `inLanguage` JSON-LD, per-language sitemap entries. **3-10× citation reach for the highest-leverage articles, no new writing required.** | 📱 | M |
| **E40** | Multi-property archive pattern (`docs/MULTI_PROPERTY_PATTERN.md` + cookiecutter) | Documents the answer to "should I merge desapega.nl / vosnos.nl / coreventures content into this archive?" — the answer is **no, clone the tooling per brand**. Ships: (1) `docs/MULTI_PROPERTY_PATTERN.md` with rationale (topical authority, archive identity, audience fit, licensing, citation cleanliness), reference architecture diagram, fork-and-customize checklist; (2) `cookiecutter-archive-template/` directory at repo root or as a separate template repo with a stripped-down version of `tools/`, `templates/`, `static/`, `.github/` ready to scaffold a new property archive in minutes. Depends on E18 shipping (Apache-2.0 code license must be in place before the template can be cleanly forked). | 📱 | XS |

## External platform follow-ups — paused

These are **not blockers** for the article archive repo. They depend on external platforms and will be revisited during future migrations.

### Radar / Hashnode

`radar.firstaimovers.com` is hosted on Hashnode. Bot-access controls may require Hashnode support or platform-level configuration. During the Search Visibility Sprint, Radar returned **429** to both Googlebot and Bingbot. This remains parked until Hashnode support or platform settings can confirm crawler allowlisting.

### www / Beehiiv

`www.firstaimovers.com` is currently hosted on Beehiiv. Low-level bot/WAF allowlisting may not be available. During the Search Visibility Sprint, www returned **403 to Bingbot** (Googlebot returns 200). Track this for the future WordPress/Hetzner migration, where Cloudflare/WAF rules, robots.txt, sitemap, and IndexNow support must be part of the launch checklist.

## Suggested execution order

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
12. **E20a** — self-hosted Airtable cron ingestion; retires Make.com. Addresses operational pain (manual runs today).
11. **E20a** — self-hosted Airtable cron ingestion; retires Make.com. Addresses operational pain (manual runs today).
12. **E15a** — split the 3,029-line test monolith. Precondition for E15b.
13. **E15b** — Playwright E2E suite locking in everything that's shipped.
14. **E18** — governance + external content-push (Flow B via `repository_dispatch` → PR; never direct main push). Generalizes E20b's dispatch wiring.
15. **E16** — dynamic docs pipeline so the new docs from E18 stay current automatically.
16. **E20b** — optional push-based Airtable trigger for sub-second ingestion latency (reuses E18's `repository_dispatch` plumbing).
17. **E17** — design overhaul, ship last so E15b screenshot baselines stick.
18. **E28** — GEO audit CI gate (S, compounds with every new article — moved earlier from prior position #23 to maximize lifetime audited inventory).
19. **E25** — Wayback snapshots (XS, set-and-forget; ship anytime).
20. **E29** — AI-training manifest (XS, scope reduced — robots.txt half already shipped via Search Visibility Sprint; remaining: meta tag injection + llms-* header).
21. **E24** — GoatCounter analytics (XS, hosted free tier; gives traffic visibility before deeper Phase 8 work).
22. **E23** — Zenodo DOI + CITATION.cff release pipeline (S, makes the archive citable).
23. **E26** — Giscus comments (S, low-effort reader engagement).
24. **E22** — RAG embedding index (M, prerequisite for E33; standalone value for downstream RAG users).
25. **E21** — MCP server on Cloudflare Workers (M, the standout AI-native epic; uses E22 for `search_articles`).
26. **E27** — PWA offline reading (M, after E17 design baselines stick).
27. **E30** — article quality CI: vale + lychee + readability (S; ship after content tooling settles).
28. **E31** — article series / learning-path metadata (M; needs editorial decision on which articles form series).
29. **E33** — "Ask the archive" chatbot POC (M, depends on E21 + E22).
30. **E32** — *(research only)* track C2PA written-content tooling; revisit Q4 2026.
31. **E37** — erratum / correction protocol (XS, pure docs/policy; unblocks scholarly posture for later epics).
32. **E40** — multi-property pattern doc + cookiecutter template (XS, depends on E18 dual-license shipping).
33. **E36** — citation graph between articles (S, pure compute, no external deps).
34. **E34** — per-article DOIs (S, extends E23; ship after Zenodo corpus-level integration is live).
35. **E35** — multi-length structured summaries (M, batched LLM-generated + human review).
36. **E38** — custom OG image renderer on Cloudflare Workers (M, closes E5 plumbing).
37. **E39** — multilingual variants for top-20 articles (M, ship after E24 surfaces traffic data).
38. **E12 / E13** — your turn on the MacBook anytime after Phase 7 ships.

## Next development candidates

These are not committed epics yet — they are the highest-value next tracks after the Search Visibility Sprint closes. Pick one per session.

| # | Track | Why now | Size |
|---|---|---|---|
| **N1** | Duplicate-title remediation | 6 historical duplicate pairs block the CI gate from being hard. Clearing them lets `continue-on-error: true` be removed. | XS |
| **N2** | Live IndexNow workflow switch | After Bing confirms key/submission health (202 accepted), switch CI from `--dry-run` to live submission after deploy. Keep non-blocking. | XS |
| **N3** | Topic hub CTR optimization | After 2–4 weeks of GSC data, tune titles/meta for hubs with impressions but low CTR. Data-driven, not speculative. | S |
| **N4** | WordPress/Hetzner migration SEO checklist | Prepare launch checklist for `www.firstaimovers.com` migration: robots.txt, sitemap, Cloudflare bot allowlisting, IndexNow, canonical redirects. | S |
| **N5** | Archive analytics / reporting | Add simple weekly visibility snapshot artifact generated from GSC/Bing exports if data access becomes available. | M |

## Status snapshot — completed

The roadmap below is what's *remaining*. For context, here's what already shipped (22 PRs, all merged):

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

Operational state today: **829 articles**, 111 canonical topics, 77 topic hub pages, 77 curated intros, ~175 articles with TL;DR, **829 local article pages**, **258 tests** on every PR, zero-touch pipeline (Make.com push → normalize → rebuild → commit → deploy).

## Known hardening follow-up

✅ **Resolved in E19.** The duplicate-title CI gate (`tools/check_duplicate_titles.py`) is now **blocking** — `continue-on-error: true` was removed after all 6 historical pairs were disambiguated with date/property qualifiers:

| # | Original title | Disambiguation | Folders |
|---|---|---|---|
| 1 | AI Consulting in Amsterdam for European SMEs | April 2026 version got `(April 2026)` qualifier | `2026-04-03-ai-consulting-amsterdam-european-smes-1` |
| 2 | AI Readiness vs. AI Consulting | April 2026 version got `(April 2026)` qualifier | `2026-04-03-ai-readiness-vs-ai-consulting` |
| 3 | The CEO Playbook for the First 90 Days of AI Adoption | April 2026 version got `(April 2026)` qualifier | `2026-04-03-ceo-playbook-first-90-days-ai-adoption-1` |
| 4 | What GitHub's Coding Agent Changes for Product Teams | April 2026 version got `(April 2026)` qualifier | `2026-04-03-github-coding-agent-product-teams-1` |
| 5 | Why Your Company Needs a Sovereign Media Engine | Radar republication got `— Radar` qualifier | `2026-03-26-sovereign-media-engine-owned-audience-2026` |
| 6 | Your Website Is Answering the Wrong Questions | Radar republication got `— Radar` qualifier | `2026-02-09-content-strategy-funnel-architecture-guide` |
