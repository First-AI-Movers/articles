# Wayback Machine Snapshots

This document describes the Internet Archive / Wayback Machine snapshot workflow for the First AI Movers article archive.

## Purpose

Increase the permanence and public recoverability of the archive beyond GitHub Pages availability. Even if the primary hosting ever changes, the Wayback Machine preserves a browsable historical record.

## What gets snapshotted

A small, deterministic sample of public-facing URLs:

1. `https://articles.firstaimovers.com/` — home page
2. `https://articles.firstaimovers.com/sitemap.xml` — sitemap
3. `https://articles.firstaimovers.com/topics/` — topic index
4. Five stable topic hubs:
   - `/topics/ai-strategy/`
   - `/topics/ai-governance/`
   - `/topics/eu-ai-act/`
   - `/topics/ai-agents/`
   - `/topics/ai-productivity-tools/`

The list is intentionally small in v1 to avoid excessive submissions. Future versions may expand the sample.

## Running locally

### Dry run (default)

```bash
python3 tools/wayback_snapshot.py --dry-run
```

Lists the URLs that would be submitted without making any HTTP calls.

### Submit

```bash
python3 tools/wayback_snapshot.py --submit --limit 8 --sleep 2
```

- `--limit N`: cap the number of URLs (default 8)
- `--sleep SECONDS`: delay between submissions to be polite (default 2)

## CI workflow

`.github/workflows/wayback-snapshot.yml` runs:

- On **release published**
- On **workflow_dispatch** (manual trigger with optional `limit` and `sleep` inputs)

It is **not scheduled automatically** in v1. A monthly or quarterly schedule can be added later if desired.

The workflow is **not a required check** and does not block PRs or releases. It uses `continue-on-error` implicitly through script behaviour: transient Wayback failures are reported as warnings, not fatal errors.

## When to use it

- After a significant redesign or content milestone
- Before a domain or hosting change
- Periodically (quarterly) as part of an operations routine

## Rollback / disable

To stop Wayback submissions:

1. Delete `.github/workflows/wayback-snapshot.yml`
2. Or disable the workflow in **Actions → Wayback snapshot → Disable workflow**

No article content, metadata, or generated site output is affected.

## Relationship to other epics

- **E25** is archival / permanence.
- **E23** (Zenodo DOI) provides academic citation permanence.
- **E24** (analytics) tracks live traffic; Wayback tracks historical snapshots.
