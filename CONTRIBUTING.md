# Contributing to the First AI Movers Article Archive

This repository is the **canonical, open-access archive** of all articles published by [First AI Movers](https://firstaimovers.com). It is maintained as a public artifact for researchers, developers, AI systems, and readers.

## Repository purpose

- Store every article as plain Markdown with structured metadata.
- Generate machine-readable catalogs (`index.json`, `feed.xml`, `feed.json`, `sitemap.xml`).
- Publish a static HTML site to [articles.firstaimovers.com](https://articles.firstaimovers.com).
- Serve as the source of truth for canonical URLs, topic hubs, and LLM-ingestion corpora (`llms-full.txt`, `llms-recent.txt`).

## Archive invariants

These rules must never be broken by any contribution:

1. **Article text is immutable once published.** Do not edit `article.md` files after publication. Typos, corrections, and updates are handled by publishing a new article.
2. **Canonical URLs are permanent.** The `canonical_url` in `metadata.json` points to the primary publishing property (Radar, Insights, LinkedIn, etc.) and must never change.
3. **Generated artifacts are never hand-edited.** `index.json`, `sitemap.xml`, `feed.xml`, `feed.json`, `llms-full.txt`, `llms-recent.txt`, and `README.md` stats patches are rebuilt by `tools/rebuild_local.py` only.
4. **No secrets or private drafts.** Every folder under `articles/` is public. Do not commit API keys, `.env` files, or unpublished drafts.
5. **No generated images.** The archive does not produce per-article OG images. Image plumbing exists in templates but remains empty unless canonical publishers already provide images.

## Source files vs generated artifacts

| Source (edit by hand) | Generated (rebuilt by tooling) |
|---|---|
| `articles/*/article.md` | `index.json` |
| `articles/*/metadata.json` | `sitemap.xml` |
| `tools/topic_intros.json` | `feed.xml` |
| `templates/*.html.j2` | `feed.json` |
| `static/style.css` | `llms-full.txt` |
| `README.md` (content) | `llms-recent.txt` |
| `ABOUT.md` | `README.md` (stats patches only) |
| `CITATION.cff` | `site/` (entire directory) |
| | `embeddings.parquet` |

**Rule of thumb:** If a file is listed in the `rebuild_local.py` commit step, it is generated and must not be hand-edited.

## Local setup

```bash
# Clone
git clone https://github.com/First-AI-Movers/articles.git
cd articles

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r tools/requirements.txt
pip install pytest
```

## Validation commands

Run these before opening any PR:

```bash
# Run the full test suite
python3 -m pytest tools/tests -v

# Validate tag normalization (dry-run)
python3 tools/normalize_tags.py --dry-run

# Rebuild all generated artifacts and static site
python3 tools/rebuild_local.py

# Check for duplicate titles
python3 tools/check_duplicate_titles.py

# Run browser-level E2E tests (requires built site/ and Playwright browser install)
npm run test:e2e

# Verify PWA assets are present after rebuild
python3 -m pytest tools/tests/test_pwa.py -v

# Verify git status is clean (or only shows expected generated changes)
git status --short
```

## IndexNow (Bing/Yandex discovery)

The archive supports [IndexNow](https://www.indexnow.org/) for notifying Bing, Yandex, and participating search engines when pages change.

- **Key source:** Doppler / GitHub secret `INDEXNOW_API_KEY_ARTICLES_FAIM` (public proof-of-host ownership, not a secret).
- **Live key URL:** `https://articles.firstaimovers.com/<key>.txt` — generated during `rebuild_local.py` from the env var.
- **Dry-run:** `python3 tools/submit_indexnow.py --dry-run` — shows payload without submitting.
- **Live submission:** `python3 tools/submit_indexnow.py` — submits the 80 archive URLs to `api.indexnow.org`.
- The script reads `sitemap.xml`, filters to `articles.firstaimovers.com` indexable pages only, and validates the URL set before submission.
- The CI workflow runs `--dry-run` after every deploy (non-blocking).
- For local testing, set `INDEXNOW_API_KEY_ARTICLES_FAIM` or `INDEXNOW_API_KEY` in your environment, or use Doppler:

  ```bash
  doppler run -- python3 tools/rebuild_local.py
  doppler run -- python3 tools/submit_indexnow.py --dry-run
  ```

- **Reserved env vars for future multi-client support:**
  - `INDEXNOW_API_KEY_RADAR_FAIM` — `radar.firstaimovers.com`
  - `INDEXNOW_API_KEY_COREVENTURES` — domain TBD

## Search visibility monitoring

See [`docs/search-visibility-monitoring.md`](docs/search-visibility-monitoring.md) for the weekly GSC/Bing/IndexNow checklist, metrics template, escalation rules, and bot-access validation commands.

## PR workflow

1. **Branch from `main`.**
2. **Make the smallest change** that achieves the goal.
3. **Run validation commands** locally.
4. **Commit** with [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat(...)` — new features
   - `fix(...)` — bug fixes
   - `docs(...)` — documentation changes
   - `test(...)` — test additions/changes
   - `refactor(...)` — code refactoring
   - `chore(...)` — tooling, dependencies, cleanup
5. **Push** and open a PR.
6. **Fill out the PR template.** Every PR must declare proof levels (code-reviewed, test-proven, CI-proven, etc.).
7. **Do not merge your own PR** unless explicitly authorized.

### Analytics changes

Changes to analytics scripts, tracking endpoints, or privacy-related configuration require explicit privacy review. See [`docs/ANALYTICS.md`](docs/ANALYTICS.md) for the current setup and rollback procedure.

### Comments moderation

Comments are powered by Giscus and stored in GitHub Discussions. Moderation (hiding, locking, or deleting comments) is handled through the GitHub Discussions UI, not through article markdown or repository changes. See [`docs/COMMENTS.md`](docs/COMMENTS.md) for setup and rollback.

### Owner review

`.github/CODEOWNERS` requires owner (`@hpcosta`) approval for changes to:
- `/articles/` — archive content
- `/tools/` — generation logic
- `/templates/` and `/static/` — site assets
- `/.github/` — CI/CD configuration
- `/tests-e2e/` — browser tests (visual regression baselines live here; update with `--update-snapshots` after intentional design changes)
- `/tools/geo_audit.py` — GEO audit for AI-citation friendliness (diagnostic; does not edit articles)
- `/package.json` and `/package-lock.json`

### Branch protection expectations

The repository expects the following branch protection rules on `main`:
- **Pull request required** — no direct pushes.
- **Status checks required** — `test` and `e2e` workflows must pass.
- **No force push** — history must remain linear and recoverable.
- **Linear history preferred** — squash-merge or rebase-merge.
- **Green CI is the merge gate** — manual reviews are encouraged for risky changes but not required for every trusted-owner PR.

These are documented expectations; verify in repository Settings → Branches.

## Commit conventions

- Use imperative mood: `feat(hardening): add duplicate-title gate`, not `added gate`.
- Scope is optional but encouraged: `feat(site)`, `fix(tools)`, `docs(roadmap)`.
- For generated-artifact rebuilds committed by CI, the bot uses `"Rebuild derived artifacts"`.

## Metadata, topics, and tags

- **Tags** (`metadata.json` `tags`) are free-form historical keywords. Leave them untouched.
- **Topics** (`metadata.json` `topics`) are canonical values derived from tags via `tools/normalize_tags.py` and `tools/tag_aliases.json`. Do not hand-edit topics.
- **Canonical topics** live in `tools/canonical_topics.json`. Adding a new canonical topic requires updating both `canonical_topics.json` and `tag_aliases.json`.
- **Services** (`metadata.json` `first_ai_movers_services`) are normalized to a closed set: `ai-strategy`, `fractional-caio`, `automation-design`, `compliance-audit`, `ai-literacy-training`.
- **String fields** (`title`, `slug`, `canonical_url`, `folder`) are whitespace-normalized by `normalize_tags.py`.

## Canonical URL rules

- Every article **must** have a `canonical_url` pointing to its primary publishing property.
- Allowed first-party hosts: `firstaimovers.com`, `www.firstaimovers.com`, `radar.firstaimovers.com`, `insights.firstaimovers.com`, `voices.firstaimovers.com`.
- Third-party hosts (LinkedIn, Medium) are accepted in `metadata.json` but are excluded from `sitemap.xml`.
- The archive's local article pages (`/articles/<slug>/`) are `noindex,follow` and declare an external `rel=canonical`. They are **not** in the sitemap.

## Duplicate-title gate

The duplicate-title CI gate (`tools/check_duplicate_titles.py`) is **blocking**. All 6 historical duplicate title pairs were disambiguated in E19. The workflow no longer uses `continue-on-error: true`.

## External publishing

The archive accepts articles from external publishing platforms via a controlled pipeline:

- **Generic push:** `repository_dispatch` event `new-article` triggers `.github/workflows/ingest-article.yml`, which validates the payload, writes files, rebuilds artifacts, and opens a PR. See [`docs/EXTERNAL_PUBLISHING.md`](docs/EXTERNAL_PUBLISHING.md) for the full contract.
- **Airtable cron:** `.github/workflows/ingest-airtable.yml` polls Airtable on a schedule and opens PRs for new records.

In both cases:
- **No direct push to `main`.** All ingestion creates a PR for review.
- **Validation runs before PR creation:** schema check, tag normalization, duplicate-title gate, pytest, rebuild.
- **Secrets live in GitHub Encrypted Secrets only.** Never pass tokens or keys in payload text.

## No secrets or private drafts

- Do not commit `.env`, API keys, or tokens.
- Do not commit unfinished article drafts. Every `articles/*/article.md` is public the moment it is pushed.
- The CI workflow has `contents: write` permission only to commit regenerated artifacts. It does not push to external APIs.
- Ingestion workflows use `secrets.GITHUB_TOKEN` by default. PRs created with this token do **not** trigger downstream `push`/`pull_request` workflows (GitHub recursion prevention). An optional `ARTICLE_INGESTION_PR_TOKEN` secret can be configured to enable automatic CI on ingestion PRs.

## Reporting proof levels

Every PR must report which proof levels were validated. Use this checklist in the PR description:

- [ ] **Code-reviewed** — logic inspected for correctness and minimalism.
- [ ] **Content-reviewed** — article text, metadata, or topic intros checked.
- [ ] **Metadata-reviewed** — `metadata.json` fields validated.
- [ ] **Test-proven** — `pytest` passes locally.
- [ ] **Generated-artifact-proven** — `rebuild_local.py` output inspected.
- [ ] **CI-proven** — GitHub Actions passes.
- [ ] **URL/canonical-proven** — canonical links, sitemap, feed URLs verified.
- [ ] **Browser/Pages-proven** — live site or browser checked (only when relevant).

## Questions?

Open an issue or contact **info@firstaimovers.com**.
