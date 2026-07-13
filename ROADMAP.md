# Roadmap

Active work for the First AI Movers article archive. Completed sprints, the full epic-by-epic completion log, and the historical merged-PR snapshot live in [`docs/ROADMAP_HISTORY.md`](docs/ROADMAP_HISTORY.md).

## Operational status

The archive is at **v1 stable** (frozen 2026-05-03) and is in a maintenance + growth-layer phase. Recent operational changes worth surfacing for any contributor landing here:

- GitHub Actions stack modernized for the 2026-06-02 Node.js 20 → 24 runner cutover: `peter-evans/create-pull-request@v8`, `actions/setup-node@v6`, `actions/upload-artifact@v7`, `actions/cache@v5`.
- `.github/workflows/ingest-article.yml` now passes the `repository_dispatch` `client_payload` through an environment variable and parses it in a quoted Python heredoc — no shell interpolation of the dispatch payload.
- The Airtable cron-write ingestion pipeline auto-closes its own `E41 cron ingestion incident:` issues on the next successful schedule-triggered run.
- The `Generated artifacts` drift check skips PRs whose only changed files are `tools/requirements.txt`, `.github/workflows/<name>.yml`, or `.github/dependabot.yml`. Any other path still runs the full drift check, and every push to `main` runs it unconditionally.

<!-- BEGIN auto:operational-state -->
Operational state today: **887 articles**, **103 canonical topics**, **77 rendered topic hubs**, **887 local noindex article pages**, sitemap limited to **80 first-party indexable URLs**, and the current test suite split across Python unit/integration tests plus Playwright E2E.
<!-- END auto:operational-state -->

## Tag legend

- 📱 — doable from cold cloud env (this Claude Code session, no special access needed)
- 💻 — needs MacBook + accounts/devices (Search Console clicks, live-site QA, design-tool review)
- **Hybrid** — primary work is 📱; verification step is 💻

Effort (rough): **XS** = ≤30 min, **S** = ~1h, **M** = ~2h, **L** = ~4h. All are sized to fit one session.

## Active multilingual rollout (E39c)

E39c is re-scoped to quota-paced growth on the DeepL Free tier (~1 article/month). 7 articles × 5 languages = 35 translated pages already shipped (PRs #123, #129, #135); 13 articles remain. Optional for archive v1 closeout. Plan and strategic options in [`docs/E39C_ROLLOUT_PLAN.md`](docs/E39C_ROLLOUT_PLAN.md).

## Next development candidates

These are not committed epics yet — they are the highest-value next tracks. Pick one per session.

| # | Track | Why now | Size |
|---|---|---|---|
| **N3** | Topic hub CTR optimization | After 2–4 weeks of GSC data, tune titles/meta for hubs with impressions but low CTR. Data-driven, not speculative. | S |
| **N4** | WordPress/Hetzner migration SEO checklist | Prepare launch checklist for `www.firstaimovers.com` migration: robots.txt, sitemap, Cloudflare bot allowlisting, IndexNow, canonical redirects. | S |
| **N5** | Archive analytics / reporting | Add simple weekly visibility snapshot artifact generated from GSC/Bing exports if data access becomes available. | M |

Completed "Next" candidates (N1, N2, N6) are recorded in [`docs/ROADMAP_HISTORY.md`](docs/ROADMAP_HISTORY.md#completed-next-candidates).

## E20a operational follow-ups

E20a is **validated in dry-run only**. Write mode remains disabled until explicitly approved.

| Follow-up | Status | Notes |
|---|---|---|
| `INGEST_DRY_RUN` repository variable | **unset** (safe) | Keep unset or set to `1`. Do **not** set to `0` until a controlled single-record write test is approved. |
| Airtable secrets | ✅ configured | `AIRTABLE_PAT`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_NAME` are set. `AIRTABLE_VIEW_NAME` is optional and not needed. |
| Dry-run validation | ✅ clean | Run 25062480810: 67 seen, 67 skipped, 0 invalid, 0 would-create. |
| Field mapping | ✅ correct | `Title` → title, `slug` → slug, `Pub Date` → published_date, `GUID` → canonical_url, `Content HTML` → article_markdown, `tags` → tags. |
| Slug derivation | ✅ working | Missing `slug` falls back to last path segment of `GUID`. Explicit Airtable `slug` is always preferred. |
| Date normalization | ✅ working | Bare dates and ISO timestamps (`2026-04-25T00:00:00.000Z`) both normalize to `YYYY-MM-DD`. |
| Content HTML | ✅ preserved as-is | No HTML-to-Markdown dependency added. Markdown allows raw HTML. Revisit if rendered output needs conversion. |
| `Link` field | ✅ ignored | Image/Beehiiv assets; not mapped. |
| Status gate | dry-run permissive | `--allow-no-status-gate` is passed in dry-run only. Write mode requires explicit `Status` field or future override. |
| PR token behavior | pending decision | Ingestion-created PRs use `GITHUB_TOKEN`, which does **not** trigger CI workflows on the created PR (GitHub recursion prevention). If automatic CI on ingestion PRs is needed later, replace with a fine-grained PAT or GitHub App token. |
| Controlled write test | **not yet done** | Recommended: pick one `--record-id` with a new (non-duplicate) article, run `--write` locally or in a dedicated workflow run, verify output, then enable scheduled write mode. |
| Make.com cutover | **not yet done** | Run side-by-side for 1 week after write mode is enabled. Observe 14 days. Delete Make.com scenario when confident. |

## E18 operational notes

E18 is **merged and active**. The following are documented expectations, not necessarily enabled in GitHub Settings:

| Item | Status | Notes |
|---|---|---|
| Branch protection on `main` | **documented expectation** | `docs/BRANCH_PROTECTION.md` lists required rules. Owner must enable in Settings → Branches. |
| `ARTICLE_INGESTION_PR_TOKEN` | **optional** | If set, `ingest-article.yml` uses it for PR creation so downstream CI triggers automatically. If absent, falls back to `GITHUB_TOKEN`; ingestion PRs may need manual close/reopen to get checks. |
| `workflow_dispatch` on `ingest-article.yml` | **uses fixture payload** | Intentional test path. Running manually opens a PR with the synthetic fixture article. Close without merging. |
| External publishing sender token | **not yet configured** | Sender needs a fine-grained PAT with `actions:write` scoped to this repo only. Documented in `docs/EXTERNAL_PUBLISHING.md`. |

## Archive v1 Closeout — ✅ Complete

The archive is frozen as **v1 stable** as of 2026-05-03. All required closeout prep is repo-grounded:

- **Final audit harness** — `tools/final_audit.py` passes 12/12 required checks; optional warnings (CHANGELOG drift, pytest with optional deps) are documented non-blockers. See `docs/FINAL_AUDIT_CHECKLIST.md`.
- **CI/Pages proof** — `build-and-deploy.yml` deploys cleanly; Pages URL returns 200; required checks green on every PR/push. See `docs/CI_PAGES_PROOF.md`.
- **Security/secrets review** — `gitleaks` green; no credentials in repo; Dependabot active; all external surfaces gated. See `docs/SECURITY_SECRETS_REVIEW.md`.
- **Release/external readiness** — All optional surfaces (Zenodo DOI, MCP, Ask, OG, IndexNow, Airtable, Giscus) are either ready or documented as deferred. See `docs/RELEASE_EXTERNAL_READINESS.md`.
- **Generated artifacts** — Drift detection active; committed artifacts current. See `docs/GENERATED_ARTIFACTS.md`.

**What remains post-v1 (optional growth layer, not blockers):**
- E39c translation rollout — 13 articles × 5 languages remaining at quota pace (~1 article/month). See `docs/E39C_ROLLOUT_PLAN.md`.
- E35 full-corpus summaries — pending owner approval.
- Live MCP/Ask/OG deployment — pending Cloudflare credentials.
- ~~Live IndexNow — pending owner flip from `--dry-run`.~~ ✅ Done (PR #178 flip + 2026-05-15 live verification: 200 OK, 80 URLs, run 25928942642).
- Zenodo DOI minting — pending release creation.
- Airtable write mode — staged in E41 (see `docs/AUTONOMOUS_AIRTABLE_PUBLISHING_PLAN.md`).

## E41 — Autonomous Airtable publishing (post-v1)

Staged unblock of daily Airtable-to-PR automation. The shipped rows (E41a, E41a', E41a'', E41a''', E41a'''', E41b, E41e, E41f, E41g, E41h) are documented in [`docs/ROADMAP_HISTORY.md`](docs/ROADMAP_HISTORY.md#e41-shipped-rows). Pending design and implementation rows:

| # | Epic | What ships | Tag | Effort |
|---|---|---|:---:|:---:|
| **E41c** | Anthropic AI polish — design only | ADR for TL;DR / summary / headline polish using Anthropic; provider, prompt contract, dry-run plan, cost guardrails. No code. | 📱 | S |
| **E41d** | Anthropic AI polish — dry-run implementation | Polish script writes to `.polish.draft.json` siblings, behind opt-in env var; no live calls in default CI; cost cap enforced in code. | 📱 | M |

Full plan, cost model, and single-record test checklist live in [`docs/AUTONOMOUS_AIRTABLE_PUBLISHING_PLAN.md`](docs/AUTONOMOUS_AIRTABLE_PUBLISHING_PLAN.md).

## External platform follow-ups — paused

These are **not blockers** for the article archive repo. They depend on external platforms and will be revisited during future migrations.

### Radar / Hashnode

`radar.firstaimovers.com` is hosted on Hashnode. Bot-access controls may require Hashnode support or platform-level configuration. During the Search Visibility Sprint, Radar returned **429** to both Googlebot and Bingbot. This remains parked until Hashnode support or platform settings can confirm crawler allowlisting.

### www / Beehiiv

`www.firstaimovers.com` is currently hosted on Beehiiv. Low-level bot/WAF allowlisting may not be available. During the Search Visibility Sprint, www returned **403 to Bingbot** (Googlebot returns 200). Track this for the future WordPress/Hetzner migration, where Cloudflare/WAF rules, robots.txt, sitemap, and IndexNow support must be part of the launch checklist.

## Epic and track numbering

Short labels that recur in commit messages, issues, and workflow comments — decoder for any reader landing on this repo:

- **E#** (E1–E40) — Epic number from the original archive roadmap. E1–E33 covered the v1 build (content depth, accessibility, governance, MCP server, embeddings, etc.); E34–E40 are the Phase 9 curatorial layer. Most are done; full per-epic history in [`docs/ROADMAP_HISTORY.md`](docs/ROADMAP_HISTORY.md).
- **N#** (N1–N6) — "Next" candidates surfaced after the Search Visibility Sprint; smaller follow-ups distinct from numbered Epics. N3, N4, N5 are still open above.
- **E20a / E20b** — Cron-trigger (`a`) and `repository_dispatch`-trigger (`b`) variants of Airtable ingestion. See `.github/workflows/ingest-airtable.yml` and `.github/workflows/ingest-airtable-dispatch.yml`.
- **E41 sub-letters** — Staged steps for the autonomous Airtable publishing pipeline. E41a/b/e/f/g/h shipped; E41c and E41d remain pending above. Full plan in [`docs/AUTONOMOUS_AIRTABLE_PUBLISHING_PLAN.md`](docs/AUTONOMOUS_AIRTABLE_PUBLISHING_PLAN.md).
- **`E41 cron ingestion incident:`** — Auto-filed issue title prefix emitted by the failure path of `.github/workflows/ingest-airtable.yml`. The success path auto-closes any open ones from prior failures.
- **"Node 24 cluster"** — The set of GitHub Actions version bumps merged ahead of the 2026-06-02 Node.js 20 → 24 runner cutover (`peter-evans/create-pull-request`, `actions/setup-node`, `actions/upload-artifact`, `actions/cache`).
- **"Generated artifacts"** — The drift-detector CI job in `.github/workflows/generated-artifacts.yml` that compares committed `index.json`, `sitemap.xml`, `feed.xml`, `feed.json`, `llms.txt`, `llms-full.txt`, `llms-recent.txt`, `README.md`, the `ROADMAP.md` auto block, and `mcp-server/src/generated/archive-data.json` against a fresh local rebuild.

## Completed history

See [`docs/ROADMAP_HISTORY.md`](docs/ROADMAP_HISTORY.md) for the full epic-by-epic completion log (Phases 1–9), the chronological merged-PR snapshot, the suggested execution order, the shipped E41 sub-letter rows, the resolved hardening follow-up table, and a record of recent maintenance sessions.
