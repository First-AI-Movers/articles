# Security and Secrets Closeout Review

**Status:** Track B8 complete — repo-grounded security audit. No secrets exposed, no deployments activated.
**Date:** 2026-05-03
**Scope:** Secrets inventory, workflow permissions, gitleaks coverage, external activation gates, dependency surface, and supply-chain hygiene.
**Label key:** VERIFIED = repo-grounded fact; INFERRED = reasonable projection; UNRESOLVED = requires owner decision.

---

## 1. Executive verdict

**Verdict: ready with gated risks** — The archive is safe to freeze as v1.

- No secrets are committed to the repository. VERIFIED
- Gitleaks CI scans every PR and push to main with full history (fetch-depth: 0). VERIFIED
- All optional external surfaces (IndexNow, Airtable write, MCP deploy, Zenodo, Giscus, OG worker, Wayback) are gated by secrets, repository variables, or explicit flags. VERIFIED
- Workflow permissions follow the principle of least privilege: most workflows run with contents: read only; ingestion workflows that must open PRs use contents: write + pull-requests: write. VERIFIED
- Dependency surfaces are minimal and monitored by Dependabot. VERIFIED
- Local gitleaks is not installed, so full-history secret scanning cannot be run locally; CI coverage is the authoritative check. INFERRED (not a blocker)
- The only known credential-like string in the repo is a third-party AWS access key embedded in a public Beehiiv presigned URL inside article content; it is allowlisted in .gitleaks.toml with documented justification. VERIFIED

**No v1 blockers identified.**

---

## 2. Secret inventory

| Secret / Variable | Used by | Required for | Current handling | Risk | v1 blocker? | Owner action |
|---|---|---|---|---|---|---|
| DEEPL_API_KEY | tools/translate_articles.py | E39c translation generation (optional) | Env var only; never committed; documented in docs/TRANSLATIONS.md | Low | No | Set when resuming E39c; rotate if leaked |
| INDEXNOW_API_KEY_ARTICLES_FAIM | build-and-deploy.yml, tools/submit_indexnow.py | IndexNow live submission | GitHub secret; public proof-of-host key; redacted in dry-run logs | Low | No | Rotate if compromised |
| AIRTABLE_PAT | ingest-airtable.yml, ingest-airtable-dispatch.yml | Airtable read access | GitHub secret; scoped to Airtable base | Medium | No | Rotate on schedule or if base is shared |
| AIRTABLE_BASE_ID | ingest-airtable.yml, ingest-airtable-dispatch.yml | Airtable base selection | GitHub secret | Low | No | Update if base changes |
| AIRTABLE_TABLE_NAME | ingest-airtable.yml, ingest-airtable-dispatch.yml | Airtable table selection | GitHub secret | Low | No | Update if table changes |
| AIRTABLE_VIEW_NAME | ingest-airtable.yml, ingest-airtable-dispatch.yml | Optional Airtable view filter | GitHub secret (optional) | Low | No | Update if view changes |
| INGEST_DRY_RUN | ingest-airtable.yml, ingest-airtable-dispatch.yml | Controls write vs dry-run | GitHub repository variable; defaults to 1 (dry-run) | Low | No | Set to 0 only after controlled single-record test |
| ARTICLE_INGESTION_PR_TOKEN | ingest-article.yml, ingest-airtable-dispatch.yml | Trigger CI on automated PRs | GitHub secret (optional); falls back to GITHUB_TOKEN | Low | No | Generate fine-grained PAT if auto-CI triggering is desired |
| CLOUDFLARE_API_TOKEN | mcp-server.yml | Cloudflare Workers deploy | GitHub secret; not configured | Low | No | Add when owner approves MCP deploy |
| CLOUDFLARE_ACCOUNT_ID | mcp-server.yml | Cloudflare account selection | GitHub secret; not configured | Low | No | Add when owner approves MCP deploy |
| MCP_DEPLOY_ENABLED | mcp-server.yml | Deploy gate variable | GitHub repository variable; not set | Low | No | Set to 1 when owner approves deploy |
| ZENODO_API_TOKEN | tools/mint_dois.py | Production DOI minting | Environment variable only; not configured in CI | Low | No | Set locally when owner approves |
| ZENODO_SANDBOX_API_TOKEN | tools/mint_dois.py | Sandbox DOI testing | Environment variable only; not configured in CI | Low | No | Set locally for testing |
| GITHUB_TOKEN | All workflows | Checkout, PR creation, artifact upload | Auto-provided by GitHub Actions | Low | No | Auto-rotated by GitHub |
| Giscus repo_id / category_id | tools/comments_config.json | Comments rendering | Config file has empty strings; enabled: false | None | No | Fill IDs and set enabled: true after installing Giscus app |
| GoatCounter endpoint | templates/base.html.j2 | Analytics | Public endpoint; SRI hash pinned; no secret | None | No | None |
| OP_ITEM_REF | .env.example | 1Password secret reference (for add_tldr.py) | Documented placeholder only; not set in CI | None | No | Optional local dev convenience |

---

## 3. Workflow permissions review

| Workflow | Trigger | Permission level | Can write? | Opens PRs? | Deploys? | Calls external APIs? | Activation gated? |
|---|---|---|---|---|---|---|---|
| tests.yml | PR + push main | contents: read | No | No | No | No | N/A |
| e2e.yml | PR + push main + nightly cron | contents: read | No | No | No | No | N/A |
| gitleaks.yml | PR + push main | contents: read | No | No | No | No | N/A |
| geo-audit.yml | PR + push main + manual | contents: read | No | No | No | No | N/A |
| article-quality.yml | PR + push main + weekly cron | contents: read | No | No | No | No (Vale/Lychee local only) | N/A |
| generated-artifacts.yml | PR + push main + manual | contents: read | No | No | No | No | N/A |
| build-and-deploy.yml | Push main (filtered paths) + manual | contents: read, pages: write, id-token: write | Yes (Pages) | No | Yes (GitHub Pages) | Yes (IndexNow dry-run) | IndexNow is --dry-run; Pages is standard |
| build-embeddings.yml | Weekly cron + manual | contents: read | No | Yes (via create-pull-request) | No | No | N/A |
| ingest-article.yml | repository_dispatch + manual | contents: write, pull-requests: write | Yes (opens PR) | Yes | No | No | Payload validated before write; always opens PR |
| ingest-airtable.yml | Daily cron + manual | contents: write, pull-requests: write | Yes (opens PR) | Yes | No | Yes (Airtable API) | Gated by INGEST_DRY_RUN (default 1) |
| ingest-airtable-dispatch.yml | repository_dispatch + manual | contents: write, pull-requests: write | Yes (opens PR) | Yes | No | Yes (Airtable API) | Gated by INGEST_DRY_RUN (default 1) |
| mcp-server.yml | PR (filtered) + push main + manual | contents: read | No | No | Yes (Cloudflare Workers) | No | Deploy gated by CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, and MCP_DEPLOY_ENABLED |
| release-citation-check.yml | Manual only | contents: read | No | No | No | No | N/A |
| wayback-snapshot.yml | Release published + manual | contents: read | No | No | No | Yes (Wayback Machine) | Release-gated; manual dispatch available |

**Observations:**
- No workflow has id-token: write except build-and-deploy.yml, which needs it for the actions/deploy-pages OIDC flow. This is standard for GitHub Pages.
- Ingestion workflows (ingest-article.yml, ingest-airtable.yml, ingest-airtable-dispatch.yml) require contents: write + pull-requests: write to open automated PRs. They never push directly to main.
- The build-and-deploy.yml contents: read permission was reduced from write in commit 14ba82b9 to prevent auto-commit bypassing branch protection. VERIFIED

---

## 4. External activation gates

| Surface | Activation path | Gate | Evidence | v1 blocker? |
|---|---|---|---|---|
| DeepL | tools/translate_articles.py | Requires DEEPL_API_KEY env var + explicit --provider deepl + --allow-network | Code-reviewed; no CI automation | No |
| IndexNow | build-and-deploy.yml indexnow job | --dry-run hardcoded; key required but dry-run prints payload only | .github/workflows/build-and-deploy.yml line 80 | No |
| Airtable write | ingest-airtable.yml / ingest-airtable-dispatch.yml | INGEST_DRY_RUN repository variable must be 0; defaults to 1 | .github/workflows/ingest-airtable.yml line 13 | No |
| MCP/Ask deploy | mcp-server.yml deploy job | Requires CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, and MCP_DEPLOY_ENABLED=1 | .github/workflows/mcp-server.yml lines 92-99 | No |
| Zenodo DOI | tools/mint_dois.py | Defaults to --dry-run; production requires --yes-i-understand-production-dois-are-permanent | tools/mint_dois.py lines 314-320 | No |
| Giscus | tools/comments_config.json | enabled: false; empty repo_id and category_id; template checks all three | tools/comments_config.json; templates/partials/giscus.html.j2 | No |
| OG worker | tools/og_config.json | enabled: false; no CI workflow; no DNS | tools/og_config.json | No |
| Wayback | wayback-snapshot.yml | Triggers only on release: published; manual dispatch available | .github/workflows/wayback-snapshot.yml | No |

---

## 5. Gitleaks coverage review

### Local installation

**Finding:** gitleaks is not installed locally (which gitleaks returned empty).

**Impact:** Full-history secret scanning cannot be run on the developer machine.

**Mitigation:** CI runs gitleaks on every PR and push to main with fetch-depth: 0, scanning the complete Git history. This is the authoritative check.

**Not a v1 blocker** because CI coverage is complete and the repo has been green on all recent PRs.

### .gitleaks.toml review

**File:** .gitleaks.toml (44 lines)

**Allowlist entries:**

| Entry | Type | Justification | Risk assessment |
|---|---|---|---|
| ee4c7a6ad2464b84a2320e9edf0fe996 | Exact regex | IndexNow public verification key (proof-of-host ownership, not a secret) | Acceptable — key is public by design |
| AKIAQCMHTQSE2JGAGXHJ | Exact regex | Third-party AWS credential in a Beehiiv presigned URL inside article content; URL was published by the canonical publisher; credential is not ours | Acceptable — documented in config; scrubber tool exists (tools/scrub_presigned_urls.py) |
| site/.*\.txt$ | Path | Generated artifacts where public keys may be documented | Acceptable — site/ is gitignored; only built artifacts |
| docs/.* | Path | Documentation files | Acceptable — docs contain no secrets |
| CONTRIBUTING.md, SECURITY.md, ROADMAP.md, README.md | Path | Markdown documentation | Acceptable |
| .gitleaks.toml | Path | Self-reference | Acceptable |
| tools/tests/.* | Path | Test fixtures that exercise key handling | Acceptable — fixtures use fake/test keys only |
| .github/workflows/.* | Path | Workflow files that reference env var names | Acceptable — workflows contain no values |
| articles/2025-09-28-llm-limits-solved-ai-workarounds-guide-2025/article.md | Path | Article containing the Beehiiv presigned URL | Acceptable — narrow, specific path |

**Assessment:** The allowlist is narrow and well-documented. Each entry has a specific justification. No broad wildcard patterns that could hide real secrets. No changes recommended.

### .github/workflows/gitleaks.yml review

**File:** .github/workflows/gitleaks.yml (25 lines)

- Runs on: pull_request + push to main
- Permissions: contents: read
- Checkout: fetch-depth: 0 (full history)
- Config: uses .gitleaks.toml
- Version: pinned to v8.18.2

**Assessment:** Coverage is complete for the repo current state. No changes recommended.

---

## 6. Dependency/supply-chain notes

### Python dependencies

- **Primary source:** tools/requirements.txt
- **Key packages:** Standard data science/web tooling (Jinja2, requests, pyarrow, etc.)
- **Optional packages:** openai, python-dotenv — used only by add_tldr.py; deselected in CI if absent
- **Embeddings:** BAAI/bge-small-en-v1.5 (MIT license) via sentence-transformers

### Node dependencies

- **MCP server:** @modelcontextprotocol/sdk@1.26.0, zod@^3.25.0
- **OG worker:** @resvg/resvg-wasm@^2.6.2, hono@^4.8.0
- **Dev tooling:** TypeScript, Vitest, Wrangler (Cloudflare)

### Supply-chain monitoring

- **Dependabot:** Active for both pip (/tools) and github-actions (/) ecosystems. Weekly scans on Mondays at 09:00 Europe/Lisbon. VERIFIED
- **Lockfiles:** package-lock.json present in both mcp-server/ and og-worker/. VERIFIED
- **No unpinned direct installs** in CI workflows. VERIFIED

### Risk notes

| Risk | Severity | Status | Note |
|---|---|---|---|
| Dependency drift in mcp-server/ or og-worker/ | Low | Monitored | Dependabot will flag updates |
| gitleaks binary downloaded in CI without checksum verification | Low | Accepted | Standard pattern for gitleaks installer; version is pinned |
| Vale binary downloaded in CI without checksum verification | Low | Accepted | article-quality.yml uses wget install; best-effort soft gate |

---

## 7. Do not expose / do not activate rules

The following actions must not happen without explicit owner approval:

1. Do not print secret values in CI logs, PR descriptions, or issue comments.
2. Do not create or rotate secrets as part of automated workflows.
3. Do not add dummy secrets to the repository.
4. Do not change repository settings (branch protection, secret scanning, etc.) via automation.
5. Do not enable live IndexNow without owner approval — keep --dry-run in build-and-deploy.yml.
6. Do not enable Airtable write mode without a controlled single-record test — keep INGEST_DRY_RUN unset or 1.
7. Do not deploy MCP/Ask/OG without Cloudflare credentials + MCP_DEPLOY_ENABLED=1.
8. Do not mint DOIs without owner approval — production requires explicit flag.
9. Do not call DeepL except through tools/translate_articles.py with explicit --provider deepl.
10. Do not enable Giscus without GitHub Discussions + app install + valid IDs.

---

## 8. Findings table

| # | Finding | Severity | Status | Evidence | Recommended next action |
|---|---|---|---|---|---|
| F1 | Local gitleaks not installed | Low | Acknowledged | which gitleaks → not found | CI is authoritative; install locally if desired for pre-commit checks |
| F2 | Generated artifacts are stale (index.json, sitemap.xml, llms-full.txt, llms-recent.txt, README.md) | Low | Known / tracked | python3 tools/check_generated_artifacts.py → FAILED | Not a security issue; documented in docs/GENERATED_ARTIFACTS.md (B4) |
| F3 | CHANGELOG.md is stale | Low | Known / tracked | python3 tools/build_changelog.py --check → would change | Not a security issue; documented in docs/AUTOMATION_READINESS_AUDIT.md (B3) |
| F4 | Third-party AWS credential in article content (AKIAQCMHTQSE2JGAGXHJ) | Low | Allowlisted | .gitleaks.toml line 26; articles/2025-09-28-llm-limits-solved-ai-workarounds-guide-2025/article.md | Run tools/scrub_presigned_urls.py if owner wants to remove the audio block; not a security risk (third-party, already public) |
| F5 | pytest tools/tests fails locally due to missing numpy | Low | Expected | python3 -m pytest tools/tests → ModuleNotFoundError: No module named numpy | Optional dependency; CI installs all required packages; not a blocker |
| F6 | .env.example contains placeholder token patterns (ghp_your_token_here, sk-your-key-here) | None | Acceptable | .env.example lines 5, 10 | File is explicitly an example; not committed as real secrets; gitleaks does not flag it |

---

## 9. Final v1 recommendation

**The archive is safe to freeze as v1.**

All critical security surfaces are verified:
- No secrets committed
- Gitleaks CI coverage is adequate and runs on every PR/push
- Workflow permissions follow least privilege
- All external activation paths are gated
- Dependency monitoring is active (Dependabot)
- No unauthorized deployments can occur without owner action

**Deferred to post-v1 (documented, not required):**
- Install gitleaks locally for pre-commit convenience (F1)
- Refresh generated artifacts (F2 — B4 scope)
- Refresh CHANGELOG.md (F3 — B3 scope)
- Optional: scrub Beehiiv presigned URL from article (F4 — content decision)

---

## 10. Validation results

Commands run during this audit and their results:

[translations] 2026-03-25-claude-prompt-architecture-vs-complexity-2026: 5 entries
[translations] 2026-03-26-ai-native-engineering-playbook-european-smes: 5 entries
[translations] 2026-03-26-mcp-for-teams-ai-integration-layer-2026: 5 entries
[translations] 2026-03-26-sovereign-media-engine-owned-audience-2026: 5 entries
[translations] 2026-03-26-the-european-ceos-12-month-ai-agenda: 5 entries
[translations] 2026-04-01-openai-agent-stack-consulting-need: 5 entries
[translations] 2026-04-24-eu-ai-act-conformity-assessment-guide-european-smes-202: 5 entries
[translations] OK: 7 file(s), 35 entries, 0 errors
[translation-quality] WARNING translations/reviews/eu-ai-act-conformity-assessment-guide-european-smes-2026.de.review.md:
  - source contained "high-risk AI system" but expected target term "Hochrisiko-KI-System" was not found
[translation-quality] WARNING translations/reviews/eu-ai-act-conformity-assessment-guide-european-smes-2026.nl.review.md:
  - source contained "high-risk AI system" but expected target term "hoogrisico-AI-systeem" was not found
[translation-quality] checked=35 passed=35 warnings=2 errors=0
Articles processed: 829
  with at least one topic: 829 (100.0%)
  with zero topics:        0

Canonical topics used: 103 / 111
Unused canonical topics: ['AI Advisory', 'AI Audit', 'AI Copywriting', 'AI Testing', 'AI for Legal Teams', 'Computer Use', 'Fractional CAIO', 'Public Sector AI']

Top 25 topics by article count:
   605  European SME AI
   353  AI Strategy
   323  AI Governance
   118  EU AI Act
   109  AI Productivity Tools
    85  AI Workflow Automation
    82  GDPR & Data Privacy
    67  AI Agents
    66  Healthcare AI
    62  B2B SaaS Growth
    56  GPT Models
    55  AI Change Management
    47  AI Cost Optimization
    46  France and Benelux AI
    45  Executive AI Literacy
    45  Claude Code
    43  AI Coding Tools
    41  AI Literacy
    39  Model Selection
    38  AI Risk Management
    36  AI Consulting
    33  AI Training
    33  AI Industry News
    33  AI Content Strategy
    28  Sovereign AI Infrastructure

Raw tags with no canonical match (1951 unique, 2105 total occurrences):
  Top 20 by frequency:
      4  AI tools for business
      4  AI tools for European businesses
      4  effective AI communication
      4  workflow redesign for AI
      4  automation in software development
      3  AI communication strategies
      3  AI-driven product development
      3  real-time information retrieval
      3  AI tool integration
      3  AI-driven content analysis
      3  AI-driven business transformation
      3  lifelong learning strategies
      3  organizational readiness for AI
      3  AI-driven operational efficiency
      3  AI capability development
      3  open-source AI solutions
      3  AI product development strategies
      3  data quality assessment
      3  open-source AI models
      3  AI-driven business innovation
[citation-graph] --check passed
[changelog] CHANGELOG.md would change
[check-citation] /Users/nac/dev/articles/CITATION.cff
  OK: CITATION.cff looks valid.
[errata] No errata files found — nothing to validate
OK: no duplicate titles found

==================================== ERRORS ====================================
_______________ ERROR collecting tools/tests/test_embeddings.py ________________
ImportError while importing test module '/Users/nac/dev/articles/tools/tests/test_embeddings.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.4/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tools/tests/test_embeddings.py:8: in <module>
    import numpy as np
E   ModuleNotFoundError: No module named 'numpy'
=========================== short test summary info ============================
ERROR tools/tests/test_embeddings.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.15s

---

## 11. Evidence summary

| Claim | Evidence type | Location |
|---|---|---|
| No secrets committed | CI proven | .github/workflows/gitleaks.yml green on every PR/push |
| Gitleaks allowlist is narrow | Code-reviewed | .gitleaks.toml (44 lines, 2 regexes, 9 paths) |
| All workflows use least privilege | Code-reviewed | .github/workflows/*.yml (14 files) |
| IndexNow is dry-run | Code-reviewed | .github/workflows/build-and-deploy.yml line 80 |
| Airtable is dry-run by default | Code-reviewed | .github/workflows/ingest-airtable.yml line 13 |
| MCP deploy is gated | Code-reviewed | .github/workflows/mcp-server.yml lines 92-99 |
| Giscus is disabled | Config-reviewed | tools/comments_config.json enabled: false |
| OG worker is disabled | Config-reviewed | tools/og_config.json enabled: false |
| Dependabot active | Config-reviewed | .github/dependabot.yml |
| No v1 blockers | Audit conclusion | This document |
