## Summary

<!-- What does this PR change and why? -->

## Business outcome

<!-- What problem does this solve for readers, contributors, or operators? -->

## Changed files

<!-- List every file that changed. Mark source files vs generated artifacts. -->

| File | Type | Notes |
|---|---|---|

## Source vs generated artifacts

<!-- Confirm you did not hand-edit any generated artifacts. -->

- [ ] I have not hand-edited `index.json`, `sitemap.xml`, `feed.xml`, `feed.json`, `llms-full.txt`, `llms-recent.txt`, or `README.md` stats.
- [ ] Any changes to generated artifacts came from running `tools/rebuild_local.py`.
- [ ] Any changes to `articles/*/metadata.json` came from running `tools/normalize_tags.py`.

## Validation checklist

- [ ] **Code-reviewed** — logic inspected for correctness and minimalism.
- [ ] **Test-proven** — `python3 -m pytest tools/tests -v` passes.
- [ ] **Dry-run proven** — `python3 tools/normalize_tags.py --dry-run` passes.
- [ ] **Rebuild proven** — `python3 tools/rebuild_local.py` completes without error.
- [ ] **Git status clean** — `git status --short` shows only expected changes.

## Content / metadata / canonical checklist

<!-- Check all that apply. Remove sections that do not apply. -->

- [ ] No article text (`article.md`) was edited unless explicitly intended.
- [ ] No `canonical_url` was changed unless explicitly intended.
- [ ] No `metadata.json` was hand-edited unless explicitly intended.
- [ ] Duplicate-title gate was checked: `python3 tools/check_duplicate_titles.py`.

## CI and deployment

- [ ] CI passes (or expected failures are documented).
- [ ] Workflow changes were inspected for permission and trigger safety.

## Live site / browser proof

<!-- Only check if this PR changes visible site behavior. -->

- [ ] Live site checked at `articles.firstaimovers.com` (relevant paths).
- [ ] Browser rendering verified (topic hubs, article pages, home, dark mode).

## Risks and follow-ups

<!-- List anything that could break, needs monitoring, or requires a follow-up PR. -->
