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
| **E1** | Topic narratives — top 10 topics | Intro + key themes + why-it-matters per topic, written and committed as `tools/topic_intros.json`. Wires the rendering plumbing for the rest. Pages affected: European SME AI, AI Strategy, AI Governance, AI Productivity Tools, EU AI Act, AI Workflow Automation, AI Agents, Healthcare AI, B2B SaaS Growth, GDPR & Data Privacy. | 📱 | M |
| **E2** | Topic narratives — mid 25 topics | Same pattern, next-tier topics (15-50 articles each). | 📱 | M |
| **E3** | Topic narratives — final 40 topics | Long tail (5-15 articles each). After this, all 75 topic hubs have unique content. | 📱 | M |
| **E4** | Topic-page TL;DR digest blocks | "Quick reads" section per topic page = first-N article TL;DRs concatenated. Scannable, citable. | 📱 | S |

## Phase 2 — Visual & social presence

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E5** | OG images + Twitter cards + author footer + JSON Feed | Per-page SVG OG image generator (home + 75 topics + about), `summary_large_image` upgrade, visible author social-links footer (LinkedIn / podcast / YouTube), `/feed.json` sibling to `feed.xml`. | 📱 | M |

## Phase 3 — V2 site features (per-article pages)

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E6** | Per-article HTML pages — renderer | `/articles/<slug>/` for every article. `<meta name=robots content="noindex,follow">` + `<link rel=canonical>` to external canonical. Schema.org `Article` JSON-LD per page. | 📱 | L |
| **E7** | Per-article enhancements | Related-articles strip (topic overlap), table of contents, reading-time chip, breadcrumb. | 📱 | M |

## Phase 4 — Hardening & ops

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E8** | Test coverage + duplicate-title CI gate + atomic writes | Adds: feed byte-stability test, XSS resistance test, llms-full byte-stability test, duplicate-title CI gate (fails PR if duplicates). Refactors 769-file metadata.json writes to temp-dir + atomic rename pattern. | 📱 | M |
| **E9** | Docs + workflow polish | `CONTRIBUTING.md`, PR template, `SECURITY.md`, rename `rebuild-index.yml` → `build-and-deploy.yml`. | 📱 | S |

## Phase 5 — Optional value-add

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E10** | Client-side internal search | JS-only fuzzy search over `index.json`. Search box on home + topics index. No backend. | Hybrid | M |
| **E11** | Accessibility audit + fixes | ARIA labels, skip-link, semantic HTML, contrast review. | 📱 | S |

## Phase 6 — User-side (you, on MacBook)

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E12** | GSC cross-domain verification + sitemap re-submission | Verify 5 hosts (articles / radar / www / insights / voices) under one Search Console property; add `Sitemap:` line to robots.txt on each canonical site you control; resubmit `/sitemap.xml`. | 💻 | S |
| **E13** | Live-site QA + Lighthouse + spot-check | Open articles.firstaimovers.com on phone & laptop; Lighthouse / PageSpeed run; review 5 topic hubs for content quality; check social-share previews after E5 ships. | 💻 | S |

## Suggested execution order

1. **E1 first** — biggest single SEO win (top 10 topics × 552/329/267/105/84/81/64/62/59/56 articles each, all need real content). Also unblocks the testing pattern for E2/E3.
2. **E4** — small bundle, high readability gain on topic pages.
3. **E5** — social-share / OG image visibility.
4. **E2 + E3** — finish narrative coverage to all 75 topics.
5. **E6 + E7** — per-article rendering (the biggest remaining v1 → v2 step).
6. **E8 + E9** — hardening, can interleave with content phases.
7. **E10 / E11** — optional polish.
8. **E12 / E13** — your turn on the MacBook anytime after we ship visible changes.

## Status snapshot — completed

The roadmap below is what's *remaining*. For context, here's what already shipped (10 PRs, all merged):

- **PR #2** Auto-rebuild CI workflow
- **PR #3** Sitemap canonical fix (per-article canonical, allowlist)
- **PR #4** Atom feed (`/feed.xml`)
- **PR #5** `llms-full.txt` (full corpus)
- **PR #6** Firecrawl orphan cleanup
- **PR #7** Tooling consolidation + tests CI
- **PR #8** Tag normalization (3,686 raw tags → 102 canonical topics) + static site v1 (75 topic hubs)
- **PR #9** SEO + GEO + security audit follow-up (14 fixes including jinja2 CVE pin, robots.txt LLM opt-in, BreadcrumbList, 107 metadata whitespace cleanups)
- **PR #10** `llms-recent.txt` (30-day rolling slice)

Operational state today: 799 articles, 102 canonical topics, 75 topic hub pages auto-deployed to GitHub Pages, 93 tests on every PR, zero-touch pipeline (Make.com push → normalize → rebuild → commit → deploy).
