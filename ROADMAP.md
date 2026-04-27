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
| **E12** | GSC cross-domain verification + sitemap re-submission | Verify 5 hosts (articles / radar / www / insights / voices) under one Search Console property; add `Sitemap:` line to robots.txt on each canonical site you control; resubmit `/sitemap.xml`. | 💻 | S |
| **E13** | Live-site QA + Lighthouse + spot-check | Open articles.firstaimovers.com on phone & laptop; Lighthouse / PageSpeed run; review 5 topic hubs for content quality; check social-share previews after E5 ships. | 💻 | S |

## Phase 7 — Professionalization (portfolio-grade hardening)

The first six phases delivered the archive. This phase makes the repository read as a professional, defensible, contributor-ready project: secret-scanning gates, a non-monolithic test suite + browser-level E2E, a documentation pipeline that stays current automatically, a deliberate visual layer, and explicit governance for a public-but-protected repo with a documented external content-push path.

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E14** | Security tooling & supply-chain hygiene | `gitleaks` action on PR + push with `.gitleaks.toml` allowlist for documented placeholders; `dependabot.yml` (weekly, pip + Actions); GitHub native secret-scanning + push-protection enabled; one-shot content scrub `tools/scrub_presigned_urls.py` (idempotent, replaces beehiiv `<audio>` blocks containing third-party presigned URLs); appended "Supported security tooling" section in `SECURITY.md`; gitleaks dry-run test against a known-bad fixture. **No history rewrite** — repository scan was clean for real secrets. | 📱 | S |
| **E15a** | Unit-test refactor | Split `tools/tests/test_tools.py` (3,029 lines) into per-module test files (`test_index_build.py`, `test_sitemap.py`, `test_feed.py`, `test_llms_corpus.py`, `test_site_build.py`, `test_topic_intros.py`, `test_quick_reads.py`, `test_per_article_pages.py`, `test_atomic_io.py`, `test_normalize_tags.py`, `test_check_duplicate_titles.py`, `test_search_index.py`); shared fixtures in `conftest.py`; `tools/tests/README.md` documenting layout; CI flips from `pytest -v` to `pytest -W error -ra --tb=short`; redundancy triage. | 📱 | M |
| **E15b** | Playwright E2E suite | `tests-e2e/` with Playwright Test using `getByRole`/`getByLabel`; ~12-15 specs covering golden paths (home → topics → topic-page intro/fallback, per-article TOC + reading-time + breadcrumb, 404 noindex, theme toggle persistence, search box, feed/sitemap parse, About JSON-LD, skip-link reachability); `axe-playwright` accessibility checks; runs against built `site/` via local static server in CI; new `.github/workflows/e2e.yml` (PR + nightly); trace + HTML report artifacts on failure. | 📱 | M |
| **E16** | Documentation pipeline + dynamic docs | New `docs/` folder with `ARCHITECTURE.md` (Mermaid dataflow), `OPERATIONS.md` (runbooks), `CHANGELOG.md` (auto-built from squash-merge titles via `tools/build_changelog.py`); centralizes README/ROADMAP/ABOUT stat-patches into `tools/update_docs.py` with `<!-- BEGIN/END auto -->` markers; idempotency tested; wired into `build-and-deploy.yml` before commit. | 📱 | M |
| **E17** | Design overhaul (Pico.css + self-hosted fonts) | Vendor Pico.css under `static/vendor/` (no CDN — reproducible builds); thin custom layer keeps existing `.topic-intro` / `.quick-reads` / `.card` overrides; self-host Inter + JetBrains Mono (OFL) under `static/fonts/` (no Google Fonts call); typography rhythm fixes; `lighthouse-ci` step in CI uploading report as PR artifact (non-blocking initially); 4 Playwright `expect(page).toHaveScreenshot()` baselines (home, topic-with-intro, per-article, about) — added in E15b; `docs/DESIGN.md` documenting tokens, scale, breakpoints. | 📱 | M |
| **E18** | Governance + dual content-push paths | **(1) Repo policy:** add `LICENSE-CODE` (Apache-2.0) for `tools/`, `templates/`, `static/`, `.github/`; keep `LICENSE` (CC BY 4.0) for `articles/`; `README.md` + `CONTRIBUTING.md` updated to clarify the split (Kubernetes-style). `.github/CODEOWNERS` requiring owner approval on `/articles/`, `/tools/`, `/templates/`, `/static/`, `/.github/`. Issue templates (`bug.yml`, `content-correction.yml`, `security.yml`). Documented branch-protection rules (PR required, CI green, linear history, no force-push). **(2) External content-push (Flow B):** `.github/workflows/ingest-article.yml` listening on `repository_dispatch` event `new-article`; `tools/ingest_article.py` validates payload against new `tools/article_schema.json`, writes `articles/<slug>/{article.md,metadata.json}`, opens a PR via `peter-evans/create-pull-request@v6` (preserves "only owners merge" rule); fine-grained PAT in sender repo, `contents:write` + `actions:read` scoped to this repo only; `docs/EXTERNAL_PUBLISHING.md` with copy-pasteable payload + sender setup; round-trip test (payload fixture → ingester writes valid files → `rebuild_local.py` succeeds). **(3) Showcase polish:** README badges (article count, tests passing, license, last build, Lighthouse score), 3-line elevator pitch, screenshot, "How this works" diagram. Tag `v1.0` release with auto-generated notes from `CHANGELOG.md`. | 📱 | M |
| **E19** | Resolve duplicate-title soft gate | Editorial pass on the 6 historical duplicate title pairs (see Known hardening follow-up below) — append date or property qualifier ("… (April 2026)" / "… — Radar") per the existing recommendation. Remove `continue-on-error: true` from `Check for duplicate article titles` step in `.github/workflows/tests.yml`. Test confirming the gate is now blocking. | 📱 | XS |

## Suggested execution order

1. ~~E1 → E2 → E3 → E4~~ — ✅ **Phase 1 complete.** All 77 topic hub pages have curated intros; 67 have Quick reads.
2. ~~E5~~ — JSON Feed + social footer + OG image plumbing. ✅ Done.
3. ~~E6~~ — per-article HTML pages renderer. ✅ Done.
4. ~~E7~~ — per-article enhancements (related articles, TOC, reading time, breadcrumbs). ✅ Done.
5. ~~E8~~ — test coverage + duplicate-title gate + atomic writes. ✅ Done.
6. ~~E9~~ — docs + workflow polish. ✅ Done.
7. ~~E10~~ — client-side internal search. ✅ Done.
8. ~~E11~~ — accessibility audit + fixes. ✅ Done.
9. **E14** — security tooling + supply-chain hygiene (cheap; gates the contributor surface E18 will widen).
10. **E19** — clear the duplicate-title soft gate so `pytest -W error` from E15a can land cleanly.
11. **E15a** — split the 3,029-line test monolith. Precondition for E15b.
12. **E15b** — Playwright E2E suite locking in everything that's shipped.
13. **E18** — governance + external content-push (Flow B via `repository_dispatch` → PR; never direct main push).
14. **E16** — dynamic docs pipeline so the new docs from E18 stay current automatically.
15. **E17** — design overhaul, ship last so E15b screenshot baselines stick.
16. **E12 / E13** — your turn on the MacBook anytime after Phase 7 ships.

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

Operational state today: 819 articles, 111 canonical topics, 77 topic hub pages, 77 curated intros, ~175 articles with TL;DR, **819 local article pages**, **222 tests** on every PR, zero-touch pipeline (Make.com push → normalize → rebuild → commit → deploy).

## Known hardening follow-up

The duplicate-title CI gate (`tools/check_duplicate_titles.py`) currently runs with `continue-on-error: true` because 6 historical duplicate title pairs exist. All 6 are **different articles with the same title** (not genuine duplicate content), so the fix requires an editorial decision to disambiguate titles.

| # | Duplicate title | Folders | Dates | Canonical hosts | Classification |
|---|---|---|---|---|---|
| 1 | AI Consulting in Amsterdam for European SMEs | `2026-04-03-ai-consulting-amsterdam-european-smes-1`<br>`2026-03-26-ai-consulting-amsterdam-european-smes` | 2026-04-03<br>2026-03-26 | Radar<br>Radar | **b** — same title, different article (revised version; `-1` suffix suggests republish) |
| 2 | AI Readiness vs. AI Consulting | `2026-04-03-ai-readiness-vs-ai-consulting`<br>`2026-03-26-ai-readiness-vs-ai-consulting-smes` | 2026-04-03<br>2026-03-26 | Radar<br>Radar | **b** — same title, different article (different slugs and topics) |
| 3 | The CEO Playbook for the First 90 Days of AI Adoption | `2026-04-03-ceo-playbook-first-90-days-ai-adoption-1`<br>`2026-03-26-ceo-playbook-first-90-days-ai-adoption` | 2026-04-03<br>2026-03-26 | Radar<br>Radar | **b** — same title, different article (revised version; `-1` suffix suggests republish) |
| 4 | What GitHub's Coding Agent Changes for Product Teams | `2026-04-03-github-coding-agent-product-teams-1`<br>`2026-03-26-github-coding-agent-product-teams` | 2026-04-03<br>2026-03-26 | Radar<br>Radar | **b** — same title, different article (revised version; `-1` suffix suggests republish) |
| 5 | Why Your Company Needs a Sovereign Media Engine | `2026-03-26-sovereign-media-engine-owned-audience-2026`<br>`2026-01-28-sovereign-media-engine-for-your-company` | 2026-03-26<br>2026-01-28 | Radar<br>First AI Movers | **b** — same title, different article (cross-property republication) |
| 6 | Your Website Is Answering the Wrong Questions | `2026-02-09-content-strategy-funnel-architecture-guide`<br>`2026-01-30-your-website-is-answering-the-wrong-questions` | 2026-02-09<br>2026-01-28 | Radar<br>First AI Movers | **b** — same title, different article (cross-property republication) |

**Recommended resolution:** Append a date or property qualifier to disambiguate (e.g., "… (April 2026)" or "… — Radar"). Once all 6 are resolved, remove `continue-on-error: true` from the `Check for duplicate article titles` step in `.github/workflows/tests.yml` to make the gate blocking.
