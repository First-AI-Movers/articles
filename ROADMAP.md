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
| **E9** | Docs + workflow polish | `CONTRIBUTING.md`, PR template, `SECURITY.md`, rename `rebuild-index.yml` → `build-and-deploy.yml`. | 📱 | S |

## Phase 5 — Optional value-add

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E10** | Client-side internal search | JS-only fuzzy search over `index.json`. Search box on home + topics index. No backend. | Hybrid | M |
| **E11** | Accessibility audit + fixes | ARIA labels, skip-link, semantic HTML, contrast review. | 📱 | S |
| *(deferred)* | Harvest canonical publisher OG images | Where canonical article pages already have OG images, harvest and reference them in archive topic pages. Requires MacBook + publisher API access. | 💻 | M |

## Phase 6 — User-side (you, on MacBook)

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E12** | GSC cross-domain verification + sitemap re-submission | Verify 5 hosts (articles / radar / www / insights / voices) under one Search Console property; add `Sitemap:` line to robots.txt on each canonical site you control; resubmit `/sitemap.xml`. | 💻 | S |
| **E13** | Live-site QA + Lighthouse + spot-check | Open articles.firstaimovers.com on phone & laptop; Lighthouse / PageSpeed run; review 5 topic hubs for content quality; check social-share previews after E5 ships. | 💻 | S |

## Suggested execution order

1. ~~E1 → E2 → E3 → E4~~ — ✅ **Phase 1 complete.** All 77 topic hub pages have curated intros; 67 have Quick reads.
2. ~~E5~~ — JSON Feed + social footer + OG image plumbing. ✅ Done.
3. ~~E6~~ — per-article HTML pages renderer. ✅ Done.
4. ~~E7~~ — per-article enhancements (related articles, TOC, reading time, breadcrumbs). ✅ Done.
5. ~~E8~~ — test coverage + duplicate-title gate + atomic writes. ✅ Done.
6. **E9** — docs + workflow polish. Next recommended epic.
7. **E10 / E11** — optional polish.
8. **E12 / E13** — your turn on the MacBook anytime after we ship visible changes.

## Status snapshot — completed

The roadmap below is what's *remaining*. For context, here's what already shipped (13 PRs, all merged):

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

Operational state today: 819 articles, 111 canonical topics, 77 topic hub pages, 77 curated intros, ~175 articles with TL;DR, **819 local article pages**, **186 tests** on every PR, zero-touch pipeline (Make.com push → normalize → rebuild → commit → deploy).

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
