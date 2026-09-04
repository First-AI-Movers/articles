# Incident-Response Runbook — First AI Movers Article Archive

**Created:** 2026-06-20 (ARTICLES-IR-RUNBOOK-ADOPT-A) · **Lane:** Security
**Scope:** the operational procedure for responding to a security or content incident in this repository — a **public, static article archive** built from `articles/**` and deployed to GitHub Pages at `articles.firstaimovers.com`. Reporting policy lives in [`/SECURITY.md`](../SECURITY.md); this runbook is the **response**.
**Related:** [`SECURITY.md`](../SECURITY.md), [`ERRATA.md`](ERRATA.md) (the correction protocol), [`OPERATIONS.md`](OPERATIONS.md), [`SECURITY_SECRETS_REVIEW.md`](SECURITY_SECRETS_REVIEW.md), [`airtable-ingestion.md`](airtable-ingestion.md), [`WAYBACK.md`](WAYBACK.md), `.github/workflows/gitleaks.yml` + `.gitleaks.toml`. **Org posture:** see the **no-paid security posture index** in the Agent Toolkit repo (`docs/06-operations/no-paid-security-posture-index.md`) for which scanners/protections are active org-wide vs. GHAS-deferred — note this is a **public** repo, so its free GitHub-native protections (secret scanning, push protection, Dependabot, CodeQL) **are** active.

> **Standing rules an incident does NOT relax.** This repo holds **no backend, no database, no authenticated service** — everything is static + public. The **no-secrets policy** ([`SECURITY.md`](../SECURITY.md)) is absolute: never commit or echo a secret value — reference it by name, rotate at source. The **archive is immutable** ([`ERRATA.md`](ERRATA.md), `CONTRIBUTING.md`): published `articles/*/article.md` are **never edited** — corrections are appended as **errata**, not rewrites. Don't paste secret values into issues/PRs/this runbook.

---

## 0. Roles

Small team — one person may hold several roles; name them at the start:

- **Incident Lead** — owns the timeline + decisions + postmortem.
- **Maintainer** — the only role that rotates secrets (GitHub repo/Actions secrets + the upstream provider), merges to `main`, and triggers a redeploy.
- **Scribe** — captures the evidence + timeline (§9).

## 1. Triage & severity

First 15 minutes — establish *what*, *blast radius*, *still live?*:

1. Is it **active** (a leaking secret, a bad article currently served on Pages) or **historical**?
2. Blast radius — one article, the whole site, a secret/token, CI, or a provider/ingestion path?
3. Is a **secret/token** involved (→ §2) or **published content** (→ §3)?

| Severity | Examples | Response |
|---|---|---|
| **SEV-1** | a leaked live token (Airtable PAT, a provider API key, the ingestion PAT), CI/workflow compromise, malicious content served on Pages | rotate now (§2) / revert the deploy (§4); page the Maintainer |
| **SEV-2** | a published article with a serious factual error / unsupported claim / wrong attribution, a content-safety issue | issue an erratum or retraction (§4) same-day |
| **SEV-3** | minor metadata/SEO issue, low-impact hardening gap, a scanner advisory | normal PR lifecycle |

Open a **private** tracking note (not a public issue — there is a `.github/ISSUE_TEMPLATE/security.yml` for *inbound* reports, but incident working-notes stay private) and start the §9 log.

## 2. Secret / token leak response

A credential committed, logged, or otherwise exposed. The repo's **no-secrets policy** means *any* secret in the tree is an incident.

1. **Rotate at source first; do not echo the value.** Rotate the affected secret in its provider **and** update the GitHub Actions secret. The secrets this repo uses (by name — verify against the workflows + [`SECURITY_SECRETS_REVIEW.md`](SECURITY_SECRETS_REVIEW.md), do not assume this list is closed): `AIRTABLE_PAT` / `AIRTABLE_BASE_ID` / `AIRTABLE_TABLE_NAME` / `AIRTABLE_VIEW_NAME` (ingestion), `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` / `MINIMAX_API_KEY` (LLM tooling), `CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_API_TOKEN` (og-worker), `INDEXNOW_API_KEY_ARTICLES_FAIM` (IndexNow — note this key is *served publicly by design*, not a secret), and **`ARTICLE_INGESTION_PR_TOKEN`** (a PAT with more scope than `GITHUB_TOKEN` — treat its leak as SEV-1).
2. **Find the exposure surface.** `gitleaks` already scans (PR + push + weekly + dispatch); review its findings, recent CI logs/artifacts, and `git log -p` / `git grep` for the secret's **name/location** (not value). If it was committed, the value is burned — rotation (step 1) is the fix, **not** a history rewrite (force-pushing a public archive is itself disruptive; rotate instead).
3. **Contain blast radius** — check whether the same secret is reused elsewhere and rotate those too.
4. Record what leaked, where, for how long, and the rotation timestamp (§9).

## 3. Publishing / content incident response

A bad or unintended article reached the live Pages site (`articles/**` → build-and-deploy → Pages).

- **Accidental publish / bad commit on `main`:** `build-and-deploy.yml` auto-deploys on push to `main` (paths `articles/**`, `tools/**`, `templates/**`, `static/**`, …). A bad merge is therefore live within one deploy. → **revert the commit (§4)** and let the rebuild redeploy.
- **Bad article / unsupported claim / wrong source or citation:** → issue a **correction or retraction erratum (§4)**; the article body itself is not edited (archive invariant). The article-quality CI (`article-quality.yml`) + citation checks are the gates that should have caught it — fix the gate as the root cause.
- **Duplicate publish:** de-duplicate via a PR removing the duplicate directory; regenerate `index.json`/`sitemap.xml`/`feed.xml` (the build does this).
- **Image/media or metadata/SEO issue:** correct the `metadata.json` / media in a PR; the build regenerates the derived artifacts (`og`-images via the Cloudflare worker, `index.json`, `feed.xml`, `llms-*.txt`).

## 4. Correction / unpublish / rollback — grounded in actual capability

**There is no CMS and no "unpublish API."** The capabilities that actually exist:

- **Correction (preferred) = append an erratum.** Per [`ERRATA.md`](ERRATA.md), `articles/*/article.md` are **immutable after publication**; a factual error, clarification, or **retraction** is recorded as a structured erratum (rendered as an aside), *not* by editing the article. This is the primary content-correction path.
- **Revert a bad deploy = git + rebuild.** Revert the offending commit on `main` via a normal PR; `build-and-deploy.yml` redeploys the corrected site to Pages. Never force-push the public archive.
- **Full takedown = remove the article directory + redeploy.** Deleting `articles/<slug>/` and rebuilding removes it from the site, `index.json`, `sitemap.xml`, and feeds. This **contradicts the archive-immutability posture**, so reserve it for genuine legal/security necessity (prefer a `retraction` erratum otherwise) and record the justification.
- **Takedown ≠ erasure (honest caveat).** A removed article may persist in **external archives/caches**: the repo runs `wayback-snapshot.yml` (Wayback Machine), URLs were submitted to **IndexNow** (search engines), and Git history retains the content. A takedown does not purge those — note this when assessing exposure, and pursue external removal separately if required.

## 5. CMS / external-push incident

- **No CMS to compromise** — the site is static GitHub Pages. The "publishing surface" is `main` + the Pages deploy (Pages OIDC, `id-token: write`/`pages: write` in `build-and-deploy.yml`).
- **Airtable ingestion is the one inbound content path:** `ingest-airtable*.yml` / `ingest-article.yml` pull from Airtable (via `AIRTABLE_PAT`) and **open PRs** (via `ARTICLE_INGESTION_PR_TOKEN`) — they do **not** publish directly, so a bad ingest surfaces as a reviewable PR. A compromised Airtable source or ingestion token → rotate the token (§2), close/scrutinize any open ingestion PRs, and review what merged during the window. See [`airtable-ingestion.md`](airtable-ingestion.md).
- **og-worker / Cloudflare:** the OpenGraph image worker uses `CLOUDFLARE_API_TOKEN`; a leak → rotate at Cloudflare + GitHub.

## 6. LLM / provider incident

The summary/embedding/translation tooling (`tools/`) calls multiple LLM providers (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `MINIMAX_API_KEY`).

- **Provider key compromise** → rotate (§2); review the provider's usage/billing for abuse.
- **Prompt/output leakage** → never paste prompts/outputs containing secrets into tickets; treat a leaked key in a prompt log as §2.
- **Generated content with unsupported claims** → an LLM-generated summary/translation/article that misstates facts is a content incident (§3/§4): issue an erratum/retraction and tighten the `article-quality.yml` / summary-automation gate that should have caught it.

## 7. CI / workflow compromise

1. **Revoke or rotate the affected credential.** Publishing workflows no longer hold a long-lived PAT (#388): they mint a short-lived, repository-scoped GitHub App installation token that expires in about an hour, so containment for that path is *revoking the **Articles Automation** App's installation or rotating `ARTICLES_AUTOMATION_APP_PRIVATE_KEY`*. That App is installed on this repository only and holds Contents + Pull requests read/write, so containment is bounded here — it is deliberately not the organization's recovery App, whose key must never be projected into a repository workflow. Rotate any provider secret the workflow could read (`AIRTABLE_PAT`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPL_API_KEY`, `INDEXNOW_API_KEY_ARTICLES_FAIM`) as normal.
2. **Inspect the workflow runs + artifacts** (`gh run list`, `gh run view --log`) for unexpected steps/egress/artifact contents.
3. **Supply chain — governed `@vN` policy (not a gap).** This repo **deliberately** pins actions to **major-version tags** (`actions/checkout@v6`, `actions/deploy-pages@v5`, `peter-evans/create-pull-request@v8`, …), **Dependabot-managed** (weekly version-updates + a cooldown) per [`SECURITY.md`](../SECURITY.md); the `zizmor` `unpinned-uses` audit is set to **`ref-pin`** in `.github/zizmor.yml` to honor this. So `@vN` is the **policy, not a finding** — do **NOT** SHA-pin during response (it would violate the governed convention). Tag-retargeting risk is mitigated by Dependabot + the cooldown; during response, verify the `@vN` tag resolves to the **expected** release and check for an unexpected re-point, rather than converting to a SHA.
4. **Scope.** No workflow uses `pull_request_target`; none run on self-hosted runners; the Pages deploy uses short-lived OIDC (`id-token: write`). Confirm no workflow gained write/secret scope it should not have.

## 8. Scanner finding response (full stack)

**This is a PUBLIC repo, so the FREE GitHub-native protections ARE available and enabled** (the public free tier — **not** paid GHAS): **secret scanning + push protection**, **Dependabot alerts + security updates**, and **CodeQL** code scanning. (Private-repo native scanning would need paid GHAS, which the org does not buy — that constraint does **not** apply to this public repo.) Reports live in the repo **Security** tab + each workflow's Actions run.

| Scanner | Detects | Posture |
|---|---|---|
| **gitleaks** (`gitleaks.yml`) | committed secrets | **required gate** (PR review; push/schedule hit = incident) |
| GitHub **secret scanning + push protection** | secrets (native, pre-receive) | **enabled** (free public) |
| **Dependabot** (alerts + security updates) | dependency vulns (npm + pip) | **enabled** (free public) |
| **CodeQL** | code-level weaknesses | **enabled** (free public) |
| **zizmor** (`zizmor-advisory.yml`) | Actions workflow-security | advisory (0 standing; governed `@vN` accepted via `ref-pin`) |

Triage:
1. **gitleaks** runs on **pull_request + push + weekly + dispatch**; a finding on a PR blocks via review, on `main`/schedule it is an incident.
2. **True positive → §2** (rotate; the committed value is burned).
3. **False positive →** add a scoped entry to `.gitleaks.toml` with a rationale (see the allowlist-rationale section in [`SECURITY.md`](../SECURITY.md)); do not broaden the allowlist beyond the specific match.
4. **Dependabot security alert →** triage by severity (critical/high first); prefer the auto-fix PR. Note `@cloudflare/vitest-pool-workers` pins mcp-server's vitest to v3 — a vitest semver-major ignore is configured for `/mcp-server` in `.github/dependabot.yml` with a documented lift condition.
5. **zizmor / CodeQL finding →** advisory/native triage; escalate by content (secret → §2; CI/supply-chain → §7).
6. Record the finding + disposition (§9).

## 9. Evidence-capture checklist

Captured by the Scribe, as you go:

- [ ] UTC timestamps for each milestone.
- [ ] Run IDs / commit SHAs / article slugs / gitleaks findings — **secret values redacted**.
- [ ] Commands run + sanitized output.
- [ ] Rotation timestamps + which secrets.
- [ ] Decisions + who made them (esp. any takedown vs erratum call).
- [ ] Evidence stored privately — **never** secret values in the public repo or a public issue.

## 10. Game-day / tabletop checklist

Run a tabletop periodically (e.g. quarterly) so the runbook stays exercised:

- [ ] Pick a scenario (a leaked App installation token; a bad article auto-deployed to Pages; a provider key in a CI log; a poisoned ingestion PR from Airtable; a gitleaks hit on `main`).
- [ ] Walk the relevant section **without** rotating real secrets or touching the live site — verify each referenced workflow/doc still exists + is accurate (e.g. `ERRATA.md` is still the correction path; `build-and-deploy.yml` is still the deploy).
- [ ] Time-box detection → containment (rotate / revert / erratum); note any unclear step or missing access.
- [ ] File runbook fixes as the output (this document is the artifact under test).
- [ ] Confirm the standing rules held (no secret echoed, archive immutability respected, no force-push of the public archive).
