# Release and External Surface Readiness Matrix

**Status:** Planning artifact — no implementation, no deployment, no external activation.  
**Date:** 2026-05-02  
**Scope:** Consolidate all gated external surfaces into one operational readiness document so archive v1 can close without pretending optional infrastructure is live.  
**Label key:** `VERIFIED` = repo-grounded fact; `INFERRED` = reasonable projection; `UNRESOLVED` = requires owner decision.

---

## 1. Readiness matrix

| Surface | Status | Required secrets/vars | Current proof | Owner decision | Next action | v1 blocker? |
|---|---|---|---|---|---|---|
| **Zenodo / corpus DOI** | `deferred` | Zenodo account linked; `ZENODO_API_TOKEN` | `docs/ZENODO_RELEASE.md` complete; no releases exist; no webhooks configured; `CITATION.cff` has DOI commented out | D6 — Mint at v1 tag or defer? | Owner decides; if "mint", create release after final audit | No |
| **CITATION.cff** | `ready` | None | `cff-version: 1.2.0`; `check_citation.py` exits 0; ORCID, license, author present; DOI placeholder is intentional | None | Keep current; uncomment DOI only after Zenodo mints | No |
| **GitHub release process** | `manual only` | None | Release checklist doc exists; no tags/releases in repo; tag convention documented (`vYYYY.MM.DD`) | D6 — When to create first release? | Create first release only after final audit + owner approval | No |
| **Wayback snapshots** | `ready but gated` | None | `.github/workflows/wayback-snapshot.yml` auto-triggers on `release: published`; manual `workflow_dispatch` available; tool has `--dry-run` default | None | Will auto-fire on first release; manual dispatch available now | No |
| **MCP server** | `ready but gated` | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `MCP_DEPLOY_ENABLED=1` | Code complete (5 tools + 3 resources); `mcp-server/test/` covers lookups, search, ask; CI runs typecheck + tests + dry-run build; `archive-data.json` committed and current | D7 — Deploy live or leave scaffolded for v2? | If "deploy", add Cloudflare secrets + set `MCP_DEPLOY_ENABLED=1` | No |
| **Ask endpoint** | `ready but gated` | Same as MCP server (shares Worker) | `POST /api/ask` implemented in `mcp-server/src/ask.ts`; validation, citations, mock fallback all present; E2E tests cover disabled-state rendering; `/ask/` page is `noindex` until live | D7 — Same as MCP (deploy together) | Same as MCP server | No |
| **Embeddings** | `ready` | None | `embeddings.parquet` committed (~2 MB); `build-embeddings.yml` runs weekly (Sundays 03:17 UTC); opens PR if changed; never pushes to main; `BAAI/bge-small-en-v1.5` (384-dim, MIT license) | None | Keep weekly schedule; monitor PRs | No |
| **IndexNow live mode** | `ready but gated` | `INDEXNOW_API_KEY_ARTICLES_FAIM` | `tools/submit_indexnow.py` shipped; `build-and-deploy.yml` runs `--dry-run` step after deploy; key validation present; multi-host support | D8 — Switch to live submission or keep dry-run? | If "live", replace `--dry-run` with live submit in `build-and-deploy.yml` | No |
| **Airtable ingestion (E20a)** | `ready but gated` | `AIRTABLE_PAT`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_NAME`, `AIRTABLE_VIEW_NAME`; `INGEST_DRY_RUN=0` | Dry-run validated (67/67 records clean); field mapping correct; cron runs daily at 06:17 UTC; write path gated by `INGEST_DRY_RUN` var | D9 — Enable write mode or keep Make.com path? | If "enable", set `INGEST_DRY_RUN=0` after controlled single-record test | No |
| **Airtable dispatch (E20b)** | `ready but gated` | Same as E20a | `repository_dispatch` endpoint validates record ID shape; reuses E20a logic; same dry-run gate | D9 — Same as E20a | Same as E20a | No |
| **External article ingestion (E18)** | `ready` | `ARTICLE_INGESTION_PR_TOKEN` (optional) | `repository_dispatch` with `new-article` type; schema validation; always opens PR (never pushes to main); fixture payload for testing | None | Monitor incoming PRs; optional token improves CI triggering | No |
| **OG image renderer** | `deferred` | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` (for deploy) | Worker scaffold complete (`og-worker/`); SVG generation working; 24 tests; PNG via `resvg-wasm` wired but not enabled; no CI workflow; no DNS; `tools/og_config.json` has `"enabled": false` | None (implicitly deferred to v2) | Enable PNG → deploy → enable `og_config.json` → add CI | No |
| **Giscus comments** | `deferred` | `repo_id`, `category_id` (from giscus.app) | Scaffold complete; `tools/comments_config.json` has `"enabled": false`; GitHub Discussions not enabled; Giscus app not installed | D5 — Enable comments for v1 or defer? | If "enable", enable Discussions → install Giscus → fill IDs → rebuild | No |
| **GoatCounter analytics** | `ready` | None (endpoint is public) | Script present in `templates/base.html.j2` with SRI hash; path override ensures local paths tracked; GDPR-compliant; no cookie banner | None | Monitor dashboard periodically | No |
| **GEO / AI-search readiness** | `ready` | None | `geo_audit.py` runs deterministic local checks (H1, heading hierarchy, TL;DR, outbound links, statistics, metadata); CI soft-gate uploads reports; no external APIs | None | Continue running as soft gate; upgrade to hard gate after editorial baseline stable | No |

---

## 2. Classification summary

### `ready` — no owner action required
- CITATION.cff
- Embeddings (`embeddings.parquet` + weekly CI)
- External article ingestion (E18)
- GoatCounter analytics
- GEO / AI-search readiness

### `ready but gated` — needs a secret, variable, or owner flip
- Wayback snapshots (auto on release; ready now)
- MCP server (needs Cloudflare credentials + `MCP_DEPLOY_ENABLED=1`)
- Ask endpoint (same gates as MCP)
- IndexNow live mode (needs `INDEXNOW_API_KEY_ARTICLES_FAIM` + `--dry-run` removal)
- Airtable ingestion E20a/E20b (needs `INGEST_DRY_RUN=0`)

### `manual only` — requires a deliberate human action
- GitHub release process (no automation creates releases)
- Zenodo DOI minting (requires release creation + Zenodo account linkage)

### `deferred` — explicitly not a v1 target
- OG image renderer (PNG not enabled, no deploy, no CI)
- Giscus comments (GitHub Discussions not enabled)

### `not a v1 blocker`
- Every item in this matrix. None of these surfaces block the archive from being a professional, citable, contributor-ready v1 artifact.

---

## 3. v1 closeout stance

### Required before v1
These are the only external surfaces that must be in a known-good state before the archive is frozen as v1:

1. **CITATION.cff is valid** — `check_citation.py` passes, metadata is accurate. ✅
2. **Analytics are live** — GoatCounter script renders, path override works. ✅
3. **GEO audit runs** — Soft gate produces reports, no catastrophic failures. ✅
4. **Embeddings regenerate weekly** — CI opens PRs, never pushes to main. ✅
5. **External ingestion creates PRs** — E18 flow validated with fixture payload. ✅

### Optional before v1 (owner-decided)
These can be enabled before v1 if the owner decides, but the archive is professionally complete without them:

- **Live IndexNow** — Low risk, reversible. Improves indexing speed.
- **Airtable write mode** — Requires controlled single-record test first.
- **MCP + Ask deploy** — Requires Cloudflare credentials + rate-limit setup.
- **Wayback auto-submit** — Fires automatically on first release.

### Explicitly deferred to v2
These are documented, scaffolded, and tested, but not targeted for v1:

- **OG image renderer** — Needs PNG enablement, deployment, DNS, CI.
- **Giscus comments** — Needs GitHub Discussions enablement, Giscus app install, ID configuration.
- **Per-article DOIs** — Tool is safe (`mint_dois.py` has strong guards), but minting 829 DOIs is a separate project.
- **Semantic search in MCP/Ask** — Disabled by default; fastembed ↔ Workers AI pooling compatibility unverified without live deployment.

---

## 4. True owner decisions

The following are **decisions**, not implementation tasks. They determine scope, timing, and cost.

| # | Decision | Options | Suggested default | Consequence |
|---|---|---|---|---|
| D6 | **Mint corpus DOI now or after final audit?** | Mint at v1 tag after audit; or defer to v2 | **Mint at v1 tag after audit** | Citation metadata gains a resolvable DOI; Zenodo integration is one-time setup |
| D7 | **Deploy MCP/Ask live or leave scaffolded?** | Deploy now (needs Cloudflare secrets); or leave scaffolded for v2 | **Leave scaffolded for v1** | All code is ready; deployment is reversible; no reader-facing degradation if deferred |
| D8 | **Live IndexNow now or keep dry-run?** | Remove `--dry-run` from `build-and-deploy.yml`; or keep dry-run | **Switch to live** (low risk, reversible) | Bing/Yandex index new articles faster; no cost; key is public proof-of-host |
| D5 | **Enable Giscus comments or keep disabled?** | Enable now (needs Discussions + app); or defer to v2 | **Defer to v2** | No comment data loss risk (none exists); safe to enable later |
| D9 | **Enable Airtable write mode or keep Make.com path?** | Set `INGEST_DRY_RUN=0` after single-record test; or keep dry-run indefinitely | **Keep dry-run for v1** | Make.com path continues to work; Airtable auto-ingestion is a convenience, not a blocker |

---

## 5. "Do not do automatically" rules

The following actions **must not** happen without explicit owner approval:

### No DOI mint without owner approval
- `tools/mint_dois.py` defaults to `--dry-run`.
- Production write requires `--yes-i-understand-production-dois-are-permanent`.
- Even then, start with `--sandbox --write --slug <slug>` first.
- Corpus-level DOI (Zenodo release) requires the owner to link Zenodo to GitHub and create a release.

### No live IndexNow switch without owner approval
- The `INDEXNOW_API_KEY_ARTICLES_FAIM` secret may or may not be set.
- The `--dry-run` step in `build-and-deploy.yml` must be replaced with a live submit step.
- This is low risk and reversible, but it is an external API call that affects search engine behavior.

### No Airtable write mode without controlled single-record test
- Set `INGEST_DRY_RUN=0` only after:
  1. A manual `workflow_dispatch` of `ingest-airtable-dispatch.yml` with a known record ID succeeds.
  2. The resulting PR is reviewed and merged cleanly.
  3. The cron workflow (E20a) is watched for one cycle.

### No MCP/Ask deployment without Cloudflare credentials and explicit enablement
- `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, and `MCP_DEPLOY_ENABLED=1` must all be present.
- Rate-limiting rules should be configured in Cloudflare before publicizing the endpoint.
- The `/ask/` page is `noindex` until live; do not remove `noindex` before deployment.

### No Giscus without GitHub Discussions and Giscus IDs
- `tools/comments_config.json` has empty `repo_id` and `category_id`.
- Enabling without valid IDs will break page rendering.
- Giscus app must be installed on `First-AI-Movers/articles` first.

---

## 6. Shortest responsible closeout recommendation

To freeze archive v1 without expanding scope:

1. **Do not enable optional surfaces now.** IndexNow, MCP/Ask, Airtable write mode, Giscus, and OG renderer are all documented as deferred or gated. Enabling any of them expands the v1 surface area and risk.

2. **Finish the final audit harness/checklist next (B7).** The final audit verifies repo structure, article integrity, generated artifacts, translations, SEO, accessibility, licensing, and security. It is the last gate before v1.

3. **Freeze v1 with optional surfaces documented as deferred/gated.** The archive is already professional, citable, and contributor-ready. The readiness matrix proves this.

4. **Handle DOI only after final audit.** If the owner approves D6, create the first GitHub release after the audit passes, which triggers Zenodo and mints the corpus DOI. Update `CITATION.cff`, `README.md`, and `docs/CITATION.md` with the real DOI in a dedicated closeout PR.

5. **Post-v1, all deferred surfaces remain in `docs/` as a backlog.** Future agents or contributors can pick up OG renderer deployment, Giscus enablement, MCP/Ask live switch, per-article DOI rollout, or E39c translation expansion without needing to rediscover the current state.

---

## 7. Evidence and proof

| Claim | Evidence type | Location |
|---|---|---|
| No releases exist | Repo-grounded | `gh release list` = empty |
| No Zenodo webhook | Repo-grounded | `gh api repos/First-AI-Movers/articles/hooks` = `[]` |
| No DOIs minted | Repo-grounded | `index.json` has 0 `"doi"` fields |
| CITATION.cff valid | Test-proven | `python3 tools/check_citation.py` exits 0 |
| Embeddings committed | Repo-grounded | `embeddings.parquet` ~2 MB at repo root |
| MCP code complete | Code-reviewed | `mcp-server/src/index.ts` has `/mcp` + `/api/ask` routes |
| MCP deploy gated | CI-reviewed | `.github/workflows/mcp-server.yml` lines 86–100 |
| Ask page `noindex` | Template-reviewed | `templates/ask.html.j2` meta robots tag |
| IndexNow dry-run | CI-reviewed | `.github/workflows/build-and-deploy.yml` line 80 |
| Airtable dry-run default | CI-reviewed | `.github/workflows/ingest-airtable.yml` line 13 |
| Giscus disabled | Config-reviewed | `tools/comments_config.json` `"enabled": false` |
| OG disabled | Config-reviewed | `tools/og_config.json` `"enabled": false` |
| GoatCounter live | Template-reviewed | `templates/base.html.j2` script block with SRI |
| GEO audit soft-gate | CI-reviewed | `.github/workflows/geo-audit.yml` uploads artifacts, does not block merges |

---

## 8. Relationship to other closeout documents

| Document | What it covers | This doc adds |
|---|---|---|
| `docs/ROADMAP_CLOSEOUT_TRACKS.md` | Two-track execution model, dependency graph, final audit design | Per-surface readiness classification, owner decisions, "do not do" rules |
| `docs/AUTOMATION_READINESS_AUDIT.md` | Workflow-by-workflow automation proof | External surface consolidation, credential inventory, v1 blocker assessment |
| `docs/GENERATED_ARTIFACTS.md` | Source-vs-generated artifact policy | Which generated artifacts feed external surfaces (embeddings, MCP data) |
| `docs/OPERATIONS.md` | Runbooks for common tasks | Cross-reference to readiness matrix for gated operations |

---

## Validation

Before merging the PR that adds this document:

```bash
# Doc-only changes expected
python3 tools/check_translations.py
python3 tools/check_translation_quality.py
python3 tools/check_generated_artifacts.py
python3 tools/normalize_tags.py --dry-run
python3 tools/build_citation_graph.py --check
git diff -- docs/RELEASE_EXTERNAL_READINESS.md docs/ROADMAP_CLOSEOUT_TRACKS.md docs/OPERATIONS.md
git status --short
```

If `build_changelog.py --check` times out locally, report it honestly and rely on CI.
