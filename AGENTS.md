# AGENTS.md — First AI Movers Article Archive

Operating rules for AI agents working in this repository. One instruction surface;
`CLAUDE.md` defers to it, and [`CONTRIBUTING.md`](CONTRIBUTING.md) covers the same
ground for humans in more detail.

## What this repository is

The public archive of Dr. Hernani Costa's articles, plus the static site and the
Python tooling that builds it. The writing is the product. Everything else exists to
publish, validate, and preserve it.

`articles/` holds the source markdown and metadata; `summaries/` and `translations/`
derive from it. `tools/` is the Python build, ingestion and validation tooling, with
its suite in `tools/tests/`; `templates/` and `static/` are site assets; `tests-e2e/`
is Playwright against the built site; `mcp-server/` and `og-worker/` are the two
TypeScript surfaces; `docs/` is durable reference.

The root `*.json`, `*.xml` and `*.txt` files — `index.json`, `feed.*`, `sitemap.xml`,
`llms*.txt` — are **generated**. Never hand-edit one: change the source and rebuild.
CI compares the committed artifacts against a fresh build and fails on drift.

## Where work state lives

GitHub Issues, Projects and pull requests are the only home for what is in flight,
blocked, or next. Do not add a roadmap, a status page, a delivery ledger, a document
inventory or an archive folder — an in-repo mirror of live status goes stale and then
misleads. A superseded document is deleted; git history is the archive.

## Authority

An admitted Issue is the authorization for the work it describes. Everything needed
to reach its stated acceptance is in scope: repository writes, deletions, branches,
PRs, Issue and review-comment writes, and child work inherits that authority. There
are no authorization levels, no per-turn approval for a class of write, and no
authorization phrases — do not reintroduce them under a new name.

## Safety boundaries

These are about *effect*. They are the real limits; nothing else needs a ceremony.

- **Publishing is an operator-governed effect.** This repository is public and a
  merge to `main` deploys the site under a named author's byline. Adding, rewriting,
  retracting or re-dating an article is an editorial decision: do it because an Issue
  asks for it, never as a side effect of a tooling change. Syndication, DOI minting
  and search-engine submission are separate effects, separately authorized.
  Corrections to a published piece follow [`docs/ERRATA.md`](docs/ERRATA.md).
- **No secrets in commits or in output** — no credentials, tokens, API keys, `.env`
  contents or pre-signed URLs in files, fixtures, logs or PR text. Secret scanning
  runs in CI, but it is a net, not a permission.
- **Nothing private goes in.** This repository is public: no internal hostnames,
  private repository names, machine paths, unpublished drafts, or client, partner and
  case material.
- **No self-approval**, and no merging around the gate.
- **Workflow changes are judged by the merge gate.** A `.github/workflows/**` change
  must declare `permissions` (never `write-all`), avoid `pull_request_target`, pin
  every non-local `uses:` to a 40-hex commit SHA, and keep `${{ secrets.* }}` and
  author-controlled text out of `run:` bodies. Satisfy those or leave the file alone.

## Building and testing

Python 3.14 is the canonical runtime; `.python-version` is the source of truth.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r tools/requirements.txt pytest

python3 -m pytest tools/tests -q            # Python suite
python3 tools/rebuild_local.py              # rebuild site/ and generated artifacts
python3 tools/check_generated_artifacts.py  # fail on generated-artifact drift
npm run test:e2e                            # Playwright, needs a built site/
```

Run the tests for the surface you touched, not the whole suite, unless the change is
broad. A new Python test goes in `tools/tests/test_<module>.py`, stays focused on one
production module, and takes shared constants from `tools/tests/_fixtures.py`.

## PR lifecycle

Squash-only, zero required approvals, one required check: `aeos-merge-ready`.

1. Branch from fresh `origin/main`; smallest coherent unit.
2. Prove it — run the tests for the surface you changed. If a change is docs-only and
   no suite covers it, say so plainly instead of claiming a proof you did not run.
3. Commit using [Conventional Commits](https://www.conventionalcommits.org/), and
   open the PR **ready**, never draft.
4. Arm squash auto-merge in the same step, while the gate is still pending — GitHub
   refuses to arm a PR that is already mergeable.
5. Do not wait and do not poll CI. Move to the next unit. Post-merge smoke runs by
   itself; a failure there is a new Issue, not a reopened decision.

## Durable canon

[`README.md`](README.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) ·
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) ·
[`docs/OPERATIONS.md`](docs/OPERATIONS.md) (runbooks) ·
[`docs/decisions/`](docs/decisions/) (accepted ADRs).
