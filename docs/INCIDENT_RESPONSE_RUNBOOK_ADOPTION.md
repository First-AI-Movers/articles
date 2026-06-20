# Incident-Response Runbook Adoption — Delivery Note

**Date:** 2026-06-20 (ARTICLES-IR-RUNBOOK-ADOPT-A) · **Lane:** Security

Closes the Domain-F incident-response gap for the article archive: the repo had a comprehensive [`SECURITY.md`](../SECURITY.md) (reporting policy, no-secrets policy, gitleaks, Airtable-trigger security) but **no consolidated incident-response runbook**.

## What landed

- **`docs/INCIDENT_RESPONSE_RUNBOOK.md`** — the operational response, all required sections: triage/severity; secret-token leak (rotate-at-source + the actual secret names + gitleaks); publishing/content incident (accidental Pages deploy, bad article, wrong citation, duplicate, media/SEO); the **correction/unpublish/rollback** path grounded in real capability; CMS/external-push (no CMS — Airtable ingestion opens PRs); LLM/provider; CI/workflow compromise; gitleaks finding response; evidence capture; tabletop.
- **`SECURITY.md`** — a one-line pointer to the runbook (no other change).
- **This delivery note.**

## Grounded in the repo's real posture (no invented capabilities)

- **Static public archive on GitHub Pages** (`articles.firstaimovers.com`) — no backend/DB/auth, per SECURITY.md.
- **Correction = append an erratum** ([`ERRATA.md`](ERRATA.md)): published `article.md` are **immutable** (archive invariant, `CONTRIBUTING.md`) — corrections/retractions are appended, not edited. **No CMS unpublish API** was invented; "takedown" is documented as git-remove + redeploy, reserved for legal/security necessity, with the honest caveat that Wayback / IndexNow / git history / caches persist (takedown ≠ erasure).
- **Publish = push→`build-and-deploy.yml`→Pages** (path-scoped to `main`); Airtable ingestion opens **PRs** (reviewable), it does not publish directly.
- **Secrets named from the actual workflows** — `AIRTABLE_PAT`, `ANTHROPIC_/OPENAI_/DEEPSEEK_/MINIMAX_API_KEY`, `CLOUDFLARE_API_TOKEN`, `INDEXNOW_API_KEY_ARTICLES_FAIM` (public-by-design), and the elevated `ARTICLE_INGESTION_PR_TOKEN` PAT — with the list flagged non-exhaustive.
- **gitleaks** runs on PR + push + weekly + dispatch; the runbook routes findings to rotate-or-allowlist.
- **CI supply chain** — the repo's actions are mutable tags (not SHA-pinned) → flagged in the runbook as a live tag-retargeting risk + a hardening follow-up (a natural `ARTICLES-WORKFLOW-ACTION-PINNING-A`).
- Contact reuses the existing `info@firstaimovers.com` from SECURITY.md; no new contact invented.

## Safety / scope

Docs-only. No live publish, no provider/API call, no Airtable/IndexNow/Cloudflare call, no secret read, no workflow/ruleset/required-check change, no production mutation.
