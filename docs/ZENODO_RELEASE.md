# Zenodo Release Pipeline

This document describes how to connect the First AI Movers Article Archive to Zenodo so that every GitHub release mints a corpus-level DOI.

> **Scope:** Corpus-level DOI only. Per-article DOIs are [E34](../ROADMAP.md) and out of scope for this document.

## User-side setup (one-time)

1. **Create or log in to a Zenodo account** at [zenodo.org](https://zenodo.org).
2. **Link GitHub** in Zenodo settings:
   - Go to **Account → GitHub**.
   - Toggle **First-AI-Movers/articles** to "On".
3. **Verify the webhook** is created:
   - In the GitHub repo, go to **Settings → Webhooks**.
   - Look for a Zenodo webhook (`https://zenodo.org/api/hooks/receivers/...`).

> **Do not create a release yet.** Complete the checklist below first.

## Tag convention

Use calendar-versioning for traceability:

```text
vYYYY.MM.DD
```

Examples:
- `v2026.04.28` — snapshot on 28 April 2026
- `v2026.05.15` — snapshot on 15 May 2026

Semantic versioning (`v1.0.0`) is acceptable but less intuitive for a continuously growing archive.

## Release checklist

Before creating a GitHub release and triggering Zenodo:

- [ ] `pytest tools/tests/` — green
- [ ] `npm run test:e2e` — green
- [ ] `gitleaks` scan — green
- [ ] `geo-audit` artifact reviewed (soft gate; does not block)
- [ ] `python3 tools/normalize_tags.py --dry-run` — no unexpected changes
- [ ] `python3 tools/check_duplicate_titles.py` — no duplicates
- [ ] `python3 tools/rebuild_local.py` — completes, 910 pages expected
- [ ] `docs/CHANGELOG.md` is up to date (`python3 tools/build_changelog.py --check`)
- [ ] `CITATION.cff` fields are correct (run `python3 tools/check_citation.py`)
- [ ] `README.md` stats are current
- [ ] (Optional) Wayback snapshot submitted via `tools/wayback_snapshot.py --submit`

## Creating a release

1. On GitHub, go to **Releases → Draft a new release**.
2. Choose the tag `vYYYY.MM.DD` (create new).
3. Title: `Archive snapshot vYYYY.MM.DD`.
4. Copy the latest CHANGELOG entries into the release notes.
5. Publish the release.

Zenodo will automatically:
- Archive the repository snapshot.
- Mint a DOI.
- Deposit metadata from `CITATION.cff` if available.

## After DOI is minted

1. **Update `CITATION.cff`** with the real DOI:
   ```yaml
   doi: "10.5281/zenodo.XXXXXXX"
   ```
2. **Update `docs/CITATION.md`** — replace placeholder DOI with real one.
3. **Update `README.md`** — add Zenodo DOI badge:
   ```markdown
   [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
   ```
4. Commit and push the updates.
5. The DOI will resolve to the latest Zenodo record; previous releases keep their own versioned DOIs.

## Rollback and limitations

- **DOI records are persistent.** Once minted, a Zenodo DOI cannot be deleted. Ensure the release is intentional.
- **Do not mint test DOIs on production Zenodo.** If you need to test the full flow, use the [Zenodo Sandbox](https://sandbox.zenodo.org) with a separate test repository.
- **Zenodo archives the full repository.** Private files, `.env` files, or secrets should never be in the repo (this is already an archive invariant).
- **Metadata updates on Zenodo** require a new release; editing the existing record does not change the archived snapshot.

## Per-article DOIs (E34 infrastructure)

> **Status:** Infrastructure shipped. No per-article DOIs minted yet.

### Workflow

1. **Sandbox first:** Always test with `--sandbox` before production.
2. **One at a time:** Start with `--slug <slug>` before any batch.
3. **Dry-run preview:** `python3 tools/mint_dois.py --dry-run --slug <slug>`
4. **Reserve only:** Use `--no-publish` to reserve a DOI without making it final.
5. **Production requires explicit approval.** The tool warns loudly before production writes.

### Safety rules

- DOI field is **write-once**. Do not edit `doi` in `metadata.json` after minting.
- No bulk runs without a reviewed plan.
- Corpus-level DOI (E23) and per-article DOIs are separate systems.

## Troubleshooting

| Issue | Fix |
|---|---|
| Zenodo did not create a record | Check that the Zenodo GitHub integration is enabled for this repo. |
| DOI not showing in CITATION.cff | Update `CITATION.cff` manually after the first DOI is issued. |
| Release tag was wrong | Zenodo archives whatever was at the tag. Create a corrected release with a new tag. |
