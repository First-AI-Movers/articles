# Generated Artifacts Policy

**Status:** Active policy — enforced by CI.  
**Date:** 2026-05-02  
**Scope:** Every file in this repo that is produced by tooling rather than authored by hand.

---

## 1. Policy

1. **Source files are canonical.**  
   `articles/*/article.md`, `articles/*/metadata.json`, `templates/`, `static/`, and configuration files are the source of truth.

2. **Generated artifacts are produced by tooling.**  
   They must never be hand-edited. If an artifact needs to change, update the source and regenerate.

3. **Committed generated artifacts must be updated via normal PRs.**  
   No workflow may push regenerated files directly to protected `main`.

4. **Pages deploys from a freshly built `site/` directory.**  
   The deployed site is always correct because it is built from source on every push to `main`. Committed artifacts may lag until a maintainer runs `rebuild_local.py` locally and opens a PR.

5. **Drift is detected, not silently tolerated.**  
   CI runs `tools/check_generated_artifacts.py` on every PR and push to `main`. If a committed artifact is stale, the check fails and names the offending file.

---

## 2. Artifact inventory

| Artifact | Produced by | Committed? | Used by Pages? | Drift risk | Update method | Check |
|---|---|---|---|---|---|---|
| `index.json` | `rebuild_local.py` | Yes | Yes (mirrored into `site/`) | Medium | Local rebuild + PR | `check_generated_artifacts.py` |
| `sitemap.xml` | `rebuild_local.py` | Yes | Yes (mirrored into `site/`) | Medium | Local rebuild + PR | `check_generated_artifacts.py` |
| `feed.xml` | `rebuild_local.py` | Yes | Yes (mirrored into `site/`) | Medium | Local rebuild + PR | `check_generated_artifacts.py` |
| `feed.json` | `rebuild_local.py` | Yes | Yes (mirrored into `site/`) | High (was never in the pre-`14ba82b9` auto-commit list) | Local rebuild + PR | `check_generated_artifacts.py` |
| `llms.txt` | `rebuild_local.py` | Yes | Yes (mirrored into `site/`) | Medium | Local rebuild + PR | `check_generated_artifacts.py` |
| `llms-full.txt` | `rebuild_local.py` | Yes | Yes (mirrored into `site/`) | Medium | Local rebuild + PR | `check_generated_artifacts.py` |
| `llms-recent.txt` | `rebuild_local.py` | Yes | Yes (mirrored into `site/`) | Medium | Local rebuild + PR | `check_generated_artifacts.py` |
| `README.md` | `rebuild_local.py` | Yes | No | Medium | Local rebuild + PR | `check_generated_artifacts.py` |
| `citation_graph.json` | `build_citation_graph.py` | Yes | Yes (loaded by site build) | Medium | Manual run + PR | `build_citation_graph.py --check` |
| `docs/CHANGELOG.md` | `build_changelog.py` | Yes | No | Low | Manual run + PR | `build_changelog.py --check` |
| `embeddings.parquet` | `build_embeddings.py` | Yes | No | Low | Weekly CI opens PR if changed | `build-embeddings.yml` |
| `site/` | `rebuild_local.py` | **No** (gitignored) | Yes (deployed to Pages) | N/A | Fresh CI build on every push | N/A — never committed |

### Notes

- **Drift risk = High** on `feed.json` because it was missing from the auto-commit list even before `14ba82b9` removed the commit step. It is now covered by the same check as the other artifacts.
- **Drift risk = Low** on `docs/CHANGELOG.md` and `embeddings.parquet` because they have their own dedicated update workflows and are not regenerated on every site build.
- **`site/`** is intentionally gitignored. The Build & Deploy workflow rebuilds it from scratch on every push, so drift is impossible.

---

## 3. How to regenerate artifacts locally

```bash
# Install dependencies if you haven't already
pip install -r tools/requirements.txt

# Regenerate all artifacts in place
python3 tools/rebuild_local.py

# Verify nothing unexpected changed
git diff --stat

# Open a PR with the regenerated artifacts
git checkout -b docs/regenerate-artifacts
git add index.json sitemap.xml feed.xml feed.json llms.txt llms-full.txt llms-recent.txt README.md
git commit -m "chore: regenerate artifacts after <describe source change>"
```

---

## 4. Drift check

### Local

```bash
python3 tools/check_generated_artifacts.py
```

Output:
- `[artifact-check] PASSED: all artifacts current` — exit 0
- `[artifact-check] FAILED: committed artifacts are stale` — exit 1, followed by the list of drifted files.

### CI

The `.github/workflows/generated-artifacts.yml` workflow runs the check on every PR and push to `main`. It does **not** auto-commit fixes.

---

## 5. What the check does (and does not do)

**Does:**
- Back up the 8 committed artifacts listed above.
- Run `rebuild_local.py`.
- Compare each artifact byte-for-byte with its backup.
- Restore the original artifacts so the working tree is unchanged.
- Fail and name the drifted file(s).

**Does not:**
- Modify the working tree permanently.
- Commit or push anything.
- Check `citation_graph.json` or `docs/CHANGELOG.md` (they have their own checks).
- Check `site/` (it is gitignored and rebuilt fresh in CI).
- Run DeepL, OpenAI, or any external API.

---

## 6. History

- **Before commit `14ba82b9`** — `build-and-deploy.yml` auto-committed regenerated artifacts to `main` after every build. This bypassed branch protection and was removed.
- **After commit `14ba82b9`** — Artifacts are no longer auto-committed. The deployed site remains correct, but committed files can lag.
- **PR #136 (B3)** — Refreshed `docs/CHANGELOG.md` and updated `docs/OPERATIONS.md` to reflect current workflows.
- **This document (B4)** — Introduces the explicit policy, the drift check, and CI enforcement.
