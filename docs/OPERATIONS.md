# Operations

Runbooks for common operational tasks in the First AI Movers article archive.

## Adding an Article Manually

Use this when an article needs to land outside the normal ingestion flows.

1. Create the folder: `mkdir articles/YYYY-MM-DD-slug`
2. Write `articles/YYYY-MM-DD-slug/article.md` with front matter:
   ```markdown
   ---
   title: "Article Title"
   published_date: "YYYY-MM-DD"
   canonical_url: "https://..."
   tags:
     - tag one
     - tag two
   ---

   Article body in Markdown.
   ```
3. Write `articles/YYYY-MM-DD-slug/metadata.json` matching the schema in `tools/article_schema.json`.
4. Run `python3 tools/normalize_tags.py --dry-run` to preview tag mapping.
5. Run `python3 tools/check_duplicate_titles.py` to verify no duplicate title exists.
6. Run `python3 tools/rebuild_local.py` to regenerate all derived artifacts.
7. Commit and open a PR. Do not push directly to `main`.

## Troubleshooting a Failed Build

### Build fails in `build-and-deploy.yml`

1. Check the **Normalize tags** step output for validation errors.
2. Check the **Rebuild** step for Python tracebacks.
3. Common causes:
   - Invalid `metadata.json` (missing required field, malformed date)
   - Duplicate article title (run `tools/check_duplicate_titles.py`)
   - Malformed front matter in `article.md`
4. Fix the source data, commit, and push. The workflow will re-run.

### Site deploys but looks wrong

1. Check that `site/` was generated locally: `python3 tools/rebuild_local.py`
2. Serve locally: `python3 -m http.server 4173 --directory site`
3. Open `http://localhost:4173` and inspect.
4. Check browser console for 404s on CSS/JS assets.
5. If templates changed, ensure `rebuild_local.py` completed without errors.

### E2E tests fail

1. Run E2E locally: `npm run test:e2e`
2. Check the `test-results/` directory for traces and screenshots.
3. Common causes:
   - Site not built before E2E run
   - Static server port conflict
   - Template change broke a selector

## Rotating Secrets

### Airtable ingestion secrets

1. Go to Repository Settings → Secrets and variables → Actions.
2. Update:
   - `AIRTABLE_PAT`
   - `AIRTABLE_BASE_ID`
   - `AIRTABLE_TABLE_NAME`
3. Run `.github/workflows/ingest-airtable.yml` manually (`workflow_dispatch`) to verify connectivity.
4. Check the dry-run output before enabling write mode.

### IndexNow key

1. Update `INDEXNOW_API_KEY_ARTICLES_FAIM` in repository secrets.
2. The key file is generated dynamically during build; no committed file to update.
3. Verify with `python3 tools/submit_indexnow.py --dry-run`.

### External publishing sender token

1. Sender generates a fine-grained PAT with `actions:write` scoped to this repo only.
2. Sender stores the PAT in their own repository secrets.
3. No changes needed in this repository.

## Running Ingestion Dry-Run vs Write Mode

### Airtable (E20a)

- **Dry-run (default):** `INGEST_DRY_RUN` is unset or set to `1`. Workflow classifies records but does not write files.
- **Write mode:** Set repository variable `INGEST_DRY_RUN=0`. Workflow will create article folders and open PRs.
- **Local dry-run:** `python3 tools/ingest_airtable.py --dry-run`
- **Local write test:** `python3 tools/ingest_airtable.py --write --record-id <id>` (test with one record first)

### External payload (E18)

- Always dry-run by default; `--write` flag required to create files.
- Local test: `cat fixture.json | python3 tools/ingest_article.py --write`
- CI test: Run `.github/workflows/ingest-article.yml` via `workflow_dispatch` (uses fixture payload; close the resulting PR without merging).

## Recovering from a Bad Deployment

1. **Identify the bad commit** via GitHub Actions history.
2. **Revert the source commit** (the article or tool change that caused the issue).
3. The `build-and-deploy.yml` workflow will rebuild and redeploy automatically.
4. If the build itself is broken, fix the build code in a branch, merge via PR, and let CI redeploy.
5. **GitHub Pages rollback:** If needed, disable Pages temporarily in Settings → Pages, fix the issue, then re-enable.

## Updating Topic Intros

Topic hub pages show curated intros from `tools/topic_intros.json`.

1. Edit `tools/topic_intros.json` to add or update a topic intro.
2. Run `python3 tools/rebuild_local.py`.
3. Verify the topic page renders correctly.
4. Commit and open a PR.

## Checking Archive Health

Run these locally to verify archive integrity:

```bash
python3 tools/check_duplicate_titles.py
python3 tools/normalize_tags.py --dry-run
python3 tools/rebuild_local.py
python3 -m pytest tools/tests -q
npm run test:e2e
```

All should pass with no unexpected changes.

## Test Suite Quick Reference

| Layer | Command | Count |
|---|---|---|
| Unit / integration | `pytest tools/tests` | ~303 |
| E2E | `npm run test:e2e` | 32 |

Optional dependencies: `openai`, `python-dotenv` (for `TestAddTldr`). These are deselected in CI if absent.
